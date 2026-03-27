"""Tests for pages admin access and secretary permissions."""

import pytest
from django.test import Client


@pytest.mark.django_db
class TestSecretaryAdminAccess:
    def test_secretary_can_access_admin(self, secretary):
        client = Client()
        client.force_login(secretary)
        response = client.get("/admin/")
        assert response.status_code == 200

    def test_secretary_can_see_pages(self, secretary):
        from django.contrib.auth.models import Permission

        # Give secretary page permissions
        perms = Permission.objects.filter(
            content_type__app_label="pages",
        )
        secretary.user_permissions.set(perms)
        secretary.save()

        client = Client()
        client.force_login(secretary)
        response = client.get("/admin/pages/page/")
        assert response.status_code == 200

    def test_secretary_can_see_documents(self, secretary):
        from django.contrib.auth.models import Permission

        perms = Permission.objects.filter(
            content_type__app_label="pages",
        )
        secretary.user_permissions.set(perms)
        secretary.save()

        client = Client()
        client.force_login(secretary)
        response = client.get("/admin/pages/document/")
        assert response.status_code == 200

    def test_secretary_cannot_see_users(self, secretary):
        client = Client()
        client.force_login(secretary)
        # Without accounts permissions, secretary should get 403
        response = client.get("/admin/accounts/user/")
        assert response.status_code == 403

    def test_citizen_cannot_access_admin(self, citizen):
        client = Client()
        client.force_login(citizen)
        response = client.get("/admin/")
        # Redirects to admin login
        assert response.status_code == 302
