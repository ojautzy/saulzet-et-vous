"""Tests for the reports app."""

import io
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from .models import Comment, Photo, Report

User = get_user_model()


def create_test_image(
    width: int = 100, height: int = 100, fmt: str = "JPEG"
) -> SimpleUploadedFile:
    """Create a test image file."""
    img = Image.new("RGB", (width, height), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    buffer.seek(0)
    ext = "jpg" if fmt == "JPEG" else fmt.lower()
    return SimpleUploadedFile(
        name=f"test.{ext}",
        content=buffer.read(),
        content_type=f"image/{ext}",
    )


class ReportTestMixin:
    """Common setup for report tests."""

    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            email="citizen@test.com",
            password="testpass123",
            first_name="Jean",
            last_name="Dupont",
            is_approved=True,
        )
        self.other_user = User.objects.create_user(
            email="other@test.com",
            password="testpass123",
            first_name="Marie",
            last_name="Martin",
            is_approved=True,
        )
        self.unapproved_user = User.objects.create_user(
            email="pending@test.com",
            password="testpass123",
            first_name="Pierre",
            last_name="Durand",
            is_approved=False,
        )
        self.client.login(email="citizen@test.com", password="testpass123")


class TestReportCreation(ReportTestMixin, TestCase):
    """Tests for creating reports."""

    def test_create_issue(self) -> None:
        resp = self.client.post(
            reverse("reports:create"),
            {"report_type": "issue", "title": "Route abimee", "description": "La route est pleine de trous."},
        )
        assert resp.status_code == 302
        report = Report.objects.get(title="Route abimee")
        assert report.report_type == Report.Type.ISSUE
        assert report.status == Report.Status.NEW
        assert report.author == self.user

    def test_create_question(self) -> None:
        resp = self.client.post(
            reverse("reports:create"),
            {"report_type": "question", "title": "Horaires mairie", "description": "Quels sont les horaires ?"},
        )
        assert resp.status_code == 302
        assert Report.objects.filter(report_type="question").count() == 1

    def test_create_idea(self) -> None:
        resp = self.client.post(
            reverse("reports:create"),
            {"report_type": "idea", "title": "Banc public", "description": "Installer un banc."},
        )
        assert resp.status_code == 302
        assert Report.objects.filter(report_type="idea").count() == 1

    def test_create_with_location(self) -> None:
        resp = self.client.post(
            reverse("reports:create"),
            {
                "report_type": "issue",
                "title": "Nid de poule",
                "description": "Devant la mairie",
                "latitude": "45.6565",
                "longitude": "2.9162",
                "location_text": "Devant la mairie",
            },
        )
        assert resp.status_code == 302
        report = Report.objects.get(title="Nid de poule")
        assert report.latitude == pytest.approx(45.6565)
        assert report.longitude == pytest.approx(2.9162)
        assert report.location_text == "Devant la mairie"

    def test_create_requires_login(self) -> None:
        self.client.logout()
        resp = self.client.get(reverse("reports:create"))
        assert resp.status_code == 302
        assert "/accounts/login/" in resp.url

    def test_unapproved_user_redirected(self) -> None:
        self.client.login(email="pending@test.com", password="testpass123")
        resp = self.client.get(reverse("reports:create"))
        assert resp.status_code == 302
        assert "pending" in resp.url


