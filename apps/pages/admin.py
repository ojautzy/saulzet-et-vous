"""Admin configuration for pages app."""

from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Document, DocumentCategory, GalleryPhoto, Page

SPECIAL_TEMPLATES = {
    Page.Template.GALERIE,
    Page.Template.HABITANTS,
    Page.Template.ACCES,
    Page.Template.EQUIPE,
    Page.Template.CONTACT,
    Page.Template.DOCUMENTS,
}

STANDARD_TEMPLATES = [
    (Page.Template.DEFAULT, Page.Template.DEFAULT.label),
    (Page.Template.FULL_WIDTH, Page.Template.FULL_WIDTH.label),
]


def _is_secretary(user):
    """Check if user is a secretary (not admin/superuser)."""
    return hasattr(user, "is_secretary") and user.is_secretary and not user.is_superuser


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1
    fields = ("title", "file", "category", "date")


class GalleryPhotoInline(admin.TabularInline):
    model = GalleryPhoto
    extra = 1
    fields = ("image", "thumbnail_preview", "title", "credit", "order", "is_published")
    readonly_fields = ("thumbnail_preview",)

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height:60px; border-radius:4px;" />',
                obj.thumbnail.url,
            )
        return "-"

    thumbnail_preview.short_description = _("Aperçu")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "parent", "menu_order", "is_published", "template", "updated_at")
    list_filter = ("is_published", "template", "parent")
    list_editable = ("menu_order", "is_published")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (None, {
            "fields": ("title", "slug", "parent", "template"),
        }),
        (_("Contenu"), {
            "fields": ("content", "excerpt", "featured_image"),
        }),
        (_("Menu et affichage"), {
            "fields": ("menu_order", "show_in_menu", "is_published"),
        }),
        (_("SEO"), {
            "fields": ("meta_description",),
            "classes": ("collapse",),
        }),
    )

    def has_change_permission(self, request, obj=None):
        if obj and _is_secretary(request.user) and obj.template in SPECIAL_TEMPLATES:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and _is_secretary(request.user):
            if obj.template in SPECIAL_TEMPLATES:
                return False
            if obj.created_by != request.user:
                return False
        return super().has_delete_permission(request, obj)

    def get_inlines(self, request, obj=None):
        inlines = [DocumentInline]
        if obj and obj.template == Page.Template.GALERIE:
            inlines.append(GalleryPhotoInline)
        return inlines

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.template in SPECIAL_TEMPLATES and "content" in form.base_fields:
            form.base_fields["content"].widget = forms.Textarea(attrs={"rows": 4})
            form.base_fields["content"].help_text = _(
                "Texte d'introduction optionnel, affiché avant le contenu "
                "spécifique de la page. La mise en forme est automatique."
            )
        if _is_secretary(request.user) and "template" in form.base_fields:
            form.base_fields["template"].choices = STANDARD_TEMPLATES
        return form

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if object_id and _is_secretary(request.user):
            try:
                obj = self.get_object(request, object_id)
                if obj and obj.template in SPECIAL_TEMPLATES:
                    messages.info(
                        request,
                        _(
                            "Cette page utilise un modèle spécial et est protégée. "
                            "Seul un administrateur peut la modifier."
                        ),
                    )
            except Exception:
                pass
        return super().changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent")


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "date", "page", "uploaded_at")
    list_filter = ("category",)
    search_fields = ("title",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ("thumbnail_preview", "title", "credit", "page", "order", "is_published", "uploaded_at")
    list_filter = ("is_published", "page")
    list_editable = ("order", "is_published")
    search_fields = ("title", "credit")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "page":
            kwargs["queryset"] = Page.objects.filter(template=Page.Template.GALERIE)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height:40px; border-radius:4px;" />',
                obj.thumbnail.url,
            )
        return "-"

    thumbnail_preview.short_description = _("Aperçu")
