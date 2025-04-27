"""
WSGI config for the NomNom test project.

Manually maintained, similar to the wsgi.py.jinja2 template in convention-template.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nomnom_dev.settings")

application = get_wsgi_application()
