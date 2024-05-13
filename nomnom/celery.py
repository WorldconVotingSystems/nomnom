import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nomnom.settings")

app = Celery("nomnom")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# This implicitly calls django.setup as a fixup, which loads tasks
app.loader.import_default_modules()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
