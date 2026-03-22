"""App configuration for reports."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReportsConfig(AppConfig):
    """Configuration for the reports app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reports"
    verbose_name = _("Sollicitations")
