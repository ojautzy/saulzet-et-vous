"""Step 2: Create initial categories and migrate existing data."""

from django.db import migrations

INITIAL_CATEGORIES = [
    {"slug": "pv", "name": "Procès-verbal de conseil", "order": 1},
    {"slug": "bulletin", "name": "Bulletin municipal", "order": 2},
    {"slug": "plu", "name": "Document PLU", "order": 3},
    {"slug": "arrete", "name": "Arrêté", "order": 4},
    {"slug": "other", "name": "Autre", "order": 5},
]


def populate_categories(apps, schema_editor):
    DocumentCategory = apps.get_model("pages", "DocumentCategory")
    Document = apps.get_model("pages", "Document")

    # Create the initial categories
    cat_map = {}
    for cat_data in INITIAL_CATEGORIES:
        cat_obj, _ = DocumentCategory.objects.get_or_create(
            slug=cat_data["slug"],
            defaults={"name": cat_data["name"], "order": cat_data["order"]},
        )
        cat_map[cat_data["slug"]] = cat_obj

    # Migrate existing documents
    for doc in Document.objects.all():
        if doc.old_category and doc.old_category in cat_map:
            doc.category = cat_map[doc.old_category]
            doc.save(update_fields=["category"])


def reverse_categories(apps, schema_editor):
    Document = apps.get_model("pages", "Document")
    for doc in Document.objects.select_related("category").all():
        if doc.category:
            doc.old_category = doc.category.slug
            doc.save(update_fields=["old_category"])


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0006_documentcategory"),
    ]

    operations = [
        migrations.RunPython(populate_categories, reverse_categories),
    ]
