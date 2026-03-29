"""Views for the notifications app."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .forms import NotificationPreferenceForm
from .models import Notification, NotificationPreference


@login_required
def notification_list_view(request: HttpRequest) -> HttpResponse:
    """Liste paginée des notifications."""
    notifications = Notification.objects.filter(recipient=request.user)

    # Filters
    notif_type = request.GET.get("type", "")
    status = request.GET.get("status", "")

    if notif_type:
        notifications = notifications.filter(notification_type=notif_type)
    if status == "unread":
        notifications = notifications.filter(is_read=False)
    elif status == "read":
        notifications = notifications.filter(is_read=True)

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "notifications/notification_list.html", {
        "page_obj": page_obj,
        "current_type": notif_type,
        "current_status": status,
        "notification_types": Notification.Type.choices,
    })


@login_required
@require_POST
def mark_read_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Marquer une notification comme lue et rediriger vers son URL."""
    notification = get_object_or_404(
        Notification, pk=pk, recipient=request.user
    )
    notification.is_read = True
    notification.save(update_fields=["is_read"])

    if notification.url:
        return redirect(notification.url)
    return redirect("notifications:notification_list")


@login_required
@require_POST
def mark_all_read_view(request: HttpRequest) -> HttpResponse:
    """Marquer toutes les notifications comme lues."""
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)

    messages.success(request, _("Toutes les notifications ont été marquées comme lues."))

    if request.headers.get("HX-Request"):
        return HttpResponse("")
    return redirect("notifications:notification_list")


@login_required
def preferences_view(request: HttpRequest) -> HttpResponse:
    """Page de préférences de notification."""
    prefs, _created = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = NotificationPreferenceForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            messages.success(request, _("Vos préférences ont été mises à jour."))
            return redirect("notifications:notification_preferences")
    else:
        form = NotificationPreferenceForm(instance=prefs)

    return render(request, "notifications/preferences.html", {"form": form})
