"""Models for site-wide settings and village data."""

from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSettings(models.Model):
    """Paramètres globaux du site, éditables dans l'admin Django.

    Singleton : une seule instance autorisée. Accès via SiteSettings.load().
    """

    # --- Identité ---
    site_name = models.CharField(
        _("Nom du site"), max_length=100, default="Saulzet & Vous",
    )
    commune_name = models.CharField(
        _("Nom de la commune"), max_length=100, default="Saulzet-le-Froid",
    )
    population = models.CharField(
        _("Population"), max_length=50, default="284 habitants",
        help_text=_("Affiché sur la page d'accueil et la page commune."),
    )

    # --- Coordonnées mairie ---
    address = models.CharField(
        _("Adresse"), max_length=200, default="Le Bourg, 63710 Saulzet-le-Froid",
    )
    phone = models.CharField(
        _("Téléphone principal"), max_length=20, default="04 73 22 81 65",
    )
    phone_secondary = models.CharField(
        _("Téléphone secondaire"), max_length=20, blank=True, default="",
        help_text=_("Optionnel. Affiché sur la carte et la page contact."),
    )
    opening_hours = models.TextField(
        _("Horaires d'ouverture"),
        default="Lundi, mardi, jeudi et vendredi\n8h30 — 12h00",
        help_text=_("Une ligne par information. Affiché sur l'accueil et la page contact."),
    )

    # --- Email — Expédition ---
    email_from_name = models.CharField(
        _("Nom de l'expéditeur"), max_length=100, default="Saulzet & Vous",
        help_text=_("Nom affiché dans le champ « De » des emails envoyés."),
    )
    email_from_address = models.EmailField(
        _("Adresse email d'expédition"), default="noreply@saulzet-le-froid.com",
        help_text=_("Adresse email utilisée comme expéditeur pour tous les emails du site."),
    )
    email_contact = models.EmailField(
        _("Email de contact (mairie)"), default="mairie@saulzet-le-froid.com",
        help_text=_("Adresse où arrivent les messages du formulaire de contact."),
    )

    # --- Email — Serveur SMTP ---
    smtp_host = models.CharField(
        _("Serveur SMTP"), max_length=200, blank=True, default="",
        help_text=_("Ex : smtp.brevo.com, smtp.gmail.com. Laisser vide pour utiliser la console (dev)."),
    )
    smtp_port = models.PositiveIntegerField(
        _("Port SMTP"), default=587,
        help_text=_("587 pour TLS (recommandé), 465 pour SSL, 25 pour non chiffré."),
    )
    smtp_username = models.CharField(
        _("Identifiant SMTP"), max_length=200, blank=True, default="",
    )
    smtp_password = models.CharField(
        _("Mot de passe SMTP"), max_length=200, blank=True, default="",
        help_text=_("Stocké en clair en base. Utiliser une clé API plutôt qu'un mot de passe personnel."),
    )
    smtp_use_tls = models.BooleanField(
        _("Utiliser TLS"), default=True,
        help_text=_("Activer pour le port 587 (recommandé). Désactiver pour le port 465 (SSL)."),
    )
    smtp_use_ssl = models.BooleanField(
        _("Utiliser SSL"), default=False,
        help_text=_("Activer uniquement pour le port 465."),
    )

    # --- Cartographie ---
    map_center_lat = models.FloatField(
        _("Latitude centre carte"), default=45.6415,
    )
    map_center_lng = models.FloatField(
        _("Longitude centre carte"), default=2.9100,
    )
    map_default_zoom = models.PositiveSmallIntegerField(
        _("Zoom par défaut"), default=13,
    )
    mairie_lat = models.FloatField(
        _("Latitude mairie"), default=45.6415,
    )
    mairie_lng = models.FloatField(
        _("Longitude mairie"), default=2.9178,
    )

    # --- Seuils métier ---
    orphan_days = models.PositiveIntegerField(
        _("Seuil sollicitations orphelines (jours)"), default=7,
        help_text=_("Nombre de jours avant qu'une sollicitation non affectée soit signalée en relance."),
    )
    cleanup_days = models.PositiveIntegerField(
        _("Seuil nettoyage (jours)"), default=30,
        help_text=_("Nombre de jours par défaut pour la suppression des sollicitations résolues/annulées."),
    )
    stats_period_days = models.PositiveIntegerField(
        _("Période statistiques (jours)"), default=180,
        help_text=_("Nombre de jours affichés dans les graphiques du tableau de bord maire."),
    )
    reminder_interval_days = models.PositiveIntegerField(
        _("Intervalle entre relances (jours)"), default=7,
        help_text=_("Nombre de jours minimum entre deux relances pour la même sollicitation."),
    )

    class Meta:
        verbose_name = _("Paramètres du site")
        verbose_name_plural = _("Paramètres du site")

    def __str__(self):
        return "Paramètres du site"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete("site_settings")

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        """Charge les paramètres depuis le cache ou la base."""
        settings = cache.get("site_settings")
        if settings is None:
            settings, _ = cls.objects.get_or_create(pk=1)
            cache.set("site_settings", settings, 300)
        return settings

    @property
    def from_email(self):
        """Retourne l'adresse formatée pour Django : 'Nom <adresse>'."""
        return f"{self.email_from_name} <{self.email_from_address}>"


class Village(models.Model):
    """Village de la commune, avec ses coordonnées GPS pour la carte."""

    name = models.CharField(_("Nom"), max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    latitude = models.FloatField(_("Latitude"))
    longitude = models.FloatField(_("Longitude"))
    order = models.PositiveSmallIntegerField(_("Ordre d'affichage"), default=0)
    is_active = models.BooleanField(_("Actif"), default=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = _("Village")
        verbose_name_plural = _("Villages")

    def __str__(self):
        return self.name
