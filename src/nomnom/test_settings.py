# from .settings import *  # noqa: F403
import subprocess

from nomnom.convention import system_configuration as cfg

# enable the nplusone profiler
INSTALLED_APPS = [
    "nomnom.apps.NomnomAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "markdownify.apps.MarkdownifyConfig",
    "django_bootstrap5",
    "nomnom.base",
    "django_svcs",
    "nomnom_dev",
    "nomnom.nominate",
    "nomnom.advise",
    "nplusone.ext.django",
]  # noqa: F405

MIDDLEWARE = [
    "nplusone.ext.django.NPlusOneMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django_svcs.middleware.request_container",
    "django_htmx.middleware.HtmxMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
]
NPLUSONE_RAISE = True

SITE_ID = 42

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "nomnom.nominate.context_processors.site",
                "nomnom.nominate.context_processors.inject_login_form",
            ],
        },
    },
]

# Tell Celery to run tasks immediately and synchronously during testing
CELERY_TASK_ALWAYS_EAGER = True
# Optional: Propagate exceptions raised in tasks to the caller
CELERY_TASK_EAGER_PROPAGATES = True

# Don't bother with persistent connections
CONN_MAX_AGE = 0
CONN_HEALTH_CHECKS = False

# let's just get the port from docker compose, if we can.
try:
    db_port = (
        subprocess.run(
            "docker compose port db 5432", shell=True, capture_output=True, check=True
        )
        .stdout.strip()
        .split(b":")[-1]
    ).decode("utf-8")
    db_host = "127.0.0.1"
except subprocess.CalledProcessError:
    db_port = str(cfg.db.port)
    db_host = cfg.db.host

# try:
#     redis_port = subprocess.run(
#         "docker compose port redis 6379", shell=True, capture_output=True, check=True
#     ).strip()
#     redis_url = f"redis://localhost:{redis_port}"
# except subprocess.CalledProcessError:
#     redis_url = cfg.redis.url

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": cfg.db.name,
        "USER": cfg.db.user,
        "PASSWORD": cfg.db.password,
        "HOST": db_host,
        "PORT": db_port,
    }
}

SECRET_KEY = "bogon"

ROOT_URLCONF = "nomnom.urls"

DEBUG_TOOLBAR_ENABLED = False
NOMNOM_ALLOW_USERNAME_LOGIN_FOR_MEMBERS = True
