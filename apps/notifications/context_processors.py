"""Context processors for notifications."""


def notifications(request):
    """Injecte le nombre de notifications non lues dans tous les templates."""
    if request.user.is_authenticated:
        from .models import Notification

        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return {"unread_notifications_count": count}
    return {"unread_notifications_count": 0}
