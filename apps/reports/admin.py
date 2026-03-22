"""Admin configuration for the reports app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Comment, Photo, Report


class PhotoInline(admin.TabularInline):
    """Inline admin for report photos."""

    model = Photo
    extra = 0
    readonly_fields = ("thumbnail_preview", "uploaded_at")
    fields = ("image", "thumbnail_preview", "original_filename", "order", "uploaded_at")

    @admin.display(description=_("Apercu"))
    def thumbnail_preview(self, obj: Photo) -> str:
        """Display a thumbnail preview in admin."""
        if obj.thumbnail:
            return f'<img src="{obj.thumbnail.url}" style="max-height: 60px;" />'
        return "-"

    thumbnail_preview.allow_tags = True  # type: ignore[attr-defined]


class CommentInline(admin.TabularInline):
    """Inline admin for report comments."""

    model = Comment
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("author", "content", "is_status_change", "old_status", "new_status", "created_at")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin for reports."""

    list_display = ("title", "report_type", "status", "author", "assigned_to", "created_at")
    list_filter = ("report_type", "status")
    search_fields = ("title", "description", "author__email")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [PhotoInline, CommentInline]
    fieldsets = (
        (None, {"fields": ("id", "title", "description", "report_type", "status")}),
        (_("Localisation"), {"fields": ("latitude", "longitude", "location_text")}),
        (_("Assignation"), {"fields": ("author", "assigned_to", "assigned_by", "assigned_at")}),
        (_("Resolution"), {"fields": ("resolution_text", "resolved_at")}),
        (_("Dates"), {"fields": ("created_at", "updated_at")}),
    )
