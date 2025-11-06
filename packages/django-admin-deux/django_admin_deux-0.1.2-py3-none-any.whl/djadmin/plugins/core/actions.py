"""Default CRUD actions provided by core plugin"""

from django.urls import reverse

from djadmin.actions import BaseAction, BulkActionMixin, FormFeaturesMixin, GeneralActionMixin, RecordActionMixin
from djadmin.actions.view_mixins import (
    BulkDeleteViewActionMixin,
    CreateViewActionMixin,
    DeleteViewActionMixin,
    DetailViewActionMixin,
    UpdateViewActionMixin,
)


class AddAction(GeneralActionMixin, FormFeaturesMixin, CreateViewActionMixin, BaseAction):
    """
    Action to add a new record.

    Displays a form to create a new instance of the model.
    Uses CreateViewActionMixin to generate a CreateView via ViewFactory.
    """

    label = 'Add'
    icon = 'plus'
    css_class = 'primary'
    django_permission_name = 'add'  # Django permission for creating records

    def get_url_pattern(self) -> str:
        """
        Get URL pattern for Add action.

        Uses __new__ convention instead of /actions/ prefix.

        Returns:
            URL pattern string (e.g., 'webshop/category/__new__/')
        """
        opts = self.model._meta
        return f'{opts.app_label}/{opts.model_name}/__new__/'

    def get_template_name(self):
        """Template for create form"""
        opts = self.model._meta
        return [
            f'djadmin/{opts.app_label}/{opts.model_name}_add.html',
            'djadmin/actions/add.html',
        ]

    def get_fields(self):
        """Get fields for create form from model_admin"""
        return self.model_admin.create_fields or self.model_admin.fields or '__all__'

    def get_form_class(self):
        """Get form class for creating new record"""
        # Validate that required features are available
        self.validate_features()

        # Check if ModelAdmin has a create-specific or generic layout
        layout = self.model_admin.create_layout or self.model_admin.layout
        if layout:
            # Build form from layout using FormBuilder
            from djadmin.forms import FormBuilder

            # Use create_form_class or form_class as base if provided
            base_form = self.model_admin.create_form_class or self.model_admin.form_class
            return FormBuilder.from_layout(layout, self.model, base_form)

        # Use create_form_class if set
        if self.model_admin.create_form_class:
            return self.model_admin.create_form_class

        # Use generic form_class if set
        if self.model_admin.form_class:
            return self.model_admin.form_class

        # Auto-generate ModelForm
        from django.forms import modelform_factory

        return modelform_factory(self.model, fields=self.get_fields())

    def get_success_url(self):
        """
        Redirect to list view after creation.

        When bound to the view, self is the view instance which has:
        - self.object: The created object
        - self.request: The current request
        """
        opts = self.model._meta
        return reverse(
            f'djadmin:{opts.app_label}_{opts.model_name}_list',
            current_app=self.admin_site.name,
        )


class EditRecordAction(RecordActionMixin, FormFeaturesMixin, UpdateViewActionMixin, BaseAction):
    """
    Action to edit an existing record.

    Displays a form to update the selected instance.
    Uses UpdateViewActionMixin to generate an UpdateView via ViewFactory.
    """

    label = 'Edit'
    icon = 'pencil'
    css_class = 'primary'
    django_permission_name = 'change'  # Django permission for updating records
    _url_name = 'edit'

    def get_url_pattern(self) -> str:
        """
        Get URL pattern for Edit action.

        Returns:
            URL pattern string with pk parameter
        """
        opts = self.model._meta
        return f'{opts.app_label}/{opts.model_name}/<int:pk>/actions/edit/'

    def get_template_name(self):
        """Template for update form"""
        opts = self.model._meta
        return [
            f'djadmin/{opts.app_label}/{opts.model_name}_edit.html',
            'djadmin/actions/edit.html',
        ]

    def get_fields(self):
        """Get fields for update form from model_admin"""
        return self.model_admin.update_fields or self.model_admin.fields or '__all__'

    def get_form_class(self):
        """Get form class for updating record"""
        # Validate that required features are available
        self.validate_features()

        # Check if ModelAdmin has an update-specific or generic layout
        layout = self.model_admin.update_layout or self.model_admin.layout
        if layout:
            # Build form from layout using FormBuilder
            from djadmin.forms import FormBuilder

            # Use update_form_class or form_class as base if provided
            base_form = self.model_admin.update_form_class or self.model_admin.form_class
            return FormBuilder.from_layout(layout, self.model, base_form)

        # Use update_form_class if set
        if self.model_admin.update_form_class:
            return self.model_admin.update_form_class

        # Use generic form_class if set
        if self.model_admin.form_class:
            return self.model_admin.form_class

        # Auto-generate ModelForm
        from django.forms import modelform_factory

        return modelform_factory(self.model, fields=self.get_fields())

    def get_success_url(self):
        """
        Redirect to list view after update.

        When bound to the view, self is the view instance which has:
        - self.object: The updated object
        - self.request: The current request
        """
        opts = self.model._meta
        return reverse(
            f'djadmin:{opts.app_label}_{opts.model_name}_list',
            current_app=self.admin_site.name,
        )


