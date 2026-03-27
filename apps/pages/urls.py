"""URL configuration for pages app."""

from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("contact/", views.contact_view, name="contact"),
    path("documents/", views.document_list_view, name="document_list"),
    path("documents/<str:category>/", views.document_list_view, name="document_list_category"),
]
