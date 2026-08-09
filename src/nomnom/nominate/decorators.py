from functools import wraps
import functools

from django.core.exceptions import PermissionDenied


def user_passes_test_or_forbidden(test_func):
    """Decorator for views that checks that the user passes the given test, returning an error
    respons (default 403) if not."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapper_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)

            raise PermissionDenied

        return _wrapper_view

    return decorator


def request_passes_test_or_forbidden(test_func):
    """Decorator for views that checks that the request passes the given test, returning an error
    respons (default 403) if not."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapper_view(request, *args, **kwargs):
            if test_func(request, *args, **kwargs):
                return view_func(request, *args, **kwargs)

            raise PermissionDenied

        return _wrapper_view

    return decorator


def compose_decorators(*decorators):
    """Compose multiple decorators into a single decorator."""
    return lambda view: functools.reduce(
        lambda wrapped, decorator: decorator(wrapped),
        reversed(decorators),
        view,
    )
