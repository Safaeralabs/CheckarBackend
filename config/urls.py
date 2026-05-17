from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/vehicles/", include("apps.vehicles.urls")),
    path("api/scheduling/", include("apps.scheduling.urls")),
    path("api/inspections/", include("apps.inspections.urls")),
    path("api/billing/", include("apps.billing.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/operations/", include("apps.operations.urls")),
    path("api/admin-panel/", include("apps.administration.urls")),
]
