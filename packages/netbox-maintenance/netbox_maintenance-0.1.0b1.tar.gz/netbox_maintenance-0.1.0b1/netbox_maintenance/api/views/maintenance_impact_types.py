from netbox.api.metadata import ContentTypeMetadata
from netbox.api.viewsets import NetBoxModelViewSet

from netbox_maintenance.api.serializers import MaintenanceImpactTypeChoicesSerializer
from netbox_maintenance.filtersets import MaintenanceImpactTypeChoicesFilterSet
from netbox_maintenance.models import MaintenanceImpactTypeChoices


class MaintenanceImpactTypeChoicesViewSet(NetBoxModelViewSet):
    metadata_class = ContentTypeMetadata
    queryset = MaintenanceImpactTypeChoices.objects.all()
    serializer_class = MaintenanceImpactTypeChoicesSerializer
    filterset_class = MaintenanceImpactTypeChoicesFilterSet
