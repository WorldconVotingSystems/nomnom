from ._version import __version__, __version_tuple__  # noqa: F401
from .celery import app as celery_app

__all__ = ("celery_app",)
