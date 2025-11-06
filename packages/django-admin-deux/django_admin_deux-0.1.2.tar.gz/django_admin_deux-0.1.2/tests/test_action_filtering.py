"""Tests for permission-aware action filtering in ListView and ModelAdmin.

Tests the check_permission() method on actions and the filter_actions()
method on ModelAdmin.
"""

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase

from djadmin import ModelAdmin, site
from djadmin.actions.base import BaseAction, GeneralActionMixin
from djadmin.plugins.permissions import HasDjangoPermission, IsStaff, IsSuperuser
from examples.webshop.factories import ProductFactory
from examples.webshop.models import Product
from tests.conftest import RegistrySaveRestoreMixin
from tests.factories import UserFactory


# Test fixtures for different permission scenarios
class ViewOnlyProductAdmin(ModelAdmin):
    """Admin with view permission only."""

    permission_class = IsStaff() & HasDjangoPermission(perm='view')


class ChangeOnlyProductAdmin(ModelAdmin):
    """Admin with change permission only."""

    permission_class = IsStaff() & HasDjangoPermission(perm='change')


class SuperuserOnlyProductAdmin(ModelAdmin):
    """Admin accessible only to superusers."""

    permission_class = IsSuperuser()


class NoPermissionProductAdmin(ModelAdmin):
    """Admin with no permission checks."""

    permission_class = None


# Custom test action for permission testing
class CustomTestAction(GeneralActionMixin, BaseAction):
    """Custom action for testing permission filtering."""

    label = 'Custom Test Action'
    permission_class = IsStaff()

    def get_template_name(self):
        return 'djadmin/model_list.html'


