"""Tests for settings_app context processors."""

import pytest
from django.test import RequestFactory

from apps.settings_app.context_processors import site_settings
from apps.settings_app.models import SiteSettings


@pytest.mark.django_db
class TestSiteSettingsContextProcessor:
    def test_injects_site_settings(self):
        factory = RequestFactory()
        request = factory.get("/")
        context = site_settings(request)
        assert "site_settings" in context
        assert isinstance(context["site_settings"], SiteSettings)

    def test_injects_active_villages(self):
        factory = RequestFactory()
        request = factory.get("/")
        context = site_settings(request)
        assert "villages" in context
        # All returned villages should be active
        for v in context["villages"]:
            assert v.is_active
