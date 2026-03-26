"""URL configuration for the reports app."""

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_list_view, name="list"),
    path("create/", views.report_create_view, name="create"),
    path("<uuid:pk>/", views.report_detail_view, name="detail"),
    path("<uuid:pk>/cancel/", views.report_cancel_view, name="cancel"),
    path("<uuid:pk>/edit/", views.report_edit_view, name="edit"),
    path("<uuid:pk>/photos/<uuid:photo_pk>/delete/", views.report_delete_photo_view, name="delete_photo"),
    path("public/", views.public_reports_view, name="public"),
]
