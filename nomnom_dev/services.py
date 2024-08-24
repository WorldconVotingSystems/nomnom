import svcs
from nomnom.convention import ConventionConfiguration, ConventionTheme, HugoAwards
from wsfs.rules import constitution_2023

nomnom_theme = ConventionTheme(
    stylesheets="css/nominate.css",
    # font_urls="https://fonts.googleapis.com/css2?family=Roboto&family=Roboto+Slab&family=Gruppo&display=swap",
    font_urls=[],
)
nomnom_convention = ConventionConfiguration(
    name="NomNom",
    subtitle="Hungry for Hugo Finalists",
    slug="nomnom",
    site_url="https://github.com/WorldconVotingSystems/nomnom/",
    hugo_help_email="nomnom-help@example.com",
    hugo_admin_email="nomnom-admin@example.com",
    registration_email="nomnom-reg@example.com",
    logo_alt_text="Nominate logo",
    authentication_backends=[],  # use pure Django users for now FIXME: stub convention login
)


# this registers _default_ developer convention values. These should all be overridden by the
# services in the convention app itself
def svcs_init(registry: svcs.Registry) -> None:
    registry.register_value(ConventionConfiguration, nomnom_convention)
    registry.register_value(ConventionTheme, nomnom_theme)
    registry.register_value(HugoAwards, constitution_2023.hugo_awards)
