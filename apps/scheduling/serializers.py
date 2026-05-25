from rest_framework import serializers

from .models import Appointment, Branch, ScheduleSlot, ServiceType, Tariff


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = "__all__"


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = "__all__"


class ScheduleSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleSlot
        fields = "__all__"


class AppointmentSerializer(serializers.ModelSerializer):
    vehicle_detail  = serializers.SerializerMethodField(read_only=True)
    service_detail  = serializers.SerializerMethodField(read_only=True)
    branch_detail   = serializers.SerializerMethodField(read_only=True)

    def get_vehicle_detail(self, obj):
        v = obj.vehicle
        if not v: return None
        return {"id": v.id, "plate": v.plate, "brand": v.brand, "model_line": v.model_line,
                "model_year": v.model_year, "vehicle_type": v.vehicle_type, "fuel_type": v.fuel_type}

    def get_service_detail(self, obj):
        s = obj.service
        if not s: return None
        return {"id": s.id, "name": s.name, "code": s.code}

    def get_branch_detail(self, obj):
        b = obj.branch
        if not b: return None
        return {"id": b.id, "name": b.name, "city": b.city}

    customer_detail       = serializers.SerializerMethodField(read_only=True)
    inspection_record     = serializers.SerializerMethodField(read_only=True)

    def get_customer_detail(self, obj):
        c = obj.customer
        if not c: return None
        return {"id": c.id, "first_name": c.first_name, "last_name": c.last_name,
                "document_number": c.document_number, "phone": c.phone, "email": c.email}

    def get_inspection_record(self, obj):
        try:
            return obj.inspection_record.id
        except Exception:
            return None

    class Meta:
        model = Appointment
        fields = "__all__"
        read_only_fields = ["customer", "status", "payment_status", "source_channel", "created_at", "updated_at"]
