"""Tests for accounts app."""

import hashlib
import secrets

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

User = get_user_model()


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
            "/accounts/register/",
            {
                "email": "new@example.com",
                "first_name": "Nouveau",
                "last_name": "Habitant",
                "phone": "0612345678",
                "address": "3 rue du Bourg",
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
            "/accounts/register/",
            {
                "email": "withpass@example.com",
                "first_name": "Avec",
                "last_name": "Motdepasse",
                "phone": "0698765432",
                "address": "5 place de l'Église",
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
            "/accounts/register/",
            {
                "email": "mismatch@example.com",
                "first_name": "Test",
                "last_name": "User",
                "phone": "0611111111",
                "address": "1 rue Test",
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
            "/accounts/magic/request/",
            {"email": "magic@example.com"},
        )
        assert response.status_code == 302
        self.user.refresh_from_db()
        assert self.user.magic_link_token is not None
        assert self.user.magic_link_expires is not None

    def test_magic_link_valid_token(self):
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        self.user.magic_link_token = token_hash
        self.user.magic_link_expires = timezone.now() + timezone.timedelta(minutes=15)
        self.user.save()

        response = self.client.get(f"/accounts/magic/{raw_token}/")
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

        response = self.client.get(f"/accounts/magic/{raw_token}/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_magic_link_invalid_token(self):
        response = self.client.get("/accounts/magic/invalid-token/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_magic_link_one_time_use(self):
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        self.user.magic_link_token = token_hash
        self.user.magic_link_expires = timezone.now() + timezone.timedelta(minutes=15)
        self.user.save()

        # First use
        self.client.get(f"/accounts/magic/{raw_token}/")
        self.client.logout()

        # Second use should fail
        response = self.client.get(f"/accounts/magic/{raw_token}/")
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

        response = self.client.get(f"/accounts/magic/{raw_token}/")
        assert response.status_code == 302
        assert "pending" in response.url

    def test_magic_link_nonexistent_email(self):
        response = self.client.post(
            "/accounts/magic/request/",
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
        response = self.client.get("/accounts/profile/")
        assert response.status_code == 302
        assert "pending" in response.url

    def test_approved_user_can_access(self):
        self.client.login(email="approved@example.com", password="testpass123")
        response = self.client.get("/accounts/profile/")
        assert response.status_code == 200

    def test_unapproved_can_access_exempt_urls(self):
        self.client.login(email="unapproved@example.com", password="testpass123")
        response = self.client.get("/accounts/pending/")
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
            "/accounts/login/password/",
            {"username": "passlogin@example.com", "password": "testpass123"},
        )
        assert response.status_code == 302
        assert response.url == "/"

    def test_invalid_login(self):
        response = self.client.post(
            "/accounts/login/password/",
            {"username": "passlogin@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 200  # re-renders form

    def test_unapproved_login_redirects_to_pending(self):
        self.user.is_approved = False
        self.user.save()
        response = self.client.post(
            "/accounts/login/password/",
            {"username": "passlogin@example.com", "password": "testpass123"},
        )
        assert response.status_code == 302
        assert "pending" in response.url
