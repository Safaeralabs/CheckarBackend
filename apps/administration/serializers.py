from rest_framework import serializers

from .models import GlobalReport


class GlobalReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalReport
        fields = "__all__"
