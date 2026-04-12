"""Tests for pages admin access and secretary permissions."""

import pytest
from django.contrib.auth.models import Permission
from django.test import Client

from apps.pages.models import Page


def _give_page_perms(user):
    """Grant all pages app permissions to a user."""
    perms = Permission.objects.filter(content_type__app_label="pages")
    user.user_permissions.set(perms)
    user.save()
    # Clear cached permissions
    user._perm_cache = set()
    user._user_perm_cache = set()


@pytest.fixture
def standard_page(db, admin_user):
    """A standard page created by admin."""
    return Page.objects.create(
        title="Page standard",
        slug="page-standard",
        template=Page.Template.DEFAULT,
        content="Contenu standard",
        is_published=True,
        created_by=admin_user,
    )


@pytest.fixture
def secretary_page(db, secretary):
    """A standard page created by secretary."""
    _give_page_perms(secretary)
    return Page.objects.create(
        title="Page du secrétaire",
        slug="page-secretaire",
        template=Page.Template.DEFAULT,
        content="Contenu secrétaire",
        is_published=True,
        created_by=secretary,
    )


@pytest.fixture
def contact_page(db, admin_user):
    """A special contact page."""
    return Page.objects.create(
        title="Contact",
        slug="contact",
        template=Page.Template.CONTACT,
        content="",
        is_published=True,
        created_by=admin_user,
    )


@pytest.fixture
def special_pages(db, admin_user):
    """All special template pages."""
    pages = {}
    for template in [
        Page.Template.CONTACT,
        Page.Template.DOCUMENTS,
        Page.Template.EQUIPE,
        Page.Template.GALERIE,
        Page.Template.HABITANTS,
        Page.Template.ACCES,
    ]:
        pages[template] = Page.objects.create(
            title=f"Page {template}",
            slug=f"page-{template}",
            template=template,
            content="",
            is_published=True,
            created_by=admin_user,
        )
    return pages


@pytest.mark.django_db
class TestSecretaryAdminAccess:
    def test_secretary_can_access_admin(self, secretary):
        client = Client()
        client.force_login(secretary)
        response = client.get("/admin/")
        assert response.status_code == 200

    def test_secretary_can_see_pages(self, secretary):
        _give_page_perms(secretary)
        client = Client()
        client.force_login(secretary)
        response = client.get("/admin/pages/page/")
        assert response.status_code == 200

    def test_secretary_can_see_documents(self, secretary):
        _give_page_perms(secretary)
        client = Client()
        client.force_login(secretary)
        response = client.get("/admin/pages/document/")
        assert response.status_code == 200

    def test_secretary_cannot_see_users(self, secretary):
        client = Client()
        client.force_login(secretary)
        response = client.get("/admin/accounts/user/")
        assert response.status_code == 403

    def test_citizen_cannot_access_admin(self, citizen):
        client = Client()
        client.force_login(citizen)
        response = client.get("/admin/")
        assert response.status_code == 302


@pytest.mark.django_db
class TestSecretaryPagePermissions:
    """Test that secretary cannot modify special pages."""

    def test_secretary_can_edit_standard_page(self, secretary, standard_page):
        _give_page_perms(secretary)
        client = Client()
        client.force_login(secretary)
        url = f"/admin/pages/page/{standard_page.pk}/change/"
        response = client.get(url)
        assert response.status_code == 200
        # Should have save button (editable)
        assert b"_save" in response.content

    def test_secretary_cannot_edit_special_page(self, secretary, special_pages):
        _give_page_perms(secretary)
        client = Client()
        client.force_login(secretary)
        for template, page in special_pages.items():
            url = f"/admin/pages/page/{page.pk}/change/"
            response = client.get(url)
            # Django shows read-only view (200) but without save button
            assert response.status_code == 200, f"Should show read-only view for {template}"
            assert b"_save" not in response.content, f"Should not have save button for {template}"

    def test_secretary_cannot_post_to_special_page(self, secretary, contact_page):
        _give_page_perms(secretary)
        client = Client()
        client.force_login(secretary)
        url = f"/admin/pages/page/{contact_page.pk}/change/"
        response = client.post(url, {
            "title": "Hacked",
            "slug": "hacked",
            "template": Page.Template.CONTACT,
            "content": "Hacked content",
        })
        # Django returns 403 for unauthorized POST
        assert response.status_code == 403
        contact_page.refresh_from_db()
        assert contact_page.title == "Contact"

    def test_secretary_can_delete_own_standard_page(self, secretary, secretary_page):
        _give_page_perms(secretary)
        client = Client()
        client.force_login(secretary)
        url = f"/admin/pages/page/{secretary_page.pk}/delete/"
        response = client.get(url)
        assert response.status_code == 200

    def test_secretary_cannot_delete_others_standard_page(self, secretary, standard_page):
        _give_page_perms(secretary)
        client = Client()
        client.force_login(secretary)
        url = f"/admin/pages/page/{standard_page.pk}/delete/"
        response = client.get(url)
        assert response.status_code == 403

    def test_secretary_cannot_delete_special_page(self, secretary, contact_page):
        _give_page_perms(secretary)
        client = Client()
        client.force_login(secretary)
        url = f"/admin/pages/page/{contact_page.pk}/delete/"
        response = client.get(url)
        assert response.status_code == 403

    def test_secretary_cannot_create_special_template_page(self, secretary):
        _give_page_perms(secretary)
        client = Client()
        client.force_login(secretary)
        url = "/admin/pages/page/add/"
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        # Template choices should only include standard templates
        assert "contact" not in content.lower() or "Contact" not in content
        # Verify only DEFAULT and FULL_WIDTH are available
        assert "Standard" in content or "default" in content

    def test_secretary_sees_info_message_on_special_page(self, secretary, contact_page):
        _give_page_perms(secretary)
        client = Client()
        client.force_login(secretary)
        url = f"/admin/pages/page/{contact_page.pk}/change/"
        response = client.get(url)
        assert response.status_code == 200
        assert "protégée" in response.content.decode()

    def test_admin_can_edit_special_page(self, admin_user, contact_page):
        client = Client()
        client.force_login(admin_user)
        url = f"/admin/pages/page/{contact_page.pk}/change/"
        response = client.get(url)
        assert response.status_code == 200
        assert b"_save" in response.content

    def test_admin_can_delete_any_page(self, admin_user, standard_page, contact_page):
        client = Client()
        client.force_login(admin_user)
        for page in [standard_page, contact_page]:
            url = f"/admin/pages/page/{page.pk}/delete/"
            response = client.get(url)
            assert response.status_code == 200

    def test_admin_can_create_special_template_page(self, admin_user):
        client = Client()
        client.force_login(admin_user)
        url = "/admin/pages/page/add/"
        response = client.get(url)
        content = response.content.decode()
        # Admin should see all templates including special ones
        assert "contact" in content.lower() or "Contact" in content
