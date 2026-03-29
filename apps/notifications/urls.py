"""URL configuration for the notifications app."""

from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list_view, name="notification_list"),
    path("<int:pk>/read/", views.mark_read_view, name="notification_mark_read"),
    path("mark-all-read/", views.mark_all_read_view, name="notification_mark_all_read"),
    path("preferences/", views.preferences_view, name="notification_preferences"),
]
