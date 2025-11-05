from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import ColorField
from utilities.forms.rendering import FieldSet

from netbox_maintenance.models import MaintenanceImpactTypeChoices


class MaintenanceImpactTypeChoicesForm(NetBoxModelForm):
    color = ColorField()

    class Meta:
        model = MaintenanceImpactTypeChoices
        fields = ("name", "description", "color", "tags")


class MaintenanceImpactTypeChoicesFilterForm(NetBoxModelFilterSetForm):
    model = MaintenanceImpactTypeChoices

    name = forms.CharField(required=False)
    description = forms.CharField(required=False)

    fieldsets = (
        FieldSet("q", "filter_id", "tag", name="Common"),
        FieldSet("name", "description", name="Attributes"),
    )
