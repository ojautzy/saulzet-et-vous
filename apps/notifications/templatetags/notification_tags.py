"""Template tags for notifications."""

from django import template

from apps.notifications.models import Notification

register = template.Library()


@register.simple_tag(takes_context=True)
def recent_notifications(context):
    """Return the 10 most recent notifications for the current user."""
    request = context.get("request")
    if request and request.user.is_authenticated:
        return Notification.objects.filter(
            recipient=request.user
        ).order_by("-created_at")[:10]
    return Notification.objects.none()
