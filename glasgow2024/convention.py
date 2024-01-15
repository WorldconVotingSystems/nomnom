from nomnom.convention import ConventionConfiguration, ConventionTheme

theme = ConventionTheme(
    stylesheets="css/glasgow2024.css",
    font_urls="https://fonts.googleapis.com/css2?family=Roboto&family=Roboto+Slab&family=Gruppo&display=swap",
)

convention = ConventionConfiguration(
    name="Glasgow in 2024",
    subtitle="A Worldcon For Our Futures",
    slug="glasgow2024",
    site_url="https://glasgow2024.org",
    hugo_help_email="hugo-help@glasgow2024.org",
    registration_email="registration@glasgow2024.org",
    logo="images/logo_withouttitle_transparent-300x293.png",
    logo_alt_text="Glasgow in 2024 logo",
)
