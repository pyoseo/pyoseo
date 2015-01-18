from django.apps import AppConfig
from actstream import registry

class OseoServerConfig(AppConfig):
    name = "oseoserver"
    verbose_name = "OSEO server"

    def ready(self):
        import oseoserver.signals.handlers
        registry.register(self.get_model("OseoUser"))
        registry.register(self.get_model("ProductOrder"))
