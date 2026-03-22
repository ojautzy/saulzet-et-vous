"""Tests for the dashboard app."""

import uuid

from django.contrib.auth import get_user_model
from django.template import RequestContext, Template
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from apps.reports.models import Comment, Report

User = get_user_model()


class DashboardTestMixin:
    """Common setup for dashboard tests."""

    def setUp(self) -> None:
        self.client = Client()
        self.citizen = User.objects.create_user(
            email="citizen@test.com",
            password="testpass123",
            first_name="Jean",
            last_name="Dupont",
            is_approved=True,
            role=User.Role.CITIZEN,
        )
        self.elected = User.objects.create_user(
            email="elected@test.com",
            password="testpass123",
            first_name="Marie",
            last_name="Martin",
            is_approved=True,
            role=User.Role.ELECTED,
        )
        self.elected2 = User.objects.create_user(
            email="elected2@test.com",
            password="testpass123",
            first_name="Pierre",
            last_name="Durand",
            is_approved=True,
            role=User.Role.ELECTED,
        )
        self.mayor = User.objects.create_user(
            email="mayor@test.com",
            password="testpass123",
            first_name="Paul",
            last_name="Lefevre",
            is_approved=True,
            role=User.Role.MAYOR,
        )
        self.unapproved_elected = User.objects.create_user(
            email="unapproved@test.com",
            password="testpass123",
            first_name="Luc",
            last_name="Bernard",
            is_approved=False,
            role=User.Role.ELECTED,
        )
        self.report = Report.objects.create(
            author=self.citizen,
            title="Route abîmée",
            description="La route est pleine de trous.",
            report_type=Report.Type.ISSUE,
            status=Report.Status.NEW,
        )


class TestDashboardAccess(DashboardTestMixin, TestCase):
    """Tests for dashboard access control."""

    def test_elected_can_access_dashboard(self) -> None:
        self.client.login(email="elected@test.com", password="testpass123")
        resp = self.client.get(reverse("dashboard:dashboard"))
        assert resp.status_code == 200

    def test_mayor_can_access_dashboard(self) -> None:
        self.client.login(email="mayor@test.com", password="testpass123")
        resp = self.client.get(reverse("dashboard:dashboard"))
        assert resp.status_code == 200

    def test_citizen_cannot_access_dashboard(self) -> None:
        self.client.login(email="citizen@test.com", password="testpass123")
        resp = self.client.get(reverse("dashboard:dashboard"))
        assert resp.status_code == 403

    def test_anonymous_cannot_access_dashboard(self) -> None:
        resp = self.client.get(reverse("dashboard:dashboard"))
        assert resp.status_code == 302
        assert "/accounts/login/" in resp.url

    def test_unapproved_elected_redirected(self) -> None:
        self.client.login(email="unapproved@test.com", password="testpass123")
        resp = self.client.get(reverse("dashboard:dashboard"))
        assert resp.status_code == 302
        assert "pending" in resp.url


class TestDashboardList(DashboardTestMixin, TestCase):
    """Tests for the dashboard list view."""

    def setUp(self) -> None:
        super().setUp()
        self.report2 = Report.objects.create(
            author=self.citizen,
            title="Question mairie",
            description="Quels sont les horaires ?",
            report_type=Report.Type.QUESTION,
            status=Report.Status.NEW,
        )
        self.report3 = Report.objects.create(
            author=self.citizen,
            title="Idée banc",
            description="Installer un banc au village.",
            report_type=Report.Type.IDEA,
            status=Report.Status.ASSIGNED,
            assigned_to=self.elected,
        )
        self.client.login(email="elected@test.com", password="testpass123")

    def test_dashboard_shows_all_reports(self) -> None:
        resp = self.client.get(reverse("dashboard:dashboard"))
        content = resp.content.decode()
        assert "Route abîmée" in content
        assert "Question mairie" in content
        assert "Idée banc" in content

    def test_filter_by_type(self) -> None:
        resp = self.client.get(
            reverse("dashboard:dashboard"), {"type": "question"},
            HTTP_HX_REQUEST="true",
        )
        content = resp.content.decode()
        assert "Question mairie" in content
        assert "Route abîmée" not in content

    def test_filter_by_status(self) -> None:
        resp = self.client.get(
            reverse("dashboard:dashboard"), {"status": "assigned"},
            HTTP_HX_REQUEST="true",
        )
        content = resp.content.decode()
        assert "Idée banc" in content
        assert "Route abîmée" not in content

    def test_filter_by_assigned(self) -> None:
        resp = self.client.get(
            reverse("dashboard:dashboard"),
            {"assigned": str(self.elected.pk)},
            HTTP_HX_REQUEST="true",
        )
        content = resp.content.decode()
        assert "Idée banc" in content
        assert "Route abîmée" not in content

    def test_status_counters(self) -> None:
        resp = self.client.get(reverse("dashboard:dashboard"))
        assert resp.context["count_new"] == 2
        assert resp.context["count_assigned"] == 1


