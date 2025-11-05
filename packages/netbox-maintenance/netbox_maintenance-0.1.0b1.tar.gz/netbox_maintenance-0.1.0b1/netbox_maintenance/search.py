from netbox.search import SearchIndex

from .models import Maintenance, MaintenanceImpact


class MaintenanceIndex(SearchIndex):
    model = Maintenance
    fields = (
        ("name", 100),
        ("summary", 200),
        ("internal_ticket", 300),
        ("comments", 5000),
    )


class MaintenanceImpactIndex(SearchIndex):
    model = MaintenanceImpact
    fields = ()  # No searchable text fields on this model
    display_attrs = ("maintenance", "impact", "object_type")


indexes = [MaintenanceIndex, MaintenanceImpactIndex]
