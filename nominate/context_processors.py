from django.conf import settings


def site(request):
    return {"USERNAME_LOGIN": settings.NOMNOM_ALLOW_USERNAME_LOGIN_FOR_MEMBERS}
