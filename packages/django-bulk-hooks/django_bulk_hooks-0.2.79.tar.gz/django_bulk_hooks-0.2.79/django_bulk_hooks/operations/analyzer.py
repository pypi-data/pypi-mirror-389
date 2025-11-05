"""
Model analyzer service - Combines validation and field tracking.

This service handles all model analysis needs:
- Input validation
- Field change detection
- Field comparison
"""

import logging

from django_bulk_hooks.helpers import extract_pks
from .field_utils import get_changed_fields, get_auto_fields, get_fk_fields

logger = logging.getLogger(__name__)


class ModelAnalyzer:
    """
    Analyzes models and validates operations.

    This service combines the responsibilities of validation and field tracking
    since they're closely related and often used together.
    """

    def __init__(self, model_cls):
        """
        Initialize analyzer for a specific model.

        Args:
            model_cls: The Django model class
        """
        self.model_cls = model_cls

    # Define validation requirements per operation
    VALIDATION_REQUIREMENTS = {
        "bulk_create": ["types"],
        "bulk_update": ["types", "has_pks"],
        "delete": ["types"],
    }

    # ========== Validation Methods ==========

    def validate_for_operation(self, objs, operation):
        """
        Centralized validation method that applies operation-specific checks.

        Args:
            objs: List of model instances
            operation: String identifier for the operation

        Returns:
            True if validation passes

        Raises:
            TypeError: If type validation fails
            ValueError: If PK validation fails
        """
        requirements = self.VALIDATION_REQUIREMENTS.get(operation, [])

        # Apply each required validation check
        if "types" in requirements:
            self._check_types(objs, operation)
        if "has_pks" in requirements:
            self._check_has_pks(objs, operation)

        return True

    def validate_for_create(self, objs):
        """
        Validate objects for bulk_create operation.

        Args:
            objs: List of model instances

        Raises:
            TypeError: If objects are not instances of model_cls
        """
        return self.validate_for_operation(objs, "bulk_create")

    def validate_for_update(self, objs):
        """
        Validate objects for bulk_update operation.

        Args:
            objs: List of model instances

        Raises:
            TypeError: If objects are not instances of model_cls
            ValueError: If objects don't have primary keys
        """
        return self.validate_for_operation(objs, "bulk_update")

    def validate_for_delete(self, objs):
        """
        Validate objects for delete operation.

        Args:
            objs: List of model instances

        Raises:
            TypeError: If objects are not instances of model_cls
        """
        return self.validate_for_operation(objs, "delete")

    def _check_types(self, objs, operation="operation"):
        """Check that all objects are instances of the model class"""
        if not objs:
            return

        invalid_types = {type(obj).__name__ for obj in objs if not isinstance(obj, self.model_cls)}

        if invalid_types:
            raise TypeError(
                f"{operation} expected instances of {self.model_cls.__name__}, but got {invalid_types}",
            )

    def _check_has_pks(self, objs, operation="operation"):
        """Check that all objects have primary keys"""
        missing_pks = [obj for obj in objs if obj.pk is None]

        if missing_pks:
            raise ValueError(
                f"{operation} cannot operate on unsaved {self.model_cls.__name__} instances. "
                f"{len(missing_pks)} object(s) have no primary key.",
            )

    # ========== Data Fetching Methods ==========

    def fetch_old_records_map(self, instances):
        """
        Fetch old records for instances in a single bulk query.

        This is the SINGLE point of truth for fetching old records.
        All other methods should delegate to this.

        Args:
            instances: List of model instances

        Returns:
            Dict[pk, instance] for O(1) lookups
        """
        pks = extract_pks(instances)
        if not pks:
            return {}

        return {obj.pk: obj for obj in self.model_cls._base_manager.filter(pk__in=pks)}

    # ========== Field Introspection Methods ==========

    def get_auto_now_fields(self):
        """
        Get fields that have auto_now or auto_now_add set.

        Returns:
            list: Field names with auto_now behavior
        """
        return get_auto_fields(self.model_cls, include_auto_now_add=True)

    def get_fk_fields(self):
        """
        Get all foreign key fields for the model.

        Returns:
            list: FK field names
        """
        return get_fk_fields(self.model_cls)

    def detect_changed_fields(self, objs):
        """
        Detect which fields have changed across a set of objects.

        This method fetches old records from the database in a SINGLE bulk query
        and compares them with the new objects to determine changed fields.

        PERFORMANCE: Uses bulk query (O(1) queries) not N queries.

        Args:
            objs: List of model instances to check

        Returns:
            List of field names that changed across any object
        """
        if not objs:
            return []

        # Fetch old records using the single source of truth
        old_records_map = self.fetch_old_records_map(objs)
        if not old_records_map:
            return []

        # Track which fields changed across ALL objects
        changed_fields_set = set()

        # Compare each object with its database state
        for obj in objs:
            if obj.pk is None:
                continue

            old_obj = old_records_map.get(obj.pk)
            if old_obj is None:
                # Object doesn't exist in DB, skip
                continue

            # Use canonical field comparison (skips auto_created fields)
            changed_fields = get_changed_fields(old_obj, obj, self.model_cls, skip_auto_fields=True)
            changed_fields_set.update(changed_fields)

        # Return as sorted list for deterministic behavior
        return sorted(changed_fields_set)

    def resolve_expression(self, field_name, expression, instance):
        """
        Resolve a SQL expression to a concrete value for a specific instance.

        This method materializes database expressions (F(), Subquery, Case, etc.)
        into concrete values by using Django's annotate() mechanism.

        Args:
            field_name: Name of the field being updated
            expression: The expression or value to resolve
            instance: The model instance to resolve for

        Returns:
            The resolved concrete value
        """
        from django.db.models import Expression
        from django.db.models.expressions import Combinable

        # Simple value - return as-is
        if not isinstance(expression, (Expression, Combinable)):
            return expression

        # For complex expressions, evaluate them in database context
        # Use annotate() which Django properly handles for all expression types
        try:
            # Create a queryset for just this instance
            instance_qs = self.model_cls.objects.filter(pk=instance.pk)

            # Use annotate with the expression and let Django resolve it
            resolved_value = (
                instance_qs.annotate(
                    _resolved_value=expression,
                )
                .values_list("_resolved_value", flat=True)
                .first()
            )

            return resolved_value
        except Exception as e:
            # If expression resolution fails, log and return original
            logger.warning(
                f"Failed to resolve expression for field '{field_name}' on {self.model_cls.__name__}: {e}. Using original value.",
            )
            return expression

    def apply_update_values(self, instances, update_kwargs):
        """
        Apply update_kwargs to instances, resolving any SQL expressions.

        This method transforms queryset.update()-style kwargs (which may contain
        F() expressions, Subquery, Case, etc.) into concrete values and applies
        them to the instances.

        Args:
            instances: List of model instances to update
            update_kwargs: Dict of {field_name: value_or_expression}

        Returns:
            List of field names that were updated
        """
        from django.db.models import Expression
        from django.db.models.expressions import Combinable

        if not instances or not update_kwargs:
            return []

        fields_updated = list(update_kwargs.keys())

        # Extract PKs
        pks = [inst.pk for inst in instances if inst.pk is not None]
        if not pks:
            return fields_updated

        # Process each field
        for field_name, value in update_kwargs.items():
            # Simple value - same for all instances
            if not isinstance(value, (Expression, Combinable)):
                for instance in instances:
                    setattr(instance, field_name, value)
                continue

            # Complex expression - resolve in single query for all instances
            try:
                # Create a queryset for all instances
                qs = self.model_cls.objects.filter(pk__in=pks)

                # Annotate with the expression and fetch results
                results = qs.annotate(
                    _resolved_value=value,
                ).values_list("pk", "_resolved_value")

                # Build mapping
                value_map = dict(results)

                # Apply to instances
                for instance in instances:
                    if instance.pk in value_map:
                        setattr(instance, field_name, value_map[instance.pk])

            except Exception as e:
                # If expression resolution fails, log and use original
                logger.warning(
                    f"Failed to resolve expression for field '{field_name}' on {self.model_cls.__name__}: {e}. Using original value.",
                )
                for instance in instances:
                    setattr(instance, field_name, value)

        return fields_updated
