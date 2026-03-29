"""Tests for notifications models."""

import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import AuditLog, Notification, NotificationPreference

User = get_user_model()


@pytest.mark.django_db
class TestNotification:
    def test_create_notification(self, citizen):
        n = Notification.objects.create(
            recipient=citizen,
            notification_type=Notification.Type.STATUS_CHANGE,
            title="Test",
            message="Test message",
        )
        assert n.pk is not None
        assert not n.is_read
        assert str(n) == f"Changement de statut → {citizen.email}"

    def test_ordering_newest_first(self, citizen):
        Notification.objects.create(
            recipient=citizen, notification_type=Notification.Type.STATUS_CHANGE,
            title="First", message="First",
        )
        n2 = Notification.objects.create(
            recipient=citizen, notification_type=Notification.Type.NEW_COMMENT,
            title="Second", message="Second",
        )
        notifications = list(Notification.objects.filter(recipient=citizen))
        assert notifications[0].pk == n2.pk


@pytest.mark.django_db
class TestNotificationPreference:
    def test_auto_created_on_user_creation(self):
        user = User.objects.create_user(
            email="prefs@test.fr", first_name="Test", last_name="Prefs",
        )
        assert NotificationPreference.objects.filter(user=user).exists()

    def test_default_all_enabled(self, citizen):
        prefs, _ = NotificationPreference.objects.get_or_create(user=citizen)
        assert prefs.email_status_change is True
        assert prefs.email_new_comment is True
        assert prefs.email_assignment is True


@pytest.mark.django_db
class TestAuditLog:
    def test_create_log(self, citizen):
        log = AuditLog.objects.create(
            user=citizen,
            action=AuditLog.Action.LOGIN,
            target_type="user",
            target_id=str(citizen.pk),
            target_label=str(citizen),
        )
        assert log.pk is not None
        assert "Connexion" in str(log)
