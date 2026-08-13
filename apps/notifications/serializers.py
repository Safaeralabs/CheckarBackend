from rest_framework import serializers

from .models import Campaign, CampaignRecipient, DeviceSession, Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class DeviceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceSession
        fields = "__all__"


class CampaignRecipientSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = CampaignRecipient
        fields = [
            "id", "user", "nombre", "email", "phone", "status",
            "provider_message_id", "error_message", "sent_at",
        ]

    def get_nombre(self, obj):
        if not obj.user:
            return ""
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


class CampaignSerializer(serializers.ModelSerializer):
    created_by_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id", "name", "channel", "subject", "message", "filters", "status",
            "created_by", "created_by_nombre", "recipients_count", "sent_count",
            "failed_count", "sent_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "status", "recipients_count", "sent_count", "failed_count", "sent_at",
        ]

    def get_created_by_nombre(self, obj):
        if not obj.created_by:
            return ""
        return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username

    def validate(self, attrs):
        channel = attrs.get("channel", getattr(self.instance, "channel", None))
        subject = attrs.get("subject", getattr(self.instance, "subject", ""))
        if channel == "email" and not subject:
            raise serializers.ValidationError({"subject": "El asunto es obligatorio para campañas de email."})
        return attrs
