from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self) -> None:
        # Carga signals (post_delete, etc.)
        from . import signals  # noqa: F401

