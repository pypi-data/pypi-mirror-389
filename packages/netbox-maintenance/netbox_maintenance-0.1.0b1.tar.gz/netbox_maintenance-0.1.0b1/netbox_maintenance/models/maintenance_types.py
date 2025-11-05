from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel


class MaintenanceTypeChoices(NetBoxModel):
    """
    Defines maintenance status types based on BCOP standard.
    https://github.com/jda/maintnote-std/blob/master/standard.md
    """

    name = models.CharField(
        max_length=100, unique=True, help_text="Maintenance type name (e.g., TENTATIVE, CONFIRMED, IN-PROCESS)"
    )

    description = models.CharField(max_length=200, blank=True, help_text="Description of this maintenance type")

    color = models.CharField(max_length=6, help_text="Hex color code (without #) for this maintenance type")

    class Meta:
        ordering = ("name",)
        verbose_name = "Maintenance Type"
        verbose_name_plural = "Maintenance Types"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:netbox_maintenance:maintenancetypechoices", args=[self.pk])


class MaintenanceImpactTypeChoices(NetBoxModel):
    """
    Defines maintenance impact types based on BCOP standard.
    https://github.com/jda/maintnote-std/blob/master/standard.md
    """

    name = models.CharField(
        max_length=100, unique=True, help_text="Impact type name (e.g., NO-IMPACT, REDUCED-REDUNDANCY, OUTAGE)"
    )

    description = models.CharField(max_length=200, blank=True, help_text="Description of this impact type")

    color = models.CharField(max_length=6, help_text="Hex color code (without #) for this impact type")

    class Meta:
        ordering = ("name",)
        verbose_name = "Maintenance Impact Type"
        verbose_name_plural = "Maintenance Impact Types"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:netbox_maintenance:maintenanceimpacttypechoices", args=[self.pk])
