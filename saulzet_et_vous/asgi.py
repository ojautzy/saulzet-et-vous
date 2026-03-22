"""ASGI config for saulzet_et_vous project."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saulzet_et_vous.settings.dev")

application = get_asgi_application()
