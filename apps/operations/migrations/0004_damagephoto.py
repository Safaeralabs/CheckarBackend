import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0003_add_signature_flow"),
    ]

    operations = [
        migrations.CreateModel(
            name="DamagePhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("damage_id", models.CharField(max_length=32)),
                ("photo_base64", models.TextField()),
                ("label", models.CharField(blank=True, max_length=120)),
                (
                    "reception",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="damage_photos",
                        to="operations.vehiclereception",
                    ),
                ),
            ],
            options={"abstract": False},
        ),
    ]
