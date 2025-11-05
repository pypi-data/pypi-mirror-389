from netbox.api.metadata import ContentTypeMetadata
from netbox.api.viewsets import NetBoxModelViewSet

from netbox_maintenance.api.serializers import MaintenanceTypeChoicesSerializer
from netbox_maintenance.filtersets import MaintenanceTypeChoicesFilterSet
from netbox_maintenance.models import MaintenanceTypeChoices


class MaintenanceTypeChoicesViewSet(NetBoxModelViewSet):
    metadata_class = ContentTypeMetadata
    queryset = MaintenanceTypeChoices.objects.all()
    serializer_class = MaintenanceTypeChoicesSerializer
    filterset_class = MaintenanceTypeChoicesFilterSet
