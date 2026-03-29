"""Signals for the notifications app."""

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AuditLog, NotificationPreference


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Auto-create notification preferences for new users."""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login in audit trail."""
    from .services import _get_client_ip

    AuditLog.objects.create(
        user=user,
        action=AuditLog.Action.LOGIN,
        target_type="user",
        target_id=str(user.pk),
        target_label=str(user)[:200],
        ip_address=_get_client_ip(request),
    )
