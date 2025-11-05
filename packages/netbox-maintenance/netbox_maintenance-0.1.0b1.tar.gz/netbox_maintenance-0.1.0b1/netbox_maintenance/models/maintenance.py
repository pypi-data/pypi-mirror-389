from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from .maintenance_types import MaintenanceTypeChoices


class Maintenance(NetBoxModel):
    """
    Represents a scheduled maintenance event.
    """

    name = models.CharField(
        max_length=100, verbose_name="Maintenance ID", help_text="The maintenance ID / ticket number"
    )

    summary = models.CharField(max_length=200, help_text="Brief summary of the maintenance event")

    status = models.ForeignKey(
        to=MaintenanceTypeChoices,
        on_delete=models.PROTECT,
        related_name="maintenances",
        help_text="Current status of the maintenance",
    )

    start = models.DateTimeField(help_text="Start date and time of the maintenance event e.g. 2022-12-25 14:30")

    end = models.DateTimeField(help_text="End date and time of the maintenance event e.g. 2022-12-26 14:30")

    internal_ticket = models.CharField(
        max_length=100,
        verbose_name="Internal Ticket #",
        help_text="An internal ticket or change reference for this maintenance",
        blank=True,
    )

    acknowledged = models.BooleanField(
        default=False, verbose_name="Acknowledged?", help_text="Confirm if this maintenance event has been acknowledged"
    )

    comments = models.TextField(blank=True)

    class Meta:
        ordering = ("-created",)
        verbose_name = "Maintenance"
        verbose_name_plural = "Maintenances"

    def __str__(self):
        return self.name

    def get_status_color(self):
        return self.status.color if self.status else None

    def get_absolute_url(self):
        return reverse("plugins:netbox_maintenance:maintenance", args=[self.pk])

    def clean(self):
        super().clean()

        # Validate that end time is after start time
        if self.start and self.end and self.end <= self.start:
            raise ValidationError({"end": "End time must be after start time."})
