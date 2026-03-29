"""Models for the notifications app."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    class Type(models.TextChoices):
        STATUS_CHANGE = "status_change", _("Changement de statut")
        NEW_COMMENT = "new_comment", _("Nouveau commentaire")
        ASSIGNMENT = "assignment", _("Affectation")
        NEW_REPORT = "new_report", _("Nouvelle sollicitation")
        NEW_REGISTRATION = "new_registration", _("Nouvelle inscription")
        CONTACT_FORM = "contact_form", _("Formulaire de contact")
        REMINDER = "reminder", _("Relance")

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    report = models.ForeignKey(
        "reports.Report",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} → {self.recipient.email}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    email_status_change = models.BooleanField(default=True)
    email_new_comment = models.BooleanField(default=True)
    email_assignment = models.BooleanField(default=True)
    email_new_report = models.BooleanField(default=True)
    email_reminder = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Préférences de notification")
        verbose_name_plural = _("Préférences de notification")

    def __str__(self):
        return f"Préférences de {self.user.email}"


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", _("Création")
        UPDATE = "update", _("Modification")
        DELETE = "delete", _("Suppression")
        STATUS_CHANGE = "status_change", _("Changement de statut")
        ASSIGN = "assign", _("Affectation")
        APPROVE = "approve", _("Approbation")
        LOGIN = "login", _("Connexion")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    target_type = models.CharField(max_length=50)
    target_id = models.CharField(max_length=50, blank=True, default="")
    target_label = models.CharField(max_length=200, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self):
        return f"{self.get_action_display()} — {self.target_type} — {self.created_at}"
