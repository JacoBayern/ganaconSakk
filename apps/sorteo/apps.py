from django.apps import AppConfig


class SorteoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sorteo'

    def ready(self):
        import apps.sorteo.signals