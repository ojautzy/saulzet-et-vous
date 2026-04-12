"""Step 1: Create DocumentCategory model and add temporary old_category column."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0005_set_galerie_template"),
    ]

    operations = [
        # Create the new DocumentCategory model
        migrations.CreateModel(
            name="DocumentCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="nom")),
                ("slug", models.SlugField(max_length=100, unique=True, verbose_name="slug")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="ordre")),
            ],
            options={
                "verbose_name": "catégorie de document",
                "verbose_name_plural": "catégories de documents",
                "ordering": ["order", "name"],
            },
        ),
        # Rename old CharField category → old_category
        migrations.RenameField(
            model_name="document",
            old_name="category",
            new_name="old_category",
        ),
        # Add new ForeignKey category field
        migrations.AddField(
            model_name="document",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="documents",
                to="pages.documentcategory",
                verbose_name="catégorie",
            ),
        ),
    ]
