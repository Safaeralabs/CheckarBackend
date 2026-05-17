from django.db import models

from apps.common.models import SoftDeleteModel, TimeStampedModel


class Branch(SoftDeleteModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    opens_at = models.TimeField()
    closes_at = models.TimeField()

    def __str__(self):
        return self.name


class ServiceType(SoftDeleteModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    vehicle_type = models.CharField(max_length=20, choices=[("light", "Vehiculo liviano"), ("motorcycle", "Motocicleta")])
    duration_minutes = models.PositiveIntegerField(default=45)
    requires_payment_in_advance = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Tariff(TimeStampedModel):
    service = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name="tariffs")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="tariffs")
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class ScheduleSlot(TimeStampedModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="schedule_slots")
    service = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name="schedule_slots")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=1)
    reserved_count = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)


class AppointmentStatusChoices(models.TextChoices):
    CREATED = "created", "Creada"
    CONFIRMED = "confirmed", "Confirmada"
    CHECKED_IN = "checked_in", "Recepcionada"
    IN_PROGRESS = "in_progress", "En inspeccion"
    COMPLETED = "completed", "Completada"
    REJECTED = "rejected", "Rechazada"
    CANCELLED = "cancelled", "Cancelada"
    NO_SHOW = "no_show", "No asistio"


class Appointment(TimeStampedModel):
    customer = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="appointments")
    vehicle = models.ForeignKey("vehicles.Vehicle", on_delete=models.CASCADE, related_name="appointments")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="appointments")
    service = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name="appointments")
    slot = models.ForeignKey(ScheduleSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments")
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=20, choices=AppointmentStatusChoices.choices, default=AppointmentStatusChoices.CREATED)
    payment_status = models.CharField(max_length=20, default="pending")
    notes = models.TextField(blank=True)
    source_channel = models.CharField(max_length=30, default="portal_cliente")
