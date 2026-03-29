"""Admin configuration for settings_app."""

from django.contrib import admin, messages
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from .models import SiteSettings, Village


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Interface d'administration des paramètres du site."""

    fieldsets = (
        (_("Identité"), {
            "fields": ("site_name", "commune_name", "population"),
        }),
        (_("Coordonnées de la mairie"), {
            "fields": ("address", "phone", "phone_secondary", "opening_hours"),
        }),
        (_("Email — Expédition"), {
            "fields": ("email_from_name", "email_from_address", "email_contact"),
        }),
        (_("Email — Serveur SMTP"), {
            "fields": ("smtp_host", "smtp_port", "smtp_username", "smtp_password", "smtp_use_tls", "smtp_use_ssl"),
            "classes": ("collapse",),
            "description": _("Configuration du serveur d'envoi d'emails. Laisser le champ « Serveur SMTP » vide pour utiliser le mode console (développement)."),
        }),
        (_("Cartographie"), {
            "fields": ("map_center_lat", "map_center_lng", "map_default_zoom", "mairie_lat", "mairie_lng"),
            "classes": ("collapse",),
        }),
        (_("Seuils et paramètres métier"), {
            "fields": ("orphan_days", "cleanup_days", "stats_period_days", "reminder_interval_days"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "test-email/",
                self.admin_site.admin_view(self.test_email_view),
                name="settings_app_sitesettings_test_email",
            ),
        ]
        return custom_urls + urls

    def test_email_view(self, request):
        """Envoie un email de test à l'adresse de contact."""
        config = SiteSettings.load()
        try:
            email = EmailMessage(
                subject="Test d'envoi — Saulzet & Vous",
                body="Cet email confirme que la configuration d'envoi fonctionne.",
                from_email=config.from_email,
                to=[config.email_contact],
            )
            email.send(fail_silently=False)
            messages.success(request, _("Email de test envoyé avec succès à %(email)s.") % {"email": config.email_contact})
        except Exception as e:
            messages.error(request, _("Erreur lors de l'envoi : %(error)s") % {"error": str(e)})

        return HttpResponseRedirect(reverse("admin:settings_app_sitesettings_changelist"))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_test_email_button"] = True
        extra_context["test_email_url"] = reverse("admin:settings_app_sitesettings_test_email")
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