class TestPhotoUpload(ReportTestMixin, TestCase):
    """Tests for photo uploads."""

    def test_upload_single_photo(self) -> None:
        img = create_test_image()
        resp = self.client.post(
            reverse("reports:create"),
            {
                "report_type": "issue",
                "title": "Photo test",
                "description": "Test avec photo",
                "photos": [img],
            },
        )
        assert resp.status_code == 302
        report = Report.objects.get(title="Photo test")
        assert report.photos.count() == 1

    def test_upload_max_photos(self) -> None:
        images = [create_test_image() for _ in range(5)]
        resp = self.client.post(
            reverse("reports:create"),
            {
                "report_type": "issue",
                "title": "Multi photos",
                "description": "Test 5 photos",
                "photos": images,
            },
        )
        assert resp.status_code == 302
        report = Report.objects.get(title="Multi photos")
        assert report.photos.count() == 5

    def test_upload_too_many_photos(self) -> None:
        images = [create_test_image() for _ in range(6)]
        resp = self.client.post(
            reverse("reports:create"),
            {
                "report_type": "issue",
                "title": "Trop de photos",
                "description": "Test 6 photos",
                "photos": images,
            },
        )
        # Should re-render form with error
        assert resp.status_code == 200
        assert Report.objects.filter(title="Trop de photos").count() == 0

    def test_upload_invalid_format(self) -> None:
        bad_file = SimpleUploadedFile(
            name="test.txt",
            content=b"not an image",
            content_type="text/plain",
        )
        resp = self.client.post(
            reverse("reports:create"),
            {
                "report_type": "issue",
                "title": "Bad file",
                "description": "Test mauvais fichier",
                "photos": [bad_file],
            },
        )
        assert resp.status_code == 200
        assert Report.objects.filter(title="Bad file").count() == 0

    def test_upload_png(self) -> None:
        img = create_test_image(fmt="PNG")
        resp = self.client.post(
            reverse("reports:create"),
            {
                "report_type": "issue",
                "title": "PNG test",
                "description": "Test PNG",
                "photos": [img],
            },
        )
        assert resp.status_code == 302
        assert Report.objects.get(title="PNG test").photos.count() == 1


class TestPhotoProcessing(ReportTestMixin, TestCase):
    """Tests for image compression and thumbnail generation."""

    def test_large_image_resized(self) -> None:
        img = create_test_image(width=3000, height=2000)
        self.client.post(
            reverse("reports:create"),
            {
                "report_type": "issue",
                "title": "Large image",
                "description": "Test resize",
                "photos": [img],
            },
        )
        photo = Photo.objects.first()
        assert photo is not None
        pil_img = Image.open(photo.image)
        assert pil_img.width <= Photo.MAX_WIDTH

    def test_thumbnail_generated(self) -> None:
        img = create_test_image(width=800, height=600)
        self.client.post(
            reverse("reports:create"),
            {
                "report_type": "issue",
                "title": "Thumb test",
                "description": "Test thumbnail",
                "photos": [img],
            },
        )
        photo = Photo.objects.first()
        assert photo is not None
        assert photo.thumbnail
        thumb = Image.open(photo.thumbnail)
        assert thumb.width <= Photo.THUMB_SIZE[0]
        assert thumb.height <= Photo.THUMB_SIZE[1]


class TestReportList(ReportTestMixin, TestCase):
    """Tests for the report list view."""

    def setUp(self) -> None:
        super().setUp()
        self.report1 = Report.objects.create(
            author=self.user,
            title="Mon signalement",
            description="Description 1",
            report_type=Report.Type.ISSUE,
        )
        self.report2 = Report.objects.create(
            author=self.user,
            title="Ma question",
            description="Description 2",
            report_type=Report.Type.QUESTION,
        )
        self.other_report = Report.objects.create(
            author=self.other_user,
            title="Autre signalement",
            description="Pas le mien",
            report_type=Report.Type.ISSUE,
        )

    def test_list_shows_own_reports(self) -> None:
        resp = self.client.get(reverse("reports:list"))
        assert resp.status_code == 200
        assert "Mon signalement" in resp.content.decode()
        assert "Ma question" in resp.content.decode()

    def test_list_hides_others_reports(self) -> None:
        resp = self.client.get(reverse("reports:list"))
        assert "Autre signalement" not in resp.content.decode()

    def test_filter_by_type(self) -> None:
        resp = self.client.get(reverse("reports:list"), {"type": "question"})
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Ma question" in content
        assert "Mon signalement" not in content

    def test_filter_by_status(self) -> None:
        self.report1.status = Report.Status.RESOLVED
        self.report1.save()
        resp = self.client.get(reverse("reports:list"), {"status": "resolved"})
        content = resp.content.decode()
        assert "Mon signalement" in content
        assert "Ma question" not in content

    def test_empty_list_message(self) -> None:
        Report.objects.filter(author=self.user).delete()
        resp = self.client.get(reverse("reports:list"))
        assert "pas encore" in resp.content.decode()


