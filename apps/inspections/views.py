from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsInspectorOrAbove, IsOperatorOrAbove

from .models import (
    AxleTirePressure,
    DocumentCheck,
    InspectionCertificate,
    InspectionChecklistItem,
    InspectionPhoto,
    InspectionRecord,
    PreEvaluationItem,
    TirePressureRecord,
)
from .serializers import (
    AxleTirePressureSerializer,
    DocumentCheckSerializer,
    InspectionCertificateSerializer,
    InspectionChecklistItemSerializer,
    InspectionPhotoSerializer,
    InspectionRecordSerializer,
    PreEvaluationItemSerializer,
    TirePressureRecordSerializer,
)

INSPECTION_TRANSITIONS = {
    "pending": {"documents_validated"},
    "documents_validated": {"pre_evaluated"},
    "pre_evaluated": {"visual_review"},
    "visual_review": {"mechanical_test"},
    "mechanical_test": {"results_recorded"},
    "results_recorded": {"approved", "rejected"},
    "approved": {"certified"},
    "rejected": set(),
    "certified": set(),
}

# Campos de timestamp a actualizar por cada transición de estado
STATUS_TIMESTAMP_FIELDS = {
    "documents_validated": "documents_validated_at",
    "pre_evaluated": "pre_evaluated_at",
    "visual_review": "visual_review_at",
    "mechanical_test": "mechanical_test_at",
    "results_recorded": "results_recorded_at",
}

# Sincroniza el estado de la cita (Appointment) cuando la inspección avanza
APPOINTMENT_STATUS_BY_INSPECTION_STATUS = {
    "documents_validated": "in_progress",
    "approved": "completed",
    "certified": "completed",
    "rejected": "rejected",
}


class InspectionRecordViewSet(viewsets.ModelViewSet):
    serializer_class = InspectionRecordSerializer
    filterset_fields = ["status", "overall_result", "inspection_type", "appointment", "appointment__branch"]
    search_fields = ["appointment__vehicle__plate", "appointment__customer__document_number"]

    def get_queryset(self):
        qs = InspectionRecord.objects.select_related(
            "appointment__vehicle", "appointment__customer",
            "appointment__branch", "appointment__service",
            "inspector", "certificate",
        ).order_by("-created_at")
        user = self.request.user
        if user.role == "customer":
            return qs.filter(appointment__customer=user)
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsOperatorOrAbove()]

    @action(detail=True, methods=["get"])
    def full_detail(self, request, pk=None):
        inspection = self.get_object()
        data = InspectionRecordSerializer(inspection, context={"request": request}).data
        data["document_checks"]       = DocumentCheckSerializer(inspection.document_checks.all(), many=True).data
        data["pre_evaluation_items"]  = PreEvaluationItemSerializer(inspection.pre_evaluation_items.all(), many=True).data
        data["checklist_items"]       = InspectionChecklistItemSerializer(inspection.checklist_items.all(), many=True).data
        try:
            data["tire_pressure"] = TirePressureRecordSerializer(inspection.tire_pressure).data
        except Exception:
            data["tire_pressure"] = None
        return Response(data)

    @action(detail=True, methods=["post"])
    def advance_status(self, request, pk=None):
        inspection = self.get_object()
        next_status = request.data.get("next_status")

        if next_status not in INSPECTION_TRANSITIONS.get(inspection.status, set()):
            return Response(
                {"detail": "Transicion de inspeccion no permitida.", "current_status": inspection.status},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        update_fields = ["status", "updated_at"]

        inspection.status = next_status

        # Registrar timestamp de la etapa alcanzada
        ts_field = STATUS_TIMESTAMP_FIELDS.get(next_status)
        if ts_field:
            setattr(inspection, ts_field, now)
            update_fields.append(ts_field)

        # Marcar inicio de inspección al salir de pending
        if next_status == "documents_validated" and inspection.started_at is None:
            inspection.started_at = now
            update_fields.append("started_at")

        # Marcar finalización al llegar a estado terminal
        if next_status in ("approved", "rejected", "certified"):
            inspection.completed_at = now
            update_fields.append("completed_at")

        inspection.save(update_fields=update_fields)

        # Mantener sincronizado el estado de la cita con el avance de la inspección
        appointment_status = APPOINTMENT_STATUS_BY_INSPECTION_STATUS.get(next_status)
        if appointment_status:
            inspection.appointment.status = appointment_status
            inspection.appointment.save(update_fields=["status", "updated_at"])

        return Response({"status": inspection.status})


class DocumentCheckViewSet(viewsets.ModelViewSet):
    queryset = DocumentCheck.objects.select_related("inspection", "validated_by").all()
    serializer_class = DocumentCheckSerializer
    permission_classes = [IsOperatorOrAbove]
    filterset_fields = ["inspection", "result", "document_type"]


class PreEvaluationItemViewSet(viewsets.ModelViewSet):
    queryset = PreEvaluationItem.objects.select_related("inspection", "evaluated_by").all()
    serializer_class = PreEvaluationItemSerializer
    permission_classes = [IsOperatorOrAbove]
    filterset_fields = ["inspection", "item_key", "result"]


class InspectionChecklistItemViewSet(viewsets.ModelViewSet):
    queryset = InspectionChecklistItem.objects.select_related("inspection").all()
    serializer_class = InspectionChecklistItemSerializer
    permission_classes = [IsInspectorOrAbove]
    filterset_fields = ["inspection", "category", "status"]


class InspectionPhotoViewSet(viewsets.ModelViewSet):
    queryset = InspectionPhoto.objects.select_related("inspection", "captured_by").all()
    serializer_class = InspectionPhotoSerializer
    permission_classes = [IsInspectorOrAbove]
    filterset_fields = ["inspection", "label"]


class TirePressureRecordViewSet(viewsets.ModelViewSet):
    queryset = TirePressureRecord.objects.select_related("inspection", "recorded_by").all()
    serializer_class = TirePressureRecordSerializer
    permission_classes = [IsInspectorOrAbove]
    filterset_fields = ["inspection"]


class AxleTirePressureViewSet(viewsets.ModelViewSet):
    queryset = AxleTirePressure.objects.select_related("record").all()
    serializer_class = AxleTirePressureSerializer
    permission_classes = [IsInspectorOrAbove]
    filterset_fields = ["record", "axle_number", "is_double_tire"]


class InspectionCertificateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InspectionCertificate.objects.select_related("inspection").all().order_by("-issued_at")
    serializer_class = InspectionCertificateSerializer
    permission_classes = [IsOperatorOrAbove]