class TestMyTasks(DashboardTestMixin, TestCase):
    """Tests for the my tasks view."""

    def setUp(self) -> None:
        super().setUp()
        self.report.status = Report.Status.ASSIGNED
        self.report.assigned_to = self.elected
        self.report.save()

        self.report2 = Report.objects.create(
            author=self.citizen,
            title="Autre tâche",
            description="En cours.",
            report_type=Report.Type.QUESTION,
            status=Report.Status.IN_PROGRESS,
            assigned_to=self.elected,
        )
        self.report3 = Report.objects.create(
            author=self.citizen,
            title="Pas ma tâche",
            description="Assignée à un autre.",
            report_type=Report.Type.IDEA,
            status=Report.Status.ASSIGNED,
            assigned_to=self.elected2,
        )
        self.client.login(email="elected@test.com", password="testpass123")

    def test_shows_only_own_tasks(self) -> None:
        resp = self.client.get(reverse("dashboard:my_tasks"))
        content = resp.content.decode()
        assert "Route abîmée" in content
        assert "Autre tâche" in content
        assert "Pas ma tâche" not in content


class TestTakeOwnership(DashboardTestMixin, TestCase):
    """Tests for taking ownership of a report."""

    def test_elected_takes_ownership(self) -> None:
        self.client.login(email="elected@test.com", password="testpass123")
        resp = self.client.post(
            reverse("dashboard:assign", kwargs={"pk": self.report.pk})
        )
        assert resp.status_code == 302
        self.report.refresh_from_db()
        assert self.report.status == Report.Status.ASSIGNED
        assert self.report.assigned_to == self.elected
        assert self.report.assigned_at is not None

    def test_take_ownership_creates_comment(self) -> None:
        self.client.login(email="elected@test.com", password="testpass123")
        self.client.post(
            reverse("dashboard:assign", kwargs={"pk": self.report.pk})
        )
        comment = Comment.objects.filter(report=self.report).first()
        assert comment is not None
        assert comment.is_status_change
        assert comment.old_status == Report.Status.NEW
        assert comment.new_status == Report.Status.ASSIGNED
        assert "Marie Martin" in comment.content

    def test_cannot_take_already_assigned(self) -> None:
        self.report.status = Report.Status.ASSIGNED
        self.report.assigned_to = self.elected2
        self.report.save()
        self.client.login(email="elected@test.com", password="testpass123")
        resp = self.client.post(
            reverse("dashboard:assign", kwargs={"pk": self.report.pk})
        )
        assert resp.status_code == 302
        self.report.refresh_from_db()
        assert self.report.assigned_to == self.elected2


class TestMayorAssign(DashboardTestMixin, TestCase):
    """Tests for mayor assigning a report to an elected official."""

    def test_mayor_assigns_to_elected(self) -> None:
        self.client.login(email="mayor@test.com", password="testpass123")
        resp = self.client.post(
            reverse("dashboard:assign", kwargs={"pk": self.report.pk}),
            {"assign_to": str(self.elected.pk)},
        )
        assert resp.status_code == 302
        self.report.refresh_from_db()
        assert self.report.status == Report.Status.ASSIGNED
        assert self.report.assigned_to == self.elected
        assert self.report.assigned_by == self.mayor

    def test_mayor_assign_creates_comment(self) -> None:
        self.client.login(email="mayor@test.com", password="testpass123")
        self.client.post(
            reverse("dashboard:assign", kwargs={"pk": self.report.pk}),
            {"assign_to": str(self.elected.pk)},
        )
        comment = Comment.objects.filter(report=self.report).first()
        assert comment is not None
        assert "Marie Martin" in comment.content
        assert "Paul Lefevre" in comment.content

    def test_non_mayor_cannot_assign_to_other(self) -> None:
        self.client.login(email="elected@test.com", password="testpass123")
        self.client.post(
            reverse("dashboard:assign", kwargs={"pk": self.report.pk}),
            {"assign_to": str(self.elected2.pk)},
        )
        # Non-mayor with assign_to: falls through to self-assign
        self.report.refresh_from_db()
        assert self.report.assigned_to == self.elected


