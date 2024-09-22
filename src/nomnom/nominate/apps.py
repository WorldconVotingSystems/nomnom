from django.apps import AppConfig
from django.conf import settings
from django_svcs.apps import svcs_from

from nomnom.convention import (
    ConventionConfiguration,
)


class NominateConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nomnom.nominate"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def ready(self) -> None:
        self.enable_signals()

        self.configure_from_convention()

        return super().ready()

    def enable_signals(self):
        from . import signals  # noqa: F401

    def configure_from_convention(self):
        convention = svcs_from().get(ConventionConfiguration)
        convention_backends = convention.authentication_backends

        settings.AUTHENTICATION_BACKENDS = convention_backends + list(
            settings.AUTHENTICATION_BACKENDS
        )
