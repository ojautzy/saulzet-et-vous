"""Shared test fixtures."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def citizen(db):
    """Create an approved citizen user."""
    return User.objects.create_user(
        email="habitant@test.fr",
        password="testpass123",
        first_name="Jean",
        last_name="Dupont",
        role=User.Role.CITIZEN,
        is_approved=True,
        village="bourg",
    )


@pytest.fixture
def elected(db):
    """Create an approved elected official."""
    return User.objects.create_user(
        email="elu@test.fr",
        password="testpass123",
        first_name="Pierre",
        last_name="Martin",
        role=User.Role.ELECTED,
        is_approved=True,
        function_title="Conseiller municipal",
        function_order=10,
    )


@pytest.fixture
def mayor(db):
    """Create an approved mayor."""
    return User.objects.create_user(
        email="maire@test.fr",
        password="testpass123",
        first_name="Marie",
        last_name="Durand",
        role=User.Role.MAYOR,
        is_approved=True,
        function_title="Maire",
        function_order=1,
    )


@pytest.fixture
def secretary(db):
    """Create a secretary user."""
    user = User.objects.create_user(
        email="secretaire@test.fr",
        password="testpass123",
        first_name="Anne",
        last_name="Secrétaire",
        role=User.Role.SECRETARY,
        is_staff=True,
    )
    return user


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        email="admin@test.fr",
        password="testpass123",
        first_name="Admin",
        last_name="Test",
    )
