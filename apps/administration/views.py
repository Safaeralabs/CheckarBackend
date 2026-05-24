from datetime import timedelta

from django.db.models import (
    Avg, Count, DurationField, ExpressionWrapper, F, Q, Sum,
)
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone
from rest_framework import views, viewsets
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import IsAdminUserRole, IsSupervisorOrAbove
from apps.inspections.models import InspectionCertificate, InspectionRecord
from apps.operations.models import VehicleReception

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
        hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total = InspectionRecord.objects.count()
        mes = InspectionRecord.objects.filter(created_at__gte=inicio_mes).count()
        aprobadas = InspectionRecord.objects.filter(overall_result="approved").count()
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

        ingresos_hoy = VehicleReception.objects.filter(
            created_at__gte=hoy_inicio,
            inspection_cost__isnull=False,
        ).aggregate(total=Sum("inspection_cost"))["total"] or 0

        ingresos_mes = VehicleReception.objects.filter(
            created_at__gte=inicio_mes,
            inspection_cost__isnull=False,
        ).aggregate(total=Sum("inspection_cost"))["total"] or 0

        return Response({
            "total_inspecciones": total,
            "inspecciones_este_mes": mes,
            "aprobadas": aprobadas,
            "clientes_nuevos_este_mes": clientes_mes,
            "rtm_vencen_30_dias": rtm_30,
            "rtm_vencen_60_dias": rtm_60,
            "rtm_vencen_90_dias": rtm_90,
            "ingresos_hoy": float(ingresos_hoy),
            "ingresos_este_mes": float(ingresos_mes),
        })


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
            resultados.append({
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
            })

        return Response({"dias_umbral": dias, "total": len(resultados), "resultados": resultados})


class InspectionReportsView(views.APIView):
    permission_classes = [IsSupervisorOrAbove]

    def get(self, request):
        try:
            dias = max(1, min(int(request.query_params.get("dias", 30)), 365))
        except (ValueError, TypeError):
            dias = 30

        ahora = timezone.now()
        desde = ahora - timedelta(days=dias)
        desde_anterior = desde - timedelta(days=dias)

        inspecciones = InspectionRecord.objects.filter(created_at__gte=desde)
        inspecciones_ant = InspectionRecord.objects.filter(
            created_at__gte=desde_anterior, created_at__lt=desde
        )

        # ── Métricas básicas ─────────────────────────────────────────────────
        total = inspecciones.count()
        aprobadas = inspecciones.filter(overall_result="approved").count()
        rechazadas = inspecciones.filter(overall_result="rejected").count()

        avg_dur = (
            inspecciones.filter(started_at__isnull=False, completed_at__isnull=False)
            .annotate(dur=ExpressionWrapper(F("completed_at") - F("started_at"), output_field=DurationField()))
            .aggregate(avg=Avg("dur"))["avg"]
        )
        avg_minutos = round(avg_dur.total_seconds() / 60, 1) if avg_dur else None

        por_tipo = {
            "oficial":    inspecciones.filter(inspection_type="official").count(),
            "pre_tecnica": inspecciones.filter(inspection_type="pre_technical").count(),
            "preventiva": inspecciones.filter(inspection_type="preventiva").count(),
        }

        # ── Ingresos del período ─────────────────────────────────────────────
        recepciones = VehicleReception.objects.filter(
            created_at__gte=desde,
            inspection_cost__isnull=False,
        )
        ingresos_total = recepciones.aggregate(total=Sum("inspection_cost"))["total"] or 0

        # ── Volumen + ingresos por día ───────────────────────────────────────
        por_dia_insp = list(
            inspecciones.annotate(dia=TruncDate("created_at"))
            .values("dia")
            .annotate(
                total=Count("id"),
                aprobadas=Count("id", filter=Q(overall_result="approved")),
                rechazadas=Count("id", filter=Q(overall_result="rejected")),
            )
            .order_by("dia")
        )

        ingresos_dia_raw = dict(
            recepciones.annotate(dia=TruncDate("created_at"))
            .values("dia")
            .annotate(ingresos=Sum("inspection_cost"))
            .values_list("dia", "ingresos")
        )

        por_dia = [
            {
                "dia": d["dia"].isoformat(),
                "total": d["total"],
                "aprobadas": d["aprobadas"],
                "rechazadas": d["rechazadas"],
                "ingresos": float(ingresos_dia_raw.get(d["dia"], 0) or 0),
            }
            for d in por_dia_insp
        ]

        # ── Hora pico ────────────────────────────────────────────────────────
        por_hora = list(
            inspecciones.annotate(hora=ExtractHour("created_at"))
            .values("hora")
            .annotate(total=Count("id"))
            .order_by("hora")
            .values("hora", "total")
        )

        # ── Rendimiento por inspector ────────────────────────────────────────
        inspectores_qs = (
            inspecciones.filter(inspector__isnull=False)
            .values("inspector__id", "inspector__first_name", "inspector__last_name", "inspector__username")
            .annotate(
                total=Count("id"),
                aprobadas=Count("id", filter=Q(overall_result="approved")),
                rechazadas=Count("id", filter=Q(overall_result="rejected")),
                avg_dur=Avg(
                    ExpressionWrapper(
                        F("completed_at") - F("started_at"),
                        output_field=DurationField(),
                    ),
                    filter=Q(started_at__isnull=False, completed_at__isnull=False),
                ),
            )
            .order_by("-total")
        )

        por_inspector = []
        for row in inspectores_qs:
            nombre = (
                f"{row['inspector__first_name']} {row['inspector__last_name']}".strip()
                or row["inspector__username"]
            )
            avg_min = None
            if row["avg_dur"]:
                avg_min = round(row["avg_dur"].total_seconds() / 60, 1)
            tasa = round(row["aprobadas"] / row["total"] * 100, 1) if row["total"] else 0
            por_inspector.append({
                "id": row["inspector__id"],
                "nombre": nombre,
                "total": row["total"],
                "aprobadas": row["aprobadas"],
                "rechazadas": row["rechazadas"],
                "tasa_aprobacion": tasa,
                "tiempo_promedio_minutos": avg_min,
            })

        # ── Período anterior (comparación) ───────────────────────────────────
        total_ant = inspecciones_ant.count()
        aprobadas_ant = inspecciones_ant.filter(overall_result="approved").count()
        ingresos_ant = VehicleReception.objects.filter(
            created_at__gte=desde_anterior,
            created_at__lt=desde,
            inspection_cost__isnull=False,
        ).aggregate(total=Sum("inspection_cost"))["total"] or 0

        def delta(actual, anterior):
            if not anterior:
                return None
            return round((actual - anterior) / anterior * 100, 1)

        return Response({
            "dias": dias,
            "total": total,
            "aprobadas": aprobadas,
            "rechazadas": rechazadas,
            "tasa_aprobacion": round(aprobadas / total * 100, 1) if total else 0,
            "tiempo_promedio_minutos": avg_minutos,
            "por_tipo": por_tipo,
            "ingresos_total": float(ingresos_total),
            "por_dia": por_dia,
            "por_hora": [{"hora": h["hora"], "total": h["total"]} for h in por_hora],
            "por_inspector": por_inspector,
            "periodo_anterior": {
                "total": total_ant,
                "aprobadas": aprobadas_ant,
                "ingresos": float(ingresos_ant),
                "delta_total": delta(total, total_ant),
                "delta_aprobadas": delta(aprobadas, aprobadas_ant),
                "delta_ingresos": delta(float(ingresos_total), float(ingresos_ant)),
            },
        })
