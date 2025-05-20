from django.urls import path
from .views import (
    SupplyListView, SupplyCreateView, SupplyDetailView, SupplyUpdateView, SupplyDeleteView,
    RequestCreateView, RequestListView, RequestDetailView, RequestUpdateView,
    CategoryCreateView, BulkSupplyUploadView,
    LowStockListView, ExpiringListView
)

urlpatterns = [
    # Supplies CRUD
    path('', SupplyListView.as_view(), name='vet-supply-list'),
    path('new/', SupplyCreateView.as_view(), name='vet-supply-create'),
    path('<int:pk>/', SupplyDetailView.as_view(), name='vet-supply-detail'),
    path('<int:pk>/edit/', SupplyUpdateView.as_view(), name='vet-supply-update'),
    path('<int:pk>/delete/', SupplyDeleteView.as_view(), name='vet-supply-delete'),
    path('bulk-upload/', BulkSupplyUploadView.as_view(), name='vet-bulk-upload'),
    
    # Requests Management - Update paths
    path('requests/', RequestListView.as_view(), name='vet-request-list'),  
    path('requests/new/', RequestCreateView.as_view(), name='vet-request-create'),
    path('requests/<int:pk>/', RequestDetailView.as_view(), name='vet-request-detail'),
    path('requests/<int:pk>/update/', RequestUpdateView.as_view(), name='vet-request-update'),

    # Category Management
    path('category/new/', CategoryCreateView.as_view(), name='vet-category-create'),

    # Add these new URL patterns
    path('low-stock/', LowStockListView.as_view(), name='vet-low-stock'),
    path('expiring/', ExpiringListView.as_view(), name='vet-expiring'),
]