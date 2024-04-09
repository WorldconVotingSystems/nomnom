import pytest
import social_core.strategy
from django.conf import settings
from django.test import override_settings
from social_django.storage import BaseDjangoStorage


# some top level fixtures we use in other modules
class DictStrategy(social_core.strategy.BaseStrategy):
    def __init__(self, settings=None):
        self.settings = {} if settings is None else settings
        super().__init__(storage=BaseDjangoStorage())

    def setting(self, name, default=None, backend=None):
        return self.settings.get(name, default)

    def request_data(self, merge=True):
        return {}

    def build_absolute_uri(self, path=None):
        return path


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
