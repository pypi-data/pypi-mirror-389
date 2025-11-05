from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from netbox_maintenance.api.serializers.maintenance_types import MaintenanceTypeChoicesSerializer
from netbox_maintenance.models import Maintenance


class MaintenanceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_maintenance-api:maintenance-detail"
    )
    status = MaintenanceTypeChoicesSerializer(nested=True)

    class Meta:
        model = Maintenance
        fields = (
            "id",
            "url",
            "display",
            "name",
            "summary",
            "status",
            "start",
            "end",
            "internal_ticket",
            "acknowledged",
            "comments",
            "tags",
            "created",
            "last_updated",
        )
        brief_fields = (
            "id",
            "url",
            "display",
            "name",
            "summary",
            "status",
        )
