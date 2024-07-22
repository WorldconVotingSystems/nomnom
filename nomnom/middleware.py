from debug_toolbar.middleware import show_toolbar as orig_show_toolbar
from django.http import HttpRequest


def show_debug_toolbar_extra(request: HttpRequest) -> bool:
    if orig_show_toolbar(request):
        return True

    # special case
    try:
        return request.user.is_superuser
    except Exception:
        return False
