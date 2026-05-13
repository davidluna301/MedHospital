from django.apps import AppConfig


class ConsultasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "consultas"
    verbose_name = "Consultas médicas"

    def ready(self):
        import consultas.signals  # noqa: F401
