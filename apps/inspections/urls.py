from rest_framework.routers import DefaultRouter

from .views import (
    AxleTirePressureViewSet,
    DocumentCheckViewSet,
    InspectionCertificateViewSet,
    InspectionChecklistItemViewSet,
    InspectionPhotoViewSet,
    InspectionRecordViewSet,
    PreEvaluationItemViewSet,
    TirePressureRecordViewSet,
)

router = DefaultRouter()
router.register("records", InspectionRecordViewSet, basename="inspection-records")
router.register("documents", DocumentCheckViewSet, basename="inspection-documents")
router.register("pre-evaluation", PreEvaluationItemViewSet, basename="inspection-pre-evaluation")
router.register("checklist", InspectionChecklistItemViewSet, basename="inspection-checklist")
router.register("photos", InspectionPhotoViewSet, basename="inspection-photos")
router.register("tire-pressure", TirePressureRecordViewSet, basename="inspection-tire-pressure")
router.register("tire-pressure-axles", AxleTirePressureViewSet, basename="inspection-tire-pressure-axles")
router.register("certificates", InspectionCertificateViewSet, basename="inspection-certificates")

urlpatterns = router.urls
