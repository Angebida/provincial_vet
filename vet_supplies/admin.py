from django.contrib import admin
from .models import VeterinarySupplyCategory, VeterinarySupply, VeterinarySupplyRequest

@admin.register(VeterinarySupplyCategory)
class VeterinarySupplyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(VeterinarySupply)
class VeterinarySupplyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'unit', 'expiration_date', 'stock_status')
    list_filter = ('category', 'unit')
    search_fields = ('name',)
    readonly_fields = ('stock_status',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category')
        }),
        ('Inventory Details', {
            'fields': ('quantity', 'unit', 'minimum_stock', 'reorder_level')
        }),
        ('Additional Info', {
            'fields': ('expiration_date', 'notes')
        }),
    )

@admin.register(VeterinarySupplyRequest)
class VeterinarySupplyRequestAdmin(admin.ModelAdmin):
    list_display = ('supply', 'quantity', 'requester', 'status', 'urgency', 'request_date')
    list_filter = ('status', 'urgency', 'supply__category')
    search_fields = ('supply__name', 'requester__username')
    actions = ['approve_requests']

    def approve_requests(self, request, queryset):
        queryset.update(status='approved', approved_by=request.user)
    approve_requests.short_description = "Approve selected requests"