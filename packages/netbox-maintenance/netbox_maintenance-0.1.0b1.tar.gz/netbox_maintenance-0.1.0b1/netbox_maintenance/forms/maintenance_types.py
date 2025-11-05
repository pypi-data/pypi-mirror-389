from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import ColorField
from utilities.forms.rendering import FieldSet

from netbox_maintenance.models import MaintenanceTypeChoices


class MaintenanceTypeChoicesForm(NetBoxModelForm):
    color = ColorField()

    class Meta:
        model = MaintenanceTypeChoices
        fields = ("name", "description", "color", "tags")


class MaintenanceTypeChoicesFilterForm(NetBoxModelFilterSetForm):
    model = MaintenanceTypeChoices

    name = forms.CharField(required=False)
    description = forms.CharField(required=False)

    fieldsets = (
        FieldSet("q", "filter_id", "tag", name="Common"),
        FieldSet("name", "description", name="Attributes"),
    )
