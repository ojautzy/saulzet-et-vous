"""URL configuration for saulzet_et_vous project."""

from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import home_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("", home_view, name="home"),
]
