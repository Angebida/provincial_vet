from django.contrib import admin
from .models import OfficeSupplyCategory, OfficeSupply, OfficeSupplyRequest

@admin.register(OfficeSupplyCategory)
class OfficeSupplyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(OfficeSupply)
class OfficeSupplyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'unit', 'reorder_level', 'needs_reorder')
    list_filter = ('category', 'unit')
    search_fields = ('name',)
    readonly_fields = ('needs_reorder',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category')
        }),
        ('Inventory Details', {
            'fields': ('quantity', 'unit', 'reorder_level', 'minimum_stock', 'location')
        }),
        ('Additional Info', {
            'fields': ('expiration_date', 'notes')
        }),
    )

@admin.register(OfficeSupplyRequest)
class OfficeSupplyRequestAdmin(admin.ModelAdmin):
    list_display = ('supply', 'quantity', 'requester', 'status', 'request_date')
    list_filter = ('status', 'supply__category')
    search_fields = ('supply__name',)
    readonly_fields = ('request_date',)
    fieldsets = (
        ('Request Details', {
            'fields': ('supply', 'quantity', 'status')
        }),
        ('Purpose', {
            'fields': ('purpose',)
        }),
        ('Approval Info', {
            'fields': ('requester', 'approved_by', 'approval_date')
        }),
    )