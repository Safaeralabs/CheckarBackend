from rest_framework import serializers

from .models import Vehicle
from .validators import validate_plate_format


class VehicleSerializer(serializers.ModelSerializer):
    owner_detail = serializers.SerializerMethodField(read_only=True)

    def get_owner_detail(self, obj):
        o = obj.owner
        if not o: return None
        return {
            "id": o.id,
            "first_name": o.first_name,
            "last_name": o.last_name,
            "email": o.email,
            "phone": o.phone,
            "document_number": o.document_number,
        }

    class Meta:
        model = Vehicle
        fields = "__all__"
        read_only_fields = ["owner", "created_at", "updated_at"]

    def validate_plate(self, value):
        value = validate_plate_format(value)
        pk = self.instance.pk if self.instance else None
        qs = Vehicle.objects.filter(plate=value)
        if pk:
            qs = qs.exclude(pk=pk)
        if qs.exists():
            raise serializers.ValidationError("Esta placa ya está registrada en el sistema.")
        return value
