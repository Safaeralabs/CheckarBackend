from django.db import models

from apps.common.models import TimeStampedModel


class Notification(TimeStampedModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=120)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=[("email", "Email"), ("sms", "SMS"), ("push", "Push"), ("in_app", "In app")])
    status = models.CharField(max_length=20, choices=[("pending", "Pendiente"), ("sent", "Enviada"), ("read", "Leida"), ("failed", "Fallida")], default="pending")
    read_at = models.DateTimeField(null=True, blank=True)
    context = models.JSONField(default=dict, blank=True)


class DeviceSession(TimeStampedModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="device_sessions")
    device_name = models.CharField(max_length=80)
    platform = models.CharField(max_length=40)
    push_token = models.CharField(max_length=255, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
