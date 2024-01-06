from django.apps import AppConfig


class NominateConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nominate"

    def ready(self) -> None:
        from . import signals  # noqa: F401

        return super().ready()
