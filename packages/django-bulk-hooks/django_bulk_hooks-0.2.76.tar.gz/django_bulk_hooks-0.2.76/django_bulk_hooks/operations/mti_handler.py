"""
Multi-table inheritance (MTI) handler service.

Handles detection and planning for multi-table inheritance operations.

This handler is PURE LOGIC - it does not execute database operations.
It returns plans (data structures) that the BulkExecutor executes.
"""

import logging

from django.db.models import AutoField

from django_bulk_hooks.operations.field_utils import get_field_value_for_db

logger = logging.getLogger(__name__)


class MTIHandler:
    """
    Handles multi-table inheritance (MTI) operation planning.

    This service detects MTI models and builds execution plans.
    It does NOT execute database operations - that's the BulkExecutor's job.

    Responsibilities:
    - Detect MTI models
    - Build inheritance chains
    - Create parent/child instances (in-memory only)
    - Return execution plans
    """

    def __init__(self, model_cls):
        """
        Initialize MTI handler for a specific model.

        Args:
            model_cls: The Django model class
        """
        self.model_cls = model_cls
        self._inheritance_chain = None

    def is_mti_model(self):
        """
        Determine if the model uses multi-table inheritance.

        Returns:
            bool: True if model has concrete parent models
        """
        # Check if this model has concrete parent models (not abstract)
        for parent in self.model_cls._meta.parents.keys():
            if not parent._meta.abstract and parent._meta.concrete_model != self.model_cls._meta.concrete_model:
                return True
        return False

    def get_inheritance_chain(self):
        """
        Get the complete inheritance chain from root to child.

        Returns:
            list: Model classes ordered from root parent to current model
                 Returns empty list if not MTI model
        """
        if self._inheritance_chain is None:
            self._inheritance_chain = self._compute_chain()
        return self._inheritance_chain

    def _compute_chain(self):
        """
        Compute the inheritance chain by walking up the parent hierarchy.

        Returns:
            list: Model classes in order [RootParent, Parent, Child]
        """
        chain = []
        current_model = self.model_cls

        while current_model:
            if not current_model._meta.proxy and not current_model._meta.abstract:
                chain.append(current_model)
                logger.debug(f"🔗 MTI_CHAIN_ADD: Added {current_model.__name__} (abstract: {current_model._meta.abstract}, proxy: {current_model._meta.proxy})")

            # Get concrete parent models (not abstract, not proxy)
            parents = [parent for parent in current_model._meta.parents.keys() if not parent._meta.proxy and not parent._meta.abstract]
            logger.debug(f"🔗 MTI_PARENTS: {current_model.__name__} has concrete parents: {[p.__name__ for p in parents]}")

            current_model = parents[0] if parents else None

        # Reverse to get root-to-child order
        chain.reverse()
        logger.debug(f"🔗 MTI_CHAIN_FINAL: {[m.__name__ for m in chain]} (length: {len(chain)})")
        return chain

    def get_parent_models(self):
        """
        Get all parent models in the inheritance chain.

        Returns:
            list: Parent model classes (excludes current model)
        """
        chain = self.get_inheritance_chain()
        if len(chain) <= 1:
            return []
        return chain[:-1]  # All except current model

    def get_local_fields_for_model(self, model_cls):
        """
        Get fields defined directly on a specific model in the chain.

        Args:
            model_cls: Model class to get fields for

        Returns:
            list: Field objects defined on this model
        """
        return list(model_cls._meta.local_fields)

    def find_model_with_unique_fields(self, unique_fields):
        """
        Find which model in the inheritance chain to query for existing records.

        For MTI upsert operations, we need to determine if the parent record exists
        to properly fire AFTER_CREATE vs AFTER_UPDATE hooks. This is critical because:
        - If parent exists but child doesn't: creating child for existing parent → AFTER_UPDATE
        - If neither exists: creating both parent and child → AFTER_CREATE

        Therefore, we find the model that contains all the unique fields, regardless
        of whether it's the parent or child model.

        Args:
            unique_fields: List of field names forming the unique constraint

        Returns:
            Model class to query for existing records (model containing unique fields)
        """
        if not unique_fields:
            return self.model_cls

        inheritance_chain = self.get_inheritance_chain()

        # For MTI models, find the model in the chain that contains ALL unique fields
        if len(inheritance_chain) > 1:
            # Walk through inheritance chain from child to parent
            for model in reversed(inheritance_chain):  # Start with child, end with root parent
                model_field_names = {f.name for f in model._meta.local_fields}
                if all(field in model_field_names for field in unique_fields):
                    return model

        # For non-MTI models or as fallback
        return self.model_cls

    # ==================== MTI BULK CREATE PLANNING ====================

    def build_create_plan(
        self,
        objs,
        batch_size=None,
        update_conflicts=False,
        unique_fields=None,
        update_fields=None,
        existing_record_ids=None,
        existing_pks_map=None,
    ):
        """
        Build an execution plan for bulk creating MTI model instances.

        This method does NOT execute any database operations.
        It returns a plan that the BulkExecutor will execute.

        Args:
            objs: List of model instances to create
            batch_size: Number of objects per batch
            update_conflicts: Enable UPSERT on conflict
            unique_fields: Fields for conflict detection
            update_fields: Fields to update on conflict
            existing_record_ids: Set of id() for objects that exist in DB (from RecordClassifier)
            existing_pks_map: Dict mapping id(obj) -> pk for existing records (from RecordClassifier)

        Returns:
            MTICreatePlan object
        """
        from django_bulk_hooks.operations.mti_plans import MTICreatePlan

        if not objs:
            return None

        inheritance_chain = self.get_inheritance_chain()
        if len(inheritance_chain) <= 1:
            raise ValueError("build_create_plan called on non-MTI model")

        batch_size = batch_size or len(objs)

        # Use provided classification (no more DB query here!)
        if existing_record_ids is None:
            existing_record_ids = set()
        if existing_pks_map is None:
            existing_pks_map = {}

        # Set PKs on existing objects so they can be updated
        if existing_pks_map:
            for obj in objs:
                if id(obj) in existing_pks_map:
                    obj.pk = existing_pks_map[id(obj)]
                    obj.id = existing_pks_map[id(obj)]

        # Build parent levels
        parent_levels = self._build_parent_levels(
            objs,
            inheritance_chain,
            update_conflicts=update_conflicts,
            unique_fields=unique_fields,
            update_fields=update_fields,
            existing_record_ids=existing_record_ids,
            existing_pks_map=existing_pks_map,
        )

        # Build child object templates (without parent links - executor adds them)
        child_objects = []
        for obj in objs:
            child_obj = self._create_child_instance_template(obj, inheritance_chain[-1])
            child_objects.append(child_obj)

        # Pre-compute child-specific fields for execution efficiency
        from django_bulk_hooks.helpers import get_fields_for_model, filter_field_names_for_model

        child_unique_fields = get_fields_for_model(inheritance_chain[-1], unique_fields or [])
        child_update_fields = get_fields_for_model(inheritance_chain[-1], update_fields or [])

        return MTICreatePlan(
            inheritance_chain=inheritance_chain,
            parent_levels=parent_levels,
            child_objects=child_objects,
            child_model=inheritance_chain[-1],
            original_objects=objs,
            batch_size=batch_size,
            existing_record_ids=existing_record_ids,
            update_conflicts=update_conflicts,
            unique_fields=unique_fields or [],
            update_fields=update_fields or [],
            child_unique_fields=child_unique_fields,
            child_update_fields=child_update_fields,
        )

    def _build_parent_levels(
        self,
        objs,
        inheritance_chain,
        update_conflicts=False,
        unique_fields=None,
        update_fields=None,
        existing_record_ids=None,
        existing_pks_map=None,
    ):
        """
        Build parent level objects for each level in the inheritance chain.

        This is pure in-memory object creation - no DB operations.

        Returns:
            List of ParentLevel objects
        """
        from django_bulk_hooks.operations.mti_plans import ParentLevel

        parent_levels = []
        parent_instances_map = {}  # Maps obj id() -> {model_class: parent_instance}

        # Set defaults
        if existing_record_ids is None:
            existing_record_ids = set()
        if existing_pks_map is None:
            existing_pks_map = {}

        for level_idx, model_class in enumerate(inheritance_chain[:-1]):
            parent_objs_for_level = []

            for obj in objs:
                # Get current parent from previous level
                current_parent = None
                if level_idx > 0:
                    prev_parents = parent_instances_map.get(id(obj), {})
                    current_parent = prev_parents.get(inheritance_chain[level_idx - 1])

                # Create parent instance
                parent_obj = self._create_parent_instance(obj, model_class, current_parent)
                parent_objs_for_level.append(parent_obj)

                # Store in map
                if id(obj) not in parent_instances_map:
                    parent_instances_map[id(obj)] = {}
                parent_instances_map[id(obj)][model_class] = parent_obj

            # Determine upsert parameters for this level
            level_update_conflicts = False
            level_unique_fields = []
            level_update_fields = []

            if update_conflicts and unique_fields:
                # Filter unique_fields and update_fields to only those in this model
                model_fields_by_name = {f.name: f for f in model_class._meta.local_fields}

                # Normalize unique fields
                normalized_unique = []
                for uf in unique_fields or []:
                    if uf in model_fields_by_name:
                        normalized_unique.append(uf)
                    elif uf.endswith("_id") and uf[:-3] in model_fields_by_name:
                        normalized_unique.append(uf[:-3])

                # Check if this model has a matching constraint
                if normalized_unique and self._has_matching_constraint(model_class, normalized_unique):
                    # Filter update fields
                    filtered_updates = [uf for uf in (update_fields or []) if uf in model_fields_by_name]

                    # If no fields to update at this level but we need upsert to prevent
                    # unique constraint violations, use one of the unique fields as a dummy
                    # update field (updating it to itself is a safe no-op)
                    if not filtered_updates and normalized_unique:
                        filtered_updates = [normalized_unique[0]]

                    # CRITICAL FIX: Always include auto_now fields in updates to ensure timestamps are updated.
                    # During MTI upsert, parent tables need auto_now fields updated even when only child fields change.
                    # This ensures parent-level timestamps (e.g., updated_at) refresh correctly on upsert.
                    auto_now_fields = self._get_auto_now_fields_for_model(model_class, model_fields_by_name)
                    if auto_now_fields:
                        # Convert to set to avoid duplicates, then back to list for consistency
                        filtered_updates = list(set(filtered_updates) | set(auto_now_fields))

                    # Only enable upsert if we have fields to update (real or dummy)
                    if filtered_updates:
                        level_update_conflicts = True
                        level_unique_fields = normalized_unique
                        level_update_fields = filtered_updates
                else:
                    # CRITICAL FIX: Even if this parent level doesn't have the unique constraint,
                    # we still need update_conflicts=True during MTI upsert. Without it, parent
                    # does plain INSERT creating a new parent record with a new PK, breaking the
                    # MTI relationship and causing child INSERT to fail on its unique constraint.
                    #
                    # Solution: Use the primary key as the unique field for parent levels.
                    # In MTI upsert with existing_pks_map, parent objects will get their PKs from
                    # bulk_create, and we need those PKs to match existing records, not create new ones.
                    if existing_record_ids and existing_pks_map:
                        # Use primary key for upsert matching at this level
                        pk_field = model_class._meta.pk
                        level_update_conflicts = True
                        level_unique_fields = [pk_field.name]
                        # Use a safe update field - pick the first available non-PK field
                        # or use the PK itself as a dummy (updating to itself is a no-op)
                        available_fields = [
                            f.name
                            for f in model_class._meta.local_fields
                            if not isinstance(f, AutoField) and f.name in model_fields_by_name
                        ]
                        level_update_fields = available_fields[:1] if available_fields else [pk_field.name]

                        # CRITICAL FIX: Include auto_now fields in update_fields to ensure timestamps are updated.
                        # During MTI upsert, parent tables need auto_now fields updated even when using dummy fields.
                        # This ensures parent-level timestamps (e.g., updated_at) refresh correctly on upsert.
                        auto_now_fields = self._get_auto_now_fields_for_model(model_class, model_fields_by_name)
                        if auto_now_fields:
                            # Convert to set to avoid duplicates, then back to list for consistency
                            level_update_fields = list(set(level_update_fields) | set(auto_now_fields))

            # Create parent level
            parent_level = ParentLevel(
                model_class=model_class,
                objects=parent_objs_for_level,
                original_object_map={id(p): id(o) for p, o in zip(parent_objs_for_level, objs)},
                update_conflicts=level_update_conflicts,
                unique_fields=level_unique_fields,
                update_fields=level_update_fields,
            )
            parent_levels.append(parent_level)

        return parent_levels

    def _get_auto_now_fields_for_model(self, model_class, model_fields_by_name):
        """
        Get auto_now (not auto_now_add) fields for a specific model.

        Only includes fields that exist in model_fields_by_name to ensure
        they're valid local fields for this model level.

        Args:
            model_class: Model class to get fields for
            model_fields_by_name: Dict of valid field names for this model level

        Returns:
            List of auto_now field names (excluding auto_now_add)
        """
        auto_now_fields = []
        for field in model_class._meta.local_fields:
            # Only include auto_now (not auto_now_add) since auto_now_add should only be set on creation
            if getattr(field, "auto_now", False) and not getattr(field, "auto_now_add", False):
                # Double-check field exists in model_fields_by_name for safety
                if field.name in model_fields_by_name:
                    auto_now_fields.append(field.name)
        return auto_now_fields

    def _has_matching_constraint(self, model_class, normalized_unique):
        """Check if model has a unique constraint matching the given fields."""
        try:
            from django.db.models import UniqueConstraint

            constraint_field_sets = [tuple(c.fields) for c in model_class._meta.constraints if isinstance(c, UniqueConstraint)]
        except Exception:
            constraint_field_sets = []

        # Check unique_together
        ut = getattr(model_class._meta, "unique_together", ()) or ()
        if isinstance(ut, tuple) and ut and not isinstance(ut[0], (list, tuple)):
            ut = (ut,)
        ut_field_sets = [tuple(group) for group in ut]

        # Check individual field uniqueness
        unique_field_sets = []
        for field in model_class._meta.local_fields:
            if field.unique and not field.primary_key:
                unique_field_sets.append((field.name,))

        # Compare as sets
        provided_set = set(normalized_unique)
        all_constraint_sets = constraint_field_sets + ut_field_sets + unique_field_sets

        for group in all_constraint_sets:
            if provided_set == set(group):
                return True
        return False

    def _create_parent_instance(self, source_obj, parent_model, current_parent):
        """
        Create a parent instance from source object (in-memory only).

        Args:
            source_obj: Original object with data
            parent_model: Parent model class to create instance of
            current_parent: Parent instance from previous level (if any)

        Returns:
            Parent model instance (not saved)
        """
        parent_obj = parent_model()

        # Copy field values from source using centralized field extraction
        for field in parent_model._meta.local_fields:
            # Skip AutoField (primary key) - let Django's bulk_create with update_conflicts
            # handle PK assignment based on unique_fields. Setting PKs manually here causes
            # conflicts when parent records exist but update_conflicts isn't properly configured
            # for this level, leading to IntegrityError on primary key constraint.
            if isinstance(field, AutoField):
                continue

            if hasattr(source_obj, field.name):
                # Use centralized field value extraction for consistent FK handling
                value = get_field_value_for_db(source_obj, field.name, source_obj.__class__)
                if value is not None:
                    setattr(parent_obj, field.attname, value)

        # Link to parent if exists
        if current_parent is not None:
            for field in parent_model._meta.local_fields:
                if hasattr(field, "remote_field") and field.remote_field and field.remote_field.model == current_parent.__class__:
                    setattr(parent_obj, field.name, current_parent)
                    break

        # Copy object state
        if hasattr(source_obj, "_state") and hasattr(parent_obj, "_state"):
            parent_obj._state.adding = source_obj._state.adding
            if hasattr(source_obj._state, "db"):
                parent_obj._state.db = source_obj._state.db

        # Use unified auto-now field handling
        from django_bulk_hooks.operations.field_utils import handle_auto_now_fields_for_inheritance_chain

        # Handle auto fields for this single parent model
        handle_auto_now_fields_for_inheritance_chain(
            [parent_model],
            [parent_obj],
            for_update=False,  # MTI create is like insert
        )

        return parent_obj

    def _create_child_instance_template(self, source_obj, child_model):
        """
        Create a child instance template (in-memory only, without parent links).

        The executor will add parent links after creating parent objects.

        Args:
            source_obj: Original object with data
            child_model: Child model class

        Returns:
            Child model instance (not saved, no parent links)
        """
        child_obj = child_model()

        # Copy field values (excluding AutoField, parent links, and inherited fields)
        # In MTI, child objects should only have values for fields defined directly on the child model
        parent_fields = set()
        for parent_model in child_model._meta.parents.keys():
            parent_fields.update(f.name for f in parent_model._meta.local_fields)

        for field in child_model._meta.local_fields:
            if isinstance(field, AutoField):
                continue

            # Skip parent link fields - executor will set these
            if field.is_relation and hasattr(field, "related_model"):
                # Check if this field is a parent link
                if child_model._meta.get_ancestor_link(field.related_model) == field:
                    continue

            # Skip inherited fields - these belong to parent models
            if field.name in parent_fields:
                continue

            if hasattr(source_obj, field.name):
                # Use centralized field value extraction for consistent FK handling
                value = get_field_value_for_db(source_obj, field.name, source_obj.__class__)
                if value is not None:
                    setattr(child_obj, field.attname, value)

        # Copy object state
        if hasattr(source_obj, "_state") and hasattr(child_obj, "_state"):
            child_obj._state.adding = source_obj._state.adding
            if hasattr(source_obj._state, "db"):
                child_obj._state.db = source_obj._state.db

        # Use unified auto-now field handling
        from django_bulk_hooks.operations.field_utils import handle_auto_now_fields_for_inheritance_chain

        # Handle auto fields for this single child model
        handle_auto_now_fields_for_inheritance_chain(
            [child_model],
            [child_obj],
            for_update=False,  # MTI create is like insert
        )

        return child_obj

    # ==================== MTI BULK UPDATE PLANNING ====================

    def build_update_plan(self, objs, fields, batch_size=None):
        """
        Build an execution plan for bulk updating MTI model instances.

        This method does NOT execute any database operations.

        Args:
            objs: List of model instances to update
            fields: List of field names to update (auto_now fields already included by executor)
            batch_size: Number of objects per batch

        Returns:
            MTIUpdatePlan object
        """
        from django_bulk_hooks.operations.mti_plans import ModelFieldGroup
        from django_bulk_hooks.operations.mti_plans import MTIUpdatePlan

        if not objs:
            return None

        inheritance_chain = self.get_inheritance_chain()
        if len(inheritance_chain) <= 1:
            raise ValueError("build_update_plan called on non-MTI model")

        batch_size = batch_size or len(objs)

        # Note: auto_now fields are already handled by executor.bulk_update()
        # which calls pre_save() and includes them in the fields list

        # Group fields by model
        field_groups = []
        for model_idx, model in enumerate(inheritance_chain):
            model_fields = []

            for field_name in fields:
                try:
                    field = self.model_cls._meta.get_field(field_name)
                    if field in model._meta.local_fields:
                        # Skip auto_now_add fields for updates
                        if not getattr(field, "auto_now_add", False):
                            model_fields.append(field_name)
                except Exception:
                    continue

            if model_fields:
                # Determine filter field
                if model_idx == 0:
                    filter_field = "pk"
                else:
                    # Find parent link
                    parent_link = None
                    for parent_model in inheritance_chain:
                        if parent_model in model._meta.parents:
                            parent_link = model._meta.parents[parent_model]
                            break
                    filter_field = parent_link.attname if parent_link else "pk"

                field_groups.append(
                    ModelFieldGroup(
                        model_class=model,
                        fields=model_fields,
                        filter_field=filter_field,
                    )
                )

        return MTIUpdatePlan(
            inheritance_chain=inheritance_chain,
            field_groups=field_groups,
            objects=objs,
            batch_size=batch_size,
        )
