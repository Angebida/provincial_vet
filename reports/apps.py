from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports'

    def ready(self):
        from django.conf import settings
        if getattr(settings, 'ENABLE_INVENTORY_SIGNALS', True):
            from . import signals
