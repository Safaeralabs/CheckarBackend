from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["vehicle_type", "fuel_type", "service_category", "is_active", "plate"]
    search_fields = ["plate", "brand", "model_line", "vin", "engine_number"]

    def get_queryset(self):
        user = self.request.user
        if user.role == "customer":
            return Vehicle.objects.filter(owner=user).order_by("-created_at")
        return Vehicle.objects.select_related("owner").all().order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
