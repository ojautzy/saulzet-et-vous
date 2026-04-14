"""Tests for accounts app."""

import hashlib
import secrets

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from apps.settings_app.models import Village

User = get_user_model()


def _get_or_create_village(slug="bourg", name="Le Bourg", lat=45.6415, lng=2.9178):
    """Helper to get or create a village for tests."""
    return Village.objects.get_or_create(
        slug=slug, defaults={"name": name, "latitude": lat, "longitude": lng, "order": 1}
    )[0]


@pytest.fixture
def client():
    return Client()


class TestUserManager(TestCase):
    """Tests for the custom UserManager."""

    def test_create_user_with_password(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Jean",
            last_name="Dupont",
        )
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert not user.is_staff
        assert not user.is_superuser
        assert user.role == User.Role.CITIZEN

    def test_create_user_without_password(self):
        user = User.objects.create_user(
            email="nopass@example.com",
            first_name="Marie",
            last_name="Martin",
        )
        assert user.email == "nopass@example.com"
        assert not user.has_usable_password()

    def test_create_user_no_email_raises(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email="", password="test123")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            first_name="Admin",
            last_name="Super",
        )
        assert user.is_staff
        assert user.is_superuser
        assert user.is_approved
        assert user.role == User.Role.ADMIN

    def test_email_normalized(self):
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM", first_name="A", last_name="B"
        )
        assert user.email == "Test@example.com"


