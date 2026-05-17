from django.db import models

from apps.common.models import TimeStampedModel


class InspectionTypeChoices(models.TextChoices):
    OFFICIAL = "official", "Oficial"
    PRE_TECHNICAL = "pre_technical", "Pre-tecnica"
    PREVENTIVA = "preventiva", "Preventiva"


class InspectionSubtypeChoices(models.TextChoices):
    PRIMERA = "primera", "Primera inspeccion"
    REINSPECCION = "reinspeccion", "Re-inspeccion"


def _default_inventory():
    return {
        "llavero": "", "equipo_carretera": "", "encendedor": "",
        "radio": "", "extintor": "", "tapete": "",
        "herramientas": "", "parlantes": "", "num_sillas": "", "otros": "",
    }


class DriverIdTypeChoices(models.TextChoices):
    CC = "cc", "Cedula de ciudadania"
    CE = "ce", "Cedula de extranjeria"
    PASSPORT = "passport", "Pasaporte"
    NIT = "nit", "NIT"
    TI = "ti", "Tarjeta de identidad"


class LicenseCategoryChoices(models.TextChoices):
    A1 = "A1", "A1"
    A2 = "A2", "A2"
    B1 = "B1", "B1"
    B2 = "B2", "B2"
    B3 = "B3", "B3"
    C1 = "C1", "C1"
    C2 = "C2", "C2"
    C3 = "C3", "C3"


class SignatureStatusChoices(models.TextChoices):
    UNSIGNED = "unsigned", "Sin firmar"
    OPERATOR_SIGNED = "operator_signed", "Firmado por operador"
    FULLY_SIGNED = "fully_signed", "Firmado por ambas partes"


class VehicleReception(TimeStampedModel):
    appointment = models.OneToOneField("scheduling.Appointment", on_delete=models.CASCADE, related_name="reception")
    received_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    arrival_time = models.DateTimeField()
    queue_position = models.PositiveIntegerField(default=0)

    # Tipo de inspección
    inspection_type = models.CharField(
        max_length=20, choices=InspectionTypeChoices.choices, default=InspectionTypeChoices.OFFICIAL
    )
    foreign_vehicle = models.BooleanField(default=False)

    # Confirmaciones básicas
    plate_confirmed = models.BooleanField(default=False)
    customer_confirmed = models.BooleanField(default=False)
    documents_complete = models.BooleanField(default=False)
    objects_in_vehicle = models.BooleanField(default=False)

    # Datos del conductor (puede diferir del propietario registrado)
    driver_is_owner = models.BooleanField(default=True)
    driver_name = models.CharField(max_length=80, blank=True)
    driver_first_surname = models.CharField(max_length=80, blank=True)
    driver_second_surname = models.CharField(max_length=80, blank=True)
    driver_id_type = models.CharField(
        max_length=20, choices=DriverIdTypeChoices.choices, default=DriverIdTypeChoices.CC
    )
    driver_id_number = models.CharField(max_length=32, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)
    driver_email = models.EmailField(blank=True)
    driver_address = models.CharField(max_length=255, blank=True)
    driver_city = models.CharField(max_length=120, blank=True)
    driver_license_category = models.CharField(
        max_length=5, choices=LicenseCategoryChoices.choices, blank=True
    )
    driver_hearing_impaired = models.BooleanField(default=False)

    notes = models.TextField(blank=True)

    # Subtipo y costo (FR-25)
    inspection_subtype = models.CharField(
        max_length=20, choices=InspectionSubtypeChoices.choices,
        default=InspectionSubtypeChoices.PRIMERA
    )
    inspection_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Inventario de objetos del vehículo (FR-25)
    inventory = models.JSONField(default=_default_inventory, blank=True)

    # Esquema de daños visuales (FR-25): [{type, x, y}]
    damage_annotations = models.JSONField(default=list, blank=True)

    # Firmas digitales (base64 PNG)
    signature_client = models.TextField(blank=True)
    signature_officer = models.TextField(blank=True)

    # Flujo de firma
    signature_status = models.CharField(
        max_length=20, choices=SignatureStatusChoices.choices,
        default=SignatureStatusChoices.UNSIGNED
    )
    signature_requested_at = models.DateTimeField(null=True, blank=True)
    client_signed_at = models.DateTimeField(null=True, blank=True)


class SystemLogEntry(TimeStampedModel):
    level = models.CharField(max_length=20, choices=[("info", "Info"), ("warning", "Warning"), ("error", "Error")])
    source = models.CharField(max_length=80)
    message = models.TextField()
    related_entity = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
