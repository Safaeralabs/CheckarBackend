from rest_framework import serializers

from .models import (
    AxleTirePressure,
    DocumentCheck,
    InspectionCertificate,
    InspectionChecklistItem,
    InspectionPhoto,
    InspectionRecord,
    PreEvaluationItem,
    TirePressureRecord,
)


class DocumentCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCheck
        fields = "__all__"


class PreEvaluationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreEvaluationItem
        fields = "__all__"


class InspectionChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionChecklistItem
        fields = "__all__"


class InspectionPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionPhoto
        fields = "__all__"


class AxleTirePressureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AxleTirePressure
        fields = "__all__"


class TirePressureRecordSerializer(serializers.ModelSerializer):
    axles = AxleTirePressureSerializer(many=True, read_only=True)

    class Meta:
        model = TirePressureRecord
        fields = "__all__"


class InspectionCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionCertificate
        fields = "__all__"


class InspectionRecordSerializer(serializers.ModelSerializer):
    vehicle_plate    = serializers.CharField(source='appointment.vehicle.plate',       read_only=True)
    vehicle_brand    = serializers.CharField(source='appointment.vehicle.brand',       read_only=True)
    vehicle_model    = serializers.CharField(source='appointment.vehicle.model_line',  read_only=True)
    vehicle_year     = serializers.IntegerField(source='appointment.vehicle.model_year', read_only=True)
    vehicle_type     = serializers.CharField(source='appointment.vehicle.vehicle_type', read_only=True)
    customer_name    = serializers.SerializerMethodField()
    certificate_data = InspectionCertificateSerializer(source='certificate', read_only=True)

    def get_customer_name(self, obj):
        c = obj.appointment.customer
        return f"{c.first_name} {c.last_name}".strip() or c.username

    class Meta:
        model = InspectionRecord
        fields = "__all__"
