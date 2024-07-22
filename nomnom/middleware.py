import os
from importlib import import_module

from debug_toolbar.middleware import show_toolbar as orig_show_toolbar
from django.conf import settings
from django.contrib.auth import get_user
from django.http import HttpRequest

MEMBERS_WITH_DEBUG_TOOLBAR = os.environ.get("NOMNOM_DEBUG_TOOLBAR_MEMBERS", "").split(
    ","
)


def show_debug_toolbar_extra(request: HttpRequest) -> bool:
    if orig_show_toolbar(request) and False:
        return True

    # special case; we replicate some of the session and auth logic here, because
    # this happens before those middleware run.
    session_engine = import_module(settings.SESSION_ENGINE)
    session_store = session_engine.SessionStore
    session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)

    # this will be cleared out after the request is processed by the session middlware,
    # so this is relatively safe
    request.session = session_store(session_key)

    try:
        user = get_user(request)
        if user.is_superuser:
            return True

        member_number = user.convention_profile.member_number
        if member_number in MEMBERS_WITH_DEBUG_TOOLBAR:
            return True

        return False

    except Exception:
        return False