class TestReportDetail(ReportTestMixin, TestCase):
    """Tests for the report detail view."""

    def setUp(self) -> None:
        super().setUp()
        self.report = Report.objects.create(
            author=self.user,
            title="Detail test",
            description="Description detail",
            report_type=Report.Type.ISSUE,
        )

    def test_detail_accessible_by_author(self) -> None:
        resp = self.client.get(reverse("reports:detail", kwargs={"pk": self.report.pk}))
        assert resp.status_code == 200
        assert "Detail test" in resp.content.decode()

    def test_detail_not_accessible_by_other(self) -> None:
        self.client.login(email="other@test.com", password="testpass123")
        resp = self.client.get(reverse("reports:detail", kwargs={"pk": self.report.pk}))
        assert resp.status_code == 404

    def test_detail_not_found_for_invalid_uuid(self) -> None:
        resp = self.client.get(reverse("reports:detail", kwargs={"pk": uuid.uuid4()}))
        assert resp.status_code == 404


class TestReportCancel(ReportTestMixin, TestCase):
    """Tests for cancelling reports."""

    def setUp(self) -> None:
        super().setUp()
        self.report = Report.objects.create(
            author=self.user,
            title="A annuler",
            description="Test annulation",
            report_type=Report.Type.ISSUE,
            status=Report.Status.NEW,
        )

    def test_cancel_new_report(self) -> None:
        resp = self.client.post(
            reverse("reports:cancel", kwargs={"pk": self.report.pk})
        )
        assert resp.status_code == 302
        self.report.refresh_from_db()
        assert self.report.status == Report.Status.CANCELLED

    def test_cancel_creates_comment(self) -> None:
        self.client.post(
            reverse("reports:cancel", kwargs={"pk": self.report.pk})
        )
        comment = Comment.objects.filter(report=self.report).first()
        assert comment is not None
        assert comment.is_status_change
        assert comment.old_status == Report.Status.NEW
        assert comment.new_status == Report.Status.CANCELLED

    def test_cannot_cancel_assigned_report(self) -> None:
        self.report.status = Report.Status.ASSIGNED
        self.report.save()
        resp = self.client.post(
            reverse("reports:cancel", kwargs={"pk": self.report.pk})
        )
        assert resp.status_code == 302
        self.report.refresh_from_db()
        assert self.report.status == Report.Status.ASSIGNED

    def test_cannot_cancel_others_report(self) -> None:
        self.client.login(email="other@test.com", password="testpass123")
        resp = self.client.post(
            reverse("reports:cancel", kwargs={"pk": self.report.pk})
        )
        assert resp.status_code == 404
        self.report.refresh_from_db()
        assert self.report.status == Report.Status.NEW

    def test_cancel_get_not_allowed(self) -> None:
        resp = self.client.get(
            reverse("reports:cancel", kwargs={"pk": self.report.pk})
        )
        assert resp.status_code == 405

    def test_cancelled_report_visible_in_list(self) -> None:
        self.report.status = Report.Status.CANCELLED
        self.report.save()
        resp = self.client.get(reverse("reports:list"))
        assert "A annuler" in resp.content.decode()


class TestAccessControl(ReportTestMixin, TestCase):
    """Tests for authentication and approval checks."""

    def test_anonymous_cannot_access_list(self) -> None:
        self.client.logout()
        resp = self.client.get(reverse("reports:list"))
        assert resp.status_code == 302
        assert "/accounts/login/" in resp.url

    def test_anonymous_cannot_access_create(self) -> None:
        self.client.logout()
        resp = self.client.get(reverse("reports:create"))
        assert resp.status_code == 302

    def test_unapproved_redirected_from_list(self) -> None:
        self.client.login(email="pending@test.com", password="testpass123")
        resp = self.client.get(reverse("reports:list"))
        assert resp.status_code == 302
        assert "pending" in resp.url

    def test_unapproved_redirected_from_create(self) -> None:
        self.client.login(email="pending@test.com", password="testpass123")
        resp = self.client.get(reverse("reports:create"))
        assert resp.status_code == 302
        assert "pending" in resp.url
