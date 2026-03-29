"""Base settings for saulzet_et_vous project."""

from pathlib import Path

from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "tinymce",
    # Local apps
    "apps.accounts",
    "apps.reports",
    "apps.dashboard",
    "apps.pages",
    "apps.settings_app",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.ApprovalMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "saulzet_et_vous.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "saulzet_et_vous.context_processors.version",
                "apps.settings_app.context_processors.site_settings",
                "apps.notifications.context_processors.notifications",
            ],
        },
    },
]

WSGI_APPLICATION = "saulzet_et_vous.wsgi.application"

# Custom user model
AUTH_USER_MODEL = "accounts.User"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("fr", _("Français")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login/Logout URLs
LOGIN_URL = "/comptes/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Magic link settings
MAGIC_LINK_EXPIRY_MINUTES = 15

# TinyMCE configuration
TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "height": 500,
    "menubar": "file edit view insert format table",
    "plugins": "advlist autolink lists link image charmap preview anchor "
               "searchreplace visualblocks code fullscreen "
               "insertdatetime media table help wordcount",
    "toolbar": "undo redo | styles | bold italic underline | "
               "alignleft aligncenter alignright alignjustify | "
               "bullist numlist outdent indent | link image | "
               "table | removeformat | help",
    "content_css": "default",
    "branding": False,
    "promotion": False,
    "license_key": "gpl",
}

# Email backend — reads SMTP config from SiteSettings (database)
EMAIL_BACKEND = "apps.settings_app.email_backend.DatabaseEmailBackend"
