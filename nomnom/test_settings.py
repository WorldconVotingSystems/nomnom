from .settings import *  # noqa: F403

# enable the nplusone profiler
INSTALLED_APPS += ["nplusone.ext.django"]  # noqa: F405
MIDDLEWARE.insert(0, "nplusone.ext.django.NPlusOneMiddleware")  # noqa: F405
NPLUSONE_RAISE = True

# Tell Celery to run tasks immediately and synchronously during testing
CELERY_TASK_ALWAYS_EAGER = True
# Optional: Propagate exceptions raised in tasks to the caller
CELERY_TASK_EAGER_PROPAGATES = True

# Don't bother with persistent connections
CONN_MAX_AGE = 0
CONN_HEALTH_CHECKS = False
