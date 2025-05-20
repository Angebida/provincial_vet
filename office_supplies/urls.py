from django.urls import path
from .views import (
    SupplyListView, SupplyCreateView, SupplyDetailView, RequestCreateView, RequestListView,
    RequestDetailView, RequestApproveView, SupplyUpdateView, CategoryCreateView, 
    BulkSupplyUploadView, LowStockListView, ExpiringListView
)

urlpatterns = [
    # Supplies Management
    path('', SupplyListView.as_view(), name='office-supply-list'),
    path('new/', SupplyCreateView.as_view(), name='office-supply-create'),
    path('<int:pk>/', SupplyDetailView.as_view(), name='office-supply-detail'),
    path('<int:pk>/edit/', SupplyUpdateView.as_view(), name='office-supply-update'),
    path('bulk-upload/', BulkSupplyUploadView.as_view(), name='office-bulk-upload'),
    
    # Request Management - Updated from Orders
    path('requests/', RequestListView.as_view(), name='office-request-list'),
    path('requests/new/', RequestCreateView.as_view(), name='office-request-create'),
    path('requests/<int:pk>/', RequestDetailView.as_view(), name='office-request-detail'),
    path('requests/<int:pk>/approve/', RequestApproveView.as_view(), name='office-request-approve'),

    # Category Management
    path('category/new/', CategoryCreateView.as_view(), name='office-category-create'),

    # Add these new URL patterns
    path('low-stock/', LowStockListView.as_view(), name='office-low-stock'),
    path('expiring/', ExpiringListView.as_view(), name='office-expiring'),
]