class TestStatusChange(DashboardTestMixin, TestCase):
    """Tests for status changes."""

    def setUp(self) -> None:
        super().setUp()
        self.report.status = Report.Status.ASSIGNED
        self.report.assigned_to = self.elected
        self.report.save()
        self.client.login(email="elected@test.com", password="testpass123")

    def test_move_to_in_progress(self) -> None:
        resp = self.client.post(
            reverse("dashboard:status", kwargs={"pk": self.report.pk}),
            {"new_status": "in_progress"},
        )
        assert resp.status_code == 302
        self.report.refresh_from_db()
        assert self.report.status == Report.Status.IN_PROGRESS

    def test_in_progress_creates_comment(self) -> None:
        self.client.post(
            reverse("dashboard:status", kwargs={"pk": self.report.pk}),
            {"new_status": "in_progress", "comment": "Je m'en occupe"},
        )
        comment = Comment.objects.filter(
            report=self.report, is_status_change=True
        ).first()
        assert comment is not None
        assert "Je m'en occupe" in comment.content

    def test_resolve_with_text(self) -> None:
        resp = self.client.post(
            reverse("dashboard:status", kwargs={"pk": self.report.pk}),
            {"new_status": "resolved", "resolution_text": "La route a été réparée."},
        )
        assert resp.status_code == 302
        self.report.refresh_from_db()
        assert self.report.status == Report.Status.RESOLVED
        assert self.report.resolution_text == "La route a été réparée."
        assert self.report.resolved_at is not None

    def test_resolve_without_text_fails(self) -> None:
        self.client.post(
            reverse("dashboard:status", kwargs={"pk": self.report.pk}),
            {"new_status": "resolved", "resolution_text": ""},
        )
        self.report.refresh_from_db()
        assert self.report.status == Report.Status.ASSIGNED

    def test_resolve_from_in_progress(self) -> None:
        self.report.status = Report.Status.IN_PROGRESS
        self.report.save()
        self.client.post(
            reverse("dashboard:status", kwargs={"pk": self.report.pk}),
            {"new_status": "resolved", "resolution_text": "Problème résolu."},
        )
        self.report.refresh_from_db()
        assert self.report.status == Report.Status.RESOLVED

    def test_non_assigned_cannot_change_status(self) -> None:
        self.client.login(email="elected2@test.com", password="testpass123")
        self.client.post(
            reverse("dashboard:status", kwargs={"pk": self.report.pk}),
            {"new_status": "in_progress"},
        )
        self.report.refresh_from_db()
        assert self.report.status == Report.Status.ASSIGNED


class TestReassign(DashboardTestMixin, TestCase):
    """Tests for reassigning a report."""

    def setUp(self) -> None:
        super().setUp()
        self.report.status = Report.Status.ASSIGNED
        self.report.assigned_to = self.elected
        self.report.save()

    def test_assigned_elected_reassigns(self) -> None:
        self.client.login(email="elected@test.com", password="testpass123")
        resp = self.client.post(
            reverse("dashboard:reassign", kwargs={"pk": self.report.pk}),
            {"assign_to": str(self.elected2.pk)},
        )
        assert resp.status_code == 302
        self.report.refresh_from_db()
        assert self.report.assigned_to == self.elected2
        assert self.report.assigned_by == self.elected
        assert self.report.status == Report.Status.ASSIGNED

    def test_reassign_creates_comment(self) -> None:
        self.client.login(email="elected@test.com", password="testpass123")
        self.client.post(
            reverse("dashboard:reassign", kwargs={"pk": self.report.pk}),
            {"assign_to": str(self.elected2.pk), "comment": "Passation"},
        )
        comment = Comment.objects.filter(
            report=self.report, is_status_change=True
        ).last()
        assert comment is not None
        assert "Marie Martin" in comment.content
        assert "Pierre Durand" in comment.content
        assert "Passation" in comment.content

    def test_mayor_can_reassign(self) -> None:
        self.client.login(email="mayor@test.com", password="testpass123")
        self.client.post(
            reverse("dashboard:reassign", kwargs={"pk": self.report.pk}),
            {"assign_to": str(self.elected2.pk)},
        )
        self.report.refresh_from_db()
        assert self.report.assigned_to == self.elected2

    def test_other_elected_cannot_reassign(self) -> None:
        self.client.login(email="elected2@test.com", password="testpass123")
        self.client.post(
            reverse("dashboard:reassign", kwargs={"pk": self.report.pk}),
            {"assign_to": str(self.mayor.pk)},
        )
        self.report.refresh_from_db()
        assert self.report.assigned_to == self.elected


