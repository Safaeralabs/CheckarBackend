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


class Campaign(TimeStampedModel):
    CHANNEL_CHOICES = [("email", "Email"), ("sms", "SMS")]
    STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("sending", "Enviando"),
        ("sent", "Enviada"),
        ("failed", "Fallida"),
    ]

    name = models.CharField(max_length=150)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    filters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="campaigns"
    )
    recipients_count = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class CampaignRecipient(TimeStampedModel):
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("sent", "Enviado"),
        ("failed", "Fallido"),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="campaign_recipients")
    user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="campaign_recipients"
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    provider_message_id = models.CharField(max_length=120, blank=True)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("campaign", "user")]
