from .settings import *  # noqa: F403

# Tell Celery to run tasks immediately and synchronously during testing
CELERY_TASK_ALWAYS_EAGER = True
# Optional: Propagate exceptions raised in tasks to the caller
CELERY_TASK_EAGER_PROPAGATES = True
