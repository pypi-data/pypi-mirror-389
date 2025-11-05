from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

_menu_items = (
    PluginMenuItem(
        link="plugins:netbox_maintenance:maintenance_list",
        link_text="Maintenances",
        buttons=(
            PluginMenuButton(
                link="plugins:netbox_maintenance:maintenance_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
            ),
            PluginMenuButton(
                link="plugins:netbox_maintenance:maintenance_bulk_import",
                title="Import",
                icon_class="mdi mdi-upload",
            ),
        ),
    ),
    PluginMenuItem(
        link="plugins:netbox_maintenance:maintenanceimpact_list",
        link_text="Maintenance Impacts",
        buttons=(
            PluginMenuButton(
                link="plugins:netbox_maintenance:maintenanceimpact_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
            ),
            PluginMenuButton(
                link="plugins:netbox_maintenance:maintenanceimpact_bulk_import",
                title="Import",
                icon_class="mdi mdi-upload",
            ),
        ),
    ),
)

_config_items = (
    PluginMenuItem(
        link="plugins:netbox_maintenance:maintenancetypechoices_list",
        link_text="Maintenance Types",
        buttons=(
            PluginMenuButton(
                link="plugins:netbox_maintenance:maintenancetypechoices_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
            ),
        ),
    ),
    PluginMenuItem(
        link="plugins:netbox_maintenance:maintenanceimpacttypechoices_list",
        link_text="Impact Types",
        buttons=(
            PluginMenuButton(
                link="plugins:netbox_maintenance:maintenanceimpacttypechoices_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
            ),
        ),
    ),
)

menu = PluginMenu(
    label="Maintenance",
    groups=(
        ("Maintenance", _menu_items),
        ("Configuration", _config_items),
    ),
    icon_class="mdi mdi-wrench-clock",
)
