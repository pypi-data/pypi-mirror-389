from netbox.api.routers import NetBoxRouter

from . import views

app_name = "netbox_maintenance"
router = NetBoxRouter()
router.register("maintenance-types", views.MaintenanceTypeChoicesViewSet)
router.register("maintenance-impact-types", views.MaintenanceImpactTypeChoicesViewSet)
router.register("maintenances", views.MaintenanceViewSet)
router.register("maintenance-impacts", views.MaintenanceImpactViewSet)

urlpatterns = router.urls
