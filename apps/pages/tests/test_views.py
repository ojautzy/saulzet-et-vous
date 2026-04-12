"""Tests for pages app views."""

import time

import pytest
from django.urls import reverse

from apps.pages.models import Page


@pytest.mark.django_db
class TestPageDetailView:
    def test_published_page_accessible(self, client):
        Page.objects.create(title="À propos", slug="a-propos", is_published=True)
        response = client.get("/a-propos/")
        assert response.status_code == 200

    def test_unpublished_page_returns_404(self, client):
        Page.objects.create(title="Brouillon", slug="brouillon", is_published=False)
        response = client.get("/brouillon/")
        assert response.status_code == 404

    def test_child_page_url(self, client):
        parent = Page.objects.create(title="Mairie", slug="mairie", is_published=True)
        Page.objects.create(
            title="Horaires", slug="horaires", parent=parent, is_published=True
        )
        response = client.get("/mairie/horaires/")
        assert response.status_code == 200

    def test_page_uses_correct_template(self, client):
        Page.objects.create(
            title="Test",
            slug="test",
            is_published=True,
            template=Page.Template.DEFAULT,
        )
        response = client.get("/test/")
        assert "pages/page_default.html" in [t.name for t in response.templates]

    def test_equipe_page_loads_team_members(self, client, mayor, elected):
        Page.objects.create(
            title="Équipe",
            slug="equipe",
            is_published=True,
            template=Page.Template.EQUIPE,
        )
        response = client.get("/equipe/")
        assert response.status_code == 200
        assert mayor in response.context["team_members"]
        assert elected in response.context["team_members"]


@pytest.mark.django_db
class TestHomeView:
    def test_home_accessible(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_home_shows_recent_pages(self, client):
        parent = Page.objects.create(title="Parent", slug="parent", is_published=True)
        child = Page.objects.create(
            title="Actualité", slug="actualite", parent=parent, is_published=True
        )
        response = client.get("/")
        assert response.status_code == 200
        assert child in response.context["recent_pages"]


@pytest.mark.django_db
class TestContactView:
    @pytest.fixture(autouse=True)
    def _disable_ratelimit(self, settings):
        settings.RATELIMIT_ENABLE = False

    def test_contact_get(self, client):
        response = client.get(reverse("contact"))
        assert response.status_code == 200
        assert "form" in response.context

    def test_contact_post_valid(self, client, mailoutbox):
        response = client.post(reverse("contact"), {
            "name": "Test User",
            "email": "test@example.fr",
            "subject": "Question",
            "message": "Bonjour, ceci est un test.",
            "timestamp": str(time.time() - 10),
        })
        assert response.status_code == 200
        assert len(mailoutbox) >= 1
        assert "Test User" in mailoutbox[0].subject

    def test_contact_post_invalid(self, client):
        response = client.post(reverse("contact"), {
            "name": "",
            "email": "invalid",
            "subject": "",
            "message": "",
            "timestamp": str(time.time() - 10),
        })
        assert response.status_code == 200
        assert response.context["form"].errors


@pytest.mark.django_db
class TestContactAntiSpam:
    """Tests for the 3 anti-spam layers on the contact form."""

    @pytest.fixture(autouse=True)
    def _disable_ratelimit(self, settings):
        settings.RATELIMIT_ENABLE = False

    VALID_DATA = {
        "name": "Marie Dupont",
        "email": "marie@example.fr",
        "subject": "Renseignement",
        "message": "Bonjour, je souhaite un renseignement.",
    }

    # -- Honeypot --

    def test_honeypot_filled_rejects(self, client):
        """A bot that fills the hidden website field is rejected."""
        data = {**self.VALID_DATA, "website": "http://spam.com", "timestamp": str(time.time() - 10)}
        response = client.post(reverse("contact"), data)
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_honeypot_empty_passes(self, client, mailoutbox):
        """A human that leaves the honeypot empty passes."""
        data = {**self.VALID_DATA, "website": "", "timestamp": str(time.time() - 10)}
        response = client.post(reverse("contact"), data)
        assert response.status_code == 200
        assert len(mailoutbox) >= 1

    # -- Timestamp --

    def test_instant_submit_rejects(self, client):
        """Submitting faster than CONTACT_MIN_SUBMIT_SECONDS is rejected."""
        data = {**self.VALID_DATA, "timestamp": str(time.time())}
        response = client.post(reverse("contact"), data)
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_missing_timestamp_rejects(self, client):
        """Missing timestamp field is rejected."""
        data = {**self.VALID_DATA}
        response = client.post(reverse("contact"), data)
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_invalid_timestamp_rejects(self, client):
        """Non-numeric timestamp is rejected."""
        data = {**self.VALID_DATA, "timestamp": "not-a-number"}
        response = client.post(reverse("contact"), data)
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_normal_submit_passes(self, client, mailoutbox):
        """A realistic delay passes all checks."""
        data = {**self.VALID_DATA, "timestamp": str(time.time() - 30)}
        response = client.post(reverse("contact"), data)
        assert response.status_code == 200
        assert len(mailoutbox) >= 1

    # -- GET embeds timestamp --

    def test_get_provides_timestamp(self, client):
        """GET response includes a hidden timestamp field with a recent value."""
        response = client.get(reverse("contact"))
        form = response.context["form"]
        ts = form.initial.get("timestamp")
        assert ts is not None
        assert abs(time.time() - float(ts)) < 5


@pytest.mark.django_db
class TestContactRateLimit:
    """Test that rate limiting is enforced on the contact form."""

    def test_rate_limit_blocks_after_threshold(self, client):
        """Posting more than 3 times per minute triggers a 403."""
        data = {
            "name": "Test",
            "email": "t@t.fr",
            "subject": "Test",
            "message": "Test",
            "timestamp": str(time.time() - 10),
        }
        for _ in range(3):
            client.post(reverse("contact"), data)
        response = client.post(reverse("contact"), data)
        assert response.status_code == 403


@pytest.mark.django_db
class TestDocumentListView:
    def test_document_list_accessible(self, client):
        response = client.get(reverse("document_list"))
        assert response.status_code == 200

    def test_document_list_with_category_filter(self, client):
        response = client.get(reverse("document_list_category", args=["pv"]))
        assert response.status_code == 200
        assert response.context["current_category"] == "pv"