class TestComment(DashboardTestMixin, TestCase):
    """Tests for adding comments."""

    def setUp(self) -> None:
        super().setUp()
        self.report.status = Report.Status.ASSIGNED
        self.report.assigned_to = self.elected
        self.report.save()
        self.client.login(email="elected@test.com", password="testpass123")

    def test_add_comment(self) -> None:
        resp = self.client.post(
            reverse("dashboard:comment", kwargs={"pk": self.report.pk}),
            {"content": "Merci pour le signalement."},
        )
        assert resp.status_code == 302
        comment = Comment.objects.filter(
            report=self.report, is_status_change=False
        ).first()
        assert comment is not None
        assert comment.content == "Merci pour le signalement."
        assert comment.author == self.elected

    def test_empty_comment_rejected(self) -> None:
        self.client.post(
            reverse("dashboard:comment", kwargs={"pk": self.report.pk}),
            {"content": ""},
        )
        assert Comment.objects.filter(report=self.report).count() == 0

    def test_comment_on_resolved_rejected(self) -> None:
        self.report.status = Report.Status.RESOLVED
        self.report.save()
        self.client.post(
            reverse("dashboard:comment", kwargs={"pk": self.report.pk}),
            {"content": "Trop tard."},
        )
        assert Comment.objects.filter(report=self.report).count() == 0


class TestNavbarBadge(DashboardTestMixin, TestCase):
    """Tests for the navbar badge counter template tag."""

    def setUp(self) -> None:
        super().setUp()
        Report.objects.create(
            author=self.citizen,
            title="Tâche 1",
            description="Desc",
            report_type=Report.Type.ISSUE,
            status=Report.Status.ASSIGNED,
            assigned_to=self.elected,
        )
        Report.objects.create(
            author=self.citizen,
            title="Tâche 2",
            description="Desc",
            report_type=Report.Type.QUESTION,
            status=Report.Status.IN_PROGRESS,
            assigned_to=self.elected,
        )
        Report.objects.create(
            author=self.citizen,
            title="Résolue",
            description="Desc",
            report_type=Report.Type.IDEA,
            status=Report.Status.RESOLVED,
            assigned_to=self.elected,
        )

    def test_badge_count_correct(self) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.user = self.elected
        template = Template(
            "{% load dashboard_tags %}{% assigned_count as c %}{{ c }}"
        )
        context = RequestContext(request, {})
        result = template.render(context)
        assert result.strip() == "2"

    def test_badge_count_zero_for_citizen(self) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.user = self.citizen
        template = Template(
            "{% load dashboard_tags %}{% assigned_count as c %}{{ c }}"
        )
        context = RequestContext(request, {})
        result = template.render(context)
        assert result.strip() == "0"


class TestDetailView(DashboardTestMixin, TestCase):
    """Tests for the elected detail view."""

    def test_elected_can_view_detail(self) -> None:
        self.client.login(email="elected@test.com", password="testpass123")
        resp = self.client.get(
            reverse("dashboard:detail", kwargs={"pk": self.report.pk})
        )
        assert resp.status_code == 200
        assert "Route abîmée" in resp.content.decode()

    def test_citizen_cannot_view_detail(self) -> None:
        self.client.login(email="citizen@test.com", password="testpass123")
        resp = self.client.get(
            reverse("dashboard:detail", kwargs={"pk": self.report.pk})
        )
        assert resp.status_code == 403

    def test_detail_shows_author_info(self) -> None:
        self.client.login(email="elected@test.com", password="testpass123")
        resp = self.client.get(
            reverse("dashboard:detail", kwargs={"pk": self.report.pk})
        )
        content = resp.content.decode()
        assert "Jean Dupont" in content
        assert "citizen@test.com" in content

    def test_detail_invalid_uuid_returns_404(self) -> None:
        self.client.login(email="elected@test.com", password="testpass123")
        resp = self.client.get(
            reverse("dashboard:detail", kwargs={"pk": uuid.uuid4()})
        )
        assert resp.status_code == 404
