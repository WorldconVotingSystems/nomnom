import os

from celery import Celery
from celery.signals import setup_logging
from django_structlog.celery.steps import DjangoStructLogInitStep

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("nomnom")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.steps["worker"].add(DjangoStructLogInitStep)  # type: ignore[assignment]

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@setup_logging.connect
def setup_celery_logging(loglevel, logfile, format, colorize, **kwargs):
    import logging

    from django.conf import settings

    # importing settings and using LOGGING should automatically
    # configure structlog.
    settings_log_config = settings.LOGGING
    logging.config.dictConfig(settings_log_config)
