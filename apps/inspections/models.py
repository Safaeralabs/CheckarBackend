from django.db import models

from apps.common.models import TimeStampedModel


class InspectionTypeChoices(models.TextChoices):
    OFFICIAL = "official", "Oficial"
    PRE_TECHNICAL = "pre_technical", "Pre-tecnica"


class InspectionStatusChoices(models.TextChoices):
    PENDING = "pending", "Pendiente"
    DOCUMENTS_VALIDATED = "documents_validated", "Documentos validados"
    PRE_EVALUATED = "pre_evaluated", "Pre-evaluacion completada"
    VISUAL_REVIEW = "visual_review", "Inspeccion visual"
    MECHANICAL_TEST = "mechanical_test", "Pruebas tecnicas"
    RESULTS_RECORDED = "results_recorded", "Resultados registrados"
    APPROVED = "approved", "Aprobada"
    REJECTED = "rejected", "Rechazada"
    CERTIFIED = "certified", "Certificado emitido"


class InspectionRecord(TimeStampedModel):
    appointment = models.OneToOneField(
        "scheduling.Appointment", on_delete=models.CASCADE, related_name="inspection_record"
    )
    inspector = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_inspections"
    )
    inspection_type = models.CharField(
        max_length=20, choices=InspectionTypeChoices.choices, default=InspectionTypeChoices.OFFICIAL
    )
    status = models.CharField(
        max_length=30, choices=InspectionStatusChoices.choices, default=InspectionStatusChoices.PENDING
    )
    overall_result = models.CharField(max_length=20, blank=True)
    observations = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # Timestamps por etapa para trazabilidad del proceso
    documents_validated_at = models.DateTimeField(null=True, blank=True)
    pre_evaluated_at = models.DateTimeField(null=True, blank=True)
    visual_review_at = models.DateTimeField(null=True, blank=True)
    mechanical_test_at = models.DateTimeField(null=True, blank=True)
    results_recorded_at = models.DateTimeField(null=True, blank=True)


class DocumentResultChoices(models.TextChoices):
    VALID = "valid", "Valido"
    INVALID = "invalid", "Invalido"
    NOT_APPLICABLE = "na", "No aplica"


class DocumentCheck(TimeStampedModel):
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.CASCADE, related_name="document_checks")
    document_type = models.CharField(max_length=80)
    result = models.CharField(
        max_length=10, choices=DocumentResultChoices.choices, default=DocumentResultChoices.VALID
    )
    notes = models.TextField(blank=True)
    validated_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)


# Ítems fijos del formulario de pre-evaluación (proceso paso 2)
PRE_EVALUATION_ITEMS = [
    ("soat_vigente", "SOAT vigente"),
    ("licencia_transito", "Presento licencia de transito"),
    ("identificacion", "Presento identificacion"),
    ("vehiculo_limpio", "Vehiculo limpio"),
    ("vehiculo_vacio", "Vehiculo vacio"),
    ("dispositivos_seguridad", "Dispositivos de seguridad deshabilitados"),
    ("sin_tapacubos", "Inexistencia de tapacubos"),
    ("preparado_inspeccion", "Vehiculo preparado para la inspeccion"),
]


class PreEvaluationResultChoices(models.TextChoices):
    YES = "yes", "Si"
    NO = "no", "No"
    NA = "na", "No aplica"


class PreEvaluationItem(TimeStampedModel):
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.CASCADE, related_name="pre_evaluation_items")
    item_key = models.CharField(max_length=40, choices=PRE_EVALUATION_ITEMS)
    result = models.CharField(max_length=5, choices=PreEvaluationResultChoices.choices)
    notes = models.TextField(blank=True)
    evaluated_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        # Un ítem por inspección (sin duplicados)
        unique_together = [("inspection", "item_key")]


class InspectionChecklistItem(TimeStampedModel):
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.CASCADE, related_name="checklist_items")
    category = models.CharField(max_length=80)
    item_name = models.CharField(max_length=120)
    status = models.CharField(
        max_length=20, choices=[("pass", "Cumple"), ("fail", "No cumple"), ("na", "No aplica")]
    )
    notes = models.TextField(blank=True)


class InspectionPhoto(TimeStampedModel):
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.CASCADE, related_name="photos")
    photo = models.ImageField(upload_to="inspection_photos/")
    label = models.CharField(max_length=120)
    captured_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)


class TirePressureRecord(TimeStampedModel):
    inspection = models.OneToOneField(InspectionRecord, on_delete=models.CASCADE, related_name="tire_pressure")
    spare_tire_1 = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    spare_tire_2 = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    no_spare_tire = models.BooleanField(default=False)
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)


class AxleTirePressure(TimeStampedModel):
    """Presión de neumáticos por eje. Soporta llantas simples y dobles (interna/externa)."""
    record = models.ForeignKey(TirePressureRecord, on_delete=models.CASCADE, related_name="axles")
    axle_number = models.PositiveSmallIntegerField()
    is_double_tire = models.BooleanField(default=False)
    # Eje con llanta simple
    single_pressure = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    # Eje con llantas dobles (izquierda y derecha, externa e interna)
    left_outer = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    left_inner = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    right_outer = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    right_inner = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    class Meta:
        unique_together = [("record", "axle_number")]
        ordering = ["axle_number"]


class InspectionCertificate(TimeStampedModel):
    inspection = models.OneToOneField(InspectionRecord, on_delete=models.CASCADE, related_name="certificate")
    certificate_number = models.CharField(max_length=40, unique=True)
    file = models.FileField(upload_to="certificates/")
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField()
