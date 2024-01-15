from importlib import import_module

from django.apps import AppConfig, apps
from django.utils.module_loading import import_string
from nomnom.convention import (
    ConfigurationError,
    ConventionConfiguration,
    ConventionTheme,
)


class NominateConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nominate"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.theme: ConventionTheme = nomnom_theme
        self.convention: ConventionConfiguration = nomnom_convention

    def ready(self) -> None:
        self.enable_signals()

        self.load_convention_theme()

    def enable_signals(self):
        from . import signals  # noqa: F401

    def load_convention_theme(self):
        convention_config_app = None
        for app in apps.get_app_configs():
            try:
                import_module(f"{app.name}.convention")
                if convention_config_app is not None:
                    raise ConfigurationError(
                        f"Only one application can define a convention; found {app} and {convention_config_app}"
                    )
                convention_config_app = app
            except ImportError:
                continue

        if convention_config_app is not None:
            try:
                self.theme = import_string(
                    f"{convention_config_app.name}.convention.theme"
                )
            except ImportError:
                ...

            try:
                self.convention = import_string(
                    f"{convention_config_app.name}.convention.convention"
                )
            except ImportError:
                ...

        return super().ready()


nomnom_theme = ConventionTheme(
    stylesheets="css/nominate.css",
    font_urls="https://fonts.googleapis.com/css2?family=Roboto&family=Roboto+Slab&family=Gruppo&display=swap",
)
nomnom_convention = ConventionConfiguration(
    name="NomNom",
    subtitle="Hungry for Hugo Finalists",
    slug="nomnom",
    site_url="https://github.com/WorldconVotingSystems/nomnom/",
    hugo_help_email="nomnom@example.com",
    registration_email="nomnom@example.com",
    logo_alt_text="Nominate logo",
)
