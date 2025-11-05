from django import forms
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelBulkEditForm, NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import CommentField, DynamicModelChoiceField, DynamicModelMultipleChoiceField
from utilities.forms.rendering import FieldSet
from utilities.forms.widgets import DateTimePicker

from netbox_maintenance.models import Maintenance, MaintenanceTypeChoices


class MaintenanceForm(NetBoxModelForm):
    status = DynamicModelChoiceField(queryset=MaintenanceTypeChoices.objects.all(), required=True)
    comments = CommentField()

    start = forms.DateTimeField(
        required=False,
        widget=DateTimePicker(),
        label=_("Start Date/Time"),
        help_text=_("Filter maintenances starting after this date and time"),
    )

    end = forms.DateTimeField(
        required=False,
        widget=DateTimePicker(),
        label=_("End Date/Time"),
        help_text=_("Filter maintenances ending before this date and time"),
    )

    class Meta:
        model = Maintenance
        fields = (
            "name",
            "summary",
            "status",
            "start",
            "end",
            "internal_ticket",
            "acknowledged",
            "comments",
            "tags",
        )


class MaintenanceFilterForm(NetBoxModelFilterSetForm):
    model = Maintenance

    name = forms.CharField(required=False)
    summary = forms.CharField(required=False)
    status_id = DynamicModelMultipleChoiceField(
        queryset=MaintenanceTypeChoices.objects.all(), required=False, label="Status"
    )
    internal_ticket = forms.CharField(required=False)
    acknowledged = forms.NullBooleanField(
        required=False,
        widget=forms.Select(
            choices=[
                ("", "Any"),
                ("true", "Yes"),
                ("false", "No"),
            ]
        ),
    )
    start = forms.DateTimeField(
        required=False,
        widget=DateTimePicker(),
        label=_("Start Date/Time"),
        help_text=_("Filter maintenances starting after this date and time"),
    )

    end = forms.DateTimeField(
        required=False,
        widget=DateTimePicker(),
        label=_("End Date/Time"),
        help_text=_("Filter maintenances ending before this date and time"),
    )

    fieldsets = (
        FieldSet("q", "filter_id", "tag", name="Common"),
        FieldSet("name", "summary", "status_id", "internal_ticket", "acknowledged", name="Attributes"),
        FieldSet("start", "end", name="Dates"),
    )


class MaintenanceBulkEditForm(NetBoxModelBulkEditForm):
    status = DynamicModelChoiceField(queryset=MaintenanceTypeChoices.objects.all(), required=False)
    acknowledged = forms.NullBooleanField(
        required=False,
        widget=forms.Select(
            choices=[
                ("", "---------"),
                ("true", "Yes"),
                ("false", "No"),
            ]
        ),
    )
    comments = CommentField()

    model = Maintenance
    fieldsets = (FieldSet("status", "acknowledged", name="Attributes"),)
    nullable_fields = ("comments",)