class TestActionCheckPermission(RegistrySaveRestoreMixin, TestCase):
    """Test the check_permission() method on BaseAction."""

    registry_models = [Product]

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.product = ProductFactory()

        # Create users with different permission levels
        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.staff_with_view = UserFactory(is_staff=True)
        self.staff_no_perms = UserFactory(is_staff=True)
        self.regular_user = UserFactory(is_staff=False)

        # Grant view permission to staff_with_view
        content_type = ContentType.objects.get_for_model(Product)
        view_perm = Permission.objects.get(codename='view_product', content_type=content_type)
        self.staff_with_view.user_permissions.add(view_perm)

    def test_superuser_has_permission_for_all_actions(self):
        """Superusers should pass permission checks for all actions."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.superuser

        # Get an action from the model_admin
        action = model_admin.general_actions[0] if model_admin.general_actions else None
        assert action is not None, 'Expected general_actions to have at least one action'

        # Check permission
        result = action.check_permission(request)
        assert result is True, 'Superuser should have permission for all actions'

    def test_regular_user_denied_for_staff_only_actions(self):
        """Regular users (non-staff) should be denied for IsStaff actions."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.regular_user

        # Get an action
        action = model_admin.general_actions[0] if model_admin.general_actions else None
        assert action is not None

        # Check permission - should be denied
        result = action.check_permission(request)
        assert result is False, 'Regular user should be denied for IsStaff & HasDjangoPermission actions'

    def test_staff_with_permission_allowed(self):
        """Staff with correct Django permission should pass check."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.staff_with_view

        # Get an action
        action = model_admin.general_actions[0] if model_admin.general_actions else None
        assert action is not None

        # Check permission - should pass (staff + view permission)
        result = action.check_permission(request)
        assert result is True, 'Staff with view permission should pass for view-only actions'

    def test_staff_without_permission_denied(self):
        """Staff without correct Django permission should be denied."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.staff_no_perms

        # Get an action
        action = model_admin.general_actions[0] if model_admin.general_actions else None
        assert action is not None

        # Check permission - should be denied (staff but no view permission)
        result = action.check_permission(request)
        assert result is False, 'Staff without view permission should be denied'

    def test_no_permission_class_allows_all(self):
        """Actions with permission_class=None should allow all users."""
        site.register(Product, NoPermissionProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.regular_user  # Even non-staff user

        # Get an action
        action = model_admin.general_actions[0] if model_admin.general_actions else None
        assert action is not None

        # Check permission - should pass (no permission check)
        result = action.check_permission(request)
        assert result is True, 'Actions with permission_class=None should allow all users'

    def test_action_level_permission_override(self):
        """Action-level permission_class should override ModelAdmin default."""

        # Create a custom action with IsSuperuser permission
        class SuperuserOnlyAction(GeneralActionMixin, BaseAction):
            label = 'Superuser Only'
            permission_class = IsSuperuser()

            def get_template_name(self):
                return 'djadmin/model_list.html'

        # Register with ViewOnlyProductAdmin but add custom action
        class CustomAdmin(ViewOnlyProductAdmin):
            general_actions = [SuperuserOnlyAction]

        site.register(Product, CustomAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.staff_with_view  # Staff with view perm, but NOT superuser

        # Get the custom action
        action = model_admin.general_actions[0]
        assert action.label == 'Superuser Only'

        # Check permission - should be denied (requires superuser)
        result = action.check_permission(request)
        assert result is False, 'Staff with view perm should be denied for superuser-only action'

        # Try with superuser
        request.user = self.superuser
        result = action.check_permission(request)
        assert result is True, 'Superuser should pass for superuser-only action'


class TestModelAdminFilterActions(RegistrySaveRestoreMixin, TestCase):
    """Test the filter_actions() method on ModelAdmin."""

    registry_models = [Product]

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.product = ProductFactory()

        # Create users
        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.staff_with_view = UserFactory(is_staff=True)
        self.regular_user = UserFactory(is_staff=False)

        # Grant view permission to staff_with_view
        content_type = ContentType.objects.get_for_model(Product)
        view_perm = Permission.objects.get(codename='view_product', content_type=content_type)
        self.staff_with_view.user_permissions.add(view_perm)

    def test_filter_actions_with_superuser(self):
        """Superuser should see all actions."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.superuser

        # Filter actions
        all_actions = model_admin.general_actions
        filtered = model_admin.filter_actions(all_actions, request)

        # Superuser should see all actions
        assert len(filtered) == len(all_actions), 'Superuser should see all actions'

    def test_filter_actions_with_view_only_user(self):
        """User with view permission should see view-only actions."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.staff_with_view

        # Filter actions
        all_actions = model_admin.general_actions
        filtered = model_admin.filter_actions(all_actions, request)

        # Should see actions (has view permission)
        assert len(filtered) > 0, 'User with view permission should see actions'

    def test_filter_actions_with_regular_user(self):
        """Regular user (non-staff) should see no actions with IsStaff requirement."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.regular_user

        # Filter actions
        all_actions = model_admin.general_actions
        filtered = model_admin.filter_actions(all_actions, request)

        # Regular user should see no actions (IsStaff required)
        assert len(filtered) == 0, 'Regular user should see no actions with IsStaff requirement'

    def test_filter_actions_with_no_permission_admin(self):
        """Admin with permission_class=None should show all actions to all users."""
        site.register(Product, NoPermissionProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.regular_user  # Even regular user

        # Filter actions
        all_actions = model_admin.general_actions
        filtered = model_admin.filter_actions(all_actions, request)

        # Should see all actions (no permission check)
        assert len(filtered) == len(all_actions), 'All users should see actions when permission_class=None'

    def test_filter_empty_action_list(self):
        """filter_actions() should handle empty action list gracefully."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.superuser

        # Filter empty list
        filtered = model_admin.filter_actions([], request)

        # Should return empty list
        assert filtered == [], 'Empty action list should return empty list'


class TestListViewActionFiltering(RegistrySaveRestoreMixin, TestCase):
    """Test action filtering in ListView context."""

    registry_models = [Product]

    def setUp(self):
        super().setUp()
        self.product = ProductFactory()

        # Create users
        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.staff_with_view = UserFactory(is_staff=True)
        self.regular_user = UserFactory(is_staff=False)

        # Grant view permission to staff_with_view
        content_type = ContentType.objects.get_for_model(Product)
        view_perm = Permission.objects.get(codename='view_product', content_type=content_type)
        self.staff_with_view.user_permissions.add(view_perm)

    def test_superuser_sees_all_actions_in_list_view(self):
        """Superuser should see all actions in list view."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        self.client.force_login(self.superuser)

        # Get list view
        url = site.reverse('webshop_product_list')
        response = self.client.get(url)

        assert response.status_code == 200
        # Check that general_actions are present
        assert 'general_actions' in response.context
        assert len(response.context['general_actions']) > 0

    def test_view_only_user_sees_filtered_actions(self):
        """User with view permission should see filtered actions."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        self.client.force_login(self.staff_with_view)

        # Get list view
        url = site.reverse('webshop_product_list')
        response = self.client.get(url)

        assert response.status_code == 200
        # Check that actions are present (user has view permission)
        assert 'general_actions' in response.context
        assert len(response.context['general_actions']) > 0

    def test_regular_user_sees_no_actions(self):
        """Regular user should see no actions in staff-only admin."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        self.client.force_login(self.regular_user)

        # Try to access list view - should be denied at view level
        url = site.reverse('webshop_product_list')
        response = self.client.get(url)

        # Should be redirected or 403
        assert response.status_code in [302, 403], 'Regular user should be denied access'

    def test_object_list_has_available_record_actions(self):
        """Record actions should be filtered in list view context."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        self.client.force_login(self.superuser)

        # Get list view
        url = site.reverse('webshop_product_list')
        response = self.client.get(url)

        assert response.status_code == 200
        # Check that record_actions are in context and filtered
        assert 'record_actions' in response.context
        assert isinstance(response.context['record_actions'], list)
        # Superuser should have access to all record actions
        assert len(response.context['record_actions']) > 0

    def test_bulk_actions_filtered_in_context(self):
        """Bulk actions should be filtered in list view context."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        self.client.force_login(self.staff_with_view)

        # Get list view
        url = site.reverse('webshop_product_list')
        response = self.client.get(url)

        assert response.status_code == 200
        # Check that bulk_actions are present and filtered
        assert 'bulk_actions' in response.context
        # Should be a list (even if empty)
        assert isinstance(response.context['bulk_actions'], list)

    def test_record_actions_filtered_in_context(self):
        """Record actions should be filtered in list view context."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        self.client.force_login(self.staff_with_view)

        # Get list view
        url = site.reverse('webshop_product_list')
        response = self.client.get(url)

        assert response.status_code == 200
        # Check that record_actions are present and filtered
        assert 'record_actions' in response.context
        # Should be a list (even if empty)
        assert isinstance(response.context['record_actions'], list)


class TestCheckPermissionMethod(RegistrySaveRestoreMixin, TestCase):
    """Test the check_permission() method implementation details."""

    registry_models = [Product]

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.product = ProductFactory()
        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.regular_user = UserFactory(is_staff=False)

    def test_check_permission_creates_view_instance(self):
        """check_permission() should create a minimal view instance."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.superuser

        # Get an action
        action = model_admin.general_actions[0]

        # Mock get_view_class to verify it's called
        original_method = action.get_view_class
        view_class_called = False

        def mock_get_view_class():
            nonlocal view_class_called
            view_class_called = True
            return original_method()

        action.get_view_class = mock_get_view_class

        # Call check_permission
        action.check_permission(request)

        # Verify get_view_class was called
        assert view_class_called, 'check_permission() should call get_view_class()'

    def test_check_permission_calls_test_func(self):
        """check_permission() should call test_func() on the view."""
        site.register(Product, ViewOnlyProductAdmin, override=True)
        model_admin = site.get_model_admins(Product)[0]
        request = self.factory.get('/')
        request.user = self.superuser

        # Get an action
        action = model_admin.general_actions[0]

        # Call check_permission
        result = action.check_permission(request)

        # Verify result (superuser should pass)
        assert result is True, 'check_permission() should return test_func() result'

    def test_check_permission_without_test_func_defaults_to_allow(self):
        """If view has no test_func, check_permission() should default to True."""
        # Create a mock view class without test_func
        from django.views.generic import TemplateView

        class ViewWithoutTestFunc(TemplateView):
            pass

        # Create a custom action that returns this view
        class CustomAction(GeneralActionMixin, BaseAction):
            label = 'Custom'

            def get_template_name(self):
                return 'djadmin/model_list.html'

            def get_view_class(self):
                return ViewWithoutTestFunc

        # Create action instance
        action = CustomAction(Product, None, site)
        request = self.factory.get('/')
        request.user = self.regular_user

        # Call check_permission
        result = action.check_permission(request)

        # Should default to True
        assert result is True, 'check_permission() should default to True if no test_func'
