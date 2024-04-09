from importlib import import_module
from typing import Annotated

import svcs
from django.apps import AppConfig, apps
from nomnom.convention import (
    ConfigurationError,
)


def convention_app_factory(svcs_container: svcs.Container) -> AppConfig | None:
    convention_app = None
    for app in apps.get_app_configs():
        try:
            import_module(f"{app.name}.convention")
            if convention_app is not None:
                raise ConfigurationError(
                    f"Only one application can define a convention; found {app} and {convention_app}"
                )
            convention_app = app
        except ImportError:
            continue

    if convention_app is not None:
        return convention_app


def svcs_init(registry: svcs.Registry):
    registry.register_factory(
        Annotated[AppConfig, "convention_app"], convention_app_factory
    )
