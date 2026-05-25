from django.db import transaction
from rest_framework import mixins, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import AuditLog, CustomerProfile, OperatorProfile, User
from .permissions import IsAdminUserRole
from .serializers import (
    AuditLogSerializer,
    ChangePasswordSerializer,
    CustomerProfileSerializer,
    LoginSerializer,
    OperatorProfileSerializer,
    PublicClientRegistrationSerializer,
    RegisterSerializer,
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


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["role", "is_active"]
    search_fields = ["username", "first_name", "last_name", "email", "document_number"]

    def get_queryset(self):
        queryset = User.objects.all().order_by("id")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(id=self.request.user.id)

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        if request.method == "GET":
            return Response(self.get_serializer(request.user).data)
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["post"], url_path="me/change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response({"token": token.key})


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


class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = AuditLog.objects.select_related("actor").all().order_by("-created_at")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUserRole]
    filterset_fields = ["action", "entity_type"]
