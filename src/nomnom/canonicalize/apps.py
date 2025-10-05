from django.apps import AppConfig
from django.db.backends.signals import connection_created


class CanonicalizeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nomnom.canonicalize"

    def ready(self) -> None:
        self.enable_signals()

        return super().ready()

    def enable_signals(self):
        from . import (
            receivers,  # noqa: F401
        )


def install_pg_trgm(sender, connection, **kwargs):
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")


connection_created.connect(install_pg_trgm)
