"""Data migration: create initial SiteSettings singleton and villages."""

from django.db import migrations

VILLAGES = [
    {"name": "Le Bourg", "slug": "bourg", "latitude": 45.6415, "longitude": 2.9178, "order": 1},
    {"name": "Souverand", "slug": "souverand", "latitude": 45.6403, "longitude": 2.9219, "order": 2},
    {"name": "Zanières", "slug": "zanieres", "latitude": 45.6407, "longitude": 2.9406, "order": 3},
    {"name": "Pessade", "slug": "pessade", "latitude": 45.6347, "longitude": 2.8895, "order": 4},
    {"name": "La Martre", "slug": "la_martre", "latitude": 45.6466, "longitude": 2.9059, "order": 5},
    {"name": "Espinasse", "slug": "espinasse", "latitude": 45.6525, "longitude": 2.9159, "order": 6},
]


def create_initial_data(apps, schema_editor):
    SiteSettings = apps.get_model("settings_app", "SiteSettings")
    Village = apps.get_model("settings_app", "Village")

    # Create singleton SiteSettings
    SiteSettings.objects.get_or_create(pk=1)

    # Create villages
    for v in VILLAGES:
        Village.objects.get_or_create(slug=v["slug"], defaults=v)


def reverse_initial_data(apps, schema_editor):
    SiteSettings = apps.get_model("settings_app", "SiteSettings")
    Village = apps.get_model("settings_app", "Village")
    SiteSettings.objects.filter(pk=1).delete()
    Village.objects.filter(slug__in=[v["slug"] for v in VILLAGES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("settings_app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_initial_data),
    ]
