from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DashboardSummaryView, GlobalReportViewSet, InspectionReportsView, RTMVencimientoView

router = DefaultRouter()
router.register("global-reports", GlobalReportViewSet, basename="global-reports")

urlpatterns = [
    path("dashboard-summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("rtm-vencimiento/", RTMVencimientoView.as_view(), name="rtm-vencimiento"),
    path("reports/", InspectionReportsView.as_view(), name="inspection-reports"),
]

urlpatterns += router.urls
