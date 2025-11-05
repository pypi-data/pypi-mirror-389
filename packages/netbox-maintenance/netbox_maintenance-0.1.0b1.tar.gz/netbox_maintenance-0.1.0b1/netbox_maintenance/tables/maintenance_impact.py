import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from netbox_maintenance.models import MaintenanceImpact


class MaintenanceImpactTable(NetBoxTable):
    maintenance = tables.Column(linkify=True)
    impact = tables.Column(linkify=True)
    object_type = columns.ContentTypeColumn()
    object = tables.Column(linkify=True, accessor="object", orderable=False)

    class Meta(NetBoxTable.Meta):
        model = MaintenanceImpact
        fields = (
            "pk",
            "id",
            "maintenance",
            "object_type",
            "object",
            "impact",
            "created",
            "last_updated",
            "actions",
        )
        default_columns = (
            "maintenance",
            "object_type",
            "object",
            "impact",
        )
