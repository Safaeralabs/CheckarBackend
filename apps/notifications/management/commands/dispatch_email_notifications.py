from django.core.management.base import BaseCommand

from apps.notifications.email_dispatcher import dispatch_pending_emails


class Command(BaseCommand):
    help = "Envía los correos electrónicos pendientes en la cola de notificaciones."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch",
            type=int,
            default=50,
            help="Máximo de emails a procesar en esta ejecución (default: 50).",
        )

    def handle(self, *args, **options):
        sent, failed = dispatch_pending_emails(batch_size=options["batch"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Despacho de emails: {sent} enviados, {failed} fallidos."
            )
        )
