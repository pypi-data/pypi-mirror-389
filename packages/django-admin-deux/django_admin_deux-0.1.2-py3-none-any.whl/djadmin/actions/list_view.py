"""ListViewAction - Built-in action for generating ListView

This is not a user-facing action. It's used internally by AdminSite
to generate the main list view for a model.
"""

from djadmin.actions.base import BaseAction
from djadmin.actions.view_mixins import ListViewActionMixin


class ListViewAction(ListViewActionMixin, BaseAction):
    """
    Built-in action for generating ListView.

    This action is automatically created by AdminSite for each registered
    model to provide the main list view. It's not meant to be instantiated
    directly by users.

    The action combines ListViewActionMixin (which specifies ListView as
    base_class) with BaseAction to create a complete action that can be
    passed to ViewFactory.

    Example usage (internal to AdminSite):
        list_action = ListViewAction(model, model_admin, admin_site)
        factory = ViewFactory()
        list_view_class = factory.create_view(list_action)
    """

    label = 'List'
    css_class = 'secondary'  # Use secondary/outline style for list links
    django_permission_name = 'view'  # Django permission for viewing list

    @property
    def url_name(self) -> str:
        """
        Get URL name for ListView.

        Overrides BaseAction.url_name to return the correct URL pattern
        that matches the ListView URL registered in AdminSite.

        Returns:
            URL name string (e.g., 'webshop_category_list')
        """
        opts = self.model._meta
        return f'{opts.app_label}_{opts.model_name}_list'

    def get_url_pattern(self) -> str:
        """
        Get URL pattern for ListView.

        ListView is the main entry point and doesn't use /actions/ prefix.

        Returns:
            URL pattern string (e.g., 'webshop/category/')
        """
        opts = self.model._meta
        return f'{opts.app_label}/{opts.model_name}/'

    def get_template_name(self):
        """
        Get template names for list view.

        Returns a list of template paths that Django will try in order:
        1. Model-specific: djadmin/{app}/{model}_list.html
        2. Generic fallback: djadmin/model_list.html

        Returns:
            List of template path strings
        """
        opts = self.model._meta
        return [
            f'djadmin/{opts.app_label}/{opts.model_name}_list.html',
            'djadmin/model_list.html',
        ]

    def get_queryset(self):
        """
        Get queryset for list view with ordering and plugin modifications.

        When this method is copied to the view class, 'self' will be the view instance.
        The view has model_admin, request, etc. as attributes.

        Returns:
            QuerySet for the model
        """
        from djadmin.plugins import pm

        # Call super to get base queryset from ListView
        # Use type(self).__mro__[1] to get the parent class in the view's MRO
        # This works because when copied to the view, self is the view instance
        queryset = super(type(self), self).get_queryset()

        # Apply ordering from model_admin (view has this as an attribute)
        if hasattr(self, 'ordering') and self.ordering:
            queryset = queryset.order_by(*self.ordering)

        # Allow plugins to modify queryset
        plugin_results = pm.hook.djadmin_modify_queryset(
            queryset=queryset,
            request=self.request,
            view=self,
        )

        # Use the last non-None result
        for result in reversed(plugin_results):
            if result is not None:
                queryset = result
                break

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add list_display to template context and filter actions based on permissions.

        When bound to the view, self is the view instance.
        Calls DjAdminViewMixin.get_context_data() via super() to get base admin context.
        """
        # Call super to get base context from DjAdminViewMixin
        context = super(type(self), self).get_context_data(**kwargs)

        # Add list_display for template iteration
        context['list_display'] = self.model_admin.list_display

        # Filter actions based on user permissions
        context['general_actions'] = self.model_admin.filter_actions(self.model_admin.general_actions, self.request)
        context['bulk_actions'] = self.model_admin.filter_actions(self.model_admin.bulk_actions, self.request)
        context['record_actions'] = self.model_admin.filter_actions(self.model_admin.record_actions, self.request)

        return context
