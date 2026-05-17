from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import TimeStampedModel


class RoleChoices(models.TextChoices):
    CUSTOMER = "customer", "Cliente"
    OPERATOR = "operator", "Operador"
    INSPECTOR = "inspector", "Inspector"
    SUPERVISOR = "supervisor", "Supervisor"
    ADMIN = "admin", "Administrador"


class User(AbstractUser):
    role = models.CharField(max_length=32, choices=RoleChoices.choices, default=RoleChoices.CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    document_number = models.CharField(max_length=32, blank=True)
    email_verified = models.BooleanField(default=False)
    mobile_notifications_enabled = models.BooleanField(default=True)


class CustomerProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    preferred_branch = models.ForeignKey(
        "scheduling.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_customers",
    )


class OperatorProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="operator_profile")
    employee_code = models.CharField(max_length=30, unique=True)
    branch = models.ForeignKey("scheduling.Branch", on_delete=models.SET_NULL, null=True, blank=True)
    can_validate_documents = models.BooleanField(default=False)
    can_release_certificate = models.BooleanField(default=False)


class AuditLog(TimeStampedModel):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events")
    action = models.CharField(max_length=120)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
