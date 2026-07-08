from django.apps import AppConfig


class TimelineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nomnom.timeline"

    def ready(self) -> None:
        self.enable_signals()

        return super().ready()

    def enable_signals(self):
        from . import (
            receivers,  # noqa: F401
        )
