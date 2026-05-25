from django.db import migrations


def seed_service_types(apps, schema_editor):
    ServiceType = apps.get_model("scheduling", "ServiceType")

    services = [
        {
            "code": "RTM-LIVIANO",
            "name": "Revisión Técnico Mecánica - Liviano",
            "description": "Inspección técnico mecánica y de emisiones para vehículos livianos (automóviles, camperos, camionetas).",
            "vehicle_type": "light",
            "duration_minutes": 45,
            "requires_payment_in_advance": False,
            "is_active": True,
        },
        {
            "code": "RTM-MOTO",
            "name": "Revisión Técnico Mecánica - Motocicleta",
            "description": "Inspección técnico mecánica y de emisiones para motocicletas.",
            "vehicle_type": "motorcycle",
            "duration_minutes": 30,
            "requires_payment_in_advance": False,
            "is_active": True,
        },
    ]

    for svc in services:
        ServiceType.objects.get_or_create(code=svc["code"], defaults=svc)


def remove_service_types(apps, schema_editor):
    ServiceType = apps.get_model("scheduling", "ServiceType")
    ServiceType.objects.filter(code__in=["RTM-LIVIANO", "RTM-MOTO"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_service_types, remove_service_types),
    ]
