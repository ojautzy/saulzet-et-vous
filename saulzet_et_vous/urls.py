"""URL configuration for saulzet_et_vous project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.pages import views as pages_views

urlpatterns = [
    # Admin Django
    path("admin/", admin.site.urls),

    # TinyMCE
    path("tinymce/", include("tinymce.urls")),

    # Authentification
    path("comptes/", include("apps.accounts.urls")),

    # Module participatif "Saulzet & Vous" sous /etvous/
    path("etvous/", include("apps.reports.urls")),
    path("etvous/tableau-de-bord/", include("apps.dashboard.urls")),
    path("etvous/notifications/", include("apps.notifications.urls")),

    # Pages CMS spéciales
    path("mentions-legales/", pages_views.legal_notice_view, name="legal_notice"),
    path("contact/", pages_views.contact_view, name="contact"),
    path("documents/", pages_views.document_list_view, name="document_list"),
    path("documents/<str:category>/", pages_views.document_list_view, name="document_list_category"),

    # Page d'accueil
    path("", pages_views.home_view, name="home"),

    # Pages CMS catch-all (DOIT être en dernier)
    path("<slug:parent_slug>/<slug:slug>/", pages_views.page_detail_view, name="page_detail_child"),
    path("<slug:slug>/", pages_views.page_detail_view, name="page_detail"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
