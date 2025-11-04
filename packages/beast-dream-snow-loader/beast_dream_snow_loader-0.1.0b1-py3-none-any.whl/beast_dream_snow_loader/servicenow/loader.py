"""Data loading functions for ServiceNow CMDB."""

from typing import Any

from beast_dream_snow_loader.models.servicenow import (
    ServiceNowEndpoint,
    ServiceNowGatewayCI,
    ServiceNowLocation,
    ServiceNowNetworkDeviceCI,
)
from beast_dream_snow_loader.servicenow.api_client import ServiceNowAPIClient

# Table name mappings (ServiceNow standard tables or custom)
# Note: Using actual available classes from CMDB CI Class Models plugin
TABLE_GATEWAY_CI = "cmdb_ci_netgear"  # Network Gear (physical hardware - UniFi Dream Machine is a physical device)
# Alternative: "cmdb_ci_network_node" (subclass of netgear, also valid for network devices)
TABLE_LOCATION = "cmdb_ci_site"  # Site/Location (cmdb_location doesn't exist)
TABLE_NETWORK_DEVICE_CI = (
    "cmdb_ci_network_node"  # Network Node (subclass of cmdb_ci_netgear)
)
TABLE_ENDPOINT = (
    "cmdb_ci"  # Use base table with sys_class_name (cmdb_endpoint doesn't exist)
)


def load_gateway_ci(client: ServiceNowAPIClient, gateway: ServiceNowGatewayCI) -> dict:
    """Load a gateway CI record into ServiceNow.

    Note: sys_id is excluded from create (ServiceNow auto-generates).
    See docs/servicenow_constraints.md for assumptions.

    Args:
        client: ServiceNow API client
        gateway: Gateway CI model instance

    Returns:
        Created record data from ServiceNow (includes auto-generated sys_id)
    """
    data = gateway.model_dump(exclude_none=True)
    # Remove sys_id if present (ServiceNow auto-generates)
    data.pop("sys_id", None)
    return client.create_record(TABLE_GATEWAY_CI, data)


def load_location(client: ServiceNowAPIClient, location: ServiceNowLocation) -> dict:
    """Load a location record into ServiceNow.

    Note: sys_id is excluded from create (ServiceNow auto-generates).
    See docs/servicenow_constraints.md for assumptions.

    Args:
        client: ServiceNow API client
        location: Location model instance

    Returns:
        Created record data from ServiceNow (includes auto-generated sys_id)
    """
    data = location.model_dump(exclude_none=True)
    # Remove sys_id if present (ServiceNow auto-generates)
    data.pop("sys_id", None)
    return client.create_record(TABLE_LOCATION, data)


def load_network_device_ci(
    client: ServiceNowAPIClient, device: ServiceNowNetworkDeviceCI
) -> dict:
    """Load a network device CI record into ServiceNow.

    Note: sys_id is excluded from create (ServiceNow auto-generates).
    See docs/servicenow_constraints.md for assumptions.

    Args:
        client: ServiceNow API client
        device: Network device CI model instance

    Returns:
        Created record data from ServiceNow (includes auto-generated sys_id)
    """
    data = device.model_dump(exclude_none=True)
    # Remove sys_id if present (ServiceNow auto-generates)
    data.pop("sys_id", None)
    return client.create_record(TABLE_NETWORK_DEVICE_CI, data)


def load_endpoint(client: ServiceNowAPIClient, endpoint: ServiceNowEndpoint) -> dict:
    """Load an endpoint record into ServiceNow.

    Note: sys_id is excluded from create (ServiceNow auto-generates).
    See docs/servicenow_constraints.md for assumptions.

    Args:
        client: ServiceNow API client
        endpoint: Endpoint model instance

    Returns:
        Created record data from ServiceNow (includes auto-generated sys_id)
    """
    data = endpoint.model_dump(exclude_none=True)
    # Remove sys_id if present (ServiceNow auto-generates)
    data.pop("sys_id", None)
    return client.create_record(TABLE_ENDPOINT, data)


