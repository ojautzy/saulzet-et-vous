"""Admin configuration for pages app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Document, Page


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1
    fields = ("title", "file", "category", "date")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "parent", "menu_order", "is_published", "template", "updated_at")
    list_filter = ("is_published", "template", "parent")
    list_editable = ("menu_order", "is_published")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [DocumentInline]

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

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "date", "page", "uploaded_at")
    list_filter = ("category",)
    search_fields = ("title",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
