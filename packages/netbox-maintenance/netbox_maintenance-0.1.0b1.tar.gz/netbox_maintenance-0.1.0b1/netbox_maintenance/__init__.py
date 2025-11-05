"""Top-level package for NetBox Maintenance Plugin."""

from importlib import metadata

from netbox.plugins import PluginConfig

# Get package metadata from pyproject.toml
_metadata = metadata.metadata("netbox_maintenance")
__version__ = _metadata["Version"]
__description__ = _metadata["Summary"]
__name__ = _metadata["Name"]
__author__ = _metadata["Author"]
__email__ = _metadata["Author-email"]


class NetBoxMaintenanceConfig(PluginConfig):
    name = __name__
    verbose_name = "NetBox Maintenance Plugin"
    description = __description__
    version = __version__
    base_url = "maintenance"
    author = __email__
    # graphql_schema = "graphql.schema"

    # Default plugin settings
    default_settings = {
        "scope_filter": [
            "dcim.device",
            "dcim.interface",
            "dcim.site",
            "dcim.rack",
            "dcim.location",
            "circuits.circuit",
            "circuits.provider",
            "ipam.ipaddress",
            "ipam.prefix",
            "ipam.vlan",
            "tenancy.tenant",
            "virtualization.virtualmachine",
            "virtualization.vminterface",
            "wireless.wirelesslan",
            "wireless.wirelesslink",
        ],
        # Define parent-child relationships for dependent field filtering
        # Format: {'child_model': ('parent_model', 'query_param_name', 'parent_attr_name')}
        # parent_attr_name is the attribute on the child model that references the parent (for display)
        # Note: Models with GenericForeignKey (like ipam.ipaddress) are not included here as they
        # don't have simple parent-child relationships. Users can select them directly.
        "parent_child_relationships": {
            "dcim.interface": ("dcim.device", "device_id", "device"),
            "dcim.module": ("dcim.device", "device_id", "device"),
            "virtualization.vminterface": ("virtualization.virtualmachine", "virtual_machine_id", "virtual_machine"),
            "dcim.location": ("dcim.site", "site_id", "site"),
            # Cannot be used: `assigned_object` does not generate an automatic reverse relation and therefore cannot be used for reverse querying. If it is a GenericForeignKey, consider adding a GenericRelation.
            # "ipam.ipaddress": (
            #    "dcim.device",
            #    "device_id",
            #    "assigned_object",
            # ),
        },
    }

    required_settings = []
    min_version = "4.4.0"
    max_version = "4.4.99"


config = NetBoxMaintenanceConfig
