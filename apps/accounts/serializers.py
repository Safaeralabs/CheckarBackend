import re

from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers

from .models import AuditLog, CustomerProfile, OperatorProfile, RoleChoices, User


# ── Shared validators (reutilizados en todos los serializers) ─────────────────

_PHONE_RE = re.compile(r"^[+\d][\d\s\-(). ]*$")


def _validate_email_unique(value: str, exclude_pk=None) -> str:
    if not value:
        return value
    qs = User.objects.filter(email__iexact=value)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise serializers.ValidationError("Este correo electrónico ya está registrado.")
    return value.lower()


def _validate_phone(value: str, exclude_pk=None) -> str:
    value = value.strip()
    if not value:
        return value
    if not _PHONE_RE.match(value):
        raise serializers.ValidationError(
            "Teléfono inválido. Use solo dígitos, espacios, guiones o el prefijo +."
        )
    digits = re.sub(r"[^\d]", "", value.lstrip("+"))
    if not (7 <= len(digits) <= 15):
        raise serializers.ValidationError(
            "El número de teléfono debe tener entre 7 y 15 dígitos."
        )
    qs = User.objects.filter(phone=value)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise serializers.ValidationError("Este número de teléfono ya está registrado.")
    return value


# ── Serializers ───────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "phone",
            "document_number",
            "email_verified",
            "mobile_notifications_enabled",
            "must_change_password",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    address = serializers.CharField(source="customer_profile.address", required=False, allow_blank=True)
    city = serializers.CharField(source="customer_profile.city", required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone",
            "document_number",
            "role",
            "address",
            "city",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.scheduling.models import Branch

        self.fields["preferred_branch"] = serializers.PrimaryKeyRelatedField(
            source="customer_profile.preferred_branch",
            queryset=Branch.objects.filter(is_active=True),
            required=False,
            allow_null=True,
        )

    def validate_role(self, value):
        if value != RoleChoices.CUSTOMER:
            raise serializers.ValidationError("Solo se permite auto registro para clientes.")
        return value

    def validate_email(self, value):
        return _validate_email_unique(value)

    def validate_phone(self, value):
        return _validate_phone(value)

    def create(self, validated_data):
        profile_data = validated_data.pop("customer_profile", {})
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        CustomerProfile.objects.create(user=user, **profile_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Credenciales invalidas.")
        if not user.is_active:
            raise serializers.ValidationError("Usuario inactivo.")
        attrs["user"] = user
        return attrs


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ["id", "user", "address", "city", "preferred_branch", "created_at", "updated_at"]


class OperatorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OperatorProfile
        fields = [
            "id",
            "user",
            "employee_code",
            "branch",
            "can_validate_documents",
            "can_release_certificate",
            "created_at",
            "updated_at",
        ]


_INTERNAL_ROLES = ["operator", "supervisor", "admin"]


class CreateInternalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "document_number", "role"]

    def validate_role(self, value):
        # Permite "inspector" solo para usuarios existentes (backward compat)
        if value not in [*_INTERNAL_ROLES, "inspector"]:
            raise serializers.ValidationError("Rol no permitido para usuarios internos.")
        return value

    def validate_email(self, value):
        return _validate_email_unique(value)

    def validate_phone(self, value):
        return _validate_phone(value)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, must_change_password=True, **validated_data)
        return user


class UpdateInternalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "document_number", "role", "is_active"]

    def validate_role(self, value):
        if value not in _INTERNAL_ROLES:
            raise serializers.ValidationError("Rol no permitido para usuarios internos.")
        return value

    def validate_email(self, value):
        pk = self.instance.pk if self.instance else None
        return _validate_email_unique(value, exclude_pk=pk)

    def validate_phone(self, value):
        pk = self.instance.pk if self.instance else None
        return _validate_phone(value, exclude_pk=pk)


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "document_number"]

    def validate_email(self, value):
        pk = self.instance.pk if self.instance else None
        return _validate_email_unique(value, exclude_pk=pk)

    def validate_phone(self, value):
        pk = self.instance.pk if self.instance else None
        return _validate_phone(value, exclude_pk=pk)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Contraseña actual incorrecta.")
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"


class VehicleForRegistrationSerializer(serializers.Serializer):
    plate = serializers.CharField(max_length=10)
    brand = serializers.CharField(max_length=80)
    model_line = serializers.CharField(max_length=120)
    model_year = serializers.IntegerField(min_value=1900, max_value=2030)
    vehicle_type = serializers.ChoiceField(choices=[("light", "Liviano"), ("heavy", "Pesado"), ("motorcycle", "Motocicleta")])
    fuel_type = serializers.ChoiceField(choices=[("gasoline", "Gasolina"), ("diesel", "Diesel"), ("hybrid", "Hibrido"), ("electric", "Electrico"), ("gas", "Gas")])
    color = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")
    registration_city = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")

    def validate_plate(self, value):
        from apps.vehicles.models import Vehicle
        from apps.vehicles.validators import validate_plate_format
        value = validate_plate_format(value)
        if Vehicle.objects.filter(plate=value).exists():
            raise serializers.ValidationError("Esta placa ya está registrada en el sistema.")
        return value


class PublicClientRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    document_number = serializers.CharField(max_length=32)
    password = serializers.CharField(min_length=8, write_only=True)
    vehicle = VehicleForRegistrationSerializer()

    def validate_email(self, value):
        return _validate_email_unique(value)

    def validate_phone(self, value):
        return _validate_phone(value)

    @transaction.atomic
    def create(self, validated_data):
        from apps.vehicles.models import Vehicle
        vehicle_data = validated_data.pop("vehicle")
        password = validated_data.pop("password")
        doc = validated_data["document_number"]
        user = User.objects.create_user(
            username=doc,
            role=RoleChoices.CUSTOMER,
            password=password,
            **validated_data,
        )
        CustomerProfile.objects.create(user=user)
        Vehicle.objects.create(owner=user, **vehicle_data)
        return user