def load_entities_with_relationships(
    client: ServiceNowAPIClient,
    gateways: list[ServiceNowGatewayCI] | None = None,
    locations: list[ServiceNowLocation] | None = None,
    devices: list[ServiceNowNetworkDeviceCI] | None = None,
    endpoints: list[ServiceNowEndpoint] | None = None,
    changeset_id: str | None = None,
    create_changeset: bool = False,
) -> dict[str, dict[str, str]]:
    """Load entities with relationships using two-phase linking.

    Phase 1: Create all records, capture returned sys_ids.
    Phase 2: Update records with relationship references using sys_ids.

    Args:
        client: ServiceNow API client
        gateways: List of gateway CI models to load
        locations: List of location models to load (may reference gateways)
        devices: List of network device CI models to load (may reference gateways/locations)
        endpoints: List of endpoint models to load (may reference locations/devices)
        changeset_id: Optional changeset ID if already in a changeset context
        create_changeset: If True and not in changeset, create one before loading

    Returns:
        Mapping of table names to dict of {source_id: sys_id} for all created records.
        Format: {
            "cmdb_ci_network_gateway": {"source_id_1": "sys_id_1", ...},
            "cmdb_location": {"source_id_2": "sys_id_2", ...},
            ...
        }

    Note:
        Relationships are handled in dependency order:
        1. Gateways (no dependencies)
        2. Locations (depend on gateways)
        3. Devices (depend on gateways and locations)
        4. Endpoints (depend on locations and devices)

        Changeset Support:
        - Check if already in changeset context (get_current_changeset)
        - If not and create_changeset=True, create changeset before loading
        - If changeset_id provided, use that changeset
        - All operations performed within changeset for transactional behavior
    """
    # Check for changeset context
    current_changeset = client.get_current_changeset()
    active_changeset_id = changeset_id or (
        current_changeset.get("sys_id") if current_changeset else None
    )

    # Inform user about changeset status before operations
    if not active_changeset_id:
        print(
            "ℹ️  Not in a changeset context. Operations will be non-transactional.\n"
            "   If you're managing changesets, you can:\n"
            "   - Create a changeset first in ServiceNow\n"
            "   - Provide changeset_id parameter when calling this function\n"
            "   - Set create_changeset=True (when implemented)\n"
            "   Proceeding with data load..."
        )
    else:
        print(f"✅ Operating within changeset: {active_changeset_id}")

    # If create_changeset=True and not in a changeset, create one
    if create_changeset and not active_changeset_id:
        # TODO: Implement create_changeset() when ServiceNow API is investigated
        # For now, this is a placeholder
        print(
            "⚠️  Changeset creation requested but not yet implemented.\n"
            "   Please create a changeset manually in ServiceNow first.\n"
            "   Proceeding without changeset (non-transactional)."
        )

    # Initialize id_mapping: {table_name: {source_id: sys_id}}
    id_mapping: dict[str, dict[str, str]] = {
        TABLE_GATEWAY_CI: {},
        TABLE_LOCATION: {},
        TABLE_NETWORK_DEVICE_CI: {},
        TABLE_ENDPOINT: {},
    }

    # Phase 1: Create all records in dependency order
    # 1. Gateways (no dependencies)
    if gateways:
        for gateway in gateways:
            result = load_gateway_ci(client, gateway)
            source_id = gateway.u_unifi_source_id
            sys_id = result.get("sys_id", "")
            if sys_id:
                id_mapping[TABLE_GATEWAY_CI][source_id] = sys_id

    # 2. Locations (depend on gateways - host_id will be set in Phase 2)
    if locations:
        for location in locations:
            result = load_location(client, location)
            source_id = location.u_unifi_source_id
            sys_id = result.get("sys_id", "")
            if sys_id:
                id_mapping[TABLE_LOCATION][source_id] = sys_id

    # 3. Devices (depend on gateways and locations - relationships set in Phase 2)
    if devices:
        for device in devices:
            result = load_network_device_ci(client, device)
            source_id = device.u_unifi_source_id
            sys_id = result.get("sys_id", "")
            if sys_id:
                id_mapping[TABLE_NETWORK_DEVICE_CI][source_id] = sys_id

    # 4. Endpoints (depend on locations and devices - relationships set in Phase 2)
    if endpoints:
        for endpoint in endpoints:
            result = load_endpoint(client, endpoint)
            source_id = endpoint.u_unifi_source_id
            sys_id = result.get("sys_id", "")
            if sys_id:
                id_mapping[TABLE_ENDPOINT][source_id] = sys_id

    # Phase 2: Update relationships
    # Update locations with host_id references
    if locations:
        for location in locations:
            location_sys_id = id_mapping[TABLE_LOCATION].get(location.u_unifi_source_id)
            if not location_sys_id:
                continue

            # Get host_id from location model if it exists (should be None initially)
            # We need to find the gateway sys_id that corresponds to the site's hostId
            # This requires the original UniFi site model to know the hostId relationship
            # For now, we'll update if host_id is already set in the model
            location_update_data: dict[str, Any] = {}
            if location.host_id:
                # Location already has host_id set (but it's a source ID, not sys_id)
                # Find the corresponding gateway sys_id
                gateway_sys_id = None
                for source_id, sys_id in id_mapping[TABLE_GATEWAY_CI].items():
                    if source_id == location.host_id:
                        gateway_sys_id = sys_id
                        break
                if gateway_sys_id:
                    location_update_data["host_id"] = gateway_sys_id

            if location_update_data:
                client.update_record(
                    TABLE_LOCATION, location_sys_id, location_update_data
                )

    # Update devices with host_id and site_id references
    if devices:
        for device in devices:
            device_sys_id = id_mapping[TABLE_NETWORK_DEVICE_CI].get(
                device.u_unifi_source_id
            )
            if not device_sys_id:
                continue

            device_update_data: dict[str, Any] = {}
            # Find gateway sys_id if host_id is set
            if device.host_id:
                gateway_sys_id = None
                for source_id, sys_id in id_mapping[TABLE_GATEWAY_CI].items():
                    if source_id == device.host_id:
                        gateway_sys_id = sys_id
                        break
                if gateway_sys_id:
                    device_update_data["host_id"] = gateway_sys_id

            # Find location sys_id if site_id is set
            if device.site_id:
                location_sys_id = None
                for source_id, sys_id in id_mapping[TABLE_LOCATION].items():
                    if source_id == device.site_id:
                        location_sys_id = sys_id
                        break
                if location_sys_id:
                    device_update_data["site_id"] = location_sys_id

            if device_update_data:
                client.update_record(
                    TABLE_NETWORK_DEVICE_CI, device_sys_id, device_update_data
                )

    # Update endpoints with site_id and device_id references
    if endpoints:
        for endpoint in endpoints:
            endpoint_sys_id = id_mapping[TABLE_ENDPOINT].get(endpoint.u_unifi_source_id)
            if not endpoint_sys_id:
                continue

            endpoint_update_data: dict[str, Any] = {}
            # Find location sys_id if site_id is set
            if endpoint.site_id:
                location_sys_id = None
                for source_id, sys_id in id_mapping[TABLE_LOCATION].items():
                    if source_id == endpoint.site_id:
                        location_sys_id = sys_id
                        break
                if location_sys_id:
                    endpoint_update_data["site_id"] = location_sys_id

            # Find device sys_id if device_id is set
            if endpoint.device_id:
                device_sys_id = None
                for source_id, sys_id in id_mapping[TABLE_NETWORK_DEVICE_CI].items():
                    if source_id == endpoint.device_id:
                        device_sys_id = sys_id
                        break
                if device_sys_id:
                    endpoint_update_data["device_id"] = device_sys_id

            if endpoint_update_data:
                client.update_record(
                    TABLE_ENDPOINT, endpoint_sys_id, endpoint_update_data
                )

    return id_mapping
