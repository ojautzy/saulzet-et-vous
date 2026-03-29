"""Tests for the send_reminders management command."""

from datetime import timedelta
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from apps.notifications.models import Notification
from apps.reports.models import Report

User = get_user_model()


@pytest.mark.django_db
class TestSendReminders:
    def test_sends_reminders_for_old_reports(self, mayor, elected):
        citizen = User.objects.create_user(
            email="c@test.fr", first_name="C", last_name="T", is_approved=True,
        )
        report = Report.objects.create(
            author=citizen, title="Old Report", description="D", report_type="issue",
        )
        Report.objects.filter(pk=report.pk).update(
            created_at=timezone.now() - timedelta(days=10)
        )

        out = StringIO()
        call_command("send_reminders", stdout=out)
        assert Notification.objects.filter(notification_type="reminder").count() >= 1
        assert "1 relance" in out.getvalue()

    def test_dry_run_sends_nothing(self, mayor, elected):
        citizen = User.objects.create_user(
            email="c2@test.fr", first_name="C", last_name="T", is_approved=True,
        )
        report = Report.objects.create(
            author=citizen, title="Old", description="D", report_type="issue",
        )
        Report.objects.filter(pk=report.pk).update(
            created_at=timezone.now() - timedelta(days=10)
        )

        out = StringIO()
        call_command("send_reminders", "--dry-run", stdout=out)
        assert Notification.objects.filter(notification_type="reminder").count() == 0
        assert "DRY RUN" in out.getvalue()

    def test_no_duplicate_within_interval(self, mayor, elected):
        citizen = User.objects.create_user(
            email="c3@test.fr", first_name="C", last_name="T", is_approved=True,
        )
        report = Report.objects.create(
            author=citizen, title="Old", description="D", report_type="issue",
        )
        Report.objects.filter(pk=report.pk).update(
            created_at=timezone.now() - timedelta(days=10)
        )

        call_command("send_reminders", stdout=StringIO())
        first_count = Notification.objects.filter(notification_type="reminder").count()
        call_command("send_reminders", stdout=StringIO())
        second_count = Notification.objects.filter(notification_type="reminder").count()
        assert first_count == second_count

    def test_custom_days_override(self, mayor, elected):
        citizen = User.objects.create_user(
            email="c4@test.fr", first_name="C", last_name="T", is_approved=True,
        )
        report = Report.objects.create(
            author=citizen, title="Recent", description="D", report_type="issue",
        )
        Report.objects.filter(pk=report.pk).update(
            created_at=timezone.now() - timedelta(days=3)
        )

        out = StringIO()
        call_command("send_reminders", "--days", "2", stdout=out)
        assert Notification.objects.filter(notification_type="reminder").count() >= 1
