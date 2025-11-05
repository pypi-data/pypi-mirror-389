from django.urls import include, path
from utilities.urls import get_model_urls

# Import views to ensure @register_model_view decorators are executed
# This is necessary because get_model_urls relies on views being registered first
from . import views  # noqa: F401


urlpatterns = (
    # MaintenanceTypeChoices views
    path(
        "maintenance-types/",
        include(get_model_urls("netbox_maintenance", "maintenancetypechoices", detail=False)),
    ),
    path(
        "maintenance-types/<int:pk>/",
        include(get_model_urls("netbox_maintenance", "maintenancetypechoices")),
    ),
    # MaintenanceImpactTypeChoices views
    path(
        "maintenance-impact-types/",
        include(get_model_urls("netbox_maintenance", "maintenanceimpacttypechoices", detail=False)),
    ),
    path(
        "maintenance-impact-types/<int:pk>/",
        include(get_model_urls("netbox_maintenance", "maintenanceimpacttypechoices")),
    ),
    # Maintenance views
    path(
        "maintenances/",
        include(get_model_urls("netbox_maintenance", "maintenance", detail=False)),
    ),
    path(
        "maintenances/<int:pk>/",
        include(get_model_urls("netbox_maintenance", "maintenance")),
    ),
    # MaintenanceImpact views
    path(
        "maintenance-impacts/",
        include(get_model_urls("netbox_maintenance", "maintenanceimpact", detail=False)),
    ),
    path(
        "maintenance-impacts/<int:pk>/",
        include(get_model_urls("netbox_maintenance", "maintenanceimpact")),
    ),
)
