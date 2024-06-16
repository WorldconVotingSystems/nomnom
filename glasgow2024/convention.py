from datetime import datetime, timezone

from nomnom.convention import (
    ConventionConfiguration,
    ConventionTheme,
    system_configuration,
)

theme = ConventionTheme(
    stylesheets="css/glasgow2024.css",
    font_urls="https://fonts.googleapis.com/css2?family=Roboto&family=Roboto+Slab&family=Gruppo&display=swap",
)

convention = ConventionConfiguration(
    name="Glasgow in 2024",
    subtitle="A Worldcon For Our Futures",
    slug="glasgow2024",
    site_url="https://glasgow2024.org",
    nomination_eligibility_cutoff=datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
    authentication_backends=[
        system_configuration.oauth.backend,
    ],
    hugo_help_email="hugo-help@glasgow2024.org",
    hugo_admin_email="hugo-admin@glasgow2024.org",
    hugo_packet_backend="digitalocean",
    registration_email="registration@glasgow2024.org",
    logo="images/logo_withouttitle_transparent-300x293.png",
    logo_alt_text="Glasgow in 2024 logo",
    urls_app_name="glasgow2024",
    advisory_votes_enabled=True,
)
