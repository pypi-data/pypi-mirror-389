import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from netbox_maintenance.models import MaintenanceImpactTypeChoices


class MaintenanceImpactTypeChoicesTable(NetBoxTable):
    name = tables.Column(linkify=True)
    color = columns.ColorColumn()

    class Meta(NetBoxTable.Meta):
        model = MaintenanceImpactTypeChoices
        fields = (
            "pk",
            "id",
            "name",
            "description",
            "color",
            "actions",
        )
        default_columns = ("name", "description", "color")
