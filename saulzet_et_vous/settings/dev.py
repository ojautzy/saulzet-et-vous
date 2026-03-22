"""Development settings for saulzet_et_vous project."""

from .base import *  # noqa: F401, F403

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-dev-key-change-in-production-saulzet-et-vous"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "saulzet.jautzy.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://saulzet.jautzy.com",
]

# Cloudflare tunnel terminates TLS and forwards HTTP to Django
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Email
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "Saulzet & Vous <noreply@saulzet.jautzy.com>"

# Site URL for magic links
SITE_URL = "https://saulzet.jautzy.com"