class DeleteRecordAction(RecordActionMixin, DeleteViewActionMixin, BaseAction):
    """
    Action to delete a single record.

    Shows confirmation page before deleting.
    Uses DeleteViewActionMixin to generate a DeleteView via ViewFactory.
    """

    label = 'Delete'
    icon = 'trash'
    css_class = 'danger'
    django_permission_name = 'delete'  # Django permission for deleting records
    confirmation_required = True
    _url_name = 'delete'

    def get_url_pattern(self) -> str:
        """
        Get URL pattern for Delete action.

        Returns:
            URL pattern string with pk parameter
        """
        opts = self.model._meta
        return f'{opts.app_label}/{opts.model_name}/<int:pk>/actions/delete/'

    def get_template_name(self):
        """Template for delete confirmation"""
        opts = self.model._meta
        return [
            f'djadmin/{opts.app_label}/{opts.model_name}_confirm_delete.html',
            'djadmin/actions/confirm_delete.html',
        ]

    def get_success_url(self):
        """
        Redirect to list view after deletion.

        When bound to the view, self is the view instance which has:
        - self.object: The deleted object (before deletion)
        - self.request: The current request
        """
        opts = self.model._meta
        return reverse(
            f'djadmin:{opts.app_label}_{opts.model_name}_list',
            current_app=self.admin_site.name,
        )


class DeleteBulkAction(BulkActionMixin, BulkDeleteViewActionMixin, BaseAction):
    """
    Action to delete multiple selected records.

    Shows confirmation page with count before deleting.
    Uses BulkDeleteViewActionMixin to generate a BulkDeleteView via ViewFactory.
    """

    label = 'Delete Selected'
    icon = 'trash'
    django_permission_name = 'delete'  # Django permission for deleting records
    confirmation_required = True
    _url_name = 'bulk_delete'

    def get_url_pattern(self) -> str:
        """
        Get URL pattern for Bulk Delete action.

        Returns:
            URL pattern string
        """
        opts = self.model._meta
        return f'{opts.app_label}/{opts.model_name}/bulk/delete/'

    def get_template_name(self):
        """Template for bulk delete confirmation"""
        opts = self.model._meta
        return [
            f'djadmin/{opts.app_label}/{opts.model_name}_confirm_bulk_delete.html',
            'djadmin/actions/confirm_bulk_delete.html',
        ]

    def get_success_url(self):
        """
        Redirect to list view after deletion.

        When bound to the view, self is the view instance which has:
        - self.request: The current request
        """
        opts = self.model._meta
        return reverse(
            f'djadmin:{opts.app_label}_{opts.model_name}_list',
            current_app=self.admin_site.name,
        )


class ViewRecordAction(RecordActionMixin, DetailViewActionMixin, BaseAction):
    """
    Action to view a record in read-only mode.

    Shows record details using the Layout API for structured display.
    Only visible when user has 'view' permission but NOT 'change' permission.
    """

    label = 'View'
    icon = 'eye'
    css_class = 'secondary'
    django_permission_name = 'view'  # Django permission for viewing records
    _url_name = 'view'

    def __init__(self, *args, **kwargs):
        """Initialize with permission that only shows for view-only users."""
        # Set permission: IsStaff & view permission & NOT change permission
        # This ensures the action only shows for users who can view but not edit
        from djadmin.plugins.permissions import HasDjangoPermission, IsStaff

        kwargs.setdefault(
            'permission_class', IsStaff() & HasDjangoPermission(perm='view') & ~HasDjangoPermission(perm='change')
        )
        super().__init__(*args, **kwargs)

    def get_url_pattern(self) -> str:
        """
        Get URL pattern for View action.

        Returns:
            URL pattern string with pk parameter
        """
        opts = self.model._meta
        return f'{opts.app_label}/{opts.model_name}/<int:pk>/actions/view/'

    def get_template_name(self):
        """Template for detail view"""
        opts = self.model._meta
        return [
            f'djadmin/{opts.app_label}/{opts.model_name}_detail.html',
            'djadmin/actions/detail.html',
        ]