class TestUserModel(TestCase):
    """Tests for the User model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="citizen@example.com",
            first_name="Pierre",
            last_name="Durand",
            role=User.Role.CITIZEN,
        )

    def test_str(self):
        assert str(self.user) == "Pierre Durand"

    def test_is_admin_property(self):
        assert not self.user.is_admin
        self.user.role = User.Role.ADMIN
        assert self.user.is_admin

    def test_is_mayor_property(self):
        assert not self.user.is_mayor
        self.user.role = User.Role.MAYOR
        assert self.user.is_mayor

    def test_is_elected_property(self):
        assert not self.user.is_elected
        self.user.role = User.Role.ELECTED
        assert self.user.is_elected
        self.user.role = User.Role.MAYOR
        assert self.user.is_elected

    def test_default_not_approved(self):
        assert not self.user.is_approved


class TestRegistration(TestCase):
    """Tests for registration flow."""

    def test_register_creates_unapproved_user(self):
        response = self.client.post(
            "/comptes/register/",
            {
                "email": "new@example.com",
                "first_name": "Nouveau",
                "last_name": "Habitant",
                "phone": "0612345678",
                "address": "3 rue du Bourg",
                "village": _get_or_create_village().pk,
                "password1": "",
                "password2": "",
            },
        )
        assert response.status_code == 302
        user = User.objects.get(email="new@example.com")
        assert not user.is_approved
        assert user.first_name == "Nouveau"
        assert not user.has_usable_password()

    def test_register_with_password(self):
        response = self.client.post(
            "/comptes/register/",
            {
                "email": "withpass@example.com",
                "first_name": "Avec",
                "last_name": "Motdepasse",
                "phone": "0698765432",
                "address": "5 place de l'Église",
                "village": _get_or_create_village().pk,
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        assert response.status_code == 302
        user = User.objects.get(email="withpass@example.com")
        assert user.has_usable_password()
        assert user.check_password("SecurePass123!")

    def test_register_password_mismatch(self):
        response = self.client.post(
            "/comptes/register/",
            {
                "email": "mismatch@example.com",
                "first_name": "Test",
                "last_name": "User",
                "phone": "0611111111",
                "address": "1 rue Test",
                "village": _get_or_create_village().pk,
                "password1": "pass1",
                "password2": "pass2",
            },
        )
        assert response.status_code == 200  # re-renders form
        assert not User.objects.filter(email="mismatch@example.com").exists()


class TestMagicLink(TestCase):
    """Tests for magic link authentication."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="magic@example.com",
            first_name="Magic",
            last_name="User",
            is_approved=True,
        )

    def test_magic_link_generation(self):
        response = self.client.post(
            "/comptes/magic/request/",
            {"email": "magic@example.com"},
        )
        assert response.status_code == 302
        self.user.refresh_from_db()
        assert self.user.magic_link_token is not None
        assert self.user.magic_link_expires is not None

    def test_magic_link_email_uses_correct_url_prefix(self):
        """Regression: the emailed magic link must use /comptes/, not /accounts/.

        The accounts app is mounted under /comptes/ in the project URLconf,
        so a hardcoded /accounts/... prefix produced 404s on click.
        """
        from django.core import mail

        mail.outbox.clear()
        self.client.post(
            "/comptes/magic/request/",
            {"email": "magic@example.com"},
        )
        assert len(mail.outbox) == 1
        body = mail.outbox[0].body
        assert "/comptes/magic/" in body
        assert "/accounts/magic/" not in body

    def test_magic_link_valid_token(self):
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        self.user.magic_link_token = token_hash
        self.user.magic_link_expires = timezone.now() + timezone.timedelta(minutes=15)
        self.user.save()

        response = self.client.get(f"/comptes/magic/{raw_token}/")
        assert response.status_code == 302
        assert response.url == "/"

        # Token should be invalidated
        self.user.refresh_from_db()
        assert self.user.magic_link_token is None

    def test_magic_link_expired_token(self):
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        self.user.magic_link_token = token_hash
        self.user.magic_link_expires = timezone.now() - timezone.timedelta(minutes=1)
        self.user.save()

        response = self.client.get(f"/comptes/magic/{raw_token}/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_magic_link_invalid_token(self):
        response = self.client.get("/comptes/magic/invalid-token/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_magic_link_one_time_use(self):
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        self.user.magic_link_token = token_hash
        self.user.magic_link_expires = timezone.now() + timezone.timedelta(minutes=15)
        self.user.save()

        # First use
        self.client.get(f"/comptes/magic/{raw_token}/")
        self.client.logout()

        # Second use should fail
        response = self.client.get(f"/comptes/magic/{raw_token}/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_magic_link_unapproved_user(self):
        self.user.is_approved = False
        self.user.save()

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        self.user.magic_link_token = token_hash
        self.user.magic_link_expires = timezone.now() + timezone.timedelta(minutes=15)
        self.user.save()

        response = self.client.get(f"/comptes/magic/{raw_token}/")
        assert response.status_code == 302
        assert "pending" in response.url

    def test_magic_link_nonexistent_email(self):
        response = self.client.post(
            "/comptes/magic/request/",
            {"email": "doesntexist@example.com"},
        )
        # Should not reveal that user doesn't exist
        assert response.status_code == 302


class TestApprovalMiddleware(TestCase):
    """Tests for the approval middleware."""

    def setUp(self):
        self.unapproved_user = User.objects.create_user(
            email="unapproved@example.com",
            password="testpass123",
            first_name="Not",
            last_name="Approved",
            is_approved=False,
        )
        self.approved_user = User.objects.create_user(
            email="approved@example.com",
            password="testpass123",
            first_name="Is",
            last_name="Approved",
            is_approved=True,
        )

    def test_unapproved_redirected_to_pending(self):
        self.client.login(email="unapproved@example.com", password="testpass123")
        response = self.client.get("/comptes/profile/")
        assert response.status_code == 302
        assert "pending" in response.url

    def test_approved_user_can_access(self):
        self.client.login(email="approved@example.com", password="testpass123")
        response = self.client.get("/comptes/profile/")
        assert response.status_code == 200

    def test_unapproved_can_access_exempt_urls(self):
        self.client.login(email="unapproved@example.com", password="testpass123")
        response = self.client.get("/comptes/pending/")
        assert response.status_code == 200

    def test_anonymous_not_affected(self):
        response = self.client.get("/")
        assert response.status_code == 200


class TestPasswordLogin(TestCase):
    """Tests for password-based login."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="passlogin@example.com",
            password="testpass123",
            first_name="Pass",
            last_name="Login",
            is_approved=True,
        )

    def test_valid_login(self):
        response = self.client.post(
            "/comptes/login/password/",
            {"username": "passlogin@example.com", "password": "testpass123"},
        )
        assert response.status_code == 302
        assert response.url == "/"

    def test_invalid_login(self):
        response = self.client.post(
            "/comptes/login/password/",
            {"username": "passlogin@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 200  # re-renders form

    def test_unapproved_login_redirects_to_pending(self):
        self.user.is_approved = False
        self.user.save()
        response = self.client.post(
            "/comptes/login/password/",
            {"username": "passlogin@example.com", "password": "testpass123"},
        )
        assert response.status_code == 302
        assert "pending" in response.url


class TestVillageField(TestCase):
    """Tests for the village field on User."""

    def test_register_with_village_required(self):
        response = self.client.post(
            "/comptes/register/",
            {
                "email": "village@example.com",
                "first_name": "Test",
                "last_name": "Village",
                "phone": "0612345678",
                "address": "3 rue du Bourg",
                "village": "",
                "password1": "",
                "password2": "",
            },
        )
        # Should re-render form (village is required)
        assert response.status_code == 200
        assert not User.objects.filter(email="village@example.com").exists()

    def test_register_with_village_success(self):
        village = _get_or_create_village()
        response = self.client.post(
            "/comptes/register/",
            {
                "email": "village@example.com",
                "first_name": "Test",
                "last_name": "Village",
                "phone": "0612345678",
                "address": "3 rue du Bourg",
                "village": village.pk,
                "password1": "",
                "password2": "",
            },
        )
        assert response.status_code == 302
        user = User.objects.get(email="village@example.com")
        assert user.village == village
        assert str(user.village) == "Le Bourg"

    def test_profile_update_village(self):
        village_bourg = _get_or_create_village()
        village_pessade = _get_or_create_village("pessade", "Pessade", 45.6347, 2.8895)
        user = User.objects.create_user(
            email="profile@example.com",
            password="testpass123",
            first_name="Pro",
            last_name="File",
            is_approved=True,
            village=village_bourg,
        )
        self.client.login(email="profile@example.com", password="testpass123")
        response = self.client.post(
            "/comptes/profile/",
            {
                "first_name": "Pro",
                "last_name": "File",
                "phone": "0612345678",
                "address": "5 rue haute",
                "village": village_pessade.pk,
            },
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.village == village_pessade

    def test_village_displayed_in_dashboard_detail(self):
        village_z = _get_or_create_village("zanieres", "Zanières", 45.6407, 2.9406)
        citizen = User.objects.create_user(
            email="citizen_v@test.com",
            password="testpass123",
            first_name="Jean",
            last_name="Dupont",
            is_approved=True,
            village=village_z,
        )
        User.objects.create_user(
            email="elected_v@test.com",
            password="testpass123",
            first_name="Marie",
            last_name="Martin",
            is_approved=True,
            role=User.Role.ELECTED,
        )
        from apps.reports.models import Report

        report = Report.objects.create(
            author=citizen,
            title="Test village display",
            description="Test",
            report_type="issue",
        )
        self.client.login(email="elected_v@test.com", password="testpass123")
        from django.urls import reverse

        response = self.client.get(
            reverse("dashboard:detail", kwargs={"pk": report.pk})
        )
        assert response.status_code == 200
        assert "Zanières" in response.content.decode()


class TestPasswordChange(TestCase):
    """Tests for the password change / set view."""

    URL = "/comptes/mot-de-passe/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="changer@example.com",
            password="oldpass123!",
            first_name="Cha",
            last_name="Nger",
            is_approved=True,
        )

    def test_requires_login(self):
        response = self.client.get(self.URL)
        assert response.status_code == 302
        assert "/comptes/login" in response.url

    def test_get_renders_change_form(self):
        self.client.login(email="changer@example.com", password="oldpass123!")
        response = self.client.get(self.URL)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Changer mon mot de passe" in content
        assert "old_password" in content

    def test_change_password_success(self):
        self.client.login(email="changer@example.com", password="oldpass123!")
        response = self.client.post(
            self.URL,
            {
                "old_password": "oldpass123!",
                "new_password1": "BrandNew$ecret42",
                "new_password2": "BrandNew$ecret42",
            },
        )
        assert response.status_code == 302
        assert response.url == "/comptes/profile/"
        self.user.refresh_from_db()
        assert self.user.check_password("BrandNew$ecret42")
        # Session preserved (still authenticated after change)
        response2 = self.client.get("/comptes/profile/")
        assert response2.status_code == 200

    def test_change_password_wrong_old_password(self):
        self.client.login(email="changer@example.com", password="oldpass123!")
        response = self.client.post(
            self.URL,
            {
                "old_password": "wrong!",
                "new_password1": "BrandNew$ecret42",
                "new_password2": "BrandNew$ecret42",
            },
        )
        assert response.status_code == 200
        self.user.refresh_from_db()
        assert self.user.check_password("oldpass123!")

    def test_change_password_validators_reject_short_password(self):
        self.client.login(email="changer@example.com", password="oldpass123!")
        response = self.client.post(
            self.URL,
            {
                "old_password": "oldpass123!",
                "new_password1": "abc",
                "new_password2": "abc",
            },
        )
        assert response.status_code == 200
        self.user.refresh_from_db()
        assert self.user.check_password("oldpass123!")

    def test_set_password_for_user_without_password(self):
        magic_user = User.objects.create_user(
            email="magic@example.com",
            first_name="Ma",
            last_name="Gic",
            is_approved=True,
        )
        assert not magic_user.has_usable_password()
        self.client.force_login(magic_user)

        # GET shows the "set" form (no old_password field)
        response = self.client.get(self.URL)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Définir un mot de passe" in content
        assert "old_password" not in content

        response = self.client.post(
            self.URL,
            {
                "new_password1": "FreshSecret$42",
                "new_password2": "FreshSecret$42",
            },
        )
        assert response.status_code == 302
        magic_user.refresh_from_db()
        assert magic_user.has_usable_password()
        assert magic_user.check_password("FreshSecret$42")
