import pytest
import social_core.strategy
from social_django.storage import BaseDjangoStorage


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


@pytest.fixture
def social_core_settings():
    return {}


@pytest.fixture
def social_core_strategy(social_core_settings):
    return DictStrategy(social_core_settings)
