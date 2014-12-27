from django.apps import AppConfig

class OseoServerConfig(AppConfig):
    name = "oseoserver"
    verbose_name = "OSEO server"

    def ready(self):
        import oseoserver.signals.handlers
