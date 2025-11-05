"""
Utilities for field value extraction and normalization.

Single source of truth for converting model instance field values
to their database representation. This eliminates duplicate FK handling
logic scattered across multiple components.
"""

import logging

from django.db.models import ForeignKey

logger = logging.getLogger(__name__)


def get_field_value_for_db(obj, field_name, model_cls=None):
    """
    Get a field value from an object in its database-ready form.

    For regular fields: returns the field value as-is
    For FK fields: returns the PK (integer) instead of the related object

    This ensures consistent handling across all operations (upsert classification,
    bulk create, bulk update, etc.)

    Args:
        obj: Model instance
        field_name: Name of the field to extract
        model_cls: Model class (optional, will infer from obj if not provided)

    Returns:
        Database-ready value (FK as integer, regular fields as-is)
    """
    if model_cls is None:
        model_cls = obj.__class__

    try:
        field = model_cls._meta.get_field(field_name)
    except Exception:  # noqa: BLE001
        # Field doesn't exist - just get attribute
        return getattr(obj, field_name, None)

    # Check if it's a ForeignKey
    if isinstance(field, ForeignKey):
        # For FK fields, always use attname (e.g., 'business_id' not 'business')
        # This gets the raw FK ID value from the database field
        return getattr(obj, field.attname, None)

    # Regular field - get normally
    return getattr(obj, field_name, None)


def get_field_values_for_db(obj, field_names, model_cls=None):
    """
    Get multiple field values from an object in database-ready form.

    Args:
        obj: Model instance
        field_names: List of field names
        model_cls: Model class (optional)

    Returns:
        Dict of {field_name: db_value}
    """
    if model_cls is None:
        model_cls = obj.__class__

    return {field_name: get_field_value_for_db(obj, field_name, model_cls) for field_name in field_names}


def normalize_field_name_to_db(field_name, model_cls):
    """
    Normalize a field name to its database column name.

    For FK fields referenced by relationship name, returns the attname (e.g., 'business' -> 'business_id')
    For regular fields, returns as-is.

    Args:
        field_name: Field name (can be 'business' or 'business_id')
        model_cls: Model class

    Returns:
        Database column name
    """
    try:
        field = model_cls._meta.get_field(field_name)
        if isinstance(field, ForeignKey):
            return field.attname  # Returns 'business_id' for 'business' field
        return field_name
    except Exception:  # noqa: BLE001
        return field_name


def get_changed_fields(old_obj, new_obj, model_cls, skip_auto_fields=False):
    """
    Get field names that have changed between two model instances.

    Uses Django's field.get_prep_value() for proper database-level comparison.
    This is the canonical implementation used by both RecordChange and ModelAnalyzer.

    Args:
        old_obj: The old model instance
        new_obj: The new model instance
        model_cls: The Django model class
        skip_auto_fields: Whether to skip auto_created fields (default False)

    Returns:
        Set of field names that have changed
    """
    changed = set()

    for field in model_cls._meta.fields:
        # Skip primary key fields - they shouldn't change
        if field.primary_key:
            continue

        # Optionally skip auto-created fields (for bulk operations)
        if skip_auto_fields and field.auto_created:
            continue

        old_val = getattr(old_obj, field.name, None)
        new_val = getattr(new_obj, field.name, None)

        # Use field's get_prep_value for database-ready comparison
        # This handles timezone conversions, type coercions, etc.
        try:
            old_prep = field.get_prep_value(old_val)
            new_prep = field.get_prep_value(new_val)
            if old_prep != new_prep:
                changed.add(field.name)
        except (TypeError, ValueError):
            # Fallback to direct comparison if get_prep_value fails
            if old_val != new_val:
                changed.add(field.name)

    return changed


def get_auto_fields(model_cls, include_auto_now_add=True):
    """
    Get auto fields from a model.

    Args:
        model_cls: Django model class
        include_auto_now_add: Whether to include auto_now_add fields

    Returns:
        List of field names
    """
    fields = []
    for field in model_cls._meta.fields:
        if getattr(field, "auto_now", False) or (include_auto_now_add and getattr(field, "auto_now_add", False)):
            fields.append(field.name)
    return fields


def get_auto_now_only_fields(model_cls):
    """Get only auto_now fields (excluding auto_now_add)."""
    return get_auto_fields(model_cls, include_auto_now_add=False)


def get_fk_fields(model_cls):
    """Get foreign key field names for a model."""
    return [field.name for field in model_cls._meta.concrete_fields if field.is_relation and not field.many_to_many]


def collect_auto_now_fields_for_inheritance_chain(inheritance_chain):
    """Collect auto_now fields across an MTI inheritance chain."""
    all_auto_now = set()
    for model_cls in inheritance_chain:
        all_auto_now.update(get_auto_now_only_fields(model_cls))
    return all_auto_now


def handle_auto_now_fields_for_inheritance_chain(models, instances, for_update=True):
    """
    Unified auto-now field handling for any inheritance chain.

    This replaces the separate collect/pre_save logic with a single comprehensive
    method that handles collection, pre-saving, and field inclusion for updates.

    Args:
        models: List of model classes in inheritance chain
        instances: List of model instances to process
        for_update: Whether this is for an update operation (vs create)

    Returns:
        Set of auto_now field names that should be included in updates
    """
    all_auto_now_fields = set()

    for model_cls in models:
        for field in model_cls._meta.local_fields:
            # For updates, only include auto_now (not auto_now_add)
            # For creates, include both
            if getattr(field, "auto_now", False) or (not for_update and getattr(field, "auto_now_add", False)):
                all_auto_now_fields.add(field.name)

                # Pre-save the field on instances
                for instance in instances:
                    if for_update:
                        # For updates, only pre-save auto_now fields
                        field.pre_save(instance, add=False)
                    else:
                        # For creates, pre-save both auto_now and auto_now_add
                        field.pre_save(instance, add=True)

    return all_auto_now_fields


def pre_save_auto_now_fields(objects, inheritance_chain):
    """Pre-save auto_now fields across inheritance chain."""
    # DEPRECATED: Use handle_auto_now_fields_for_inheritance_chain instead
    auto_now_fields = collect_auto_now_fields_for_inheritance_chain(inheritance_chain)

    for field_name in auto_now_fields:
        # Find which model has this field
        for model_cls in inheritance_chain:
            try:
                field = model_cls._meta.get_field(field_name)
                if getattr(field, "auto_now", False):
                    for obj in objects:
                        field.pre_save(obj, add=False)
                    break
            except Exception:
                continue
