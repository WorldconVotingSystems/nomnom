import svcs
from nomnom.convention import ConventionConfiguration, ConventionTheme

from . import convention


def svcs_init(registry: svcs.Registry) -> None:
    registry.register_value(ConventionConfiguration, convention.convention)
    registry.register_value(ConventionTheme, convention.theme)
