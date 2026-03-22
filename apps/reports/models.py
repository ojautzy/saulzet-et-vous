"""Models for the reports (sollicitations) app."""

import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _
from PIL import Image


class Report(models.Model):
    """A citizen report (sollicitation) to elected officials."""

    class Type(models.TextChoices):
        QUESTION = "question", _("Question")
        IDEA = "idea", _("Idee / Suggestion")
        ISSUE = "issue", _("Signalement")

    class Status(models.TextChoices):
        NEW = "new", _("Nouveau")
        ASSIGNED = "assigned", _("Pris en charge")
        IN_PROGRESS = "in_progress", _("En cours")
        RESOLVED = "resolved", _("Resolu")
        CANCELLED = "cancelled", _("Annule")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_("titre"), max_length=200)
    description = models.TextField(_("description"))
    report_type = models.CharField(
        _("type"),
        max_length=10,
        choices=Type.choices,
        default=Type.ISSUE,
    )
    status = models.CharField(
        _("statut"),
        max_length=15,
        choices=Status.choices,
        default=Status.NEW,
    )
    latitude = models.FloatField(_("latitude"), null=True, blank=True)
    longitude = models.FloatField(_("longitude"), null=True, blank=True)
    location_text = models.CharField(
        _("description du lieu"), max_length=255, blank=True
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name=_("auteur"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_reports",
        verbose_name=_("assigne a"),
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments_made",
        verbose_name=_("assigne par"),
    )
    resolution_text = models.TextField(_("texte de resolution"), blank=True)
    created_at = models.DateTimeField(_("date de creation"), auto_now_add=True)
    updated_at = models.DateTimeField(_("date de modification"), auto_now=True)
    assigned_at = models.DateTimeField(_("date d'assignation"), null=True, blank=True)
    resolved_at = models.DateTimeField(_("date de resolution"), null=True, blank=True)

    class Meta:
        verbose_name = _("sollicitation")
        verbose_name_plural = _("sollicitations")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_cancellable(self) -> bool:
        """Return True if the report can be cancelled."""
        return self.status == self.Status.NEW

    @property
    def type_label(self) -> str:
        """Return the human-readable type label."""
        return self.get_report_type_display()

    @property
    def status_label(self) -> str:
        """Return the human-readable status label."""
        return self.get_status_display()


def photo_upload_path(instance: "Photo", filename: str) -> str:
    """Generate upload path for report photos."""
    return f"reports/photos/{instance.report.created_at:%Y/%m}/{instance.id}_{filename}"


def thumbnail_upload_path(instance: "Photo", filename: str) -> str:
    """Generate upload path for photo thumbnails."""
    return f"reports/thumbnails/{instance.report.created_at:%Y/%m}/{instance.id}_{filename}"


class Photo(models.Model):
    """A photo attached to a report."""

    MAX_WIDTH = 1920
    JPEG_QUALITY = 85
    THUMB_SIZE = (400, 300)
    THUMB_QUALITY = 75

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name=_("sollicitation"),
    )
    image = models.ImageField(_("image"), upload_to="reports/photos/%Y/%m/")
    thumbnail = models.ImageField(
        _("miniature"), upload_to="reports/thumbnails/%Y/%m/", blank=True
    )
    original_filename = models.CharField(_("nom du fichier"), max_length=255)
    uploaded_at = models.DateTimeField(_("date d'upload"), auto_now_add=True)
    order = models.PositiveIntegerField(_("ordre"), default=0)

    class Meta:
        verbose_name = _("photo")
        verbose_name_plural = _("photos")
        ordering = ["order", "uploaded_at"]

    def __str__(self) -> str:
        return self.original_filename

    def process_image(self) -> None:
        """Compress, resize the image, and generate a thumbnail."""
        if not self.image:
            return

        img = Image.open(self.image)

        # Convert HEIC or other modes to RGB
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if wider than MAX_WIDTH
        if img.width > self.MAX_WIDTH:
            ratio = self.MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((self.MAX_WIDTH, new_height), Image.LANCZOS)

        # Save compressed image
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=self.JPEG_QUALITY, optimize=True)
        buffer.seek(0)
        filename = self.original_filename.rsplit(".", 1)[0] + ".jpg"
        self.image.save(filename, ContentFile(buffer.read()), save=False)

        # Generate thumbnail
        buffer.seek(0)
        thumb = Image.open(BytesIO(buffer.getvalue()))
        thumb.thumbnail(self.THUMB_SIZE, Image.LANCZOS)
        thumb_buffer = BytesIO()
        thumb.save(
            thumb_buffer, format="JPEG", quality=self.THUMB_QUALITY, optimize=True
        )
        thumb_buffer.seek(0)
        thumb_filename = f"thumb_{filename}"
        self.thumbnail.save(
            thumb_filename, ContentFile(thumb_buffer.read()), save=False
        )


class Comment(models.Model):
    """A comment or status change on a report."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("sollicitation"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("auteur"),
    )
    content = models.TextField(_("contenu"))
    is_status_change = models.BooleanField(_("changement de statut"), default=False)
    old_status = models.CharField(
        _("ancien statut"), max_length=15, null=True, blank=True
    )
    new_status = models.CharField(
        _("nouveau statut"), max_length=15, null=True, blank=True
    )
    created_at = models.DateTimeField(_("date de creation"), auto_now_add=True)

    class Meta:
        verbose_name = _("commentaire")
        verbose_name_plural = _("commentaires")
        ordering = ["created_at"]

    def __str__(self) -> str:
        if self.is_status_change:
            return f"Changement de statut: {self.old_status} -> {self.new_status}"
        return f"Commentaire de {self.author}"
