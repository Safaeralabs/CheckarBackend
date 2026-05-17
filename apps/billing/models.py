from django.db import models

from apps.common.models import TimeStampedModel


class PaymentStatusChoices(models.TextChoices):
    PENDING = "pending", "Pendiente"
    AUTHORIZED = "authorized", "Autorizado"
    PAID = "paid", "Pagado"
    FAILED = "failed", "Fallido"
    REFUNDED = "refunded", "Reintegrado"


class Invoice(TimeStampedModel):
    appointment = models.OneToOneField("scheduling.Appointment", on_delete=models.CASCADE, related_name="invoice")
    invoice_number = models.CharField(max_length=40, unique=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    taxes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.PENDING)
    pdf = models.FileField(upload_to="invoices/", null=True, blank=True)


class PaymentTransaction(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="transactions")
    provider = models.CharField(max_length=50)
    provider_reference = models.CharField(max_length=80, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
