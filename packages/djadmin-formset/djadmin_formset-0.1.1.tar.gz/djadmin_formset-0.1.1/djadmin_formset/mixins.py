"""
View mixins for djadmin-formset plugin.

Provides minimal glue code to connect djadmin's Layout API to django-formset's
FormCollectionViewMixin. The heavy lifting is done by:
- FormCollectionViewMixin: Handles JSON POST, renders FormCollections
- FormFactory: Converts Layout to FormCollection
- EditCollectionView: Provides form_collection_valid() that saves via construct_instance()
"""


class DjAdminFormsetBaseMixin:
    """
    Base mixin that provides get_collection_class() for FormCollectionViewMixin.

    This mixin provides:
    - get_collection_class() to convert Layout to FormCollection
    - _flatten_fieldsets_in_place() to preprocess FormCollection structure
    - form_collection_valid() that flattens and delegates to django-formset

    The key insight is that our hierarchical FormCollection structure (Fieldsets, Rows)
    splits fields across multiple forms. We flatten Fieldsets/Rows into single forms
    per instance, then delegate to django-formset's construct_instance() which handles
    both parent fields and Collection (inline) CRUD operations correctly.

    This approach:
    - Eliminates IntegrityError for CREATE (all required fields in one form)
    - Fixes field name conflicts for UPDATE (proper form structure)
    - Works for both CREATE and UPDATE with unified logic
    - Delegates to django-formset for Collections (create/update/delete)

    Subclasses:
    - DjAdminFormsetCreateMixin: For CREATE actions (creates new instance)
    - DjAdminFormsetUpdateMixin: For UPDATE actions (loads existing instance)
    """

    def _get_action_specific_layout(self):
        """
        Get the appropriate layout based on the action type.

        Follows the same pattern as FormFeaturesMixin.get_form_features():
        - CreateViewActionMixin → create_layout or layout
        - UpdateViewActionMixin → update_layout or layout
        - Other actions → layout

        Note: Attributes are copied from model_admin to view by the core plugin's
        djadmin_get_action_view_attributes hook.

        Handles two scenarios:
        1. Tests: View directly inherits from action mixin → check isinstance(self, Mixin)
        2. Production: Base class replaced by plugin → check isinstance(self.action, Mixin)

        Returns:
            Layout: The appropriate layout for this action
        """
        from djadmin.actions.view_mixins import CreateViewActionMixin, UpdateViewActionMixin

        # Check both self (for tests/direct inheritance) and self.action (for production/base class replacement)
        action_obj = (
            self if isinstance(self, CreateViewActionMixin | UpdateViewActionMixin) else getattr(self, 'action', None)
        )

        if isinstance(action_obj, CreateViewActionMixin):
            # Create action: use create_layout or fallback to layout
            return getattr(self, 'create_layout', None) or getattr(self, 'layout', None)
        elif isinstance(action_obj, UpdateViewActionMixin):
            # Update action: use update_layout or fallback to layout
            return getattr(self, 'update_layout', None) or getattr(self, 'layout', None)
        else:
            # Other actions: use generic layout
            return getattr(self, 'layout', None)

    def get_collection_class(self):
        """
        Get the FormCollection class for this view.

        Called by FormCollectionViewMixin.get_form_collection().
        Converts the ModelAdmin's layout to a django-formset FormCollection.

        Returns:
            type: A FormCollection subclass built from the layout, or None
        """
        from djadmin_formset.factories import FormFactory
        from djadmin_formset.renderers import DjAdminFormRenderer

        # Get action-specific layout (follows FormFeaturesMixin pattern)
        layout = self._get_action_specific_layout()

        # If no layout, return None and FormCollectionViewMixin will use standard forms
        if not layout:
            return None

        # Convert to FormCollection using FormFactory
        # FormFactory creates all necessary forms internally from the model and layout
        form_collection_class = FormFactory.from_layout(
            layout=layout,
            model=self.model_admin.model,
            base_form=getattr(self, 'base_form_class', None),
            renderer=getattr(layout, 'renderer', None) or DjAdminFormRenderer,
        )

        return form_collection_class

    def _flatten_fieldsets_in_place(self, form_collection, instance):
        """
        Recursively flatten Fieldsets/Rows by merging forms in-place.

        For has_many=False (Fieldsets/Rows):
            1. Recursively flatten any nested Fieldsets/Rows
            2. Collect all forms' cleaned_data
            3. Merge into first form's cleaned_data
            4. Replace valid_holders with single merged form
            5. Update parent's cleaned_data dict

        For has_many=True (Collections):
            1. Keep Collection structure unchanged
            2. For each sibling, recursively flatten its Fieldsets/Rows

        Modifies form_collection.valid_holders and cleaned_data in-place.

        Args:
            form_collection: FormCollection to flatten
            instance: Model instance for this FormCollection
        """
        from django.forms import BaseModelForm
        from formset.collection import FormCollection

        if getattr(form_collection, 'has_many', False):
            # This is a Collection - process each sibling recursively
            for sibling_holders in form_collection.valid_holders:
                for _name, holder in sibling_holders.items():
                    if isinstance(holder, FormCollection):
                        # Recursively flatten Fieldsets within this Collection sibling
                        self._flatten_fieldsets_in_place(holder, holder.instance)
        else:
            # This is a Fieldset/Row - merge all forms into one, preserve Collections
            merged_data = {}
            first_form = None
            forms_to_merge = []
            collections = {}  # Preserve Collections

            # First pass: collect forms and Collections separately
            for name, holder in form_collection.valid_holders.items():
                if isinstance(holder, FormCollection):
                    if getattr(holder, 'has_many', False):
                        # This is a Collection - preserve it, don't flatten
                        collections[name] = holder
                    else:
                        # This is a nested Fieldset/Row - recurse to flatten it
                        self._flatten_fieldsets_in_place(holder, instance)
                        # After recursion, extract the merged form
                        if holder.valid_holders and isinstance(holder.valid_holders, dict):
                            nested_form = next(iter(holder.valid_holders.values()))
                            if hasattr(nested_form, 'cleaned_data'):
                                forms_to_merge.append(nested_form)
                elif isinstance(holder, BaseModelForm):
                    # Regular form - add to merge list
                    forms_to_merge.append(holder)

            # Second pass: merge all cleaned_data
            for form in forms_to_merge:
                merged_data.update(form.cleaned_data)
                if first_form is None:
                    first_form = form

            # Build new valid_holders with merged form + preserved Collections
            if first_form:
                first_form.cleaned_data = merged_data
                first_form.instance = instance
                # Start with merged form, then add Collections
                new_holders = {'main': first_form}
                new_holders.update(collections)
                form_collection.valid_holders = new_holders

    def form_collection_valid(self, form_collection):
        """
        Handle successful validation by flattening and delegating to django-formset.

        Steps:
        1. Flatten Fieldsets/Rows into single forms per instance
        2. Manually construct instance from flattened forms
        3. Let django-formset handle Collections (has_many=True)
        4. Save and return success response

        Works for both CREATE and UPDATE by preprocessing the FormCollection structure
        before construction. Flattening eliminates the IntegrityError (CREATE) and field
        name conflict (UPDATE) bugs.

        Args:
            form_collection: The validated FormCollection

        Returns:
            JsonResponse with success_url or revalidation response
        """
        from django.db import transaction
        from django.http import JsonResponse
        from formset.collection import FormCollection

        with transaction.atomic():
            # Flatten Fieldsets/Rows in-place
            self._flatten_fieldsets_in_place(form_collection, self.object)

            # After flattening, all Fieldsets/Rows should have a single 'main' form
            # with all fields merged. Manually apply cleaned_data to the instance.
            if 'main' in form_collection.valid_holders:
                merged_form = form_collection.valid_holders['main']
                # Separate M2M fields from regular fields
                m2m_data = {}
                for field_name, value in merged_form.cleaned_data.items():
                    try:
                        field = self.object._meta.get_field(field_name)
                        if field.many_to_many:
                            # Save M2M fields for after instance is saved
                            m2m_data[field_name] = value
                        else:
                            # Regular field - set directly
                            setattr(self.object, field_name, value)
                    except Exception:
                        # Field might not exist on model, skip it
                        pass

                # Save instance first (required before setting M2M fields)
                self.object.save()

                # Now set M2M fields
                for field_name, value in m2m_data.items():
                    getattr(self.object, field_name).set(value)

            # Handle Collections separately (they weren't flattened)
            for _name, holder in form_collection.valid_holders.items():
                if isinstance(holder, FormCollection) and getattr(holder, 'has_many', False):
                    # CRITICAL: Pass parent instance so django-formset can set the FK!
                    # Django-formset uses this to do: child_instance.fk_field = parent_instance
                    # Our custom retrieve_instance() ensures each form.instance is the CHILD,
                    # so construct_instance() applies data to child, then sets FK.
                    holder.construct_instance(self.object)  # Pass parent for FK linking

        # Revalidate in case of integrity errors
        if form_collection.is_valid():
            return JsonResponse({'success_url': self.get_success_url()})
        else:
            return self.form_collection_invalid(form_collection)


