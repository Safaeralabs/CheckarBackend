from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsSupervisorOrAbove

from .models import Campaign, CampaignRecipient, DeviceSession, Notification
from .senders import build_campaign_recipients, resolve_recipients_queryset, send_campaign
from .serializers import (
    CampaignRecipientSerializer,
    CampaignSerializer,
    DeviceSessionSerializer,
    NotificationSerializer,
)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "channel"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")


class DeviceSessionViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSessionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["platform"]

    def get_queryset(self):
        return DeviceSession.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.select_related("created_by").all().order_by("-created_at")
    serializer_class = CampaignSerializer
    permission_classes = [IsSupervisorOrAbove]
    filterset_fields = ["channel", "status"]

    def perform_create(self, serializer):
        campaign = serializer.save(created_by=self.request.user)
        build_campaign_recipients(campaign)

    def perform_update(self, serializer):
        campaign = serializer.save()
        if campaign.status == "draft":
            build_campaign_recipients(campaign)

    @action(detail=False, methods=["post"])
    def preview_recipients(self, request):
        channel = request.data.get("channel")
        filters = request.data.get("filters") or {}
        if channel not in ("email", "sms"):
            return Response({"detail": "channel debe ser 'email' o 'sms'."}, status=status.HTTP_400_BAD_REQUEST)
        count = resolve_recipients_queryset(channel, filters).count()
        return Response({"count": count})

    @action(detail=True, methods=["get"])
    def recipients(self, request, pk=None):
        campaign = self.get_object()
        qs = campaign.campaign_recipients.select_related("user").order_by("status", "id")
        return Response(CampaignRecipientSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status not in ("draft", "failed"):
            return Response(
                {"detail": f"La campaña ya está en estado '{campaign.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sent, failed = send_campaign(campaign)
        campaign.refresh_from_db()
        return Response(CampaignSerializer(campaign).data | {"enviados": sent, "fallidos": failed})
