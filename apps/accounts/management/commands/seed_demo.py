from django.core.management.base import BaseCommand
from django.db import transaction


USERS = [
    {
        "username": "admin",
        "password": "checkar123",
        "first_name": "Admin",
        "last_name": "Checkar",
        "email": "admin@checkar.co",
        "role": "admin",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "username": "supervisor1",
        "password": "checkar123",
        "first_name": "Carlos",
        "last_name": "Medina",
        "email": "supervisor@checkar.co",
        "role": "supervisor",
    },
    {
        "username": "operador1",
        "password": "checkar123",
        "first_name": "Luis",
        "last_name": "García",
        "email": "operador@checkar.co",
        "role": "operator",
    },
    {
        "username": "inspector1",
        "password": "checkar123",
        "first_name": "Juan",
        "last_name": "Pérez",
        "email": "inspector@checkar.co",
        "role": "inspector",
    },
    {
        "username": "cliente1",
        "password": "checkar123",
        "first_name": "María",
        "last_name": "López",
        "email": "cliente@checkar.co",
        "role": "customer",
    },
]

BRANCH = {
    "code": "CDA-RCH-01",
    "name": "Checkar CDA Riohacha",
    "city": "Riohacha",
    "address": "Calle 15 No. 12B-44",
    "phone": "3001234567",
    "opens_at": "07:00",
    "closes_at": "17:00",
}


class Command(BaseCommand):
    help = "Crea usuarios y sucursal demo si no existen (idempotente)"

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.accounts.models import User
        from apps.scheduling.models import Branch

        created_users = 0
        for data in USERS:
            if User.objects.filter(username=data["username"]).exists():
                continue
            User.objects.create_user(
                username=data["username"],
                password=data["password"],
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                email=data.get("email", ""),
                role=data["role"],
                is_staff=data.get("is_staff", False),
                is_superuser=data.get("is_superuser", False),
            )
            created_users += 1

        branch_created = False
        if not Branch.objects.filter(code=BRANCH["code"]).exists():
            Branch.objects.create(**{**BRANCH, "opens_at": "07:00:00", "closes_at": "17:00:00"})
            branch_created = True

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_demo: {created_users} usuario(s) creado(s), "
                f"sucursal {'creada' if branch_created else 'ya existía'}."
            )
        )
