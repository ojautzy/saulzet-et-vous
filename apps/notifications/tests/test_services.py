"""Tests for notification services."""

import pytest
from django.contrib.auth import get_user_model
from django.core import mail

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.services import (
    notify,
    notify_assignment,
    notify_new_comment,
    notify_new_registration,
    notify_new_report,
    notify_status_change,
)
from apps.reports.models import Comment, Report

User = get_user_model()


@pytest.mark.django_db
class TestNotify:
    def test_creates_notification(self, citizen):
        n = notify(
            recipient=citizen,
            notification_type=Notification.Type.STATUS_CHANGE,
            title="Test",
            message="Test msg",
        )
        assert n.pk is not None
        assert Notification.objects.filter(recipient=citizen).count() == 1

    def test_sends_email_when_prefs_enabled(self, citizen):
        prefs, _ = NotificationPreference.objects.get_or_create(user=citizen)
        prefs.email_status_change = True
        prefs.save()
        notify(
            recipient=citizen,
            notification_type=Notification.Type.STATUS_CHANGE,
            title="Test",
            message="Test msg",
            email_template="status_change",
            email_subject="Test Subject",
            email_context={"report": None, "old_status": "new", "new_status": "assigned", "changed_by": None},
        )
        assert len(mail.outbox) == 1

    def test_no_email_when_prefs_disabled(self, citizen):
        prefs, _ = NotificationPreference.objects.get_or_create(user=citizen)
        prefs.email_status_change = False
        prefs.save()
        notify(
            recipient=citizen,
            notification_type=Notification.Type.STATUS_CHANGE,
            title="Test",
            message="Test msg",
            email_template="status_change",
            email_subject="Test",
            email_context={},
        )
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestNotifyStatusChange:
    def test_notifies_author(self, citizen, elected):
        report = Report.objects.create(
            author=citizen, title="Test", description="Desc", report_type="issue",
        )
        notify_status_change(report, "new", "assigned", elected)
        assert Notification.objects.filter(recipient=citizen, notification_type="status_change").count() == 1

    def test_no_notification_if_author_changed_own(self, citizen):
        report = Report.objects.create(
            author=citizen, title="Test", description="Desc", report_type="issue",
        )
        notify_status_change(report, "new", "cancelled", citizen)
        assert Notification.objects.filter(recipient=citizen, notification_type="status_change").count() == 0


@pytest.mark.django_db
class TestNotifyNewComment:
    def test_notifies_author_when_elected_comments(self, citizen, elected):
        report = Report.objects.create(
            author=citizen, assigned_to=elected, title="T", description="D", report_type="idea",
        )
        comment = Comment.objects.create(report=report, author=elected, content="Reply")
        notify_new_comment(report, comment, elected)
        assert Notification.objects.filter(recipient=citizen, notification_type="new_comment").exists()

    def test_notifies_elected_when_author_comments(self, citizen, elected):
        report = Report.objects.create(
            author=citizen, assigned_to=elected, title="T", description="D", report_type="idea",
        )
        comment = Comment.objects.create(report=report, author=citizen, content="Question")
        notify_new_comment(report, comment, citizen)
        assert Notification.objects.filter(recipient=elected, notification_type="new_comment").exists()


@pytest.mark.django_db
class TestNotifyNewReport:
    def test_notifies_elected_and_mayor(self, citizen, elected, mayor):
        report = Report.objects.create(
            author=citizen, title="T", description="D", report_type="question",
        )
        notify_new_report(report)
        assert Notification.objects.filter(notification_type="new_report").count() == 2


@pytest.mark.django_db
class TestNotifyAssignment:
    def test_notifies_assigned_elected(self, elected, mayor):
        report = Report.objects.create(
            author=User.objects.create_user(email="c@t.fr", first_name="C", last_name="T"),
            title="T", description="D", report_type="issue",
        )
        notify_assignment(report, elected, mayor)
        assert Notification.objects.filter(recipient=elected, notification_type="assignment").exists()

    def test_no_notification_self_assign(self, elected):
        report = Report.objects.create(
            author=User.objects.create_user(email="c2@t.fr", first_name="C", last_name="T"),
            title="T", description="D", report_type="issue",
        )
        notify_assignment(report, elected, elected)
        assert not Notification.objects.filter(notification_type="assignment").exists()


@pytest.mark.django_db
class TestNotifyNewRegistration:
    def test_notifies_admins_only(self, admin_user, mayor):
        new_user = User.objects.create_user(
            email="new@test.fr", first_name="New", last_name="User",
        )
        notify_new_registration(new_user)
        notifs = Notification.objects.filter(notification_type="new_registration")
        assert notifs.count() == 1
        assert notifs.first().recipient == admin_user
