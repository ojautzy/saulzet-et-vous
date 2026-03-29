"""Admin configuration for accounts app."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

User = get_user_model()


@admin.action(description=_("Approuver les comptes sélectionnés"))
def approve_users(modeladmin, request, queryset) -> None:
    """Approve selected user accounts and notify them by email."""
    from apps.settings_app.models import SiteSettings

    config = SiteSettings.load()
    updated = queryset.filter(is_approved=False)
    for user in updated:
        user.is_approved = True
        user.save(update_fields=["is_approved"])
        send_mail(
            subject=_("Votre compte a été validé — Saulzet & Vous"),
            message=render_to_string(
                "accounts/emails/account_approved.txt",
                {"user": user},
            ),
            from_email=config.from_email,
            recipient_list=[user.email],
            fail_silently=True,
        )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the User model."""

    list_display = ("email", "last_name", "first_name", "role", "is_approved", "created_at")
    list_filter = ("role", "is_approved", "is_staff")
    search_fields = ("email", "first_name", "last_name", "address")
    ordering = ("-created_at",)
    actions = [approve_users]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Informations personnelles"), {"fields": ("first_name", "last_name", "phone", "address", "village")}),
        (_("Rôle et approbation"), {"fields": ("role", "is_approved")}),
        (_("Équipe municipale"), {
            "fields": ("photo", "function_title", "function_order"),
            "classes": ("collapse",),
        }),
        (
            _("Permissions"),
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
                "classes": ("collapse",),
            },
        ),
        (_("Dates"), {"fields": ("last_login", "created_at")}),
    )
    readonly_fields = ("created_at",)

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
            },
        ),
    )
