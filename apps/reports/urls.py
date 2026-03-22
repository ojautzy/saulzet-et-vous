"""URL configuration for the reports app."""

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_list_view, name="list"),
    path("create/", views.report_create_view, name="create"),
    path("<uuid:pk>/", views.report_detail_view, name="detail"),
    path("<uuid:pk>/cancel/", views.report_cancel_view, name="cancel"),
]
