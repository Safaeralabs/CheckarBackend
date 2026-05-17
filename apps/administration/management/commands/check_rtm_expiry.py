from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Genera notificaciones (in-app y email) para vehículos con RTM próxima a vencer."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=90,
            help="Anticipación en días para detectar vencimientos (default: 90).",
        )
        parser.add_argument(
            "--send-emails",
            action="store_true",
            default=False,
            help="Despachar inmediatamente los emails generados.",
        )

    def handle(self, *args, **options):
        from apps.inspections.models import InspectionCertificate
        from apps.notifications.models import Notification

        dias = options["dias"]
        ahora = timezone.now()
        limite = ahora + timedelta(days=dias)

        certificados = (
            InspectionCertificate.objects.filter(expires_at__gte=ahora, expires_at__lte=limite)
            .select_related("inspection__appointment__vehicle__owner")
        )

        inapp_creadas = 0
        email_creadas = 0
        omitidas = 0

        for cert in certificados:
            try:
                vehicle = cert.inspection.appointment.vehicle
                owner = vehicle.owner
            except Exception:
                continue

            dias_restantes = (cert.expires_at.date() - ahora.date()).days
            titulo = "Tu revisión técnico-mecánica está próxima a vencer"
            mensaje = (
                f"La RTM de tu vehículo {vehicle.plate} "
                f"({vehicle.brand} {vehicle.model_line}) "
                f"vence el {cert.expires_at.strftime('%d/%m/%Y')} "
                f"({dias_restantes} días restantes). "
                "Agenda tu próxima revisión en Checkar CDA."
            )
            contexto = {
                "certificado_id": cert.id,
                "placa": vehicle.plate,
                "dias_restantes": dias_restantes,
            }

            # Notificación in-app
            ya_inapp = Notification.objects.filter(
                user=owner,
                channel="in_app",
                context__certificado_id=cert.id,
                status__in=["pending", "sent"],
            ).exists()

            if not ya_inapp:
                Notification.objects.create(
                    user=owner,
                    title=titulo,
                    message=mensaje,
                    channel="in_app",
                    context=contexto,
                )
                inapp_creadas += 1
            else:
                omitidas += 1

            # Notificación email (solo si el propietario tiene email)
            if owner.email:
                ya_email = Notification.objects.filter(
                    user=owner,
                    channel="email",
                    context__certificado_id=cert.id,
                    status__in=["pending", "sent"],
                ).exists()

                if not ya_email:
                    Notification.objects.create(
                        user=owner,
                        title=titulo,
                        message=mensaje,
                        channel="email",
                        context=contexto,
                    )
                    email_creadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"RTM check ({dias} días): "
                f"{inapp_creadas} notif. in-app creadas, "
                f"{email_creadas} notif. email creadas, "
                f"{omitidas} omitidas (ya existían)."
            )
        )

        if options["send_emails"] and email_creadas > 0:
            from apps.notifications.email_dispatcher import dispatch_pending_emails
            sent, failed = dispatch_pending_emails()
            self.stdout.write(
                self.style.SUCCESS(f"Emails despachados: {sent} enviados, {failed} fallidos.")
            )
