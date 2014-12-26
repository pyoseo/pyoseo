from django.apps import AppConfig

class OseoServerConfig(AppConfig):
    name = "oseoserver"
    verbose_name = "OSEO server"

    def ready(self):
        from django.db.models import signals
