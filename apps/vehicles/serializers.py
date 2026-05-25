from rest_framework import serializers

from .models import Vehicle
from .validators import validate_plate_format


class VehicleSerializer(serializers.ModelSerializer):
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
