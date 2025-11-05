"""
Bulk operation coordinator - Single entry point for all bulk operations.

This facade hides the complexity of wiring up multiple services and provides
a clean, simple API for the QuerySet to use.
"""

import logging

from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.db.models import QuerySet

from django_bulk_hooks.helpers import build_changeset_for_create
from django_bulk_hooks.helpers import build_changeset_for_delete
from django_bulk_hooks.helpers import build_changeset_for_update
from django_bulk_hooks.helpers import extract_pks

logger = logging.getLogger(__name__)


class BulkOperationCoordinator:
    """
    Single entry point for coordinating bulk operations.

    This coordinator manages all services and provides a clean facade
    for the QuerySet. It wires up services and coordinates the hook
    lifecycle for each operation type.

    Services are created lazily and cached.
    """

    def __init__(self, queryset):
        """
        Initialize coordinator for a queryset.

        Args:
            queryset: Django QuerySet instance
        """
        self.queryset = queryset
        self.model_cls = queryset.model

        # Lazy initialization
        self._analyzer = None
        self._mti_handler = None
        self._record_classifier = None
        self._executor = None
        self._dispatcher = None

    def _get_or_create_service(self, service_name, service_class, *args, **kwargs):
        """
        Generic lazy service initialization.

        Args:
            service_name: Name of the service attribute (e.g., 'analyzer')
            service_class: The class to instantiate
            *args, **kwargs: Arguments to pass to the service constructor

        Returns:
            The service instance
        """
        attr_name = f"_{service_name}"
        if getattr(self, attr_name) is None:
            setattr(self, attr_name, service_class(*args, **kwargs))
        return getattr(self, attr_name)

    @property
    def analyzer(self):
        """Get or create ModelAnalyzer"""
        from django_bulk_hooks.operations.analyzer import ModelAnalyzer

        return self._get_or_create_service("analyzer", ModelAnalyzer, self.model_cls)

    @property
    def mti_handler(self):
        """Get or create MTIHandler"""
        from django_bulk_hooks.operations.mti_handler import MTIHandler

        return self._get_or_create_service("mti_handler", MTIHandler, self.model_cls)

    @property
    def record_classifier(self):
        """Get or create RecordClassifier"""
        from django_bulk_hooks.operations.record_classifier import RecordClassifier

        return self._get_or_create_service("record_classifier", RecordClassifier, self.model_cls)

    @property
    def executor(self):
        """Get or create BulkExecutor"""
        from django_bulk_hooks.operations.bulk_executor import BulkExecutor

        return self._get_or_create_service(
            "executor",
            BulkExecutor,
            queryset=self.queryset,
            analyzer=self.analyzer,
            mti_handler=self.mti_handler,
            record_classifier=self.record_classifier,
        )

    @property
    def dispatcher(self):
        """Get or create Dispatcher"""
        from django_bulk_hooks.dispatcher import get_dispatcher

        return self._get_or_create_service("dispatcher", get_dispatcher)

    @property
    def inheritance_chain(self):
        """Single source of truth for inheritance chain"""
        return self.mti_handler.get_inheritance_chain()

    def _validate_objects_for_operation(self, objs, operation_type):
        """
        Validate objects exist and return appropriate empty result.

        Args:
            objs: List of objects to validate
            operation_type: 'create', 'update', 'delete', or 'validate'

        Returns:
            Appropriate empty result for the operation type, or None if objects exist
        """
        if not objs:
            empty_results = {
                "create": objs,
                "update": 0,
                "delete": (0, {}),
                "validate": None,
            }
            return empty_results[operation_type]
        return None  # Continue with operation

    def _dispatch_hooks_for_models(self, models_in_chain, changeset, event_suffix, bypass_hooks=False):
        """
        Dispatch hooks for all models in inheritance chain.

        Args:
            models_in_chain: List of model classes in MTI inheritance chain
            changeset: The changeset to use as base
            event_suffix: Event name suffix (e.g., 'before_create', 'validate_update')
            bypass_hooks: Whether to skip hook execution
        """
        logger.debug(f"🔄 DISPATCH_MODELS: Iterating through {len(models_in_chain)} models for {event_suffix}: {[m.__name__ for m in models_in_chain]}")
        for i, model_cls in enumerate(models_in_chain):
            logger.debug(f"🔄 DISPATCH_ITERATION: {i+1}/{len(models_in_chain)} - Dispatching to {model_cls.__name__} for {event_suffix}")
            model_changeset = self._build_changeset_for_model(changeset, model_cls)
            logger.debug(f"🔄 CHANGESET_MODEL: Created changeset with model_cls={model_changeset.model_cls.__name__}")
            self.dispatcher.dispatch(model_changeset, event_suffix, bypass_hooks=bypass_hooks)

    # ==================== PUBLIC API ====================

    @transaction.atomic
    def create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
        bypass_hooks=False,
        bypass_validation=False,
    ):
        """
        Execute bulk create with hooks.

        Args:
            objs: List of model instances to create
            batch_size: Number of objects per batch
            ignore_conflicts: Ignore conflicts if True
            update_conflicts: Update on conflict if True
            update_fields: Fields to update on conflict
            unique_fields: Fields to check for conflicts
            bypass_hooks: Skip all hooks if True
            bypass_validation: Skip validation hooks if True

        Returns:
            List of created objects
        """
        empty_result = self._validate_objects_for_operation(objs, "create")
        if empty_result is not None:
            return empty_result

        # Validate
        self.analyzer.validate_for_create(objs)

        # For upsert operations, classify records upfront
        existing_record_ids = set()
        existing_pks_map = {}
        if update_conflicts and unique_fields:
            # For MTI models, query the parent model that has the unique fields
            query_model = None
            if self.mti_handler.is_mti_model():
                query_model = self.mti_handler.find_model_with_unique_fields(unique_fields)
                logger.info(f"MTI model detected: querying {query_model.__name__} for unique fields {unique_fields}")

            existing_record_ids, existing_pks_map = self.record_classifier.classify_for_upsert(objs, unique_fields, query_model=query_model)
            logger.info(f"Upsert operation: {len(existing_record_ids)} existing, {len(objs) - len(existing_record_ids)} new records")
            logger.debug(f"Existing record IDs: {existing_record_ids}")
            logger.debug(f"Existing PKs map: {existing_pks_map}")

        # Build initial changeset
        changeset = build_changeset_for_create(
            self.model_cls,
            objs,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )

        # Execute with hook lifecycle
        def operation():
            return self.executor.bulk_create(
                objs,
                batch_size=batch_size,
                ignore_conflicts=ignore_conflicts,
                update_conflicts=update_conflicts,
                update_fields=update_fields,
                unique_fields=unique_fields,
                existing_record_ids=existing_record_ids,
                existing_pks_map=existing_pks_map,
            )

        return self._execute_with_mti_hooks(
            changeset=changeset,
            operation=operation,
            event_prefix="create",
            bypass_hooks=bypass_hooks,
            bypass_validation=bypass_validation,
        )

    @transaction.atomic
    def update(
        self,
        objs,
        fields,
        batch_size=None,
        bypass_hooks=False,
        bypass_validation=False,
    ):
        """
        Execute bulk update with hooks.

        Args:
            objs: List of model instances to update
            fields: List of field names to update
            batch_size: Number of objects per batch
            bypass_hooks: Skip all hooks if True
            bypass_validation: Skip validation hooks if True

        Returns:
            Number of objects updated
        """
        empty_result = self._validate_objects_for_operation(objs, "update")
        if empty_result is not None:
            return empty_result

        # Validate
        self.analyzer.validate_for_update(objs)

        # Fetch old records using analyzer (single source of truth)
        old_records_map = self.analyzer.fetch_old_records_map(objs)

        # Build changeset
        from django_bulk_hooks.changeset import ChangeSet
        from django_bulk_hooks.changeset import RecordChange

        changes = [
            RecordChange(
                new_record=obj,
                old_record=old_records_map.get(obj.pk),
                changed_fields=fields,
            )
            for obj in objs
        ]
        changeset = ChangeSet(self.model_cls, changes, "update", {"fields": fields})

        # Execute with hook lifecycle
        def operation():
            return self.executor.bulk_update(objs, fields, batch_size=batch_size)

        return self._execute_with_mti_hooks(
            changeset=changeset,
            operation=operation,
            event_prefix="update",
            bypass_hooks=bypass_hooks,
            bypass_validation=bypass_validation,
        )

    @transaction.atomic
    def update_queryset(
        self,
        update_kwargs,
        bypass_hooks=False,
        bypass_validation=False,
    ):
        """
        Execute queryset.update() with full hook support.

        ARCHITECTURE & PERFORMANCE TRADE-OFFS
        ======================================

        To support hooks with queryset.update(), we must:
        1. Fetch old state (SELECT all matching rows)
        2. Execute database update (UPDATE in SQL)
        3. Fetch new state (SELECT all rows again)
        4. Run VALIDATE_UPDATE hooks (validation only)
        5. Run BEFORE_UPDATE hooks (CAN modify instances)
        6. Persist BEFORE_UPDATE modifications (bulk_update)
        7. Run AFTER_UPDATE hooks (read-only side effects)

        Performance Cost:
        - 2 SELECT queries (before/after)
        - 1 UPDATE query (actual update)
        - 1 bulk_update (if hooks modify data)

        Trade-off: Hooks require loading data into Python. If you need
        maximum performance and don't need hooks, use bypass_hooks=True.

        Hook Semantics:
        - BEFORE_UPDATE hooks run after the DB update and CAN modify instances
        - Modifications are auto-persisted (framework handles complexity)
        - AFTER_UPDATE hooks run after BEFORE_UPDATE and are read-only
        - This enables cascade logic and computed fields based on DB values
        - User expectation: BEFORE_UPDATE hooks can modify data

        Why this approach works well:
        - Allows hooks to see Subquery/F() computed values
        - Enables HasChanged conditions on complex expressions
        - Maintains SQL performance (Subquery stays in database)
        - Meets user expectations: BEFORE_UPDATE can modify instances
        - Clean separation: BEFORE for modifications, AFTER for side effects

        For true "prevent write" semantics, intercept at a higher level
        or use bulk_update() directly (which has true before semantics).
        """
        from django_bulk_hooks.context import get_bypass_hooks

        # Fast path: no hooks at all
        if bypass_hooks or get_bypass_hooks():
            return QuerySet.update(self.queryset, **update_kwargs)

        # Full hook lifecycle path
        return self._execute_queryset_update_with_hooks(
            update_kwargs=update_kwargs,
            bypass_validation=bypass_validation,
        )

    def _execute_queryset_update_with_hooks(
        self,
        update_kwargs,
        bypass_validation=False,
    ):
        """
        Execute queryset update with full hook lifecycle support.

        This method implements the fetch-update-fetch pattern required
        to support hooks with queryset.update(). BEFORE_UPDATE hooks can
        modify instances and modifications are auto-persisted.

        Args:
            update_kwargs: Dict of fields to update
            bypass_validation: Skip validation hooks if True

        Returns:
            Number of rows updated
        """
        # Step 0: Extract relationships that hooks might access to avoid N+1 queries
        hook_relationships = self._extract_hook_relationships()

        # Step 1: Fetch old state (before database update) with relationships preloaded
        if hook_relationships:
            logger.info(f"🔗 BULK PRELOAD: Fetching {self.queryset.count()} old instances with select_related({list(hook_relationships)})")
            old_queryset = self.queryset.select_related(*hook_relationships)
        else:
            logger.info(f"🔗 BULK PRELOAD: Fetching {self.queryset.count()} old instances without select_related")
            old_queryset = self.queryset

        old_instances = list(old_queryset)
        logger.info(f"✅ Fetched {len(old_instances)} old instances")
        if not old_instances:
            return 0

        old_records_map = {inst.pk: inst for inst in old_instances}

        # Step 2: Execute native Django update
        # Use stored reference to parent class method - clean and simple
        update_count = QuerySet.update(self.queryset, **update_kwargs)

        if update_count == 0:
            return 0

        # Step 3: Fetch new state (after database update) with relationships preloaded
        # This captures any Subquery/F() computed values
        # Use primary keys to fetch updated instances since queryset filters may no longer match
        pks = [inst.pk for inst in old_instances]

        if hook_relationships:
            logger.info(f"🔗 BULK PRELOAD: Fetching {len(pks)} new instances with select_related({list(hook_relationships)})")
            new_queryset = self.model_cls.objects.filter(pk__in=pks).select_related(*hook_relationships)
        else:
            logger.info(f"🔗 BULK PRELOAD: Fetching {len(pks)} new instances without select_related")
            new_queryset = self.model_cls.objects.filter(pk__in=pks)

        new_instances = list(new_queryset)
        logger.info(f"✅ Fetched {len(new_instances)} new instances")

        # Step 4: Build changeset
        changeset = build_changeset_for_update(
            self.model_cls,
            new_instances,
            update_kwargs,
            old_records_map=old_records_map,
        )

        # Mark as queryset update for potential hook inspection
        changeset.operation_meta["is_queryset_update"] = True
        changeset.operation_meta["allows_modifications"] = True

        # Step 5: Get MTI inheritance chain
        models_in_chain = self._get_models_in_chain(self.model_cls)

        # Step 6: Run VALIDATE hooks (if not bypassed)
        if not bypass_validation:
            self._dispatch_hooks_for_models(models_in_chain, changeset, "validate_update", bypass_hooks=False)

        # Step 7: Run BEFORE_UPDATE hooks with modification tracking
        modified_fields = self._run_before_update_hooks_with_tracking(
            new_instances,
            models_in_chain,
            changeset,
        )

        # Step 8: Auto-persist BEFORE_UPDATE modifications
        if modified_fields:
            self._persist_hook_modifications(new_instances, modified_fields)

        # Step 9: Take snapshot before AFTER_UPDATE hooks
        pre_after_hook_state = self._snapshot_instance_state(new_instances)

        # Step 10: Run AFTER_UPDATE hooks (read-only side effects)
        self._dispatch_hooks_for_models(models_in_chain, changeset, "after_update", bypass_hooks=False)

        # Step 11: Auto-persist AFTER_UPDATE modifications (if any)
        after_modified_fields = self._detect_modifications(new_instances, pre_after_hook_state)
        if after_modified_fields:
            self._persist_hook_modifications(new_instances, after_modified_fields)

        return update_count

    def _run_before_update_hooks_with_tracking(self, instances, models_in_chain, changeset):
        """
        Run BEFORE_UPDATE hooks and detect modifications.

        This is what users expect - BEFORE_UPDATE hooks can modify instances
        and those modifications will be automatically persisted. The framework
        handles the complexity internally.

        Returns:
            Set of field names that were modified by hooks
        """
        # Snapshot current state
        pre_hook_state = self._snapshot_instance_state(instances)

        # Run BEFORE_UPDATE hooks
        self._dispatch_hooks_for_models(models_in_chain, changeset, "before_update", bypass_hooks=False)

        # Detect modifications
        return self._detect_modifications(instances, pre_hook_state)

    def _snapshot_instance_state(self, instances):
        """
        Create a snapshot of current instance field values.

        Args:
            instances: List of model instances

        Returns:
            Dict mapping pk -> {field_name: value}
        """
        snapshot = {}

        for instance in instances:
            if instance.pk is None:
                continue

            field_values = {}
            for field in self.model_cls._meta.get_fields():
                # Skip relations that aren't concrete fields
                if field.many_to_many or field.one_to_many:
                    continue

                field_name = field.name
                try:
                    field_values[field_name] = getattr(instance, field_name)
                except (AttributeError, FieldDoesNotExist):
                    # Field not accessible (e.g., deferred field)
                    field_values[field_name] = None

            snapshot[instance.pk] = field_values

        return snapshot

    def _detect_modifications(self, instances, pre_hook_state):
        """
        Detect which fields were modified by comparing to snapshot.

        Args:
            instances: List of model instances
            pre_hook_state: Previous state snapshot from _snapshot_instance_state

        Returns:
            Set of field names that were modified
        """
        modified_fields = set()

        for instance in instances:
            if instance.pk not in pre_hook_state:
                continue

            old_values = pre_hook_state[instance.pk]

            for field_name, old_value in old_values.items():
                try:
                    current_value = getattr(instance, field_name)
                except (AttributeError, FieldDoesNotExist):
                    current_value = None

                # Compare values
                if current_value != old_value:
                    modified_fields.add(field_name)

        return modified_fields

    def _persist_hook_modifications(self, instances, modified_fields):
        """
        Persist modifications made by hooks using bulk_update.

        This creates a "cascade" effect similar to Salesforce workflows.

        Args:
            instances: List of modified instances
            modified_fields: Set of field names that were modified
        """
        logger.info(
            f"Hooks modified {len(modified_fields)} field(s): {', '.join(sorted(modified_fields))}",
        )
        logger.info("Auto-persisting modifications via bulk_update")

        # Use Django's bulk_update directly (not our hook version)
        # Create a fresh QuerySet to avoid recursion
        fresh_qs = QuerySet(model=self.model_cls, using=self.queryset.db)
        QuerySet.bulk_update(fresh_qs, instances, list(modified_fields))

    @transaction.atomic
    def delete(self, bypass_hooks=False, bypass_validation=False):
        """
        Execute delete with hooks.

        Args:
            bypass_hooks: Skip all hooks if True
            bypass_validation: Skip validation hooks if True

        Returns:
            Tuple of (count, details dict)
        """
        # Get objects
        objs = list(self.queryset)
        empty_result = self._validate_objects_for_operation(objs, "delete")
        if empty_result is not None:
            return empty_result

        # Validate
        self.analyzer.validate_for_delete(objs)

        # Build changeset
        changeset = build_changeset_for_delete(self.model_cls, objs)

        # Execute with hook lifecycle
        def operation():
            # Use stored reference to parent method - clean and simple
            return QuerySet.delete(self.queryset)

        return self._execute_with_mti_hooks(
            changeset=changeset,
            operation=operation,
            event_prefix="delete",
            bypass_hooks=bypass_hooks,
            bypass_validation=bypass_validation,
        )

    def clean(self, objs, is_create=None):
        """
        Execute validation hooks only (no database operations).

        This is used by Django's clean() method to hook VALIDATE_* events
        without performing the actual operation.

        Args:
            objs: List of model instances to validate
            is_create: True for create, False for update, None to auto-detect

        Returns:
            None
        """
        empty_result = self._validate_objects_for_operation(objs, "validate")
        if empty_result is not None:
            return

        # Auto-detect if is_create not specified
        if is_create is None:
            is_create = objs[0].pk is None

        # Use centralized validation logic (consistent with other operations)
        if is_create:
            self.analyzer.validate_for_create(objs)
        else:
            self.analyzer.validate_for_update(objs)

        # Build changeset based on operation type
        if is_create:
            changeset = build_changeset_for_create(self.model_cls, objs)
            event = "validate_create"
        else:
            # For update validation, no old records needed - hooks handle their own queries
            changeset = build_changeset_for_update(self.model_cls, objs, {})
            event = "validate_update"

        # Dispatch validation event for entire inheritance chain
        models_in_chain = self._get_models_in_chain(self.model_cls)
        self._dispatch_hooks_for_models(models_in_chain, changeset, event)

    # ==================== MTI PARENT HOOK SUPPORT ====================

    def _build_changeset_for_model(self, original_changeset, target_model_cls):
        """
        Build a changeset for a specific model in the MTI inheritance chain.

        This allows parent model hooks to receive the same instances but with
        the correct model_cls for hook registration matching.

        Args:
            original_changeset: The original changeset (for child model)
            target_model_cls: The model class to build changeset for (parent model)

        Returns:
            ChangeSet for the target model
        """
        from django_bulk_hooks.changeset import ChangeSet

        # Create new changeset with target model but same record changes
        return ChangeSet(
            model_cls=target_model_cls,
            changes=original_changeset.changes,
            operation_type=original_changeset.operation_type,
            operation_meta=original_changeset.operation_meta,
        )

    def _get_models_in_chain(self, model_cls):
        """
        Get all models in the inheritance chain for hook dispatching.

        DEPRECATED: Use self.inheritance_chain property instead for consistency.
        This method is kept for backward compatibility.

        Args:
            model_cls: The model class to start from

        Returns:
            List of model classes in inheritance order [child, parent1, parent2, ...]
        """
        return self.inheritance_chain

    def _execute_with_mti_hooks(
        self,
        changeset,
        operation,
        event_prefix,
        bypass_hooks=False,
        bypass_validation=False,
    ):
        """
        Execute operation with hooks for entire MTI inheritance chain.

        This method dispatches hooks for both child and parent models when
        dealing with MTI models, ensuring parent model hooks fire when
        child instances are created/updated/deleted.

        Args:
            changeset: ChangeSet for the child model
            operation: Callable that performs the actual DB operation
            event_prefix: 'create', 'update', or 'delete'
            bypass_hooks: Skip all hooks if True
            bypass_validation: Skip validation hooks if True

        Returns:
            Result of operation
        """
        if bypass_hooks:
            return operation()

        # Reset hook execution tracking for this new operation
        self.dispatcher._reset_executed_hooks()
        logger.debug(f"🚀 MTI_OPERATION_START: {event_prefix} operation for {changeset.model_cls.__name__}")

        # Get all models in inheritance chain
        models_in_chain = self._get_models_in_chain(changeset.model_cls)
        logger.debug(f"🔗 MTI_CHAIN_START: {len(models_in_chain)} models in chain for {changeset.model_cls.__name__}")

        # Extract and preload relationships needed by hook conditions upfront
        # This prevents duplicate queries by avoiding per-hook preloading
        condition_relationships = self._extract_condition_relationships_for_operation(changeset, models_in_chain)
        if condition_relationships:
            logger.info(f"🔗 BULK PRELOAD: Preloading {len(condition_relationships)} condition relationships for {changeset.model_cls.__name__} hooks")
            self.dispatcher._preload_condition_relationships(changeset, condition_relationships)
            # Mark that relationships have been preloaded to avoid per-hook duplication
            changeset.operation_meta['relationships_preloaded'] = True
        else:
            logger.info(f"🔗 BULK PRELOAD: No condition relationships to preload for {changeset.model_cls.__name__} hooks")

        # VALIDATE phase - for all models in chain
        if not bypass_validation:
            self._dispatch_hooks_for_models(models_in_chain, changeset, f"validate_{event_prefix}")

        # BEFORE phase - for all models in chain
        self._dispatch_hooks_for_models(models_in_chain, changeset, f"before_{event_prefix}")

        # Execute the actual operation
        result = operation()

        # AFTER phase - for all models in chain
        # Use result if operation returns modified data (for create operations)
        if result and isinstance(result, list) and event_prefix == "create":
            # Check if this was an upsert operation
            is_upsert = self._is_upsert_operation(result)
            if is_upsert:
                # Split hooks for upsert: after_create for created, after_update for updated
                self._dispatch_upsert_after_hooks(result, models_in_chain)
            else:
                # Normal create operation
                from django_bulk_hooks.helpers import build_changeset_for_create

                changeset = build_changeset_for_create(changeset.model_cls, result)

                self._dispatch_hooks_for_models(models_in_chain, changeset, f"after_{event_prefix}")
        else:
            # Non-create operations (update, delete)
            self._dispatch_hooks_for_models(models_in_chain, changeset, f"after_{event_prefix}")

        return result

    def _get_fk_fields_being_updated(self, update_kwargs):
        """
        Get the relationship names for FK fields being updated.

        This helps @select_related avoid preloading relationships that are
        being modified, which can cause cache conflicts.

        Args:
            update_kwargs: Dict of fields being updated

        Returns:
            Set of relationship names (e.g., {'business'}) for FK fields being updated
        """
        fk_relationships = set()

        for field_name in update_kwargs.keys():
            try:
                field = self.model_cls._meta.get_field(field_name)
                if (
                    field.is_relation
                    and not field.many_to_many
                    and not field.one_to_many
                    and hasattr(field, "attname")
                    and field.attname == field_name
                ):
                    # This is a FK field being updated by its attname (e.g., business_id)
                    # Add the relationship name (e.g., 'business') to skip list
                    fk_relationships.add(field.name)
            except FieldDoesNotExist:
                # If field lookup fails, skip it
                continue

        return fk_relationships

    def _is_upsert_operation(self, result_objects):
        """
        Check if the operation was an upsert (with update_conflicts=True).

        Args:
            result_objects: List of objects returned from the operation

        Returns:
            True if this was an upsert operation, False otherwise
        """
        if not result_objects:
            return False

        # Check if any object has upsert metadata
        return hasattr(result_objects[0], "_bulk_hooks_upsert_metadata")

    def _dispatch_upsert_after_hooks(self, result_objects, models_in_chain):
        """
        Dispatch after hooks for upsert operations, splitting by create/update.

        This matches Salesforce behavior:
        - Records that were created fire after_create hooks
        - Records that were updated fire after_update hooks

        Args:
            result_objects: List of objects returned from the operation
            models_in_chain: List of model classes in the MTI inheritance chain
        """
        logger.debug(f"🔀 UPSERT_AFTER_START: Processing {len(result_objects)} result objects with {len(models_in_chain)} models in chain")
        # Split objects based on metadata set by the executor
        created_objects = []
        updated_objects = []

        if not result_objects:
            return

        # First pass: collect objects with metadata and objects needing timestamp check
        objects_needing_timestamp_check = []
        for obj in result_objects:
            # Check if metadata was set
            if hasattr(obj, "_bulk_hooks_was_created"):
                was_created = getattr(obj, "_bulk_hooks_was_created", True)
                if was_created:
                    created_objects.append(obj)
                else:
                    updated_objects.append(obj)
            else:
                # Need to check timestamps - collect for bulk query
                objects_needing_timestamp_check.append(obj)

        # Bulk fetch timestamps for objects without metadata (avoids N+1 queries)
        if objects_needing_timestamp_check:
            # Group by model class to handle MTI scenarios
            objects_by_model = {}
            for obj in objects_needing_timestamp_check:
                model_cls = obj.__class__
                if model_cls not in objects_by_model:
                    objects_by_model[model_cls] = []
                objects_by_model[model_cls].append(obj)

            # Fetch timestamps in bulk for each model class
            for model_cls, objs in objects_by_model.items():
                if hasattr(model_cls, "created_at") and hasattr(model_cls, "updated_at"):
                    # Bulk fetch timestamps for all objects of this model
                    pks = extract_pks(objs)
                    if pks:
                        timestamp_map = {
                            record["pk"]: (record["created_at"], record["updated_at"])
                            for record in model_cls.objects.filter(pk__in=pks).values("pk", "created_at", "updated_at")
                        }

                        # Classify each object based on timestamps
                        for obj in objs:
                            if obj.pk in timestamp_map:
                                created_at, updated_at = timestamp_map[obj.pk]
                                if created_at and updated_at:
                                    time_diff = abs((updated_at - created_at).total_seconds())
                                    if time_diff <= 1.0:  # Within 1 second = just created
                                        created_objects.append(obj)
                                    else:
                                        updated_objects.append(obj)
                                else:
                                    # No timestamps, default to created
                                    created_objects.append(obj)
                            else:
                                # Object not found, treat as created
                                created_objects.append(obj)
                    else:
                        # No PKs, default all to created
                        created_objects.extend(objs)
                else:
                    # No timestamp fields, default to created
                    created_objects.extend(objs)

        logger.info(f"Upsert after hooks: {len(created_objects)} created, {len(updated_objects)} updated")

        # Dispatch after_create hooks for created objects
        if created_objects:
            logger.debug(f"🔀 UPSERT_DISPATCH_CREATE: Dispatching after_create for {len(created_objects)} created objects")
            from django_bulk_hooks.helpers import build_changeset_for_create

            create_changeset = build_changeset_for_create(self.model_cls, created_objects)
            # Mark that relationships have been preloaded to avoid per-hook duplication
            create_changeset.operation_meta['relationships_preloaded'] = True

            self._dispatch_hooks_for_models(models_in_chain, create_changeset, "after_create", bypass_hooks=False)

        # Dispatch after_update hooks for updated objects
        if updated_objects:
            logger.debug(f"🔀 UPSERT_DISPATCH_UPDATE: Dispatching after_update for {len(updated_objects)} updated objects")
            # Fetch old records for proper change detection
            old_records_map = self.analyzer.fetch_old_records_map(updated_objects)

            from django_bulk_hooks.helpers import build_changeset_for_update

            update_changeset = build_changeset_for_update(
                self.model_cls,
                updated_objects,
                update_kwargs={},  # Empty since we don't know specific fields
                old_records_map=old_records_map,
            )
            # Mark that relationships have been preloaded to avoid per-hook duplication
            update_changeset.operation_meta['relationships_preloaded'] = True

            self._dispatch_hooks_for_models(models_in_chain, update_changeset, "after_update", bypass_hooks=False)

        # Clean up temporary metadata
        self._cleanup_upsert_metadata(result_objects)

    def _extract_condition_relationships_for_operation(self, changeset, models_in_chain):
        """
        Extract relationships needed by hook conditions for this specific operation.

        This is different from _extract_hook_relationships which gets ALL possible relationships
        for queryset operations. This method only gets relationships needed by hooks that will
        actually run in this operation.

        Args:
            changeset: The changeset for this operation
            models_in_chain: List of model classes in inheritance chain

        Returns:
            set: Set of relationship field names to preload
        """
        relationships = set()
        dispatcher = self.dispatcher

        # Get the events that will run in this operation
        event_prefix = changeset.operation_type
        events_to_check = [f"validate_{event_prefix}", f"before_{event_prefix}", f"after_{event_prefix}"]

        for model_cls in models_in_chain:
            for event in events_to_check:
                hooks = dispatcher.registry.get_hooks(model_cls, event)

                for handler_cls, method_name, condition, priority in hooks:
                    # Only extract relationships from conditions (not @select_related)
                    if condition:
                        condition_relationships = dispatcher._extract_condition_relationships(condition, model_cls)
                        relationships.update(condition_relationships)

        return relationships

    def _extract_hook_relationships(self):
        """
        Extract all relationship paths that hooks might access for this model and its MTI parents.

        This prevents N+1 queries by preloading all relationships that any hook
        (condition or @select_related) might access during bulk operations.

        Returns:
            set: Set of relationship field names to preload with select_related
        """
        relationships = set()

        # Get the dispatcher to access hook registry
        dispatcher = self.dispatcher

        # Get all models in the inheritance chain (including parents for MTI)
        models_to_check = self._get_models_in_chain(self.model_cls)

        # Check hooks for all relevant events that might run during bulk operations
        events_to_check = ['before_update', 'after_update', 'validate_update']

        for model_cls in models_to_check:
            logger.info(f"🔍 BULK PRELOAD: Checking hooks for model {model_cls.__name__}")
            for event in events_to_check:
                hooks = dispatcher.registry.get_hooks(model_cls, event)
                logger.info(f"  🔍 Found {len(hooks)} hooks for {model_cls.__name__}.{event}")

                for handler_cls, method_name, condition, priority in hooks:
                    logger.info(f"    → Checking {handler_cls.__name__}.{method_name}")

                    # Extract relationships from conditions
                    if condition:
                        condition_relationships = dispatcher._extract_condition_relationships(condition, model_cls)
                        if condition_relationships:
                            logger.info(f"      📋 Condition relationships for {model_cls.__name__}: {condition_relationships}")
                            relationships.update(condition_relationships)

                    # Extract relationships from @select_related decorators
                    try:
                        method = getattr(handler_cls, method_name, None)
                        if method:
                            select_related_fields = getattr(method, "_select_related_fields", None)
                            if select_related_fields and hasattr(select_related_fields, '__iter__'):
                                logger.info(f"      🔗 @select_related fields on {handler_cls.__name__}.{method_name}: {list(select_related_fields)}")
                                relationships.update(select_related_fields)
                    except Exception as e:
                        logger.warning(f"      ❌ Failed to extract @select_related from {handler_cls.__name__}.{method_name}: {e}")

        # AGGRESSIVE APPROACH: Also preload ALL relationship fields on the model
        # This prevents N+1 queries from any relationship access during hook execution
        try:
            for field in self.model_cls._meta.get_fields():
                if field.is_relation and not field.many_to_many and not field.one_to_many:
                    # This is a forward foreign key relationship
                    field_name = field.name
                    logger.info(f"      🔗 AUTO: Adding all relationship fields including {field_name}")
                    relationships.add(field_name)
        except Exception as e:
            logger.warning(f"      ❌ Failed to extract all relationship fields: {e}")

        logger.info(f"🔗 BULK PRELOAD: Total extracted relationships for {self.model_cls.__name__}: {list(relationships)}")
        return relationships

    def _cleanup_upsert_metadata(self, result_objects):
        """
        Clean up temporary metadata added during upsert operations.

        Args:
            result_objects: List of objects to clean up
        """
        for obj in result_objects:
            if hasattr(obj, "_bulk_hooks_was_created"):
                delattr(obj, "_bulk_hooks_was_created")
            if hasattr(obj, "_bulk_hooks_upsert_metadata"):
                delattr(obj, "_bulk_hooks_upsert_metadata")
