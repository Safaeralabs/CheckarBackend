from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User


class Command(BaseCommand):
    help = (
        "Resetea la contraseña de un usuario existente (por username) y lo "
        "obliga a definir una nueva la próxima vez que inicie sesión."
    )

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="Username del usuario a resetear")
        parser.add_argument("--password", required=True, help="Contraseña temporal a asignar")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"No existe un usuario con username={username!r}")

        user.set_password(password)
        user.is_active = True
        user.must_change_password = True
        user.save(update_fields=["password", "is_active", "must_change_password"])

        self.stdout.write(self.style.SUCCESS(
            f"[CHECKAR] Contraseña reseteada para '{username}'. "
            f"Deberá definir una nueva contraseña al iniciar sesión."
        ))
