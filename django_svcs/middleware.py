import svcs
from django.http import HttpRequest, HttpResponse

from . import apps


def request_container(get_response):
    """Middleware that attaches a service container to the request"""

    def middleware(request: HttpRequest) -> HttpResponse:
        setattr(
            request, apps._KEY_CONTAINER, svcs.Container(registry=apps.get_registry())
        )
        return get_response(request)

    return middleware
