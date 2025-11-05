import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from netbox_maintenance.models import Maintenance

ADD_IMPACT_BUTTON = """
{% if perms.netbox_maintenance.add_maintenanceimpact %}
<a href="{% url 'plugins:netbox_maintenance:maintenanceimpact_bulk_update' %}?maintenance={{ record.pk }}&return_url={{ request.path }}" class="btn btn-sm btn-indigo" title="BulkUpdate AssignedObjects">
    <i class="mdi mdi-pencil-box-multiple"></i>
</a>
{% endif %}
"""


class MaintenanceTable(NetBoxTable):
    name = tables.Column(linkify=True)
    status = tables.Column(linkify=True)
    start = columns.DateTimeColumn()
    end = columns.DateTimeColumn()
    acknowledged = columns.BooleanColumn()
    tags = columns.TagColumn()

    actions = columns.ActionsColumn(extra_buttons=ADD_IMPACT_BUTTON, split_actions=True)

    class Meta(NetBoxTable.Meta):
        model = Maintenance
        fields = (
            "pk",
            "id",
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
            "actions",
        )
        default_columns = (
            "name",
            "summary",
            "status",
            "start",
            "end",
            "acknowledged",
        )
