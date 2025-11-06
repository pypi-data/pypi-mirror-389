"""Tests for action URL routing"""

import pytest
from django.urls import resolve, reverse

from djadmin import AdminSite, ModelAdmin
from djadmin.plugins.core.actions import AddAction, DeleteBulkAction, DeleteRecordAction, EditRecordAction
from examples.webshop.models import Product


@pytest.fixture
def configured_site():
    """AdminSite with actions configured"""
    site = AdminSite(name='test_admin')

    class ProductAdmin(ModelAdmin):
        general_actions = [AddAction]
        record_actions = [EditRecordAction, DeleteRecordAction]
        bulk_actions = [DeleteBulkAction]

    site.register(Product, ProductAdmin)
    return site


class TestActionURLPatterns:
    """Test action URL pattern generation (no reverse lookups)"""

    def test_general_action_url_pattern_created(self, db):
        """General actions should have URL patterns created"""

        class ProductAdmin(ModelAdmin):
            general_actions = [AddAction]

        site = AdminSite(name='test_admin')
        site.register(Product, ProductAdmin)

        urlpatterns = site.get_urls()

        # Find the add action pattern
        add_patterns = [p for p in urlpatterns if p.name == 'webshop_product_add']
        assert len(add_patterns) == 1
        # AddAction uses custom __new__ URL pattern
        assert str(add_patterns[0].pattern) == 'webshop/product/__new__/'

    def test_record_action_url_pattern_created(self, db):
        """Record actions should have URL patterns created"""

        class ProductAdmin(ModelAdmin):
            record_actions = [EditRecordAction]

        site = AdminSite(name='test_admin')
        site.register(Product, ProductAdmin)

        urlpatterns = site.get_urls()

        # Find the edit action pattern
        edit_patterns = [p for p in urlpatterns if p.name == 'webshop_product_edit']
        assert len(edit_patterns) == 1
        assert str(edit_patterns[0].pattern) == 'webshop/product/<int:pk>/actions/edit/'

    def test_bulk_action_url_pattern_created(self, db):
        """Bulk actions should have URL patterns created"""

        class ProductAdmin(ModelAdmin):
            bulk_actions = [DeleteBulkAction]

        site = AdminSite(name='test_admin')
        site.register(Product, ProductAdmin)

        urlpatterns = site.get_urls()

        # Find the bulk delete pattern
        bulk_patterns = [p for p in urlpatterns if p.name == 'webshop_product_bulk_delete']
        assert len(bulk_patterns) == 1
        assert str(bulk_patterns[0].pattern) == 'webshop/product/bulk/delete/'

    def test_multiple_action_types_all_created(self, db):
        """Multiple action types should all create URL patterns"""

        class ProductAdmin(ModelAdmin):
            general_actions = [AddAction]
            record_actions = [EditRecordAction, DeleteRecordAction]
            bulk_actions = [DeleteBulkAction]

        site = AdminSite(name='test_admin')
        site.register(Product, ProductAdmin)

        urlpatterns = site.get_urls()
        pattern_names = [p.name for p in urlpatterns]

        # All action URLs should exist
        assert 'webshop_product_add' in pattern_names
        assert 'webshop_product_edit' in pattern_names
        assert 'webshop_product_delete' in pattern_names
        assert 'webshop_product_bulk_delete' in pattern_names

    def test_action_url_name_format(self, db):
        """Action URL names should follow correct format"""

        class ProductAdmin(ModelAdmin):
            pass

        site = AdminSite(name='test_admin')
        site.register(Product, ProductAdmin)

        # Check URL name format: {app}_{model}_{action_name}
        model_admin_instance = site.get_model_admins(Product)[0]

        add_action = AddAction(Product, model_admin_instance, site)
        assert add_action.get_url_name() == 'webshop_product_add'

        edit_action = EditRecordAction(Product, model_admin_instance, site)
        assert edit_action.get_url_name() == 'webshop_product_edit'

        delete_bulk_action = DeleteBulkAction(Product, model_admin_instance, site)
        assert delete_bulk_action.get_url_name() == 'webshop_product_bulk_delete'

    def test_custom_action_url_pattern_created(self, db):
        """Custom actions should create URL patterns correctly"""
        from djadmin.actions import BaseAction, GeneralActionMixin
        from djadmin.actions.view_mixins import TemplateViewActionMixin

        class CustomAction(GeneralActionMixin, TemplateViewActionMixin, BaseAction):
            label = 'Custom'

            def get_template_name(self):
                return 'custom.html'

        class ProductAdmin(ModelAdmin):
            general_actions = [CustomAction]

        site = AdminSite(name='test_admin')
        site.register(Product, ProductAdmin)

        urlpatterns = site.get_urls()

        # Find the custom action pattern
        custom_patterns = [p for p in urlpatterns if p.name == 'webshop_product_custom']
        assert len(custom_patterns) == 1
        # Custom action uses default URL pattern (app/model/actions/classname/)
        assert str(custom_patterns[0].pattern) == 'webshop/product/actions/customaction/'


class TestActionURLReverseLookups:
    """Test reverse URL lookups with namespace"""

    @pytest.fixture(autouse=True)
    def setup_urls(self, configured_site, settings):
        """Set up URLconf for reverse lookup tests"""
        from django.urls import include, path

        urlpatterns = [
            path('djadmin/', include(configured_site.urls)),
        ]

        settings.ROOT_URLCONF = type('URLConf', (), {'urlpatterns': urlpatterns})

    def test_reverse_general_action(self):
        """Test reverse lookup for general action"""
        url = reverse('test_admin:webshop_product_add')
        # AddAction uses custom __new__ URL pattern
        assert url == '/djadmin/webshop/product/__new__/'

    def test_reverse_record_action(self):
        """Test reverse lookup for record action"""
        url = reverse('test_admin:webshop_product_edit', args=[123])
        assert url == '/djadmin/webshop/product/123/actions/edit/'

    def test_reverse_bulk_action(self):
        """Test reverse lookup for bulk action"""
        url = reverse('test_admin:webshop_product_bulk_delete')
        assert url == '/djadmin/webshop/product/bulk/delete/'

    def test_reverse_all_action_types(self):
        """Test reverse lookup for all action types"""
        # General action
        assert reverse('test_admin:webshop_product_add')

        # Record actions
        assert reverse('test_admin:webshop_product_edit', args=[1])
        assert reverse('test_admin:webshop_product_delete', args=[1])

        # Bulk action
        assert reverse('test_admin:webshop_product_bulk_delete')

    def test_resolve_general_action_url(self):
        """Test resolving general action URL"""
        # AddAction uses custom __new__ URL pattern
        url = '/djadmin/webshop/product/__new__/'
        match = resolve(url)
        assert match.url_name == 'webshop_product_add'
        assert match.namespace == 'test_admin'

    def test_resolve_record_action_url(self):
        """Test resolving record action URL"""
        url = '/djadmin/webshop/product/123/actions/edit/'
        match = resolve(url)
        assert match.url_name == 'webshop_product_edit'
        assert match.namespace == 'test_admin'
        assert match.kwargs['pk'] == 123

    def test_resolve_bulk_action_url(self):
        """Test resolving bulk action URL"""
        url = '/djadmin/webshop/product/bulk/delete/'
        match = resolve(url)
        assert match.url_name == 'webshop_product_bulk_delete'
        assert match.namespace == 'test_admin'

    def test_action_view_callable(self):
        """Action URLs should resolve to callable views"""
        url = reverse('test_admin:webshop_product_add')
        match = resolve(url)
        assert callable(match.func)
