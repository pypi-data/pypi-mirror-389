from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from netbox_maintenance.models import MaintenanceTypeChoices


class MaintenanceTypeChoicesSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_maintenance-api:maintenancetypechoices-detail"
    )

    class Meta:
        model = MaintenanceTypeChoices
        fields = (
            "id",
            "url",
            "display",
            "name",
            "description",
            "color",
            "tags",
            "created",
            "last_updated",
        )
        brief_fields = (
            "id",
            "url",
            "display",
            "name",
        )
