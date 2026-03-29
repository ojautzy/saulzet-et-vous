"""Tests for the custom email backend."""

import pytest
from django.core.mail.backends.console import EmailBackend as ConsoleBackend

from apps.settings_app.email_backend import DatabaseEmailBackend
from apps.settings_app.models import SiteSettings


@pytest.mark.django_db
class TestDatabaseEmailBackend:
    def test_uses_console_when_no_smtp_host(self):
        config = SiteSettings.load()
        config.smtp_host = ""
        config.save()
        backend = DatabaseEmailBackend()
        assert isinstance(backend, ConsoleBackend)

    def test_uses_smtp_when_host_configured(self):
        config = SiteSettings.load()
        config.smtp_host = "smtp.test.com"
        config.smtp_port = 587
        config.save()
        backend = DatabaseEmailBackend()
        assert backend.host == "smtp.test.com"
        assert backend.port == 587
        # Reset
        config.smtp_host = ""
        config.save()

    def test_reads_smtp_credentials(self):
        config = SiteSettings.load()
        config.smtp_host = "smtp.test.com"
        config.smtp_username = "user@test.com"
        config.smtp_password = "secret"
        config.smtp_use_tls = True
        config.smtp_use_ssl = False
        config.save()
        backend = DatabaseEmailBackend()
        assert backend.username == "user@test.com"
        assert backend.password == "secret"
        assert backend.use_tls is True
        assert backend.use_ssl is False
        # Reset
        config.smtp_host = ""
        config.save()
