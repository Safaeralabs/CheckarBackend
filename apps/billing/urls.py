from rest_framework.routers import DefaultRouter

from .views import InvoiceViewSet, PaymentTransactionViewSet

router = DefaultRouter()
router.register("invoices", InvoiceViewSet, basename="invoices")
router.register("transactions", PaymentTransactionViewSet, basename="transactions")

urlpatterns = router.urls
