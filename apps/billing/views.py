from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Invoice, PaymentTransaction
from .serializers import InvoiceSerializer, PaymentTransactionSerializer


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status"]
    search_fields = ["invoice_number", "appointment__vehicle__plate"]

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.select_related("appointment", "appointment__customer")
        if user.role == "customer":
            return queryset.filter(appointment__customer=user).order_by("-created_at")
        return queryset.order_by("-created_at")


class PaymentTransactionViewSet(viewsets.ModelViewSet):
    queryset = PaymentTransaction.objects.select_related("invoice").all().order_by("-created_at")
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["invoice", "status", "provider"]

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        transaction = self.get_object()
        if transaction.status not in {"pending", "authorized"}:
            return Response({"detail": "La transaccion no puede confirmarse desde su estado actual."}, status=status.HTTP_400_BAD_REQUEST)
        transaction.status = "paid"
        transaction.save(update_fields=["status", "updated_at"])
        return Response({"status": transaction.status})