class DjAdminFormsetCreateMixin(DjAdminFormsetBaseMixin):
    """
    Mixin for CREATE actions (AddAction).

    Responsibility: Create a new model instance before form_collection_valid() saves it.

    The base class handles all the form processing logic. This mixin only needs to:
    1. Override get_object() to return None (no existing object)
    2. Override post() to create a new instance and bypass EditCollectionView.post()
       (which would overwrite self.object with None from get_object())
    """

    def get_object(self, queryset=None):
        """
        Return None for CREATE actions.

        FormCollectionViewMixin.get_form_collection() checks if get_object() is callable
        and calls it if so. For CREATE actions, there is no existing object, so we
        return None instead of raising an error.
        """
        return None

    def post(self, request, *args, **kwargs):
        """
        Create a new instance and handle form submission.

        We must bypass EditCollectionView.post() because it does:
            self.object = self.get_object()
        which would overwrite our newly created instance with None.

        Instead, we call FormCollectionViewMixin.post() directly.
        """
        from formset.views import FormCollectionViewMixin

        # Create a new instance of the model
        self.object = self.model_admin.model()

        # Skip EditCollectionView.post() to avoid self.object being set to None
        # Call FormCollectionViewMixin.post() directly
        return FormCollectionViewMixin.post(self, request, *args, **kwargs)


class DjAdminFormsetUpdateMixin(DjAdminFormsetBaseMixin):
    """
    Mixin for UPDATE actions (EditRecordAction).

    Inherits all functionality from DjAdminFormsetBaseMixin. The unified
    form_collection_valid() method in the base class works for both CREATE
    and UPDATE actions through the fieldset flattening approach.

    No overrides needed - the base class handles everything.
    """

    pass
