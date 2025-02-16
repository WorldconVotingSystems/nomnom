from datetime import datetime
from unittest import mock

import icecream
import pytest
import social_core.strategy
import svcs
from django.apps import apps
from django.conf import settings
from django.test import override_settings
from social_django.storage import BaseDjangoStorage

from nomnom.convention import ConventionConfiguration, ConventionTheme, HugoAwards

icecream.install()


# some top level fixtures we use in other modules
class DictStrategy(social_core.strategy.BaseStrategy):
    def __init__(self, settings=None):
        self.settings = {} if settings is None else settings

        # we also need a request here, for svcs context; the strategy instance is plenty
        self.request = self
        super().__init__(storage=BaseDjangoStorage())

    def setting(self, name, default=None, backend=None):
        return self.settings.get(name, default)

    def request_data(self, merge=True):
        return {}

    def build_absolute_uri(self, path=None):
        return path


@pytest.fixture(name="registry", autouse=True)
def get_registry():
    registry = svcs.Registry()
    with mock.patch.object(apps.get_app_config("django_svcs"), "registry", registry):
        yield registry


@pytest.fixture(autouse=True, name="convention")
def test_convention(registry: svcs.Registry) -> ConventionConfiguration:
    convention = ConventionConfiguration(
        name="NomNom Testing",
        subtitle="Test Convention",
        slug="test",
        site_url="https://example.com/",
        hugo_help_email="nomnom-help@example.com",
        hugo_admin_email="nomnom-admin@example.com",
        registration_email="nomnom-reg@example.com",
        logo_alt_text="Nominate logo",
        nomination_eligibility_cutoff=datetime(2024, 1, 31),
    )
    registry.register_value(ConventionConfiguration, convention)
    return convention


@pytest.fixture(autouse=True, name="theme")
def test_theme(registry: svcs.Registry) -> ConventionTheme:
    theme = ConventionTheme(
        stylesheets="css/nominate.css",
        font_urls=[],
    )
    registry.register_value(ConventionTheme, theme)
    return theme


@pytest.fixture(autouse=True, name="constitution")
def test_constitution(registry: svcs.Registry):
    from nomnom.wsfs.rules import constitution_2023

    registry.register_value(HugoAwards, constitution_2023.hugo_awards)
    return constitution_2023


@pytest.fixture(autouse=True)
def disable_whitenoise():
    original_middleware = settings.MIDDLEWARE

    # Create a modified middleware list excluding the one you want to disable
    modified_middleware = list(
        filter(
            lambda x: x != "whitenoise.middleware.WhiteNoiseMiddleware",
            original_middleware,
        )
    )

    # Apply the modified middleware list
    with override_settings(MIDDLEWARE=modified_middleware):
        yield


@pytest.fixture
def social_core_settings():
    return {}


@pytest.fixture
def social_core_strategy(social_core_settings):
    return DictStrategy(social_core_settings)
