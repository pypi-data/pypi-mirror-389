from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from .maintenance import Maintenance
from .maintenance_types import MaintenanceImpactTypeChoices


class MaintenanceImpact(NetBoxModel):
    """
    Represents the impact of a maintenance event on a specific NetBox object.
    Uses GenericForeignKey to allow linking to any NetBox model.
    """

    maintenance = models.ForeignKey(
        to=Maintenance, on_delete=models.CASCADE, related_name="impacts", verbose_name="Maintenance"
    )

    object_type = models.ForeignKey(
        to=ContentType, on_delete=models.CASCADE, help_text="Type of object affected by this maintenance"
    )

    object_id = models.PositiveBigIntegerField(help_text="ID of the affected object")

    object = GenericForeignKey(ct_field="object_type", fk_field="object_id")

    impact = models.ForeignKey(
        to=MaintenanceImpactTypeChoices,
        on_delete=models.PROTECT,
        related_name="maintenance_impacts",
        help_text="Level of impact on the object",
    )

    class Meta:
        ordering = ("maintenance", "impact")
        verbose_name = "Maintenance Impact"
        verbose_name_plural = "Maintenance Impacts"
        unique_together = ("maintenance", "object_type", "object_id")

    def __str__(self):
        return f"{self.maintenance.name} - {self.object}"

    def get_impact_color(self):
        return self.impact.color if self.impact else None

    def get_absolute_url(self):
        return reverse("plugins:netbox_maintenance:maintenanceimpact", args=[self.pk])
