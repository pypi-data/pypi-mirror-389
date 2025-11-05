"""
Bulk executor service for database operations.

This service coordinates bulk database operations with validation and MTI handling.
"""

import logging

from django.db import transaction
from django.db.models import AutoField, ForeignKey, Case, When, Value
from django.db.models.constants import OnConflict
from django.db.models.functions import Cast

from django_bulk_hooks.operations.field_utils import (
    get_field_value_for_db,
    collect_auto_now_fields_for_inheritance_chain,
    pre_save_auto_now_fields,
)
from django_bulk_hooks.helpers import tag_upsert_metadata

logger = logging.getLogger(__name__)


class BulkExecutor:
    """
    Executes bulk database operations.

    This service coordinates validation, MTI handling, and actual database
    operations. It's the only service that directly calls Django ORM methods.

    Dependencies are explicitly injected via constructor.
    """

    def __init__(self, queryset, analyzer, mti_handler, record_classifier):
        """
        Initialize bulk executor with explicit dependencies.

        Args:
            queryset: Django QuerySet instance
            analyzer: ModelAnalyzer instance (replaces validator + field_tracker)
            mti_handler: MTIHandler instance
            record_classifier: RecordClassifier instance
        """
        self.queryset = queryset
        self.analyzer = analyzer
        self.mti_handler = mti_handler
        self.record_classifier = record_classifier
        self.model_cls = queryset.model

    def _handle_upsert_metadata_tagging(
        self, result_objects, objs, update_conflicts, unique_fields, existing_record_ids=None, existing_pks_map=None
    ):
        """

        Handle classification and metadata tagging for upsert operations.



        This centralizes the logic that was duplicated between MTI and non-MTI paths.



        Args:

            result_objects: List of objects returned from the bulk operation

            objs: Original list of objects passed to bulk_create

            update_conflicts: Whether this was an upsert operation

            unique_fields: Fields used for conflict detection

            existing_record_ids: Pre-classified existing record IDs (optional)

            existing_pks_map: Pre-classified existing PK mapping (optional)



        Returns:

            None - modifies result_objects in place with metadata

        """

        if not (update_conflicts and unique_fields):
            return

        # Classify records if not already done

        if existing_record_ids is None or existing_pks_map is None:
            existing_record_ids, existing_pks_map = self.record_classifier.classify_for_upsert(objs, unique_fields)

        # Tag the metadata
        tag_upsert_metadata(result_objects, existing_record_ids, existing_pks_map)

    def bulk_create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
        existing_record_ids=None,
        existing_pks_map=None,
        **kwargs,
    ):
        """
        Execute bulk create operation.

        NOTE: Coordinator is responsible for validation before calling this method.
        This executor trusts that inputs have already been validated.

        Args:
            objs: List of model instances to create (pre-validated)
            batch_size: Number of objects to create per batch
            ignore_conflicts: Whether to ignore conflicts
            update_conflicts: Whether to update on conflict
            update_fields: Fields to update on conflict
            unique_fields: Fields to use for conflict detection
            **kwargs: Additional arguments

        Returns:
            List of created objects
        """
        if not objs:
            return objs

        # Check if this is an MTI model and route accordingly
        if self.mti_handler.is_mti_model():
            # Use pre-classified records if provided, otherwise classify now
            if existing_record_ids is None or existing_pks_map is None:
                existing_record_ids = set()
                existing_pks_map = {}
                if update_conflicts and unique_fields:
                    # For MTI, find which model has the unique fields and query THAT model
                    # This handles the schema migration case where parent exists but child doesn't
                    query_model = self.mti_handler.find_model_with_unique_fields(unique_fields)
                    logger.info(f"MTI upsert: querying {query_model.__name__} for unique fields {unique_fields}")

                    existing_record_ids, existing_pks_map = self.record_classifier.classify_for_upsert(
                        objs, unique_fields, query_model=query_model
                    )
                    logger.info(
                        f"MTI Upsert classification: {len(existing_record_ids)} existing, {len(objs) - len(existing_record_ids)} new"
                    )
                    logger.info(f"existing_record_ids: {existing_record_ids}")
                    logger.info(f"existing_pks_map: {existing_pks_map}")

            # Build execution plan with classification results
            plan = self.mti_handler.build_create_plan(
                objs,
                batch_size=batch_size,
                update_conflicts=update_conflicts,
                update_fields=update_fields,
                unique_fields=unique_fields,
                existing_record_ids=existing_record_ids,
                existing_pks_map=existing_pks_map,
            )
            # Execute the plan
            result = self._execute_mti_create_plan(plan)

        else:
            # Non-MTI model - use Django's native bulk_create
            result = self._execute_bulk_create(
                objs,
                batch_size,
                ignore_conflicts,
                update_conflicts,
                update_fields,
                unique_fields,
                **kwargs,
            )

        # Unified upsert metadata handling for both paths
        self._handle_upsert_metadata_tagging(result, objs, update_conflicts, unique_fields, existing_record_ids, existing_pks_map)

        return result

    def _execute_bulk_create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
        **kwargs,
    ):
        """
        Execute the actual Django bulk_create.

        This is the only method that directly calls Django ORM.
        We must call the base Django QuerySet to avoid recursion.
        """
        from django.db.models import QuerySet

        # Create a base Django queryset (not our HookQuerySet)
        base_qs = QuerySet(model=self.model_cls, using=self.queryset.db)

        return base_qs.bulk_create(
            objs,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )

    def bulk_update(self, objs, fields, batch_size=None):
        """
        Execute bulk update operation.

        NOTE: Coordinator is responsible for validation before calling this method.
        This executor trusts that inputs have already been validated.

        Args:
            objs: List of model instances to update (pre-validated)
            fields: List of field names to update
            batch_size: Number of objects to update per batch

        Returns:
            Number of objects updated
        """
        if not objs:
            return 0

        # Ensure auto_now fields are included and pre-saved for all models
        # This handles both MTI and non-MTI models uniformly (SOC & DRY)
        fields = list(fields)  # Make a copy so we can modify it

        # Get models to check - for MTI, check entire inheritance chain
        if self.mti_handler.is_mti_model():
            models_to_check = self.mti_handler.get_inheritance_chain()
        else:
            models_to_check = [self.model_cls]

        # Use unified auto-now field handling
        from django_bulk_hooks.operations.field_utils import handle_auto_now_fields_for_inheritance_chain

        auto_now_fields = handle_auto_now_fields_for_inheritance_chain(models_to_check, objs, for_update=True)

        # Add auto_now fields to the update list if not already present
        for auto_now_field in auto_now_fields:
            if auto_now_field not in fields:
                fields.append(auto_now_field)

        # Check if this is an MTI model and route accordingly
        if self.mti_handler.is_mti_model():
            logger.info(f"Detected MTI model {self.model_cls.__name__}, using MTI bulk update")
            # Build execution plan (fields already have auto_now included)
            plan = self.mti_handler.build_update_plan(objs, fields, batch_size=batch_size)
            # Execute the plan
            return self._execute_mti_update_plan(plan)

        # Non-MTI model - use Django's native bulk_update
        # Validation already done by coordinator
        from django.db.models import QuerySet

        base_qs = QuerySet(model=self.model_cls, using=self.queryset.db)
        return base_qs.bulk_update(objs, fields, batch_size=batch_size)

    # ==================== MTI PLAN EXECUTION ====================

    def _execute_mti_create_plan(self, plan):
        """
        Execute an MTI create plan.

        This is where ALL database operations happen for MTI bulk_create.
        Handles both new records (INSERT) and existing records (UPDATE) for upsert.

        Args:
            plan: MTICreatePlan object from MTIHandler

        Returns:
            List of created/updated objects with PKs assigned
        """
        from django.db.models import QuerySet as BaseQuerySet

        if not plan:
            return []

        with transaction.atomic(using=self.queryset.db, savepoint=False):
            # Step 1: Upsert all parent objects level by level using Django's native upsert
            parent_instances_map = {}  # Maps original obj id() -> {model: parent_instance}

            for parent_level in plan.parent_levels:
                # Use base QuerySet to avoid recursion
                base_qs = BaseQuerySet(model=parent_level.model_class, using=self.queryset.db)

                # Build bulk_create kwargs
                bulk_kwargs = {"batch_size": len(parent_level.objects)}

                if parent_level.update_conflicts:
                    # Let Django handle the upsert - it will INSERT or UPDATE as needed
                    bulk_kwargs["update_conflicts"] = True
                    bulk_kwargs["unique_fields"] = parent_level.unique_fields

                    # Filter update fields to only those that exist in this parent model
                    parent_model_fields = {field.name for field in parent_level.model_class._meta.local_fields}
                    filtered_update_fields = [field for field in parent_level.update_fields if field in parent_model_fields]
                    if filtered_update_fields:
                        bulk_kwargs["update_fields"] = filtered_update_fields

                # Perform the upsert - Django handles INSERT vs UPDATE automatically
                upserted_parents = base_qs.bulk_create(parent_level.objects, **bulk_kwargs)

                # Copy generated fields back to parent objects
                for upserted_parent, parent_obj in zip(upserted_parents, parent_level.objects):
                    for field in parent_level.model_class._meta.local_fields:
                        # Use attname for ForeignKey fields to avoid triggering database queries
                        field_attr = field.attname if isinstance(field, ForeignKey) else field.name
                        upserted_value = getattr(upserted_parent, field_attr, None)
                        if upserted_value is not None:
                            setattr(parent_obj, field_attr, upserted_value)

                    parent_obj._state.adding = False
                    parent_obj._state.db = self.queryset.db

                # Map parents back to original objects
                for parent_obj in parent_level.objects:
                    orig_obj_id = parent_level.original_object_map[id(parent_obj)]
                    if orig_obj_id not in parent_instances_map:
                        parent_instances_map[orig_obj_id] = {}
                    parent_instances_map[orig_obj_id][parent_level.model_class] = parent_obj

            # Step 2: Add parent links to child objects and set PKs appropriately
            for child_obj, orig_obj in zip(plan.child_objects, plan.original_objects):
                parent_instances = parent_instances_map.get(id(orig_obj), {})

                # Set parent links and PKs for all objects (since in MTI, child PK = parent PK)
                for parent_model, parent_instance in parent_instances.items():
                    parent_link = plan.child_model._meta.get_ancestor_link(parent_model)
                    if parent_link:
                        parent_pk = parent_instance.pk
                        setattr(child_obj, parent_link.attname, parent_pk)
                        setattr(child_obj, parent_link.name, parent_instance)
                        # In MTI, the child PK IS the parent link
                        child_obj.pk = parent_pk
                        child_obj.id = parent_pk
                    else:
                        logger.warning(f"No parent link found for {parent_model} in {plan.child_model}")

            # Step 3: Handle child objects
            # Note: We can't use bulk_create on child MTI models, so we use _batched_insert for new records
            # and bulk_update for existing records
            base_qs = BaseQuerySet(model=plan.child_model, using=self.queryset.db)

            # For MTI child objects, we need to distinguish between truly new records and existing records for upsert operations
            objs_without_pk, objs_with_pk = [], []

            # Check which CHILD records actually exist in the child table
            if plan.update_conflicts:
                # For upsert, check which child records exist based on the parent PKs
                parent_pks_to_check = []
                for child_obj in plan.child_objects:
                    child_pk = getattr(child_obj, plan.child_model._meta.pk.attname, None)
                    if child_pk:
                        parent_pks_to_check.append(child_pk)

                existing_child_pks = set()
                if parent_pks_to_check:
                    existing_child_pks = set(base_qs.filter(pk__in=parent_pks_to_check).values_list("pk", flat=True))

                # Split based on whether child record exists
                for child_obj in plan.child_objects:
                    child_pk = getattr(child_obj, plan.child_model._meta.pk.attname, None)
                    if child_pk and child_pk in existing_child_pks:
                        # Child record exists - update it
                        objs_with_pk.append(child_obj)
                    else:
                        # Child record doesn't exist - insert it
                        objs_without_pk.append(child_obj)
            else:
                # Not an upsert - all are new records
                objs_without_pk = plan.child_objects
                objs_with_pk = []

            # For objects with PK (existing records in upsert), use bulk_update
            if objs_with_pk and plan.update_fields:
                # Filter update fields to only those that exist in the child model
                child_model_fields = {field.name for field in plan.child_model._meta.local_fields}
                filtered_child_update_fields = [field for field in plan.update_fields if field in child_model_fields]

                if filtered_child_update_fields:
                    base_qs.bulk_update(objs_with_pk, filtered_child_update_fields)

                # Mark as not adding
                for obj in objs_with_pk:
                    obj._state.adding = False
                    obj._state.db = self.queryset.db

            # For objects without PK (new records), use _batched_insert
            if objs_without_pk:
                base_qs._prepare_for_bulk_create(objs_without_pk)
                opts = plan.child_model._meta

                # Include all local fields except auto-generated ones
                # For MTI, we need to include the parent link (which is the PK)
                filtered_fields = [f for f in opts.local_fields if not f.generated]

                # Prepare conflict resolution parameters for upsert using pre-computed fields
                on_conflict = None
                batched_unique_fields = None
                batched_update_fields = None

                # Only set up upsert logic if we have child-specific unique fields
                if plan.update_conflicts and plan.child_unique_fields:
                    batched_unique_fields = plan.child_unique_fields
                    batched_update_fields = plan.child_update_fields

                    if batched_update_fields:
                        # We have both unique fields and update fields on child - use UPDATE
                        on_conflict = OnConflict.UPDATE
                    else:
                        # We have unique fields on child but no update fields - use IGNORE
                        # This handles the case where all update fields are on parent tables
                        on_conflict = OnConflict.IGNORE
                        batched_update_fields = None

                # Build kwargs for _batched_insert call
                kwargs = {
                    "batch_size": len(objs_without_pk),
                }
                # Only pass conflict resolution parameters if we have unique fields for this table
                if batched_unique_fields:
                    kwargs.update(
                        {
                            "on_conflict": on_conflict,
                            "update_fields": batched_update_fields,
                            "unique_fields": batched_unique_fields,
                        }
                    )

                returned_columns = base_qs._batched_insert(
                    objs_without_pk,
                    filtered_fields,
                    **kwargs,
                )
                if returned_columns:
                    for obj, results in zip(objs_without_pk, returned_columns):
                        if hasattr(opts, "db_returning_fields"):
                            for result, field in zip(results, opts.db_returning_fields):
                                setattr(obj, field.attname, result)
                        obj._state.adding = False
                        obj._state.db = self.queryset.db
                else:
                    for obj in objs_without_pk:
                        obj._state.adding = False
                        obj._state.db = self.queryset.db

            # All child objects are now created/updated
            created_children = plan.child_objects

            # Step 4: Copy PKs and auto-generated fields back to original objects
            pk_field_name = plan.child_model._meta.pk.name

            for orig_obj, child_obj in zip(plan.original_objects, created_children):
                # Copy PK
                child_pk = getattr(child_obj, pk_field_name)
                setattr(orig_obj, pk_field_name, child_pk)

                # Copy auto-generated fields from all levels
                parent_instances = parent_instances_map.get(id(orig_obj), {})

                for model_class in plan.inheritance_chain:
                    # Get source object for this level
                    if model_class in parent_instances:
                        source_obj = parent_instances[model_class]
                    elif model_class == plan.child_model:
                        source_obj = child_obj
                    else:
                        continue

                    # Copy auto-generated field values
                    for field in model_class._meta.local_fields:
                        if field.name == pk_field_name:
                            continue

                        # Skip parent link fields
                        if hasattr(field, "remote_field") and field.remote_field:
                            parent_link = plan.child_model._meta.get_ancestor_link(model_class)
                            if parent_link and field.name == parent_link.name:
                                continue

                        # Copy auto_now_add, auto_now, and db_returning fields
                        if (
                            getattr(field, "auto_now_add", False)
                            or getattr(field, "auto_now", False)
                            or getattr(field, "db_returning", False)
                        ):
                            source_value = getattr(source_obj, field.name, None)
                            if source_value is not None:
                                setattr(orig_obj, field.name, source_value)

                # Update object state
                orig_obj._state.adding = False
                orig_obj._state.db = self.queryset.db

        return plan.original_objects

    def _execute_mti_update_plan(self, plan):
        """
        Execute an MTI update plan.

        Updates each table in the inheritance chain using CASE/WHEN for bulk updates.

        Args:
            plan: MTIUpdatePlan object from MTIHandler

        Returns:
            Number of objects updated
        """
        from django.db.models import Case
        from django.db.models import QuerySet as BaseQuerySet
        from django.db.models import Value
        from django.db.models import When

        if not plan:
            return 0

        total_updated = 0

        # Get PKs for filtering
        root_pks = [
            getattr(obj, "pk", None) or getattr(obj, "id", None)
            for obj in plan.objects
            if getattr(obj, "pk", None) or getattr(obj, "id", None)
        ]

        if not root_pks:
            return 0

        with transaction.atomic(using=self.queryset.db, savepoint=False):
            # Update each table in the chain
            for field_group in plan.field_groups:
                if not field_group.fields:
                    continue

                base_qs = BaseQuerySet(model=field_group.model_class, using=self.queryset.db)

                # Check if records exist
                existing_count = base_qs.filter(**{f"{field_group.filter_field}__in": root_pks}).count()
                if existing_count == 0:
                    continue

                # Build CASE statements for bulk update
                case_statements = {}
                for field_name in field_group.fields:
                    field = field_group.model_class._meta.get_field(field_name)
                    when_statements = []

                    # Determine the correct output field for type casting
                    # For ForeignKey fields, use the target field to ensure correct SQL types
                    is_fk = isinstance(field, ForeignKey)
                    case_output_field = field.target_field if is_fk else field

                    for pk, obj in zip(root_pks, plan.objects):
                        obj_pk = getattr(obj, "pk", None) or getattr(obj, "id", None)
                        if obj_pk is None:
                            continue

                        # Get the field value using centralized field extraction
                        value = get_field_value_for_db(obj, field_name, obj.__class__)

                        # Handle NULL values specially for ForeignKey fields
                        if is_fk and value is None:
                            # For ForeignKey fields with None values, use Cast to ensure proper NULL type
                            # PostgreSQL needs explicit type casting for NULL values in CASE statements
                            when_statements.append(
                                When(
                                    **{field_group.filter_field: pk},
                                    then=Cast(Value(None), output_field=case_output_field),
                                ),
                            )
                        else:
                            # For non-None values or non-FK fields, use Value with output_field
                            when_statements.append(
                                When(
                                    **{field_group.filter_field: pk},
                                    then=Value(value, output_field=case_output_field),
                                ),
                            )

                    if when_statements:
                        case_statements[field_name] = Case(*when_statements, output_field=case_output_field)

                # Execute bulk update
                if case_statements:
                    try:
                        updated_count = base_qs.filter(
                            **{f"{field_group.filter_field}__in": root_pks},
                        ).update(**case_statements)
                        total_updated += updated_count
                    except Exception as e:
                        logger.error(f"MTI bulk update failed for {field_group.model_class.__name__}: {e}")

        return total_updated

    def delete_queryset(self):
        """
        Execute delete on the queryset.

        NOTE: Coordinator is responsible for validation before calling this method.
        This executor trusts that inputs have already been validated.

        Returns:
            Tuple of (count, details dict)
        """
        if not self.queryset:
            return 0, {}

        # Execute delete via QuerySet
        # Validation already done by coordinator
        from django.db.models import QuerySet

        return QuerySet.delete(self.queryset)
