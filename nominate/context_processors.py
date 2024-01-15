from urllib.parse import urlparse

from django.apps import apps
from django.conf import settings
from django.templatetags.static import static
from nomnom.convention import ConventionConfiguration


def site(request):
    convention: ConventionConfiguration = apps.get_app_config("nominate").convention

    return {
        "USERNAME_LOGIN": settings.NOMNOM_ALLOW_USERNAME_LOGIN_FOR_MEMBERS,
        "HUGO_HELP_EMAIL": convention.get_hugo_help_email(request),
        "REGISTRATION_EMAIL": convention.get_registration_email(request),
        "CONVENTION_NAME": convention.name,
        "CONVENTION_SUBTITLE": convention.subtitle,
        "CONVENTION_SLUG": convention.slug,
        "CONVENTION_SITE_URL": convention.site_url,
        "CONVENTION_LOGO_ALT_TEXT": convention.logo_alt_text,
        "CONVENTION_LOGO": url_or_static(convention.logo),
    }


def url_or_static(url: str) -> str:
    urlparts = urlparse(url)
    if bool(urlparts.scheme):
        return url
    return static(url)
