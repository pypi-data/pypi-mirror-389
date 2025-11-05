import django_filters
from django.contrib.contenttypes.models import ContentType
from netbox.filtersets import NetBoxModelFilterSet

from netbox_maintenance.models import Maintenance, MaintenanceImpact, MaintenanceImpactTypeChoices


class MaintenanceImpactFilterSet(NetBoxModelFilterSet):
    maintenance_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Maintenance.objects.all(),
        label="Maintenance"
    )
    impact_id = django_filters.ModelMultipleChoiceFilter(
        queryset=MaintenanceImpactTypeChoices.objects.all(),
        label="Impact Type"
    )
    object_type_id = django_filters.ModelMultipleChoiceFilter(
        queryset=ContentType.objects.all(),
        label="Object Type"
    )

    class Meta:
        model = MaintenanceImpact
        fields = ("id", "maintenance", "impact", "object_type", "object_id")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(maintenance__name__icontains=value)
