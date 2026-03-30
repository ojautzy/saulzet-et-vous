"""Set the existing gallery page to use the galerie template."""

from django.db import migrations


def set_galerie_template(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    Page.objects.filter(slug="galerie", parent__slug="decouvrir").update(
        template="galerie"
    )


def revert_galerie_template(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    Page.objects.filter(slug="galerie", parent__slug="decouvrir").update(
        template="default"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0004_galleryphoto"),
    ]

    operations = [
        migrations.RunPython(set_galerie_template, revert_galerie_template),
    ]
