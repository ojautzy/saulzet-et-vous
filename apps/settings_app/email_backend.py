"""Custom email backend that reads SMTP config from SiteSettings."""

from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from django.core.mail.backends.smtp import EmailBackend as SmtpBackend


class DatabaseEmailBackend(SmtpBackend):
    """Backend email qui lit la config SMTP depuis SiteSettings.

    Si smtp_host est vide, bascule automatiquement sur ConsoleBackend (mode dev).
    """

    def __init__(self, **kwargs):
        from apps.settings_app.models import SiteSettings

        config = SiteSettings.load()

        if not config.smtp_host:
            self.__class__ = ConsoleBackend
            ConsoleBackend.__init__(self, **kwargs)
            return

        kwargs["host"] = config.smtp_host
        kwargs["port"] = config.smtp_port
        kwargs["username"] = config.smtp_username
        kwargs["password"] = config.smtp_password
        kwargs["use_tls"] = config.smtp_use_tls
        kwargs["use_ssl"] = config.smtp_use_ssl
        super().__init__(**kwargs)
