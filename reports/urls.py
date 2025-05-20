from django.urls import path
from .views import DashboardView, export_report, InventoryMovementListView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('export/', export_report, name='export-report'),
    path('movements/', InventoryMovementListView.as_view(), name='inventory-movements'),
]