"""URL configuration for the dashboard app."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("maire/", views.mayor_dashboard_view, name="mayor_dashboard"),
    path("my-tasks/", views.my_tasks_view, name="my_tasks"),
    path("<uuid:pk>/", views.detail_view, name="detail"),
    path("<uuid:pk>/assign/", views.assign_view, name="assign"),
    path("<uuid:pk>/status/", views.status_view, name="status"),
    path("<uuid:pk>/reassign/", views.reassign_view, name="reassign"),
    path("<uuid:pk>/comment/", views.comment_view, name="comment"),
    path("<uuid:pk>/toggle-visibility/", views.toggle_visibility_view, name="toggle_visibility"),
    path("admin/cleanup/", views.admin_cleanup_view, name="admin_cleanup"),
    path("admin/cleanup/cancelled/", views.admin_cleanup_cancelled_view, name="admin_cleanup_cancelled"),
    path("admin/cleanup/resolved/", views.admin_cleanup_resolved_view, name="admin_cleanup_resolved"),
    path("admin/cleanup/resolved/count/", views.admin_cleanup_resolved_count_view, name="admin_cleanup_resolved_count"),
    # Administration améliorée
    path("inscriptions/", views.registration_list_view, name="registration_list"),
    path("inscriptions/<int:pk>/approve/", views.registration_approve_view, name="registration_approve"),
    path("inscriptions/<int:pk>/reject/", views.registration_reject_view, name="registration_reject"),
    path("export/", views.export_csv_view, name="export_csv"),
    path("journal/", views.audit_log_view, name="audit_log"),
    path("documentation/", views.documentation_view, name="documentation"),
]
