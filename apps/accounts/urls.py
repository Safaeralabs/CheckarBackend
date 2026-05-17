from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditLogViewSet,
    CustomerProfileViewSet,
    LoginView,
    LogoutView,
    OperatorProfileViewSet,
    PublicClientRegistrationView,
    RegisterView,
    SessionView,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("customers", CustomerProfileViewSet, basename="customers")
router.register("operators", OperatorProfileViewSet, basename="operators")
router.register("audit-logs", AuditLogViewSet, basename="audit-logs")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("registro-publico/", PublicClientRegistrationView.as_view(), name="registro-publico"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("session/", SessionView.as_view(), name="session"),
]

urlpatterns += router.urls
