from importlib import import_module
from typing import Protocol, cast

import svcs
from django.apps import AppConfig, apps
from django.conf import LazySettings, Settings, settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

_KEY_CONTAINER = "svcs_container"


class DjangoRegistryContainer(Protocol):
    registry: svcs.Registry


class SvcsConfig(AppConfig):
    """Django AppConfig for the services module

    This appconfig creates a registry for services and initializes it with services from the project
    and all installed apps that provide `services.svcs_init` functions.

    In order to be fully functional, it's necessary to add request wrapping middleware
    to your project by including the `django_svcs.middleware.request_container` middleware
    in your `MIDDLEWARE` setting. It must be before any middleware that accesses services.
    """

    name = "django_svcs"
    verbose_name = "Services"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def ready(self) -> None:
        registry = svcs.Registry()

        if "django_svcs.middleware.request_container" not in settings.MIDDLEWARE:
            raise ImproperlyConfigured(
                "The request_container middleware must be included in your MIDDLEWARE setting"
            )

        for app_config in apps.get_app_configs():
            try:
                services_for_app = import_module(f"{app_config.name}.services")
            except ImportError:
                continue

            if hasattr(services_for_app, "svcs_init"):
                services_for_app.svcs_init(registry)

        self.registry = registry


def get_registry(app_config: DjangoRegistryContainer | None = None) -> svcs.Registry:
    """Get the registry from the app config, or from the registered appconfig"""
    registry_holder = (
        cast(DjangoRegistryContainer, apps.get_app_config("django_svcs"))
        if app_config is None
        else app_config
    )
    return registry_holder.registry


def svcs_from(
    context: HttpRequest | Settings | LazySettings | None = None,
) -> svcs.Container:
    """Get the current container from either the request or the settings object.

    The settings should be used to access services with no request context; this is useful when
    working in task contexts.

    """
    if context is None:
        from django.conf import settings

        context = settings

    if not hasattr(context, _KEY_CONTAINER):
        setattr(context, _KEY_CONTAINER, svcs.Container(registry=get_registry()))

    return getattr(context, _KEY_CONTAINER)
