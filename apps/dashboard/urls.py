"""URL configuration for the dashboard app."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("my-tasks/", views.my_tasks_view, name="my_tasks"),
    path("<uuid:pk>/", views.detail_view, name="detail"),
    path("<uuid:pk>/assign/", views.assign_view, name="assign"),
    path("<uuid:pk>/status/", views.status_view, name="status"),
    path("<uuid:pk>/reassign/", views.reassign_view, name="reassign"),
    path("<uuid:pk>/comment/", views.comment_view, name="comment"),
]
