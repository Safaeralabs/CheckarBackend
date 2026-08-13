from rest_framework.routers import DefaultRouter

from .views import CampaignViewSet, DeviceSessionViewSet, NotificationViewSet

router = DefaultRouter()
router.register("campaigns", CampaignViewSet, basename="campaigns")
router.register("devices", DeviceSessionViewSet, basename="device-sessions")
router.register("", NotificationViewSet, basename="notifications")

urlpatterns = router.urls
