import json

from django import forms
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from netbox.forms import NetBoxModelBulkEditForm, NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import (
    ContentTypeMultipleChoiceField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
)
from utilities.forms.rendering import FieldSet, TabbedGroups

from netbox_maintenance import config as plugin_config
from netbox_maintenance.models import Maintenance, MaintenanceImpact, MaintenanceImpactTypeChoices
from netbox_maintenance.utils.content_types import get_allowed_content_types


class MaintenanceImpactAddForm(NetBoxModelForm):
    """
    Form for creating multiple MaintenanceImpact records.
    Uses TabbedGroups with a tab for each configured object type from scope_filter.
    Each tab contains a multi-select field allowing selection of multiple objects.
    """

    maintenance = DynamicModelChoiceField(queryset=Maintenance.objects.all(), required=True, label="Maintenance")

    impact = DynamicModelChoiceField(
        queryset=MaintenanceImpactTypeChoices.objects.all(), required=True, label="Impact Type"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize instance variables
        self._selected_objects = []
        self._preselected_object = None
        self._preselected_model_path = None
        self._active_tab_index = None

        # Check for object_type and object_id in initial data (from query parameters)
        object_type_id = self.initial.get("object_type")
        object_id = self.initial.get("object_id")

        if object_type_id and object_id:
            try:
                # Get the object that should be pre-selected
                content_type = ContentType.objects.get(pk=object_type_id)
                obj = content_type.get_object_for_this_type(pk=object_id)
                self._preselected_object = obj
                self._preselected_model_path = f"{content_type.app_label}.{content_type.model}"
            except (ContentType.DoesNotExist, Exception):
                pass

        # Build dynamic fields and fieldsets
        tab_fields = self._build_dynamic_fields()
        self.fieldsets = self._build_fieldsets(tab_fields)

        # Pre-select the object if one was provided
        if self._preselected_object and self._preselected_model_path:
            field_name = self._preselected_model_path.replace(".", "_")
            if field_name in self.fields:
                self.initial[field_name] = [self._preselected_object.pk]

        # Mark the active tab index for JavaScript
        self._mark_active_tab()

    def _get_parent_info(self, parent_info):
        """
        Extract parent relationship configuration from parent_info tuple.

        Args:
            parent_info: Tuple with parent configuration (path, query_param) or (path, query_param, parent_attr)

        Returns:
            Tuple of (parent_path, query_param, parent_attr) or None if invalid
        """
        if not parent_info:
            return None

        if len(parent_info) == 3:
            return parent_info
        elif len(parent_info) == 2:
            # Backwards compatibility: if only 2 elements, no parent_attr
            return parent_info[0], parent_info[1], None
        return None

    def _create_parent_field(self, parent_model_class, parent_field_name, model_class):
        """
        Create a parent selector field for filtering child objects.

        Args:
            parent_model_class: The parent Django model class
            parent_field_name: Name for the parent selector field
            model_class: The child Django model class (for help text)
        """
        self.fields[parent_field_name] = DynamicModelMultipleChoiceField(
            queryset=parent_model_class.objects.all(),
            required=False,
            selector=True,
            label=f"{parent_model_class._meta.verbose_name_plural.title()} (Filter)",
            help_text=f"Select one or more {parent_model_class._meta.verbose_name_plural} to filter {model_class._meta.verbose_name_plural}",
        )

    def _create_child_field(self, model_class, field_name, parent_field_name, query_param, parent_attr):
        """
        Create a child field with parent filtering support.

        Args:
            model_class: The Django model class
            field_name: Name for the form field
            parent_field_name: Name of the parent field for query params
            query_param: Query parameter name for filtering
            parent_attr: Attribute name for the parent relationship (for display)
        """
        field_context = {}
        if parent_attr:
            field_context["parent"] = parent_attr

        self.fields[field_name] = DynamicModelMultipleChoiceField(
            queryset=model_class.objects.all(),
            query_params={query_param: f"${parent_field_name}"},
            required=False,
            selector=True,
            label=model_class._meta.verbose_name_plural.title(),
            context=field_context,
        )

    def _create_simple_field(self, model_class, field_name):
        """
        Create a simple DynamicModelMultipleChoiceField without parent relationship.

        Args:
            model_class: The Django model class
            field_name: Name for the form field
        """
        self.fields[field_name] = DynamicModelMultipleChoiceField(
            queryset=model_class.objects.all(),
            required=False,
            selector=True,
            label=model_class._meta.verbose_name_plural.title(),
        )

    def _build_dynamic_fields(self):
        """
        Build dynamic fields for each model in scope_filter with parent-child relationships.

        Returns:
            List of FieldSet objects for each model
        """
        scope_filter = plugin_config.default_settings.get("scope_filter", [])
        parent_child_map = plugin_config.default_settings.get("parent_child_relationships", {})
        tab_fields = []

        for tab_index, model_path in enumerate(scope_filter):
            try:
                app_label, model_name = model_path.split(".")
                model_class = apps.get_model(app_label, model_name)
                field_name = f"{app_label}_{model_name}"

                # Track which tab should be active if this is the preselected model
                if self._preselected_model_path == model_path:
                    self._active_tab_index = tab_index

                # Check if this model has a parent dependency
                parent_info = parent_child_map.get(model_path)
                parent_config = self._get_parent_info(parent_info)

                if parent_config:
                    # Create parent-child field pair
                    parent_path, query_param, parent_attr = parent_config
                    parent_app, parent_model = parent_path.split(".")
                    parent_model_class = apps.get_model(parent_app, parent_model)
                    parent_field_name = f"{field_name}_parent"

                    # Create parent selector and child field
                    self._create_parent_field(parent_model_class, parent_field_name, model_class)
                    self._create_child_field(model_class, field_name, parent_field_name, query_param, parent_attr)

                    # Both fields go in the tab
                    tab_field_list = [parent_field_name, field_name]
                else:
                    # Create simple field without parent
                    self._create_simple_field(model_class, field_name)
                    tab_field_list = [field_name]

                # Create a tab for this model
                tab_fields.append(FieldSet(*tab_field_list, name=model_class._meta.verbose_name_plural.title()))

            except (ValueError, LookupError):
                # Skip invalid model paths
                continue

        return tab_fields

    def _mark_active_tab(self):
        """
        Add data attribute to mark which tab should be active.
        This is used by JavaScript to automatically activate the correct tab.
        """
        if self._active_tab_index is not None:
            scope_filter = plugin_config.default_settings.get("scope_filter", [])
            if self._active_tab_index < len(scope_filter):
                model_path = scope_filter[self._active_tab_index]
                field_name = model_path.replace(".", "_")

                if field_name in self.fields:
                    # Add data attribute to the field's widget
                    self.fields[field_name].widget.attrs["data-active-tab"] = "true"

    def _build_fieldsets(self, tab_fields):
        """
        Build the final fieldset structure with tabbed groups.

        Args:
            tab_fields: List of FieldSet objects for dynamic fields

        Returns:
            Tuple of FieldSet objects
        """
        if tab_fields:
            return (
                FieldSet("maintenance", "impact", name=_("Maintenance Details")),
                FieldSet(TabbedGroups(*tab_fields), name=_("Affected Objects")),
                FieldSet("tags", name=_("Tags")),
            )
        else:
            # Fallback if no valid models found
            return (FieldSet("maintenance", "impact", "tags", name=_("Maintenance Details")),)

    def _collect_selected_objects(self):
        """
        Collect all selected objects from dynamic fields across all tabs.

        Returns:
            List of tuples (model_path, object)
        """
        scope_filter = plugin_config.default_settings.get("scope_filter", [])
        selected_objects = []

        for model_path in scope_filter:
            try:
                app_label, model_name = model_path.split(".")
                field_name = f"{app_label}_{model_name}"

                if field_name in self.cleaned_data and self.cleaned_data[field_name]:
                    for obj in self.cleaned_data[field_name]:
                        selected_objects.append((model_path, obj))

            except ValueError:
                continue

        return selected_objects

    def clean(self):
        """
        Validate that at least one object is selected across all tabs.
        """
        super().clean()

        # Collect all selected objects from dynamic fields
        selected_objects = self._collect_selected_objects()

        if not selected_objects:
            raise ValidationError(_("At least one object must be selected."))

        # Store selected objects for save()
        self._selected_objects = selected_objects

        return self.cleaned_data

    def _get_or_create_impact(self, model_path, obj, maintenance, impact, tags, changelog_message, commit):
        """
        Get existing or create new MaintenanceImpact record for a single object.

        Args:
            model_path: String like "app_label.model_name"
            obj: The object to create impact for
            maintenance: Maintenance instance
            impact: Impact type
            tags: List of tags to apply
            changelog_message: Optional changelog message
            commit: Whether to save to database

        Returns:
            MaintenanceImpact instance (existing or newly created)
        """
        try:
            app_label, model_name = model_path.split(".")
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)

            # Check if this combination already exists
            existing = MaintenanceImpact.objects.filter(
                maintenance=maintenance, object_type=content_type, object_id=obj.pk
            ).first()

            if existing:
                return existing

            # Create new MaintenanceImpact
            impact_record = MaintenanceImpact(
                maintenance=maintenance, object_type=content_type, object_id=obj.pk, impact=impact
            )

            if commit:
                # Set changelog message before save (NetBox standard)
                if changelog_message:
                    impact_record._changelog_message = changelog_message
                impact_record.save()
                if tags:
                    impact_record.tags.set(tags)

            return impact_record

        except (ValueError, ContentType.DoesNotExist):
            return None

    def save(self, commit=True):
        """
        Create multiple MaintenanceImpact records, one for each selected object.
        Override ModelForm.save() to prevent saving self.instance.
        """
        # Validate that we have selected objects
        if not hasattr(self, "_selected_objects") or not self._selected_objects:
            raise ValidationError(_("No objects selected. Please select at least one object from the tabs below."))

        # Don't call super().save() - we create records manually
        maintenance = self.cleaned_data["maintenance"]
        impact = self.cleaned_data["impact"]
        tags = self.cleaned_data.get("tags", [])

        # Extract changelog message from form data (it's in self.data, not cleaned_data)
        # because it's not a model field, just a changelog field
        changelog_message = self.data.get("changelog_message", "")

        created_impacts = []

        # Create a MaintenanceImpact record for each selected object
        for model_path, obj in self._selected_objects:
            impact_record = self._get_or_create_impact(
                model_path, obj, maintenance, impact, tags, changelog_message, commit
            )
            if impact_record:
                created_impacts.append(impact_record)

        # Return the first impact (created or existing) for compatibility with views
        if not created_impacts:
            raise ValidationError(_("Failed to create any MaintenanceImpact records."))

        return created_impacts[0]

    class Meta:
        model = MaintenanceImpact
        fields = ("maintenance", "impact", "tags")


