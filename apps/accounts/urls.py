"""URL configuration for accounts app."""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("login/password/", views.PasswordLoginView.as_view(), name="login_password"),
    path("magic/request/", views.magic_link_request_view, name="magic_link_request"),
    path("magic/<str:token>/", views.magic_link_verify_view, name="magic_link_verify"),
    path("register/", views.register_view, name="register"),
    path("pending/", views.pending_view, name="pending"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("delete/", views.delete_account_view, name="delete_account"),
]
