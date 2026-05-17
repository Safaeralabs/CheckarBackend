from django.db import models

from apps.common.models import TimeStampedModel


class GlobalReport(TimeStampedModel):
    name = models.CharField(max_length=120)
    report_type = models.CharField(max_length=60)
    generated_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    file = models.FileField(upload_to="global_reports/", null=True, blank=True)
