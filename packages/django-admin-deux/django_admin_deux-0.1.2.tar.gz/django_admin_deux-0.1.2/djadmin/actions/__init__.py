"""Action system for django-admin-deux"""

from .base import (
    BaseAction,
    BulkActionMixin,
    ConfirmationActionMixin,
    DownloadActionMixin,
    FormActionMixin,
    GeneralActionMixin,
    RecordActionMixin,
    RedirectActionMixin,
    ViewActionMixin,
)
from .list_view import ListViewAction
from .view_mixins import (
    CreateViewActionMixin,
    FormFeaturesMixin,
    FormViewActionMixin,
    ListViewActionMixin,
    RedirectViewActionMixin,
    TemplateViewActionMixin,
    UpdateViewActionMixin,
)

__all__ = [
    # Base classes and action type mixins
    'BaseAction',
    'GeneralActionMixin',
    'BulkActionMixin',
    'RecordActionMixin',
    'FormActionMixin',
    'ViewActionMixin',
    'ConfirmationActionMixin',
    'RedirectActionMixin',
    'DownloadActionMixin',
    # Built-in actions
    'ListViewAction',
    # View type mixins
    'FormFeaturesMixin',
    'FormViewActionMixin',
    'CreateViewActionMixin',
    'UpdateViewActionMixin',
    'ListViewActionMixin',
    'TemplateViewActionMixin',
    'RedirectViewActionMixin',
]
