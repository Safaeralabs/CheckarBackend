from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.accounts.permissions import IsAdminUserRole

from .models import Appointment, Branch, ScheduleSlot, ServiceType, Tariff
from .serializers import (
    AppointmentSerializer,
    BranchSerializer,
    ScheduleSlotSerializer,
    ServiceTypeSerializer,
    TariffSerializer,
)

APPOINTMENT_TRANSITIONS = {
    "created": {"confirmed", "cancelled"},
    "confirmed": {"checked_in", "cancelled", "no_show"},
    "checked_in": {"in_progress"},
    "in_progress": {"completed", "rejected"},
    "completed": set(),
    "rejected": set(),
    "cancelled": set(),
    "no_show": set(),
}


class BranchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Branch.objects.filter(is_active=True).order_by("name")
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["city"]
    search_fields = ["name", "code", "city"]


class ServiceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceType.objects.filter(is_active=True).order_by("name")
    serializer_class = ServiceTypeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["vehicle_type"]
    search_fields = ["name", "code"]


class TariffViewSet(viewsets.ModelViewSet):
    queryset = Tariff.objects.select_related("service", "branch").all().order_by("-valid_from")
    serializer_class = TariffSerializer
    permission_classes = [IsAdminUserRole]
    filterset_fields = ["branch", "service", "is_active"]


class ScheduleSlotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ScheduleSlot.objects.select_related("branch", "service").filter(is_available=True).order_by("start_time")
    serializer_class = ScheduleSlotSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["branch", "service", "is_available"]


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["branch", "service", "status", "vehicle"]
    search_fields = ["vehicle__plate", "customer__document_number"]

    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.select_related("customer", "vehicle", "branch", "service", "slot", "reception")
        if user.role == "customer":
            return queryset.filter(customer=user).order_by("-scheduled_for")
        return queryset.order_by("-scheduled_for")

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        if "cancelled" not in APPOINTMENT_TRANSITIONS.get(appointment.status, set()):
            return Response({"detail": "La cita no puede cancelarse desde su estado actual."}, status=status.HTTP_400_BAD_REQUEST)
        appointment.status = "cancelled"
        appointment.save(update_fields=["status", "updated_at"])
        return Response({"status": appointment.status})
