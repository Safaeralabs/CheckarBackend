from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet, BranchViewSet, ScheduleSlotViewSet, ServiceTypeViewSet, TariffViewSet

router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branches")
router.register("services", ServiceTypeViewSet, basename="services")
router.register("tariffs", TariffViewSet, basename="tariffs")
router.register("slots", ScheduleSlotViewSet, basename="slots")
router.register("appointments", AppointmentViewSet, basename="appointments")

urlpatterns = router.urls
