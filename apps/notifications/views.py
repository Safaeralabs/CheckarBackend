from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import DeviceSession, Notification
from .serializers import DeviceSessionSerializer, NotificationSerializer


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
