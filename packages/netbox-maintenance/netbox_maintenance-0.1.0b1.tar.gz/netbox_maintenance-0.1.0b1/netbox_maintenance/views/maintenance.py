from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from netbox_maintenance.filtersets import MaintenanceFilterSet, MaintenanceImpactFilterSet
from netbox_maintenance.forms import MaintenanceBulkEditForm, MaintenanceFilterForm, MaintenanceForm
from netbox_maintenance.models import Maintenance, MaintenanceImpact
from netbox_maintenance.tables import MaintenanceImpactTable, MaintenanceTable


@register_model_view(Maintenance, "list", path="", detail=False)
class MaintenanceListView(generic.ObjectListView):
    queryset = Maintenance.objects.all()
    table = MaintenanceTable
    filterset = MaintenanceFilterSet
    filterset_form = MaintenanceFilterForm


@register_model_view(Maintenance)
class MaintenanceView(generic.ObjectView):
    queryset = Maintenance.objects.all()


@register_model_view(Maintenance, name="impacts", path="impacts")
class MaintenanceImpactsView(generic.ObjectChildrenView):
    """Custom maintenance view that displays maintenance impacts as a tab."""

    queryset = Maintenance.objects.all()
    child_model = MaintenanceImpact
    table = MaintenanceImpactTable
    filterset = MaintenanceImpactFilterSet
    template_name = "netbox_maintenance/maintenance_impact_list.html"
    hide_if_empty = False
    tab = ViewTab(
        label="Impacts",
        badge=lambda obj: obj.impacts.count(),
        permission="netbox_maintenance.view_maintenanceimpact",
    )

    def get_children(self, request, parent):
        """Get impacts related to this maintenance."""
        return MaintenanceImpact.objects.filter(maintenance=parent)


@register_model_view(Maintenance, "add", detail=False)
@register_model_view(Maintenance, "edit")
class MaintenanceEditView(generic.ObjectEditView):
    queryset = Maintenance.objects.all()
    form = MaintenanceForm


@register_model_view(Maintenance, "delete")
class MaintenanceDeleteView(generic.ObjectDeleteView):
    queryset = Maintenance.objects.all()


@register_model_view(Maintenance, "bulk_edit", path="edit", detail=False)
class MaintenanceBulkEditView(generic.BulkEditView):
    queryset = Maintenance.objects.all()
    filterset = MaintenanceFilterSet
    table = MaintenanceTable
    form = MaintenanceBulkEditForm


@register_model_view(Maintenance, "bulk_delete", path="delete", detail=False)
class MaintenanceBulkDeleteView(generic.BulkDeleteView):
    queryset = Maintenance.objects.all()
    filterset = MaintenanceFilterSet
    table = MaintenanceTable


@register_model_view(Maintenance, "bulk_import", path="import", detail=False)
class MaintenanceBulkImportView(generic.BulkImportView):
    queryset = Maintenance.objects.all()
    model_form = MaintenanceForm
    table = MaintenanceTable
