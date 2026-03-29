"""Shared test fixtures."""

import pytest
from django.contrib.auth import get_user_model

from apps.settings_app.models import Village

User = get_user_model()


@pytest.fixture
def village_bourg(db):
    """Create the Le Bourg village."""
    return Village.objects.get_or_create(
        slug="bourg",
        defaults={"name": "Le Bourg", "latitude": 45.6415, "longitude": 2.9178, "order": 1},
    )[0]


@pytest.fixture
def citizen(db, village_bourg):
    """Create an approved citizen user."""
    return User.objects.create_user(
        email="habitant@test.fr",
        password="testpass123",
        first_name="Jean",
        last_name="Dupont",
        role=User.Role.CITIZEN,
        is_approved=True,
        village=village_bourg,
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
