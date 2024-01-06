from django.conf import settings


def site(request):
    return {
        "USERNAME_LOGIN": settings.NOMNOM_ALLOW_USERNAME_LOGIN_FOR_MEMBERS,
        "HUGO_HELP_EMAIL": settings.NOMNOM_CONVENTION_HUGO_HELP_EMAIL,
    }
