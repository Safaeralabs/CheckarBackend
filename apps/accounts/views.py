from django.db import transaction
from rest_framework import mixins, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import AuditLog, CustomerProfile, OperatorProfile, User
from .permissions import IsAdminUserRole, IsSupervisorOrAbove
from .serializers import (
    AuditLogSerializer,
    ChangePasswordSerializer,
    CreateInternalUserSerializer,
    CustomerProfileSerializer,
    LoginSerializer,
    OperatorProfileSerializer,
    PublicClientRegistrationSerializer,
    RegisterSerializer,
    UpdateInternalUserSerializer,
    UpdateProfileSerializer,
    UserSerializer,
)


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class RegisterView(views.APIView):
    permission_classes = []

    @transaction.atomic
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        AuditLog.objects.create(
            actor=user,
            action="register",
            entity_type="user",
            entity_id=str(user.id),
            metadata={"role": user.role},
            ip_address=_client_ip(request),
        )
        return Response({"token": token.key, "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        AuditLog.objects.create(
            actor=user,
            action="login",
            entity_type="user",
            entity_id=str(user.id),
            metadata={"role": user.role},
            ip_address=_client_ip(request),
        )
        return Response({"token": token.key, "user": UserSerializer(user).data})


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        AuditLog.objects.create(
            actor=request.user,
            action="logout",
            entity_type="user",
            entity_id=str(request.user.id),
            metadata={"role": request.user.role},
            ip_address=_client_ip(request),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": UserSerializer(request.user).data})


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["role", "is_active"]
    search_fields = ["username", "first_name", "last_name", "email", "document_number"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("create", "partial_update", "reset_password", "resend_credentials"):
            return [IsSupervisorOrAbove()]
        if self.action == "destroy":
            return [IsAdminUserRole()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateInternalUserSerializer
        if self.action == "partial_update":
            return UpdateInternalUserSerializer
        return UserSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response(
                {"detail": "No puedes eliminar tu propia cuenta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        import secrets
        from apps.common.emails import send_internal_user_credentials_email
        temp_password = secrets.token_urlsafe(10)
        user = serializer.save(password=temp_password)
        send_internal_user_credentials_email(user, temp_password)

    def get_queryset(self):
        queryset = User.objects.all().order_by("id")
        if self.request.user.role in ("admin", "supervisor"):
            if self.request.query_params.get("internal"):
                return queryset.exclude(role="customer")
            return queryset
        return queryset.filter(id=self.request.user.id)

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        if request.method == "GET":
            return Response(UserSerializer(request.user).data)
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["post"], url_path="me/change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.must_change_password = False
        request.user.save()
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response({"token": token.key})

    @action(detail=True, methods=["post"], url_path="resend-credentials")
    def resend_credentials(self, request, pk=None):
        import secrets as sec
        from apps.common.emails import send_internal_user_credentials_email
        user = self.get_object()
        new_password = sec.token_urlsafe(10)
        user.set_password(new_password)
        user.must_change_password = True
        user.save()
        email_sent = False
        try:
            send_internal_user_credentials_email(user, new_password)
            email_sent = True
        except Exception:
            pass
        return Response({
            "password": new_password,
            "email_sent": email_sent,
            "username": user.username,
        })

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get("new_password", "")
        if len(new_password) < 8:
            return Response({"new_password": ["Mínimo 8 caracteres."]}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        Token.objects.filter(user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CustomerProfile.objects.select_related("user", "preferred_branch")
        if self.request.user.role == "customer":
            return queryset.filter(user=self.request.user)
        return queryset.all()


class OperatorProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OperatorProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = OperatorProfile.objects.select_related("user", "branch")
        if self.request.user.role in {"operator", "inspector", "supervisor"}:
            return queryset.filter(user=self.request.user)
        return queryset.all()


class PublicClientRegistrationView(views.APIView):
    permission_classes = []

    def post(self, request):
        serializer = PublicClientRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        AuditLog.objects.create(
            actor=user,
            action="public_registration",
            entity_type="user",
            entity_id=str(user.id),
            metadata={"role": user.role, "source": "public_link"},
            ip_address=_client_ip(request),
        )
        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class SetupAdminView(views.APIView):
    """
    Endpoint temporal para recrear el admin desde Railway sin necesitar terminal.
    Requiere la cabecera X-Setup-Token igual a la variable de entorno SETUP_TOKEN.
    Eliminar SETUP_TOKEN del entorno para desactivar este endpoint.
    """
    permission_classes = []

    def post(self, request):
        import os, secrets as sec
        expected = os.getenv("SETUP_TOKEN", "")
        if not expected:
            return Response({"detail": "Endpoint desactivado."}, status=status.HTTP_403_FORBIDDEN)
        token = request.headers.get("X-Setup-Token", "")
        if token != expected:
            return Response({"detail": "Token inválido."}, status=status.HTTP_403_FORBIDDEN)

        password = request.data.get("password") or sec.token_urlsafe(12)
        username = request.data.get("username", "admin")
        email    = request.data.get("email", "admin@checkar.co")

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "first_name": "Administrador",
                      "role": "admin", "is_active": True, "must_change_password": True},
        )
        if not created:
            user.role = "admin"
            user.is_active = True
            user.must_change_password = True
        user.set_password(password)
        user.save()

        return Response({
            "created": created,
            "username": user.username,
            "password": password,
            "must_change_password": True,
        }, status=status.HTTP_200_OK)


class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = AuditLog.objects.select_related("actor").all().order_by("-created_at")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUserRole]
    filterset_fields = ["action", "entity_type"]
