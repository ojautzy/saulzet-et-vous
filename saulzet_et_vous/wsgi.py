"""WSGI config for saulzet_et_vous project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saulzet_et_vous.settings.dev")

application = get_wsgi_application()