class MaintenanceImpactEditForm(NetBoxModelForm):
    """
    Form for editing a single MaintenanceImpact record.
    The affected object is displayed as read-only.
    """

    maintenance = DynamicModelChoiceField(queryset=Maintenance.objects.all(), required=True, label="Maintenance")

    impact = DynamicModelChoiceField(
        queryset=MaintenanceImpactTypeChoices.objects.all(), required=True, label="Impact Type"
    )

    affected_object = forms.CharField(
        label="Affected Object",
        required=False,
        widget=forms.TextInput(attrs={"readonly": "readonly", "class": "form-control"}),
        help_text="The object affected by this maintenance (read-only)",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If editing an existing instance, populate the affected_object field
        if self.instance and self.instance.pk and self.instance.object:
            # Display as "ObjectType: Object"
            self.initial["affected_object"] = f"{self.instance.object_type}: {self.instance.object}"
            self.fields["affected_object"].widget.attrs["disabled"] = "disabled"

    class Meta:
        model = MaintenanceImpact
        fields = (
            "maintenance",
            "affected_object",
            "impact",
            "tags",
        )


class MaintenanceImpactBulkUpdateForm(NetBoxModelForm):
    """
    Form for bulk updating MaintenanceImpact records for a maintenance.
    Uses tabs with a section for each configured object type from scope_filter.
    Each tab contains a multi-select field allowing selection of multiple objects.
    """

    maintenance = DynamicModelChoiceField(
        queryset=Maintenance.objects.all(),
        required=True,
        label="Maintenance",
        disabled=True,
    )

    impact = DynamicModelChoiceField(
        queryset=MaintenanceImpactTypeChoices.objects.all(),
        required=True,
        label="Impact Type",
        help_text="Select the impact type to apply to all selected objects.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize instance variables
        self._selected_objects = []
        self._maintenance_id = self.initial.get("maintenance")

        # Initialize maintenance field
        if self._maintenance_id:
            self.fields["maintenance"].initial = self._maintenance_id
            self._existing_objects_by_model = self._load_existing_impacts(self._maintenance_id)
        else:
            self._existing_objects_by_model = {}

        # Build dynamic fields and fieldsets
        tab_fields = self._build_dynamic_fields()
        self.fieldsets = self._build_fieldsets(tab_fields)

    def _load_existing_impacts(self, maintenance_id):
        """
        Load and group existing MaintenanceImpact records by model type.

        Args:
            maintenance_id: ID of the maintenance to load impacts for

        Returns:
            Dict mapping model_path to list of objects
        """
        existing_impacts = MaintenanceImpact.objects.filter(maintenance_id=maintenance_id).select_related("object_type")

        existing_objects_by_model = {}
        for impact in existing_impacts:
            model_path = f"{impact.object_type.app_label}.{impact.object_type.model}"
            if model_path not in existing_objects_by_model:
                existing_objects_by_model[model_path] = []
            if impact.object:
                existing_objects_by_model[model_path].append(impact.object)

        return existing_objects_by_model

    def _get_parent_attr(self, parent_info):
        """
        Extract parent attribute name from parent_info configuration.

        Args:
            parent_info: Tuple with parent configuration (path, query_param, parent_attr)

        Returns:
            Parent attribute name or None
        """
        if parent_info and len(parent_info) == 3:
            return parent_info[2]
        return None

    def _create_field_with_parent(self, model_class, field_name, parent_attr):
        """
        Create a DynamicModelMultipleChoiceField with parent relationship support.

        Args:
            model_class: The Django model class
            field_name: Name for the form field
            parent_attr: Attribute name for the parent relationship
        """
        field_context = {}
        if parent_attr:
            field_context["parent"] = parent_attr

        base_queryset = model_class.objects.all()
        if parent_attr:
            base_queryset = base_queryset.select_related(parent_attr)

        self.fields[field_name] = DynamicModelMultipleChoiceField(
            queryset=base_queryset,
            required=False,
            selector=True,
            label=model_class._meta.verbose_name_plural.title(),
            context=field_context,
        )

    def _create_simple_field(self, model_class, field_name):
        """
        Create a DynamicModelMultipleChoiceField without parent relationship.

        Args:
            model_class: The Django model class
            field_name: Name for the form field
        """
        self.fields[field_name] = DynamicModelMultipleChoiceField(
            queryset=model_class.objects.all(),
            required=False,
            selector=True,
            label=model_class._meta.verbose_name_plural.title(),
        )

    def _prepopulate_field(self, field_name, existing_objects):
        """
        Pre-populate field with existing objects and add data attributes for JavaScript.

        Args:
            field_name: Name of the field to populate
            existing_objects: List of existing objects to pre-populate
        """
        self.initial[field_name] = [obj.pk for obj in existing_objects]
        preloaded_ids = [obj.pk for obj in existing_objects]
        self.fields[field_name].widget.attrs["data-preloaded-ids"] = json.dumps(preloaded_ids)

    def _add_parent_display_data(self, field_name, existing_objects, parent_attr):
        """
        Add parent display data as JSON attribute for JavaScript enhancement.

        Args:
            field_name: Name of the field
            existing_objects: List of existing objects
            parent_attr: Attribute name for accessing parent object
        """
        if not parent_attr:
            return

        parent_display_map = {}
        for obj in existing_objects:
            parent_obj = getattr(obj, parent_attr, None) if hasattr(obj, parent_attr) else None
            if parent_obj:
                parent_display_map[obj.pk] = {"display": str(obj), "parent": str(parent_obj)}

        if parent_display_map:
            self.fields[field_name].widget.attrs["data-parent-display"] = json.dumps(parent_display_map)

    def _build_dynamic_fields(self):
        """
        Build dynamic fields for each model in scope_filter.

        Returns:
            List of FieldSet objects for each model
        """
        scope_filter = plugin_config.default_settings.get("scope_filter", [])
        parent_child_map = plugin_config.default_settings.get("parent_child_relationships", {})
        tab_fields = []

        for model_path in scope_filter:
            try:
                app_label, model_name = model_path.split(".")
                model_class = apps.get_model(app_label, model_name)
                field_name = f"{app_label}_{model_name}"

                # Get parent info if available
                parent_info = parent_child_map.get(model_path)
                parent_attr = self._get_parent_attr(parent_info)

                # Create the appropriate field type
                if parent_info:
                    self._create_field_with_parent(model_class, field_name, parent_attr)
                else:
                    self._create_simple_field(model_class, field_name)

                # Pre-populate with existing objects if available
                existing_objects = self._existing_objects_by_model.get(model_path, [])
                if existing_objects:
                    self._prepopulate_field(field_name, existing_objects)
                    self._add_parent_display_data(field_name, existing_objects, parent_attr)

                # Create a tab for this model
                tab_fields.append(FieldSet(field_name, name=model_class._meta.verbose_name_plural.title()))

            except (ValueError, LookupError):
                # Skip invalid model paths
                continue

        return tab_fields

    def _build_fieldsets(self, tab_fields):
        """
        Build the final fieldset structure for the form.

        Args:
            tab_fields: List of FieldSet objects for dynamic fields

        Returns:
            Tuple of FieldSet objects
        """
        if tab_fields:
            return (
                FieldSet("maintenance", "impact", name=_("Maintenance Details")),
                FieldSet("tags", name=_("Tags")),
                FieldSet("", name=_("Affected Objects")),
                *tab_fields,
            )
        else:
            # Fallback if no valid models found
            return (FieldSet("maintenance", "impact", "tags", name=_("Maintenance Details")),)

    def _restore_maintenance_field(self):
        """
        Restore maintenance field from stored ID since disabled fields don't appear in cleaned_data.

        Raises:
            ValidationError: If maintenance_id is missing or invalid
        """
        if "maintenance" not in self.cleaned_data or self.cleaned_data["maintenance"] is None:
            if not self._maintenance_id:
                raise ValidationError(_("Maintenance is required."))
            try:
                self.cleaned_data["maintenance"] = Maintenance.objects.get(pk=self._maintenance_id)
            except Maintenance.DoesNotExist:
                raise ValidationError(_("Invalid maintenance ID."))

    def _collect_selected_objects(self):
        """
        Collect all selected objects from dynamic fields across all tabs.

        Returns:
            List of tuples (model_path, object)
        """
        scope_filter = plugin_config.default_settings.get("scope_filter", [])
        selected_objects = []

        for model_path in scope_filter:
            try:
                app_label, model_name = model_path.split(".")
                field_name = f"{app_label}_{model_name}"

                if field_name in self.cleaned_data and self.cleaned_data[field_name]:
                    for obj in self.cleaned_data[field_name]:
                        selected_objects.append((model_path, obj))

            except ValueError:
                continue

        return selected_objects

    def clean(self):
        """
        Validate that at least one object is selected across all tabs.
        Since maintenance field is disabled, restore it from stored maintenance_id.
        """
        super().clean()

        # Restore maintenance field (disabled fields don't appear in cleaned_data)
        self._restore_maintenance_field()

        # Collect all selected objects from dynamic fields
        selected_objects = self._collect_selected_objects()

        if not selected_objects:
            raise ValidationError(_("At least one object must be selected."))

        # Store selected objects for save()
        self._selected_objects = selected_objects

        return self.cleaned_data

    def _build_selected_set(self):
        """
        Convert selected objects to a set of (content_type_id, object_id) tuples.

        Returns:
            Set of tuples (content_type_id, object_id)
        """
        selected_set = set()
        for model_path, obj in self._selected_objects:
            try:
                app_label, model_name = model_path.split(".")
                content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                selected_set.add((content_type.id, obj.pk))
            except (ValueError, ContentType.DoesNotExist):
                continue
        return selected_set

    def _delete_removed_impacts(self, to_remove, maintenance, changelog_message):
        """
        Delete MaintenanceImpact records for objects that were removed from the form.

        Args:
            to_remove: Set of (content_type_id, object_id) tuples to delete
            maintenance: Maintenance instance
            changelog_message: Optional changelog message
        """
        for content_type_id, object_id in to_remove:
            impact_records = MaintenanceImpact.objects.filter(
                maintenance=maintenance, object_type_id=content_type_id, object_id=object_id
            )
            for impact_record in impact_records:
                if hasattr(impact_record, "snapshot"):
                    impact_record.snapshot()
                if changelog_message:
                    impact_record._changelog_message = changelog_message
                impact_record.delete()

    def _update_existing_impacts(self, to_keep, maintenance, impact, tags, changelog_message):
        """
        Update MaintenanceImpact records that exist in both form and database.

        Args:
            to_keep: Set of (content_type_id, object_id) tuples to update
            maintenance: Maintenance instance
            impact: Impact type to set
            tags: List of tags to apply
            changelog_message: Optional changelog message
        """
        for content_type_id, object_id in to_keep:
            impact_record = MaintenanceImpact.objects.filter(
                maintenance=maintenance, object_type_id=content_type_id, object_id=object_id
            ).first()

            if impact_record:
                # Update impact type if changed
                if impact_record.impact != impact:
                    impact_record.impact = impact
                    if changelog_message:
                        impact_record._changelog_message = changelog_message
                    impact_record.save()

                # Update tags
                if tags:
                    impact_record.tags.set(tags)

    def _create_new_impacts(self, to_add, maintenance, impact, tags, changelog_message):
        """
        Create new MaintenanceImpact records for objects added in the form.

        Args:
            to_add: Set of (content_type_id, object_id) tuples to create
            maintenance: Maintenance instance
            impact: Impact type to set
            tags: List of tags to apply
            changelog_message: Optional changelog message

        Returns:
            List of created MaintenanceImpact instances
        """
        created_impacts = []
        for content_type_id, object_id in to_add:
            impact_record = MaintenanceImpact(
                maintenance=maintenance, object_type_id=content_type_id, object_id=object_id, impact=impact
            )
            if changelog_message:
                impact_record._changelog_message = changelog_message
            impact_record.save()

            if tags:
                impact_record.tags.set(tags)

            created_impacts.append(impact_record)

        return created_impacts

    def save(self, commit=True):
        """
        Update MaintenanceImpact records based on form changes:
        - Delete impacts for objects that were removed
        - Create impacts for objects that were added
        - Update impact type for existing objects
        """
        # Validate that we have selected objects
        if not hasattr(self, "_selected_objects") or not self._selected_objects:
            raise ValidationError(_("No objects selected. Please select at least one object from the tabs below."))

        # Don't call super().save() - we manage records manually
        maintenance = self.cleaned_data["maintenance"]
        impact = self.cleaned_data["impact"]
        tags = self.cleaned_data.get("tags", [])
        changelog_message = self.data.get("changelog_message", "")

        # Get all existing impacts for this maintenance
        existing_impacts = MaintenanceImpact.objects.filter(maintenance=maintenance)
        existing_set = {(imp.object_type_id, imp.object_id) for imp in existing_impacts}

        # Build set of selected objects
        selected_set = self._build_selected_set()

        # Determine what needs to be added, removed, or kept
        to_add = selected_set - existing_set  # Objects in form but not in DB
        to_remove = existing_set - selected_set  # Objects in DB but not in form
        to_keep = existing_set & selected_set  # Objects in both

        if commit:
            # Process changes
            if to_remove:
                self._delete_removed_impacts(to_remove, maintenance, changelog_message)

            if to_keep:
                self._update_existing_impacts(to_keep, maintenance, impact, tags, changelog_message)

            if to_add:
                self._create_new_impacts(to_add, maintenance, impact, tags, changelog_message)

        # Return the first impact for compatibility with views
        all_impacts = list(MaintenanceImpact.objects.filter(maintenance=maintenance))
        if not all_impacts:
            raise ValidationError(_("No MaintenanceImpact records exist after save."))

        return all_impacts[0]

    class Meta:
        model = MaintenanceImpact
        fields = ("maintenance", "impact", "tags")


class MaintenanceImpactFilterForm(NetBoxModelFilterSetForm):
    model = MaintenanceImpact

    maintenance_id = DynamicModelMultipleChoiceField(
        queryset=Maintenance.objects.all(), required=False, label="Maintenance"
    )
    impact_id = DynamicModelMultipleChoiceField(
        queryset=MaintenanceImpactTypeChoices.objects.all(), required=False, label="Impact"
    )
    object_type_id = ContentTypeMultipleChoiceField(
        queryset=get_allowed_content_types(), required=False, label="Object Type"
    )

    fieldsets = (
        FieldSet("q", "filter_id", "tag", name="Common"),
        FieldSet("maintenance_id", "impact_id", "object_type_id", name="Attributes"),
    )


class MaintenanceImpactBulkEditForm(NetBoxModelBulkEditForm):
    impact = DynamicModelChoiceField(queryset=MaintenanceImpactTypeChoices.objects.all(), required=False)

    model = MaintenanceImpact
    fieldsets = (FieldSet("impact", name="Attributes"),)
    nullable_fields = ()
