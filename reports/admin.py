from django.contrib import admin
from .models import InventoryMovement

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'category', 'action', 'quantity', 'timestamp')
    list_filter = ('action', 'item_type')
    search_fields = ('item_name', 'category')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'previous_quantity')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('content_type', 'object_id', 'action')
        return self.readonly_fields