"""Tests for settings_app models."""

import pytest
from django.core.cache import cache

from apps.settings_app.models import SiteSettings, Village


@pytest.mark.django_db
class TestSiteSettings:
    def setup_method(self):
        cache.clear()

    def test_singleton_creation(self):
        s = SiteSettings.load()
        assert s.pk == 1

    def test_singleton_prevents_second_instance(self):
        SiteSettings.load()
        s2 = SiteSettings(site_name="Test")
        s2.save()
        assert s2.pk == 1
        assert SiteSettings.objects.count() == 1

    def test_load_creates_if_missing(self):
        SiteSettings.objects.all().delete()
        cache.clear()
        s = SiteSettings.load()
        assert s.pk == 1
        assert SiteSettings.objects.count() == 1

    def test_cache_invalidated_on_save(self):
        s = SiteSettings.load()
        cache.set("site_settings", s, 300)
        s.site_name = "Nouveau nom"
        s.save()
        assert cache.get("site_settings") is None

    def test_from_email_property(self):
        s = SiteSettings.load()
        s.email_from_name = "Test"
        s.email_from_address = "test@example.com"
        assert s.from_email == "Test <test@example.com>"

    def test_delete_prevented(self):
        s = SiteSettings.load()
        s.delete()
        assert SiteSettings.objects.filter(pk=1).exists()

    def test_default_values(self):
        s = SiteSettings.load()
        assert s.orphan_days == 7
        assert s.cleanup_days == 30
        assert s.stats_period_days == 180


@pytest.mark.django_db
class TestVillage:
    def test_create_village(self):
        v = Village.objects.create(
            name="Test Village", slug="test-village",
            latitude=45.0, longitude=2.0, order=1,
        )
        assert str(v) == "Test Village"

    def test_ordering(self):
        Village.objects.all().delete()
        Village.objects.create(name="B", slug="b", latitude=0, longitude=0, order=2)
        Village.objects.create(name="A", slug="a", latitude=0, longitude=0, order=1)
        slugs = list(Village.objects.values_list("slug", flat=True))
        assert slugs == ["a", "b"]

    def test_is_active_filter(self):
        Village.objects.all().delete()
        Village.objects.create(name="Active", slug="active", latitude=0, longitude=0, is_active=True)
        Village.objects.create(name="Inactive", slug="inactive", latitude=0, longitude=0, is_active=False)
        active = Village.objects.filter(is_active=True)
        assert active.count() == 1
        assert active.first().name == "Active"

    def test_initial_villages_exist(self):
        """Data migration should have created 6 villages."""
        assert Village.objects.count() >= 6
        assert Village.objects.filter(slug="bourg").exists()
        assert Village.objects.filter(slug="pessade").exists()
