from rest_framework import serializers

from .models import SystemLogEntry, VehicleReception


class VehicleReceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleReception
        fields = "__all__"


class SystemLogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemLogEntry
        fields = "__all__"


class WalkInSerializer(serializers.Serializer):
    # Siempre requerido
    plate           = serializers.CharField(max_length=10)
    inspection_type = serializers.ChoiceField(choices=["official", "pre_technical"], default="official")

    # Solo si la placa NO existe en el sistema
    first_name      = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name       = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    document_number = serializers.CharField(max_length=32,  required=False, allow_blank=True, default="")
    phone           = serializers.CharField(max_length=20,  required=False, allow_blank=True, default="")
    email           = serializers.EmailField(required=False, allow_blank=True, default="")

    brand           = serializers.CharField(max_length=80,  required=False, allow_blank=True, default="")
    model_line      = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    model_year      = serializers.IntegerField(min_value=1900, max_value=2030, required=False, default=2020)
    vehicle_type    = serializers.ChoiceField(
        choices=["light", "heavy", "motorcycle"], required=False, default="light"
    )
    fuel_type       = serializers.ChoiceField(
        choices=["gasoline", "diesel", "hybrid", "electric", "gas"], required=False, default="gasoline"
    )
    color             = serializers.CharField(max_length=40,  required=False, allow_blank=True, default="")
    registration_city = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
