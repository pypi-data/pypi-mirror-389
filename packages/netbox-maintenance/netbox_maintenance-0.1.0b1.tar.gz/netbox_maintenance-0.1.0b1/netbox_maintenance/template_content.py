"""Template content extensions for NetBox Maintenance Plugin."""

import logging
from typing import List, Type

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.db.utils import OperationalError
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from netbox_maintenance.models import Maintenance, MaintenanceImpact
from netbox_maintenance.tables.maintenance import MaintenanceTable

logger = logging.getLogger(__name__)

# Get plugin settings
PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netbox_maintenance", {})


def register_maintenance_tab_view(model: Type[Model]) -> None:
    """
    Creates and registers a maintenance tab view for a model.

    Args:
        model: Django model class to add the tab view to
    """
    from netbox_maintenance.filtersets.maintenance import MaintenanceFilterSet

    view_name = "maintenances"
    view_path = "maintenances"

    class MaintenanceTabView(generic.ObjectChildrenView):
        queryset = model.objects.all()
        child_model = Maintenance
        table = MaintenanceTable
        filterset = MaintenanceFilterSet
        template_name = "netbox_maintenance/inc/object_maintenances.html"
        tab = ViewTab(
            label="Maintenances",
            badge=lambda obj: MaintenanceImpact.objects.filter(
                object_type=ContentType.objects.get_for_model(obj), object_id=obj.pk
            ).count(),
            permission="netbox_maintenance.view_maintenanceimpact",
            weight=1000,
        )

        def get_children(self, request, parent):
            """Get maintenances for this object as a queryset."""
            content_type = ContentType.objects.get_for_model(parent)

            # Get maintenance IDs that have impacts on this object
            impact_maintenance_ids = MaintenanceImpact.objects.filter(
                object_type=content_type, object_id=parent.pk
            ).values_list("maintenance_id", flat=True)

            # Return a queryset of maintenances
            return Maintenance.objects.filter(id__in=impact_maintenance_ids)

    # Register the view
    register_model_view(model, name=view_name, path=view_path)(MaintenanceTabView)


def get_template_extensions() -> List:
    """
    Registers maintenance tab views for all models in the scope_filter.

    Returns:
        List: Empty list (all extensions are registered as views)
    """
    try:
        # Get scope filter from settings
        scope_filter = PLUGIN_SETTINGS.get("scope_filter", [])

        # Process each model in scope filter
        for app_model_name in scope_filter:
            try:
                app_label, model_name = app_model_name.split(".")
                model = apps.get_model(app_label, model_name)
                register_maintenance_tab_view(model)
            except (LookupError, ValueError) as e:
                logger.error(f"Failed to register maintenance tab for '{app_model_name}': {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error registering maintenance tab for '{app_model_name}'")
                logger.debug(f"Error details: {str(e)}", exc_info=True)
                continue

    except OperationalError:
        logger.error("Database is not ready, skipping template extensions setup")
    except Exception as e:
        logger.error("Unexpected error in template extensions setup")
        logger.debug(f"Error details: {str(e)}", exc_info=True)

    return []


# Generate all template extensions
template_extensions = get_template_extensions()
