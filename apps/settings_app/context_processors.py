"""Context processors for settings_app."""


def site_settings(request):
    """Injecte les paramètres du site dans tous les templates."""
    from apps.settings_app.models import SiteSettings, Village

    settings = SiteSettings.load()
    return {
        "site_settings": settings,
        "villages": Village.objects.filter(is_active=True),
    }
