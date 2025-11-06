"""
Utility functions for djadmin-formset plugin.

Provides helpers for working with django-formset FormCollections,
including test utilities for building POST data.
"""

from decimal import Decimal


def _convert_value_for_json(value):
    """Convert Python values to JSON-serializable format."""
    if isinstance(value, Decimal):
        return str(value)
    elif isinstance(value, list | tuple):
        return [_convert_value_for_json(v) for v in value]
    elif isinstance(value, dict):
        return {k: _convert_value_for_json(v) for k, v in value.items()}
    return value


def build_create_post_data(model_admin, **field_values):
    """
    Build hierarchical POST data for testing CREATE operations.

    Builds the hierarchical structure from scratch based on the layout,
    populating fields with the provided values.

    Args:
        model_admin: The ModelAdmin instance with a layout
        **field_values: Field values to include in the POST data

    Returns:
        dict: Hierarchical data dict ready for JSON POST

    Example:
        >>> post_data = build_create_post_data(
        ...     product_admin,
        ...     name='New Product',
        ...     price='99.99',
        ...     category=category.id
        ... )
        >>> response = client.post(url, data=post_data, content_type='application/json')
    """
    from djadmin.layout import Collection, Field, Fieldset, Row

    from djadmin_formset.factories import FormFactory

    # Get layout
    layout = getattr(model_admin, 'layout', None)
    if not layout:
        raise ValueError(f'{model_admin.__class__.__name__} has no layout')

    hierarchical_data = {}

    def build_structure(item, item_index, parent_dict):
        """Build hierarchical structure from layout."""
        if isinstance(item, Field):
            # Single field: {field_name: {field_name: value}}
            value = field_values.get(item.name, '')
            parent_dict[item.name] = {item.name: value}

        elif isinstance(item, Fieldset):
            # Fieldset: nested dict
            fieldset_name = FormFactory._slugify_legend(item.legend) or f'fieldset_{item_index}'
            fieldset_dict = {}
            for idx, field_item in enumerate(item.fields):
                build_structure(field_item, idx, fieldset_dict)
            parent_dict[fieldset_name] = fieldset_dict

        elif isinstance(item, Row):
            # Row: {row_name: {'main': {field1: val1, ...}}}
            row_name = f'row_{item_index}'
            row_main = {}
            for field in item.fields:
                if isinstance(field, Field):
                    row_main[field.name] = field_values.get(field.name, '')
            parent_dict[row_name] = {'main': row_main}

        elif isinstance(item, Collection):
            # Collection: list of dicts (empty for create)
            parent_dict[item.name] = field_values.get(item.name, [])

    for idx, item in enumerate(layout.items):
        build_structure(item, idx, hierarchical_data)

    # Convert Decimal and other non-JSON-serializable values
    hierarchical_data = _convert_value_for_json(hierarchical_data)

    # Wrap in formset_data key as expected by FormCollectionViewMixin
    return {'formset_data': hierarchical_data}


def build_update_post_data(model_admin, instance, **field_updates):
    """
    Build hierarchical POST data for testing UPDATE operations.

    Uses django-formset's model_to_dict() to get current data from the instance,
    then updates with the provided field values.

    Args:
        model_admin: The ModelAdmin instance with a layout
        instance: The model instance being updated
        **field_updates: Field values to update/override

    Returns:
        dict: Hierarchical data dict ready for JSON POST

    Example:
        >>> post_data = build_update_post_data(
        ...     product_admin,
        ...     instance=product,
        ...     price='149.99'  # Update just the price
        ... )
        >>> response = client.post(url, data=post_data, content_type='application/json')
    """
    from djadmin_formset.factories import FormFactory
    from djadmin_formset.renderers import DjAdminFormRenderer

    # Get layout
    layout = getattr(model_admin, 'layout', None)
    if not layout:
        raise ValueError(f'{model_admin.__class__.__name__} has no layout')

    # Build FormCollection
    form_collection_class = FormFactory.from_layout(
        layout=layout,
        model=model_admin.model,
        renderer=DjAdminFormRenderer,
    )

    # Use model_to_dict to get hierarchical data from instance
    hierarchical_data = form_collection_class().model_to_dict(instance)

    # Update fields with provided values
    def update_fields(data_dict, field_updates):
        """Recursively update field values in hierarchical structure."""
        for key, value in data_dict.items():
            if isinstance(value, dict):
                # Check if this is a single-field form: {field_name: {field_name: value}}
                if len(value) == 1 and list(value.keys())[0] == key:
                    # Update this field if it's in field_updates
                    if key in field_updates:
                        data_dict[key] = {key: field_updates[key]}
                elif 'main' in value and isinstance(value['main'], dict):
                    # This is a row form: {row_name: {'main': {field1: val1, ...}}}
                    for field_name in value['main'].keys():
                        if field_name in field_updates:
                            value['main'][field_name] = field_updates[field_name]
                else:
                    # Recurse into nested structures
                    update_fields(value, field_updates)

    update_fields(hierarchical_data, field_updates)

    # Convert Decimal and other non-JSON-serializable values
    hierarchical_data = _convert_value_for_json(hierarchical_data)

    # Wrap in formset_data key as expected by FormCollectionViewMixin
    return {'formset_data': hierarchical_data}
