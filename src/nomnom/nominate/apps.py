from django.apps import AppConfig


class NominateConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nomnom.nominate"
    label = "nominate"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def ready(self) -> None:
        self.enable_signals()

        return super().ready()

    def enable_signals(self):
        from . import signals  # noqa: F401
