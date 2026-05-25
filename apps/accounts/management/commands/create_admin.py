import secrets

from django.core.management.base import BaseCommand

from apps.accounts.models import RoleChoices, User


class Command(BaseCommand):
    help = "Crea o resetea el usuario administrador principal."

    def add_arguments(self, parser):
        parser.add_argument("--username",  default="admin",          help="Nombre de usuario (default: admin)")
        parser.add_argument("--email",     default="admin@checkar.co", help="Correo del admin")
        parser.add_argument("--password",  default=None,             help="Contraseña (se genera automáticamente si se omite)")
        parser.add_argument("--first-name", default="Administrador", dest="first_name")

    def handle(self, *args, **options):
        # Si ya hay un admin activo, no toca nada
        if User.objects.filter(role=RoleChoices.ADMIN, is_active=True).exists():
            self.stdout.write("Admin activo ya existe — sin cambios.")
            return

        username   = options["username"]
        email      = options["email"]
        password   = options["password"] or "checkar123"
        first_name = options["first_name"]

        # Puede existir inactivo (borrado desde el panel)
        user = User.objects.filter(role=RoleChoices.ADMIN).first() \
            or User.objects.filter(username=username).first()

        if user:
            user.role = RoleChoices.ADMIN
            user.is_active = True
            user.must_change_password = False
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"[CHECKAR] Admin reactivado:\n"
                f"  Usuario:    {user.username}\n"
                f"  Contraseña: {password}"
            ))
        else:
            user = User.objects.create_user(
                username=username, email=email, first_name=first_name,
                last_name="", role=RoleChoices.ADMIN,
                is_active=True, must_change_password=False,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(
                f"[CHECKAR] Admin creado:\n"
                f"  Usuario:    {username}\n"
                f"  Contraseña: {password}"
            ))
