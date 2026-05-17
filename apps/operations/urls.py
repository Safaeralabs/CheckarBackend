from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import SystemLogEntryViewSet, VehicleReceptionViewSet, WalkInView

router = DefaultRouter()
router.register("receptions", VehicleReceptionViewSet, basename="receptions")
router.register("logs", SystemLogEntryViewSet, basename="system-logs")

urlpatterns = [
    path("walk-in/", WalkInView.as_view(), name="walk-in"),
] + router.urls
