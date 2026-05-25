from django.db import transaction
from django.utils import timezone
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsOperatorOrAbove, IsSupervisorOrAbove

from .models import DamagePhoto, SignatureStatusChoices, SystemLogEntry, VehicleReception
from .serializers import DamagePhotoSerializer, SystemLogEntrySerializer, VehicleReceptionSerializer, WalkInSerializer


class VehicleReceptionViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleReceptionSerializer
    filterset_fields = [
        "appointment__branch", "plate_confirmed", "customer_confirmed",
        "documents_complete", "appointment", "signature_status",
    ]
    search_fields = ["appointment__vehicle__plate", "appointment__customer__document_number"]

    def get_queryset(self):
        qs = VehicleReception.objects.select_related(
            "appointment__vehicle", "appointment__customer", "received_by"
        ).order_by("-arrival_time")
        user = self.request.user
        if user.role == "customer":
            return qs.filter(appointment__customer=user)
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve", "client_sign"):
            return [IsAuthenticated()]
        return [IsOperatorOrAbove()]

    @action(detail=True, methods=["post"], url_path="request_signature")
    def request_signature(self, request, pk=None):
        """
        Operator has already saved their signature.
        Mark reception as operator_signed and notify the client.
        """
        from apps.notifications.models import Notification

        rec = self.get_object()

        if not rec.signature_officer:
            return Response(
                {"detail": "El operador debe firmar antes de solicitar la firma del cliente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rec.signature_status = SignatureStatusChoices.OPERATOR_SIGNED
        rec.signature_requested_at = timezone.now()
        rec.save(update_fields=["signature_status", "signature_requested_at"])

        client = rec.appointment.customer
        Notification.objects.create(
            user=client,
            title="Firma requerida — Recepción de vehículo",
            message=(
                f"El CDA ha preparado la recepción de tu vehículo "
                f"{rec.appointment.vehicle.plate}. "
                "Revisa los detalles y firma para autorizar el inicio de la inspección."
            ),
            channel="in_app",
            status="sent",
            context={"reception_id": rec.id, "type": "signature_request"},
        )

        from apps.common.emails import send_signature_request_email
        send_signature_request_email(client, rec)

        return Response({"signature_status": rec.signature_status})

    @action(detail=True, methods=["post"], url_path="client_sign")
    def client_sign(self, request, pk=None):
        """
        Client submits their signature from the customer portal.
        """
        rec = self.get_object()
        user = request.user

        if user.role != "customer" or rec.appointment.customer_id != user.id:
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

        if rec.signature_status not in (
            SignatureStatusChoices.OPERATOR_SIGNED, SignatureStatusChoices.FULLY_SIGNED
        ):
            return Response(
                {"detail": "La recepción aún no ha sido firmada por el operador."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sig = request.data.get("signature_client", "").strip()
        if not sig:
            return Response({"detail": "Firma requerida."}, status=status.HTTP_400_BAD_REQUEST)

        rec.signature_client = sig
        rec.signature_status = SignatureStatusChoices.FULLY_SIGNED
        rec.client_signed_at = timezone.now()
        rec.save(update_fields=["signature_client", "signature_status", "client_signed_at"])

        return Response({"signature_status": rec.signature_status})

    @action(detail=True, methods=["post"], url_path="damage_photos")
    def add_damage_photo(self, request, pk=None):
        rec = self.get_object()
        damage_id = str(request.data.get("damage_id", "")).strip()
        photo_base64 = request.data.get("photo_base64", "").strip()
        label = request.data.get("label", "")
        if not damage_id or not photo_base64:
            return Response(
                {"detail": "damage_id y photo_base64 son requeridos."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        photo = DamagePhoto.objects.create(
            reception=rec, damage_id=damage_id, photo_base64=photo_base64, label=label
        )
        return Response(DamagePhotoSerializer(photo).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"damage_photos/(?P<photo_id>[0-9]+)")
    def remove_damage_photo(self, request, pk=None, photo_id=None):
        rec = self.get_object()
        try:
            photo = rec.damage_photos.get(id=photo_id)
        except DamagePhoto.DoesNotExist:
            return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)
        photo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemLogEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SystemLogEntrySerializer
    permission_classes = [IsSupervisorOrAbove]
    filterset_fields = ["level", "source"]

    def get_queryset(self):
        qs = SystemLogEntry.objects.all().order_by("-created_at")
        desde = self.request.query_params.get("desde")
        if desde:
            from django.utils.dateparse import parse_date
            try:
                dt = parse_date(desde)
                if dt:
                    qs = qs.filter(created_at__date__gte=dt)
            except Exception:
                pass
        return qs


class WalkInView(views.APIView):
    """
    Ingreso rápido sin cita previa.
    POST: busca vehículo por placa; si no existe crea cliente+vehículo.
    Crea Appointment (walk_in) + VehicleReception + InspectionRecord en una transacción.
    """
    permission_classes = [IsOperatorOrAbove]

    @transaction.atomic
    def post(self, request):
        from apps.accounts.models import CustomerProfile, RoleChoices, User
        from apps.inspections.models import InspectionRecord
        from apps.scheduling.models import Appointment, Branch, ServiceType
        from apps.vehicles.models import Vehicle

        serializer = WalkInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        plate = data["plate"].upper().strip()
        is_new_client = False

        # ── 1. Buscar vehículo por placa ─────────────────────────────────
        vehicle = Vehicle.objects.filter(plate=plate).select_related("owner").first()

        if not vehicle:
            # ── 2a. Crear cliente y vehículo ────────────────────────────
            is_new_client = True
            doc = data.get("document_number", "").strip()
            email = data.get("email", "").strip().lower()
            phone = data.get("phone", "").strip()
            if not doc:
                return Response(
                    {"detail": "El número de documento es requerido para registrar un cliente nuevo."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not email:
                return Response(
                    {"detail": "El email es requerido para registrar un cliente nuevo y enviarle sus credenciales de acceso."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Unicidad: solo verificar si el documento no existe aún
            # (si ya existe, get_or_create reutiliza al usuario existente)
            if not User.objects.filter(document_number=doc).exists():
                if User.objects.filter(email__iexact=email).exists():
                    return Response(
                        {"detail": "Este correo electrónico ya está registrado en el sistema."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if phone and User.objects.filter(phone=phone).exists():
                    return Response(
                        {"detail": "Este número de teléfono ya está registrado en el sistema."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            owner, created = User.objects.get_or_create(
                document_number=doc,
                defaults={
                    "username": doc,
                    "first_name": data.get("first_name", ""),
                    "last_name": data.get("last_name", ""),
                    "phone": data.get("phone", ""),
                    "email": email,
                    "role": RoleChoices.CUSTOMER,
                },
            )
            if created:
                owner.set_password(doc)
                owner.save(update_fields=["password"])
                CustomerProfile.objects.create(user=owner)
                # Enviar credenciales por email
                from apps.common.emails import send_welcome_email
                send_welcome_email(owner, initial_password=doc)

            vehicle = Vehicle.objects.create(
                owner=owner,
                plate=plate,
                brand=data.get("brand", ""),
                model_line=data.get("model_line", ""),
                model_year=data.get("model_year", 2020),
                vehicle_type=data.get("vehicle_type", "light"),
                fuel_type=data.get("fuel_type", "gasoline"),
                color=data.get("color", ""),
                registration_city=data.get("registration_city", ""),
            )
        else:
            owner = vehicle.owner

        # ── 3. Determinar sede ───────────────────────────────────────────
        branch = None
        try:
            branch = request.user.operator_profile.branch
        except Exception:
            pass
        if not branch:
            branch = Branch.objects.filter(is_active=True).first()
        if not branch:
            return Response(
                {"detail": "No hay sedes activas configuradas en el sistema."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 4. Determinar tipo de servicio ───────────────────────────────
        veh_type_srv = "motorcycle" if vehicle.vehicle_type == "motorcycle" else "light"
        service = (
            ServiceType.objects.filter(is_active=True, vehicle_type=veh_type_srv).first()
            or ServiceType.objects.filter(is_active=True).first()
        )
        if not service:
            return Response(
                {"detail": "No hay tipos de servicio configurados."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 5. Crear cita walk-in ────────────────────────────────────────
        now = timezone.now()
        appointment = Appointment.objects.create(
            customer=owner,
            vehicle=vehicle,
            branch=branch,
            service=service,
            scheduled_for=now,
            status="checked_in",
            source_channel="walk_in",
        )

        # ── 6. Crear recepción ───────────────────────────────────────────
        VehicleReception.objects.create(
            appointment=appointment,
            received_by=request.user,
            arrival_time=now,
            inspection_type=data["inspection_type"],
            driver_is_owner=True,
            plate_confirmed=True,
        )

        # ── 7. Crear registro de inspección ──────────────────────────────
        inspection = InspectionRecord.objects.create(
            appointment=appointment,
            inspector=request.user,
            inspection_type=data["inspection_type"],
        )

        return Response(
            {
                "inspection_id": inspection.id,
                "appointment_id": appointment.id,
                "vehicle_id": vehicle.id,
                "is_new_client": is_new_client,
                "owner_name": f"{owner.first_name} {owner.last_name}".strip(),
                "owner_email": owner.email,
            },
            status=status.HTTP_201_CREATED,
        )
