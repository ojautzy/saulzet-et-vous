"""Tests for pages app views."""

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
        })
        assert response.status_code == 200
        assert len(mailoutbox) == 1
        assert "Question" in mailoutbox[0].subject

    def test_contact_post_invalid(self, client):
        response = client.post(reverse("contact"), {
            "name": "",
            "email": "invalid",
            "subject": "",
            "message": "",
        })
        assert response.status_code == 200
        assert response.context["form"].errors


@pytest.mark.django_db
class TestDocumentListView:
    def test_document_list_accessible(self, client):
        response = client.get(reverse("document_list"))
        assert response.status_code == 200

    def test_document_list_with_category_filter(self, client):
        response = client.get(reverse("document_list_category", args=["pv"]))
        assert response.status_code == 200
        assert response.context["current_category"] == "pv"
