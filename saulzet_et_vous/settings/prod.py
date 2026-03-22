"""Production settings for saulzet_et_vous project."""

import environ

from .base import *  # noqa: F401, F403

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")  # noqa: F405

SECRET_KEY = env("SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Database
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.example.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Saulzet & Vous <noreply@saulzet.jautzy.com>")

# Site URL for magic links
SITE_URL = env("SITE_URL", default="https://saulzet.jautzy.com")

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
