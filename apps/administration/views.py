from datetime import timedelta

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import views, viewsets
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import IsAdminUserRole, IsSupervisorOrAbove
from apps.inspections.models import InspectionCertificate, InspectionRecord

from .models import GlobalReport
from .serializers import GlobalReportSerializer


class GlobalReportViewSet(viewsets.ModelViewSet):
    queryset = GlobalReport.objects.select_related("generated_by").all().order_by("-created_at")
    serializer_class = GlobalReportSerializer
    permission_classes = [IsAdminUserRole]
    filterset_fields = ["report_type"]


class DashboardSummaryView(views.APIView):
    permission_classes = [IsSupervisorOrAbove]

    def get(self, request):
        ahora = timezone.now()
        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total = InspectionRecord.objects.count()
        mes = InspectionRecord.objects.filter(created_at__gte=inicio_mes).count()
        aprobadas = InspectionRecord.objects.filter(overall_result="approved").count()
        rechazadas = InspectionRecord.objects.filter(overall_result="rejected").count()
        clientes_mes = User.objects.filter(role="customer", date_joined__gte=inicio_mes).count()
        rtm_30 = InspectionCertificate.objects.filter(
            expires_at__gte=ahora, expires_at__lte=ahora + timedelta(days=30)
        ).count()
        rtm_60 = InspectionCertificate.objects.filter(
            expires_at__gte=ahora, expires_at__lte=ahora + timedelta(days=60)
        ).count()
        rtm_90 = InspectionCertificate.objects.filter(
            expires_at__gte=ahora, expires_at__lte=ahora + timedelta(days=90)
        ).count()

        return Response(
            {
                "total_inspecciones": total,
                "inspecciones_este_mes": mes,
                "aprobadas": aprobadas,
                "rechazadas": rechazadas,
                "clientes_nuevos_este_mes": clientes_mes,
                "rtm_vencen_30_dias": rtm_30,
                "rtm_vencen_60_dias": rtm_60,
                "rtm_vencen_90_dias": rtm_90,
            }
        )


class RTMVencimientoView(views.APIView):
    permission_classes = [IsSupervisorOrAbove]

    def get(self, request):
        try:
            dias = max(1, min(int(request.query_params.get("dias", 60)), 365))
        except (ValueError, TypeError):
            dias = 60

        ahora = timezone.now()
        limite = ahora + timedelta(days=dias)

        certificados = (
            InspectionCertificate.objects.filter(expires_at__gte=ahora, expires_at__lte=limite)
            .select_related("inspection__appointment__vehicle__owner")
            .order_by("expires_at")
        )

        resultados = []
        for cert in certificados:
            try:
                vehicle = cert.inspection.appointment.vehicle
                owner = vehicle.owner
            except Exception:
                continue
            dias_restantes = (cert.expires_at.date() - ahora.date()).days
            resultados.append(
                {
                    "certificado_id": cert.id,
                    "numero_certificado": cert.certificate_number,
                    "fecha_vencimiento": cert.expires_at.date().isoformat(),
                    "vence_en_dias": dias_restantes,
                    "vehiculo": {
                        "id": vehicle.id,
                        "placa": vehicle.plate,
                        "marca": vehicle.brand,
                        "modelo": vehicle.model_line,
                        "anio": vehicle.model_year,
                        "tipo": vehicle.vehicle_type,
                    },
                    "propietario": {
                        "id": owner.id,
                        "nombre": f"{owner.first_name} {owner.last_name}".strip(),
                        "telefono": owner.phone,
                        "email": owner.email,
                        "documento": owner.document_number,
                    },
                }
            )

        return Response({"dias_umbral": dias, "total": len(resultados), "resultados": resultados})


class InspectionReportsView(views.APIView):
    permission_classes = [IsSupervisorOrAbove]

    def get(self, request):
        try:
            dias = max(1, min(int(request.query_params.get("dias", 30)), 365))
        except (ValueError, TypeError):
            dias = 30

        desde = timezone.now() - timedelta(days=dias)
        inspecciones = InspectionRecord.objects.filter(created_at__gte=desde)

        total = inspecciones.count()
        aprobadas = inspecciones.filter(overall_result="approved").count()
        rechazadas = inspecciones.filter(overall_result="rejected").count()

        avg_dur = (
            inspecciones.filter(started_at__isnull=False, completed_at__isnull=False)
            .annotate(dur=ExpressionWrapper(F("completed_at") - F("started_at"), output_field=DurationField()))
            .aggregate(avg=Avg("dur"))["avg"]
        )
        avg_minutos = round(avg_dur.total_seconds() / 60, 1) if avg_dur else None

        oficial = inspecciones.filter(inspection_type="official").count()
        pre_tecnica = inspecciones.filter(inspection_type="pre_technical").count()

        por_dia = list(
            inspecciones.annotate(dia=TruncDate("created_at"))
            .values("dia")
            .annotate(
                total=Count("id"),
                aprobadas=Count("id", filter=Q(overall_result="approved")),
                rechazadas=Count("id", filter=Q(overall_result="rejected")),
            )
            .order_by("dia")
        )

        return Response(
            {
                "dias": dias,
                "total": total,
                "aprobadas": aprobadas,
                "rechazadas": rechazadas,
                "tasa_aprobacion": round(aprobadas / total * 100, 1) if total > 0 else 0,
                "tiempo_promedio_minutos": avg_minutos,
                "por_tipo": {"oficial": oficial, "pre_tecnica": pre_tecnica},
                "por_dia": [
                    {
                        "dia": d["dia"].isoformat(),
                        "total": d["total"],
                        "aprobadas": d["aprobadas"],
                        "rechazadas": d["rechazadas"],
                    }
                    for d in por_dia
                ],
            }
        )
