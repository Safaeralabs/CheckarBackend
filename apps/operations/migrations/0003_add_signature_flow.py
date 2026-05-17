from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0002_add_fr25_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehiclereception",
            name="signature_status",
            field=models.CharField(
                choices=[
                    ("unsigned", "Sin firmar"),
                    ("operator_signed", "Firmado por operador"),
                    ("fully_signed", "Firmado por ambas partes"),
                ],
                default="unsigned",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="vehiclereception",
            name="signature_requested_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="vehiclereception",
            name="client_signed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
