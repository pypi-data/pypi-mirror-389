"""Utilities for handling ContentType filtering based on plugin configuration."""

from django.conf import settings
from django.contrib.contenttypes.models import ContentType


def get_allowed_content_types():
    """
    Get a queryset of ContentTypes that are allowed for maintenance based on plugin configuration.
    
    Returns:
        QuerySet: Filtered ContentType queryset based on scope_filter setting
    """
    # Get the scope_filter from plugin configuration
    plugin_config = settings.PLUGINS_CONFIG.get('netbox_maintenance', {})
    scope_filter = plugin_config.get('scope_filter', [])
    
    if not scope_filter:
        # If no filter is configured, return empty queryset
        return ContentType.objects.none()
    
    # Parse the scope_filter list to build a queryset filter
    # Each item should be in format "app_label.model"
    query_filters = []
    
    for item in scope_filter:
        try:
            app_label, model = item.split('.', 1)
            query_filters.append((app_label, model))
        except ValueError:
            # Skip invalid format items
            continue
    
    if not query_filters:
        return ContentType.objects.none()
    
    # Build Q objects for filtering
    from django.db.models import Q
    q_objects = Q()
    
    for app_label, model in query_filters:
        q_objects |= Q(app_label=app_label, model=model)
    
    # Return filtered ContentTypes, ordered by app_label and model
    return ContentType.objects.filter(q_objects).order_by('app_label', 'model')
