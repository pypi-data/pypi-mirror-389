from netbox.api.fields import ContentTypeField
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from netbox_maintenance.api.serializers.maintenance import MaintenanceSerializer
from netbox_maintenance.api.serializers.maintenance_impact_types import (
    MaintenanceImpactTypeChoicesSerializer,
)
from core.models.object_types import ObjectType
from netbox_maintenance.models import MaintenanceImpact


class MaintenanceImpactSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_maintenance-api:maintenanceimpact-detail"
    )
    maintenance = MaintenanceSerializer(nested=True)
    impact = MaintenanceImpactTypeChoicesSerializer(nested=True)
    object_type = ContentTypeField(queryset=ObjectType.objects.all())
    object = serializers.SerializerMethodField(read_only=True)

    def get_object(self, instance):
        """
        Return a representation of the related object (using GenericForeignKey).
        """
        if instance.object:
            return {
                'id': instance.object_id,
                'display': str(instance.object),
                'url': instance.object.get_absolute_url() if hasattr(instance.object, 'get_absolute_url') else None,
            }
        return None

    class Meta:
        model = MaintenanceImpact
        fields = (
            "id",
            "url",
            "display",
            "maintenance",
            "object_type",
            "object_id",
            "object",
            "impact",
            "tags",
            "created",
            "last_updated",
        )
        brief_fields = (
            "id",
            "url",
            "display",
            "maintenance",
            "object_type",
            "object_id",
            "object",
        )
