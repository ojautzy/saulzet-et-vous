"""Tests for mayor dashboard functionality."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.reports.models import Comment, Report


@pytest.fixture
def report(citizen):
    """Create a sample report."""
    return Report.objects.create(
        title="Nid de poule",
        description="Grosse bosse sur la route principale",
        report_type=Report.Type.ISSUE,
        author=citizen,
    )


@pytest.mark.django_db
class TestMayorDashboard:
    def test_mayor_can_access(self, mayor):
        client = Client()
        client.force_login(mayor)
        response = client.get(reverse("dashboard:mayor_dashboard"))
        assert response.status_code == 200

    def test_elected_cannot_access(self, elected):
        client = Client()
        client.force_login(elected)
        response = client.get(reverse("dashboard:mayor_dashboard"))
        assert response.status_code == 403

    def test_citizen_cannot_access(self, citizen):
        client = Client()
        client.force_login(citizen)
        response = client.get(reverse("dashboard:mayor_dashboard"))
        assert response.status_code == 403

    def test_dashboard_shows_counts(self, mayor, report):
        client = Client()
        client.force_login(mayor)
        response = client.get(reverse("dashboard:mayor_dashboard"))
        assert response.context["counts"]["new"] == 1
        assert response.context["total"] == 1

    def test_dashboard_shows_elected_workload(self, mayor, elected, report):
        # Assign report to elected
        report.status = Report.Status.ASSIGNED
        report.assigned_to = elected
        report.save()

        client = Client()
        client.force_login(mayor)
        response = client.get(reverse("dashboard:mayor_dashboard"))
        workload = response.context["elected_workload"]
        assert len(workload) >= 1


@pytest.mark.django_db
class TestAssignment:
    def test_mayor_can_assign(self, mayor, elected, report):
        client = Client()
        client.force_login(mayor)
        response = client.post(
            reverse("dashboard:assign", args=[report.pk]),
            {"assign_to": elected.pk},
        )
        assert response.status_code == 302
        report.refresh_from_db()
        assert report.status == Report.Status.ASSIGNED
        assert report.assigned_to == elected
        # Check auto-comment created
        assert Comment.objects.filter(report=report, is_status_change=True).exists()

    def test_elected_cannot_assign_to_others(self, elected, report):
        """Regular elected can only self-assign, not assign to others."""
        from apps.accounts.models import User

        other = User.objects.create_user(
            email="autre@test.fr",
            password="testpass123",
            first_name="Autre",
            last_name="Élu",
            role=User.Role.ELECTED,
            is_approved=True,
        )
        client = Client()
        client.force_login(elected)
        # POST with assign_to but elected is not mayor -> self-assigns
        client.post(
            reverse("dashboard:assign", args=[report.pk]),
            {"assign_to": other.pk},
        )
        report.refresh_from_db()
        # Self-assigned because is_mayor is False
        assert report.assigned_to == elected

    def test_reassign_creates_comment(self, mayor, elected, report):
        # First assign
        report.status = Report.Status.ASSIGNED
        report.assigned_to = mayor
        report.save()

        client = Client()
        client.force_login(mayor)
        response = client.post(
            reverse("dashboard:reassign", args=[report.pk]),
            {"assign_to": elected.pk},
        )
        assert response.status_code == 302
        report.refresh_from_db()
        assert report.assigned_to == elected
        comments = Comment.objects.filter(report=report, is_status_change=True)
        assert comments.exists()
