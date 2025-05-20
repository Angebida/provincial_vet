from django.contrib import admin
from .models import UnitMeasure

@admin.register(UnitMeasure)
class UnitMeasureAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'display_name')
    ordering = ['order', 'display_name']
