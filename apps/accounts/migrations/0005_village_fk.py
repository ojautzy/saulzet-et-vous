"""Multi-step migration: convert village CharField to ForeignKey.

Steps:
1. Add a temporary village_new FK field
2. Data migration: convert text values to FK references
3. Remove old village CharField
4. Rename village_new to village
"""

import django.db.models.deletion
from django.db import migrations, models

SLUG_MAP = {
    "bourg": "bourg",
    "souverand": "souverand",
    "zanieres": "zanieres",
    "pessade": "pessade",
    "la_martre": "la_martre",
    "espinasse": "espinasse",
}


def convert_village_text_to_fk(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Village = apps.get_model("settings_app", "Village")

    village_by_slug = {v.slug: v for v in Village.objects.all()}

    for user in User.objects.exclude(village="").exclude(village__isnull=True):
        slug = user.village
        if slug in village_by_slug:
            user.village_new = village_by_slug[slug]
            user.save(update_fields=["village_new"])


def reverse_convert(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.filter(village_new__isnull=False).select_related("village_new"):
        user.village = user.village_new.slug
        user.save(update_fields=["village"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_user_function_order_user_function_title_user_photo_and_more"),
        ("settings_app", "0002_initial_data"),
    ]

    operations = [
        # Step 1: Add temporary FK field
        migrations.AddField(
            model_name="user",
            name="village_new",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="residents_new",
                to="settings_app.village",
                verbose_name="village",
            ),
        ),
        # Step 2: Data migration
        migrations.RunPython(convert_village_text_to_fk, reverse_convert),
        # Step 3: Remove old CharField
        migrations.RemoveField(
            model_name="user",
            name="village",
        ),
        # Step 4: Rename new field to village
        migrations.RenameField(
            model_name="user",
            old_name="village_new",
            new_name="village",
        ),
        # Step 5: Update the field options to match the final model
        migrations.AlterField(
            model_name="user",
            name="village",
            field=models.ForeignKey(
                blank=True,
                help_text="Village ou hameau de résidence à Saulzet-le-Froid.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="residents",
                to="settings_app.village",
                verbose_name="village",
            ),
        ),
    ]
