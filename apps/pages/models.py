"""Models for the CMS pages app."""

from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from PIL import Image
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
        GALERIE = "galerie", _("Galerie photos")

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


class DocumentCategory(models.Model):
    """Dynamic, admin-editable document category."""

    name = models.CharField(_("nom"), max_length=100)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)
    order = models.PositiveIntegerField(_("ordre"), default=0)

    class Meta:
        verbose_name = _("catégorie de document")
        verbose_name_plural = _("catégories de documents")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Document(models.Model):
    title = models.CharField(_("titre"), max_length=200)
    file = models.FileField(_("fichier"), upload_to="documents/")
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("catégorie"),
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


class GalleryPhoto(models.Model):
    """A photo in the commune gallery."""

    MAX_WIDTH = 1920
    JPEG_QUALITY = 85
    THUMB_SIZE = (400, 300)
    THUMB_QUALITY = 75

    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="gallery_photos",
        verbose_name=_("page"),
    )
    image = models.ImageField(_("image"), upload_to="gallery/photos/%Y/%m/")
    thumbnail = models.ImageField(
        _("miniature"), upload_to="gallery/thumbnails/%Y/%m/", blank=True
    )
    title = models.CharField(_("légende"), max_length=200, blank=True)
    credit = models.CharField(
        _("crédits photo"),
        max_length=200,
        blank=True,
        help_text=_("Nom du photographe ou source."),
    )
    order = models.PositiveIntegerField(_("ordre"), default=0)
    is_published = models.BooleanField(_("publiée"), default=True)
    uploaded_at = models.DateTimeField(_("ajoutée le"), auto_now_add=True)

    class Meta:
        verbose_name = _("photo de galerie")
        verbose_name_plural = _("photos de galerie")
        ordering = ["order", "-uploaded_at"]

    def __str__(self):
        return self.title or f"Photo #{self.pk}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new and self.image:
            self.process_image()
        super().save(*args, **kwargs)

    def process_image(self):
        """Compress, resize the image, and generate a thumbnail."""
        if not self.image:
            return

        img = Image.open(self.image)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if wider than MAX_WIDTH
        if img.width > self.MAX_WIDTH:
            ratio = self.MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((self.MAX_WIDTH, new_height), Image.LANCZOS)

        # Save compressed image
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=self.JPEG_QUALITY, optimize=True)
        buffer.seek(0)
        original_name = self.image.name.rsplit("/", 1)[-1]
        filename = original_name.rsplit(".", 1)[0] + ".jpg"
        self.image.save(filename, ContentFile(buffer.read()), save=False)

        # Generate thumbnail
        buffer.seek(0)
        thumb = Image.open(BytesIO(buffer.getvalue()))
        thumb.thumbnail(self.THUMB_SIZE, Image.LANCZOS)
        thumb_buffer = BytesIO()
        thumb.save(
            thumb_buffer, format="JPEG", quality=self.THUMB_QUALITY, optimize=True
        )
        thumb_buffer.seek(0)
        self.thumbnail.save(
            f"thumb_{filename}", ContentFile(thumb_buffer.read()), save=False
        )
