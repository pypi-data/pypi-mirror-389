
import django_filters
from netbox.filtersets import NetBoxModelFilterSet

from netbox_maintenance.models import MaintenanceTypeChoices


class MaintenanceTypeChoicesFilterSet(NetBoxModelFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = MaintenanceTypeChoices
        fields = ("id", "name", "description", "color")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(name__icontains=value) | queryset.filter(description__icontains=value)
