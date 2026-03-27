"""Models for the CMS pages app."""

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField


class Page(models.Model):
    class Template(models.TextChoices):
        DEFAULT = "default", _("Standard")
        FULL_WIDTH = "full_width", _("Pleine largeur")
        CONTACT = "contact", _("Page de contact")
        DOCUMENTS = "documents", _("Liste de documents")
        EQUIPE = "equipe", _("Équipe municipale")
        HABITANTS = "habitants", _("Habitants")
        ACCES = "acces", _("Accès et plan")

    title = models.CharField(_("titre"), max_length=200)
    slug = models.SlugField(
        _("slug"),
        max_length=200,
        unique=True,
        help_text=_("Identifiant dans l'URL. Généré automatiquement depuis le titre."),
    )
    content = HTMLField(_("contenu"), blank=True)
    excerpt = models.TextField(
        _("résumé"),
        blank=True,
        help_text=_("Court résumé affiché dans les listes et les accès rapides."),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("page parente"),
        help_text=_("Laisser vide pour une page de premier niveau."),
    )
    menu_order = models.PositiveIntegerField(
        _("ordre dans le menu"),
        default=0,
        help_text=_("Les pages sont triées par ce nombre (croissant)."),
    )
    is_published = models.BooleanField(_("publiée"), default=True)
    show_in_menu = models.BooleanField(_("afficher dans le menu"), default=True)
    template = models.CharField(
        _("gabarit"),
        max_length=20,
        choices=Template.choices,
        default=Template.DEFAULT,
    )
    meta_description = models.CharField(
        _("description SEO"),
        max_length=160,
        blank=True,
    )
    featured_image = models.ImageField(
        _("image d'en-tête"),
        upload_to="pages/images/",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(_("créée le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modifiée le"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pages_created",
        verbose_name=_("créée par"),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pages_updated",
        verbose_name=_("modifiée par"),
    )

    class Meta:
        verbose_name = _("page")
        verbose_name_plural = _("pages")
        ordering = ["menu_order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.parent:
            return f"/{self.parent.slug}/{self.slug}/"
        return f"/{self.slug}/"

    @property
    def breadcrumb(self):
        """Retourne la liste des ancêtres pour le fil d'Ariane."""
        crumbs = []
        page = self
        while page:
            crumbs.insert(0, page)
            page = page.parent
        return crumbs


class Document(models.Model):
    class Category(models.TextChoices):
        PV = "pv", _("Procès-verbal de conseil")
        BULLETIN = "bulletin", _("Bulletin municipal")
        PLU = "plu", _("Document PLU")
        ARRETE = "arrete", _("Arrêté")
        OTHER = "other", _("Autre")

    title = models.CharField(_("titre"), max_length=200)
    file = models.FileField(_("fichier"), upload_to="documents/")
    category = models.CharField(
        _("catégorie"),
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    date = models.DateField(
        _("date du document"),
        null=True,
        blank=True,
        help_text=_("Date du document (ex: date du conseil municipal)."),
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("page associée"),
    )
    uploaded_at = models.DateTimeField(_("uploadé le"), auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("uploadé par"),
    )

    class Meta:
        verbose_name = _("document")
        verbose_name_plural = _("documents")
        ordering = ["-date", "-uploaded_at"]

    def __str__(self):
        return self.title

    @property
    def file_extension(self):
        return self.file.name.rsplit(".", 1)[-1].lower() if self.file else ""

    @property
    def file_size_display(self):
        """Retourne la taille du fichier en format lisible."""
        if not self.file:
            return ""
        size = self.file.size
        for unit in ["o", "Ko", "Mo", "Go"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} To"
