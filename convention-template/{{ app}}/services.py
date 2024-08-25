import svcs

from nomnom.convention import ConventionConfiguration, ConventionTheme, HugoAwards
from nomnom.wsfs.rules import constitution_2023

from . import convention


def svcs_init(registry: svcs.Registry) -> None:
    registry.register_value(ConventionConfiguration, convention.convention)
    registry.register_value(ConventionTheme, convention.theme)
    registry.register_value(HugoAwards, constitution_2023.hugo_awards)
