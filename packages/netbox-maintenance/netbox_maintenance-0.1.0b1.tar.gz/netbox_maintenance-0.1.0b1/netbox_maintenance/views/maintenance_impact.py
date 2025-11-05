from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.urls import reverse
from netbox.views import generic
from utilities.views import get_action_url, register_model_view

from netbox_maintenance.filtersets import MaintenanceImpactFilterSet
from netbox_maintenance.forms import (
    MaintenanceImpactAddForm,
    MaintenanceImpactBulkEditForm,
    MaintenanceImpactBulkUpdateForm,
    MaintenanceImpactEditForm,
    MaintenanceImpactFilterForm,
)
from netbox_maintenance.models import MaintenanceImpact
from netbox_maintenance.models.maintenance import Maintenance
from netbox_maintenance.tables import MaintenanceImpactTable


@register_model_view(MaintenanceImpact, "list", path="", detail=False)
class MaintenanceImpactListView(generic.ObjectListView):
    queryset = MaintenanceImpact.objects.all()
    table = MaintenanceImpactTable
    filterset = MaintenanceImpactFilterSet
    filterset_form = MaintenanceImpactFilterForm


@register_model_view(MaintenanceImpact)
class MaintenanceImpactView(generic.ObjectView):
    queryset = MaintenanceImpact.objects.all()


@register_model_view(MaintenanceImpact, "add", detail=False)
class MaintenanceImpactAddView(generic.ObjectEditView):
    queryset = MaintenanceImpact.objects.all()
    form = MaintenanceImpactAddForm
    template_name = "netbox_maintenance/maintenanceimpact_add.html"

    def get_extra_addanother_params(self, request):
        """Preserve object_type, object_id, and return_url parameters for 'Add Another' functionality."""
        params = {}
        if request.GET.get("object_type"):
            params["object_type"] = request.GET.get("object_type")
        if request.GET.get("object_id"):
            params["object_id"] = request.GET.get("object_id")
        if request.GET.get("return_url"):
            params["return_url"] = request.GET.get("return_url")
        return params

    def get_return_url(self, request, instance):
        # First, check if return_url was provided in the query parameters
        return_url = request.GET.get("return_url") or request.POST.get("return_url")
        if return_url:
            return return_url

        # Try to get maintenance from instance first
        maintenance = None
        if instance and hasattr(instance, "maintenance"):
            maintenance = instance.maintenance

        # Fallback: get maintenance from POST data if not on instance
        if not maintenance and request.method == "POST":
            maintenance_id = request.POST.get("maintenance")
            if maintenance_id:
                try:
                    maintenance = Maintenance.objects.get(pk=maintenance_id)
                except Maintenance.DoesNotExist:
                    pass

        # If still no maintenance found, return to maintenance list
        if not maintenance:
            return reverse("plugins:netbox_maintenance:maintenance_list")

        # Return to the maintenance detail page
        return get_action_url(maintenance, action=None, kwargs={"pk": maintenance.pk})


@register_model_view(MaintenanceImpact, "edit")
class MaintenanceImpactEditView(generic.ObjectEditView):
    queryset = MaintenanceImpact.objects.all()
    form = MaintenanceImpactEditForm


@register_model_view(MaintenanceImpact, name="bulk_update", path="bulk_update", detail=False)
class MaintenanceImpactBulkUpdateView(generic.ObjectEditView):
    queryset = MaintenanceImpact.objects.all()
    form = MaintenanceImpactBulkUpdateForm
    template_name = "netbox_maintenance/maintenanceimpact_bulk_update.html"

    def alter_object(self, instance, request, args, kwargs):
        instance.maintenance = get_object_or_404(Maintenance, pk=request.GET.get("maintenance"))
        return instance

    def get_extra_context(self, request, instance):
        context = super().get_extra_context(request, instance)

        # Get maintenance from URL parameter
        maintenance_id = request.GET.get("maintenance")
        if maintenance_id:
            maintenance = get_object_or_404(Maintenance, pk=maintenance_id)

            # Get all impacts for this maintenance and count by impact type
            impact_counts = (
                MaintenanceImpact.objects.filter(maintenance=maintenance)
                .values("impact__name")  # Group by impact type name
                .annotate(count=Count("id"))
                .order_by("impact__name")
            )

            # Add to context
            context["maintenance"] = maintenance
            context["impact_type_counts"] = impact_counts

        return context

    def get_extra_addanother_params(self, request):
        return {
            "maintenance": request.GET.get("maintenance"),
        }

    def get_return_url(self, request, instance):
        if not instance.maintenance:
            return reverse("plugins:netbox_maintenance:maintenance")

        obj = instance.maintenance
        return get_action_url(obj, action=None, kwargs={"pk": obj.pk})

        # Add TAB here
        # if return_url.startswith(reverse('ipam:fhrpgroupassignment_add')):
        #    return_url += f'&group={obj.pk}'


@register_model_view(MaintenanceImpact, "delete")
class MaintenanceImpactDeleteView(generic.ObjectDeleteView):
    queryset = MaintenanceImpact.objects.all()


@register_model_view(MaintenanceImpact, "bulk_edit", path="edit", detail=False)
class MaintenanceImpactBulkEditView(generic.BulkEditView):
    queryset = MaintenanceImpact.objects.all()
    filterset = MaintenanceImpactFilterSet
    table = MaintenanceImpactTable
    form = MaintenanceImpactBulkEditForm


@register_model_view(MaintenanceImpact, "bulk_delete", path="delete", detail=False)
class MaintenanceImpactBulkDeleteView(generic.BulkDeleteView):
    queryset = MaintenanceImpact.objects.all()
    filterset = MaintenanceImpactFilterSet
    table = MaintenanceImpactTable


@register_model_view(MaintenanceImpact, "bulk_import", path="import", detail=False)
class MaintenanceImpactBulkImportView(generic.BulkImportView):
    queryset = MaintenanceImpact.objects.all()
    model_form = MaintenanceImpactAddForm
    table = MaintenanceImpactTable
