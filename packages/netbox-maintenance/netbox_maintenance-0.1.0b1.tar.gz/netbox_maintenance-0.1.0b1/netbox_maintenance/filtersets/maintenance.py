import django_filters
from netbox.filtersets import NetBoxModelFilterSet

from netbox_maintenance.models import Maintenance, MaintenanceTypeChoices, MaintenanceImpact


class MaintenanceFilterSet(NetBoxModelFilterSet):
    name = django_filters.CharFilter()
    summary = django_filters.CharFilter()
    status_id = django_filters.ModelMultipleChoiceFilter(
        queryset=MaintenanceTypeChoices.objects.all(),
        label="Status"
    )
    internal_ticket = django_filters.CharFilter()
    acknowledged = django_filters.BooleanFilter()
    start = django_filters.DateTimeFromToRangeFilter()
    end = django_filters.DateTimeFromToRangeFilter()
    object_type_id = django_filters.NumberFilter(method='filter_by_object')
    object_id = django_filters.NumberFilter(method='filter_by_object')

    class Meta:
        model = Maintenance
        fields = ("id", "name", "summary", "status", "internal_ticket", "acknowledged", "object_type_id", "object_id")
    
    def filter_by_object(self, queryset, name, value):
        """Filter maintenances by related object through MaintenanceImpact."""
        if name == 'object_type_id':
            # Store for use with object_id
            self.object_type_id = value
            if hasattr(self, 'object_id'):
                return self._filter_by_both()
            return queryset
        elif name == 'object_id':
            # Store for use with object_type_id
            self.object_id = value
            if hasattr(self, 'object_type_id'):
                return self._filter_by_both()
            return queryset
        return queryset
    
    def _filter_by_both(self):
        """Filter when both object_type_id and object_id are present."""
        # Get maintenances that have impacts on this specific object
        impact_maintenance_ids = MaintenanceImpact.objects.filter(
            object_type_id=self.object_type_id,
            object_id=self.object_id
        ).values_list('maintenance_id', flat=True)
        
        return Maintenance.objects.filter(id__in=impact_maintenance_ids)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            name__icontains=value
        ) | queryset.filter(
            summary__icontains=value
        ) | queryset.filter(
            internal_ticket__icontains=value
        ) | queryset.filter(
            comments__icontains=value
        )
