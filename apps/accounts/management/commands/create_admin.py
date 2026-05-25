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
        username   = options["username"]
        email      = options["email"]
        password   = options["password"] or secrets.token_urlsafe(12)
        first_name = options["first_name"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": "",
                "role": RoleChoices.ADMIN,
                "is_active": True,
                "must_change_password": True,
            },
        )

        if not created:
            # Si ya existía, solo resetea la contraseña y lo reactiva
            user.role = RoleChoices.ADMIN
            user.is_active = True
            user.must_change_password = True
            user.save(update_fields=["role", "is_active", "must_change_password"])

        user.set_password(password)
        user.save(update_fields=["password"])

        action = "Creado" if created else "Reseteado"
        self.stdout.write(self.style.SUCCESS(
            f"{action} admin:\n"
            f"  Usuario:    {username}\n"
            f"  Contraseña: {password}\n"
            f"  Email:      {email}\n"
            f"  (deberá cambiar la contraseña en el primer login)"
        ))
