from netbox.api.metadata import ContentTypeMetadata
from netbox.api.viewsets import NetBoxModelViewSet

from netbox_maintenance.api.serializers import MaintenanceImpactSerializer
from netbox_maintenance.filtersets import MaintenanceImpactFilterSet
from netbox_maintenance.models import MaintenanceImpact


class MaintenanceImpactViewSet(NetBoxModelViewSet):
    metadata_class = ContentTypeMetadata
    queryset = MaintenanceImpact.objects.all()
    serializer_class = MaintenanceImpactSerializer
    filterset_class = MaintenanceImpactFilterSet
