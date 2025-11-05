from netbox.views import generic
from utilities.views import register_model_view

from netbox_maintenance.filtersets import MaintenanceTypeChoicesFilterSet
from netbox_maintenance.forms import MaintenanceTypeChoicesFilterForm, MaintenanceTypeChoicesForm
from netbox_maintenance.models import MaintenanceTypeChoices
from netbox_maintenance.tables import MaintenanceTypeChoicesTable


@register_model_view(MaintenanceTypeChoices, "list", path="", detail=False)
class MaintenanceTypeChoicesListView(generic.ObjectListView):
    queryset = MaintenanceTypeChoices.objects.all()
    table = MaintenanceTypeChoicesTable
    filterset = MaintenanceTypeChoicesFilterSet
    filterset_form = MaintenanceTypeChoicesFilterForm


@register_model_view(MaintenanceTypeChoices)
class MaintenanceTypeChoicesView(generic.ObjectView):
    queryset = MaintenanceTypeChoices.objects.all()


@register_model_view(MaintenanceTypeChoices, "add", detail=False)
@register_model_view(MaintenanceTypeChoices, "edit")
class MaintenanceTypeChoicesEditView(generic.ObjectEditView):
    queryset = MaintenanceTypeChoices.objects.all()
    form = MaintenanceTypeChoicesForm


@register_model_view(MaintenanceTypeChoices, "delete")
class MaintenanceTypeChoicesDeleteView(generic.ObjectDeleteView):
    queryset = MaintenanceTypeChoices.objects.all()


@register_model_view(MaintenanceTypeChoices, "bulk_delete", path="delete", detail=False)
class MaintenanceTypeChoicesBulkDeleteView(generic.BulkDeleteView):
    queryset = MaintenanceTypeChoices.objects.all()
    filterset = MaintenanceTypeChoicesFilterSet
    table = MaintenanceTypeChoicesTable


@register_model_view(MaintenanceTypeChoices, "bulk_import", path="import", detail=False)
class MaintenanceTypeChoicesBulkImportView(generic.BulkImportView):
    queryset = MaintenanceTypeChoices.objects.all()
    model_form = MaintenanceTypeChoicesForm
    table = MaintenanceTypeChoicesTable
