from netbox.api.metadata import ContentTypeMetadata
from netbox.api.viewsets import NetBoxModelViewSet

from netbox_maintenance.api.serializers import MaintenanceSerializer
from netbox_maintenance.filtersets import MaintenanceFilterSet
from netbox_maintenance.models import Maintenance


class MaintenanceViewSet(NetBoxModelViewSet):
    metadata_class = ContentTypeMetadata
    queryset = Maintenance.objects.all()
    serializer_class = MaintenanceSerializer
    filterset_class = MaintenanceFilterSet
