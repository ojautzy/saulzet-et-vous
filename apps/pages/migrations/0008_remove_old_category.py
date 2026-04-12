"""Step 3: Remove the old_category CharField now that data is migrated."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0007_populate_document_categories"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="document",
            name="old_category",
        ),
    ]
