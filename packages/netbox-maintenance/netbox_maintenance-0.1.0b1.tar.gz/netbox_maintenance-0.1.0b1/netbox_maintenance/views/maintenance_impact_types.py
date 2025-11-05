from netbox.views import generic
from utilities.views import register_model_view

from netbox_maintenance.filtersets import MaintenanceImpactTypeChoicesFilterSet
from netbox_maintenance.forms import (
    MaintenanceImpactTypeChoicesFilterForm,
    MaintenanceImpactTypeChoicesForm,
)
from netbox_maintenance.models import MaintenanceImpactTypeChoices
from netbox_maintenance.tables import MaintenanceImpactTypeChoicesTable


@register_model_view(MaintenanceImpactTypeChoices, "list", path="", detail=False)
class MaintenanceImpactTypeChoicesListView(generic.ObjectListView):
    queryset = MaintenanceImpactTypeChoices.objects.all()
    table = MaintenanceImpactTypeChoicesTable
    filterset = MaintenanceImpactTypeChoicesFilterSet
    filterset_form = MaintenanceImpactTypeChoicesFilterForm


@register_model_view(MaintenanceImpactTypeChoices)
class MaintenanceImpactTypeChoicesView(generic.ObjectView):
    queryset = MaintenanceImpactTypeChoices.objects.all()


@register_model_view(MaintenanceImpactTypeChoices, "add", detail=False)
@register_model_view(MaintenanceImpactTypeChoices, "edit")
class MaintenanceImpactTypeChoicesEditView(generic.ObjectEditView):
    queryset = MaintenanceImpactTypeChoices.objects.all()
    form = MaintenanceImpactTypeChoicesForm


@register_model_view(MaintenanceImpactTypeChoices, "delete")
class MaintenanceImpactTypeChoicesDeleteView(generic.ObjectDeleteView):
    queryset = MaintenanceImpactTypeChoices.objects.all()


@register_model_view(MaintenanceImpactTypeChoices, "bulk_delete", path="delete", detail=False)
class MaintenanceImpactTypeChoicesBulkDeleteView(generic.BulkDeleteView):
    queryset = MaintenanceImpactTypeChoices.objects.all()
    filterset = MaintenanceImpactTypeChoicesFilterSet
    table = MaintenanceImpactTypeChoicesTable


@register_model_view(MaintenanceImpactTypeChoices, "bulk_import", path="import", detail=False)
class MaintenanceImpactTypeChoicesBulkImportView(generic.BulkImportView):
    queryset = MaintenanceImpactTypeChoices.objects.all()
    model_form = MaintenanceImpactTypeChoicesForm
    table = MaintenanceImpactTypeChoicesTable
