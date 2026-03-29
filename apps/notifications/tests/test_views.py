"""Tests for notifications views."""

import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification

User = get_user_model()


@pytest.mark.django_db
class TestNotificationListView:
    def test_requires_login(self, client):
        response = client.get("/etvous/notifications/")
        assert response.status_code == 302

    def test_lists_notifications(self, client, citizen):
        Notification.objects.create(
            recipient=citizen, notification_type="status_change",
            title="Test", message="Msg",
        )
        client.force_login(citizen)
        response = client.get("/etvous/notifications/")
        assert response.status_code == 200
        assert len(response.context["page_obj"]) == 1

    def test_filter_by_type(self, client, citizen):
        Notification.objects.create(
            recipient=citizen, notification_type="status_change",
            title="SC", message="Msg",
        )
        Notification.objects.create(
            recipient=citizen, notification_type="new_comment",
            title="NC", message="Msg",
        )
        client.force_login(citizen)
        response = client.get("/etvous/notifications/?type=status_change")
        assert len(response.context["page_obj"]) == 1

    def test_filter_unread(self, client, citizen):
        Notification.objects.create(
            recipient=citizen, notification_type="status_change",
            title="Read", message="Msg", is_read=True,
        )
        Notification.objects.create(
            recipient=citizen, notification_type="status_change",
            title="Unread", message="Msg", is_read=False,
        )
        client.force_login(citizen)
        response = client.get("/etvous/notifications/?status=unread")
        assert len(response.context["page_obj"]) == 1


@pytest.mark.django_db
class TestMarkRead:
    def test_mark_notification_read(self, client, citizen):
        n = Notification.objects.create(
            recipient=citizen, notification_type="status_change",
            title="Test", message="Msg",
        )
        client.force_login(citizen)
        response = client.post(f"/etvous/notifications/{n.pk}/read/")
        assert response.status_code == 302
        n.refresh_from_db()
        assert n.is_read

    def test_mark_all_read(self, client, citizen):
        for i in range(3):
            Notification.objects.create(
                recipient=citizen, notification_type="status_change",
                title=f"Test {i}", message="Msg",
            )
        client.force_login(citizen)
        response = client.post("/etvous/notifications/mark-all-read/")
        assert response.status_code == 302
        assert Notification.objects.filter(recipient=citizen, is_read=False).count() == 0


@pytest.mark.django_db
class TestPreferences:
    def test_view_preferences(self, client, citizen):
        client.force_login(citizen)
        response = client.get("/etvous/notifications/preferences/")
        assert response.status_code == 200

    def test_update_preferences(self, client, citizen):
        client.force_login(citizen)
        response = client.post("/etvous/notifications/preferences/", {
            "email_status_change": True,
            "email_new_comment": False,
            "email_assignment": True,
            "email_new_report": False,
            "email_reminder": True,
        })
        assert response.status_code == 302
        citizen.notification_preferences.refresh_from_db()
        assert citizen.notification_preferences.email_new_comment is False
