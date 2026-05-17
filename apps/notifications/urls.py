from rest_framework.routers import DefaultRouter

from .views import DeviceSessionViewSet, NotificationViewSet

router = DefaultRouter()
router.register("", NotificationViewSet, basename="notifications")
router.register("devices", DeviceSessionViewSet, basename="device-sessions")

urlpatterns = router.urls
