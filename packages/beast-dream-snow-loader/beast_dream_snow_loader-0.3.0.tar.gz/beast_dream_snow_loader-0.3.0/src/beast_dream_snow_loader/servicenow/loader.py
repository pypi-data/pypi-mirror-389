"""Data loading functions for ServiceNow CMDB."""

from beast_dream_snow_loader.models.servicenow import (
    ServiceNowEndpoint,
    ServiceNowGatewayCI,
    ServiceNowLocation,
    ServiceNowNetworkDeviceCI,
)
from beast_dream_snow_loader.servicenow.api_client import ServiceNowAPIClient

# Table name mappings (ServiceNow standard tables)
# Per ADR-0001: docs/adr/0001-servicenow-ci-class-selection.md
TABLE_GATEWAY_CI = "cmdb_ci_netgear"  # Physical network hardware (has table)
TABLE_LOCATION = "cmdb_ci_site"  # Site/location class (use cmdb_ci with sys_class_name)
TABLE_NETWORK_DEVICE_CI = (
    "cmdb_ci_network_node"  # Network node class (use cmdb_ci with sys_class_name)
)
TABLE_ENDPOINT = (
    "cmdb_ci"  # Base table with sys_class_name (cmdb_endpoint doesn't exist)
)


def load_gateway_ci(client: ServiceNowAPIClient, gateway: ServiceNowGatewayCI) -> dict:
    """Load a gateway CI record into ServiceNow.

    Note: sys_id is excluded from create (ServiceNow auto-generates).
    Falls back to base cmdb_ci table if specific table doesn't exist.
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

    try:
        return client.create_record(TABLE_GATEWAY_CI, data)
    except Exception as e:
        # Fallback to base cmdb_ci table if specific table doesn't exist
        if "Invalid table" in str(e) or "403" in str(e) or "400" in str(e):
            data["sys_class_name"] = TABLE_GATEWAY_CI
            return client.create_record(TABLE_ENDPOINT, data)
        raise


def load_location(client: ServiceNowAPIClient, location: ServiceNowLocation) -> dict:
    """Load a location record into ServiceNow.

    Per ADR-0001: Uses cmdb_ci_site class via cmdb_ci table with sys_class_name.
    cmdb_ci_site is a class, not a table - must use base cmdb_ci with sys_class_name.

    Args:
        client: ServiceNow API client
        location: Location model instance

    Returns:
        Created record data from ServiceNow (includes auto-generated sys_id)
    """
    data = location.model_dump(exclude_none=True)
    # Remove sys_id if present (ServiceNow auto-generates)
    data.pop("sys_id", None)
    # cmdb_ci_site is a class, not a table - use base cmdb_ci with sys_class_name
    # Per ADR-0001: docs/adr/0001-servicenow-ci-class-selection.md
    data["sys_class_name"] = TABLE_LOCATION
    return client.create_record(TABLE_ENDPOINT, data)


def load_network_device_ci(
    client: ServiceNowAPIClient, device: ServiceNowNetworkDeviceCI
) -> dict:
    """Load a network device CI record into ServiceNow.

    Per ADR-0001: Uses cmdb_ci_network_node class via cmdb_ci table with sys_class_name.
    cmdb_ci_network_node is a class, not a table - must use base cmdb_ci with sys_class_name.

    Args:
        client: ServiceNow API client
        device: Network device CI model instance

    Returns:
        Created record data from ServiceNow (includes auto-generated sys_id)
    """
    data = device.model_dump(exclude_none=True)
    # Remove sys_id if present (ServiceNow auto-generates)
    data.pop("sys_id", None)
    # cmdb_ci_network_node is a class, not a table - use base cmdb_ci with sys_class_name
    # Per ADR-0001: docs/adr/0001-servicenow-ci-class-selection.md
    data["sys_class_name"] = TABLE_NETWORK_DEVICE_CI
    return client.create_record(TABLE_ENDPOINT, data)


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
    """Load entities with relationships using multi-phase batch processing.

    Phase 1: Batch create all CI records, capture returned sys_ids.
    Phase 2: Batch create relationship records in cmdb_rel_ci using captured sys_ids.

    This is a performance optimization for batch operations through the REST API Table API.
    ServiceNow requires sys_ids for relationships, which are only available after record creation.
    By batching creates in phases, we optimize for speed compared to sequential one-by-one processing.

    Alternative approach (slower but potentially transactional): A single web service call
    that accepts a tree structure and processes everything in one operation. This is not
    implemented here as it would be slower for small updates, especially through the Table API.

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
    # Note: Both gateways and devices use cmdb_ci_netgear table, but we track them separately
    id_mapping: dict[str, dict[str, str]] = {
        TABLE_GATEWAY_CI: {},  # Gateways in cmdb_ci_netgear
        TABLE_LOCATION: {},  # Locations in cmn_location
        TABLE_NETWORK_DEVICE_CI: {},  # Devices also in cmdb_ci_netgear (same table as gateways)
        TABLE_ENDPOINT: {},  # Endpoints in cmdb_ci
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

    # Phase 2: Create relationships using cmdb_rel_ci table
    # Location → Gateway relationship (Location is Managed by Gateway)
    if locations:
        for location in locations:
            location_sys_id = id_mapping[TABLE_LOCATION].get(location.u_unifi_source_id)
            if not location_sys_id:
                print(
                    f"⚠️  Phase 2: Location {location.u_unifi_source_id} not found in id_mapping"
                )
                continue

            # Create relationship: Location is Managed by Gateway
            if location.host_id:
                gateway_sys_id = None
                for source_id, sys_id in id_mapping[TABLE_GATEWAY_CI].items():
                    if source_id == location.host_id:
                        gateway_sys_id = sys_id  # sys_id IS the ID in ServiceNow
                        break
                if gateway_sys_id:
                    # Create relationship: parent (Gateway) → child (Location)
                    rel_data = {
                        "parent": gateway_sys_id,
                        "child": location_sys_id,
                        "type": "Managed by::Manages",
                    }
                    try:
                        client.create_record("cmdb_rel_ci", rel_data)
                        print(
                            f"✅ Phase 2: Created relationship Gateway → Location ({location.u_unifi_source_id})"
                        )
                    except Exception as e:
                        print(
                            f"⚠️  Phase 2: Failed to create relationship for location {location.u_unifi_source_id}: {e}"
                        )
                else:
                    print(
                        f"⚠️  Phase 2: Gateway {location.host_id} not found in id_mapping for location {location.u_unifi_source_id}"
                    )
            else:
                print(
                    f"⚠️  Phase 2: Location {location.u_unifi_source_id} has no host_id set"
                )

    # Device → Gateway and Device → Location relationships
    if devices:
        for device in devices:
            device_sys_id = id_mapping[TABLE_NETWORK_DEVICE_CI].get(
                device.u_unifi_source_id
            )
            if not device_sys_id:
                print(
                    f"⚠️  Phase 2: Device {device.u_unifi_source_id} not found in id_mapping"
                )
                continue

            # Create relationship: Device is Managed by Gateway
            if device.host_id:
                gateway_sys_id = None
                for source_id, sys_id in id_mapping[TABLE_GATEWAY_CI].items():
                    if source_id == device.host_id:
                        gateway_sys_id = sys_id  # sys_id IS the ID in ServiceNow
                        break
                if gateway_sys_id:
                    rel_data = {
                        "parent": gateway_sys_id,
                        "child": device_sys_id,
                        "type": "Managed by::Manages",
                    }
                    try:
                        client.create_record("cmdb_rel_ci", rel_data)
                        print(
                            f"✅ Phase 2: Created relationship Gateway → Device ({device.u_unifi_source_id})"
                        )
                    except Exception as e:
                        print(
                            f"⚠️  Phase 2: Failed to create Gateway→Device relationship: {e}"
                        )

            # Create relationship: Device is Located at Site
            if device.site_id:
                location_sys_id = None
                for source_id, sys_id in id_mapping[TABLE_LOCATION].items():
                    if source_id == device.site_id:
                        location_sys_id = sys_id  # sys_id IS the ID in ServiceNow
                        break
                if location_sys_id:
                    rel_data = {
                        "parent": location_sys_id,
                        "child": device_sys_id,
                        "type": "Located in::Contains",
                    }
                    try:
                        client.create_record("cmdb_rel_ci", rel_data)
                        print(
                            f"✅ Phase 2: Created relationship Location → Device ({device.u_unifi_source_id})"
                        )
                    except Exception as e:
                        print(
                            f"⚠️  Phase 2: Failed to create Location→Device relationship: {e}"
                        )

    # Endpoint → Location and Endpoint → Device relationships
    if endpoints:
        for endpoint in endpoints:
            endpoint_sys_id = id_mapping[TABLE_ENDPOINT].get(endpoint.u_unifi_source_id)
            if not endpoint_sys_id:
                print(
                    f"⚠️  Phase 2: Endpoint {endpoint.u_unifi_source_id} not found in id_mapping"
                )
                continue

            # Create relationship: Endpoint is Located at Site
            if endpoint.site_id:
                location_sys_id = None
                for source_id, sys_id in id_mapping[TABLE_LOCATION].items():
                    if source_id == endpoint.site_id:
                        location_sys_id = sys_id  # sys_id IS the ID in ServiceNow
                        break
                if location_sys_id:
                    rel_data = {
                        "parent": location_sys_id,
                        "child": endpoint_sys_id,
                        "type": "Located in::Contains",
                    }
                    try:
                        client.create_record("cmdb_rel_ci", rel_data)
                        print(
                            f"✅ Phase 2: Created relationship Location → Endpoint ({endpoint.u_unifi_source_id})"
                        )
                    except Exception as e:
                        print(
                            f"⚠️  Phase 2: Failed to create Location→Endpoint relationship: {e}"
                        )

            # Create relationship: Endpoint Connects through Device
            if endpoint.device_id:
                device_sys_id = None
                for source_id, sys_id in id_mapping[TABLE_NETWORK_DEVICE_CI].items():
                    if source_id == endpoint.device_id:
                        device_sys_id = sys_id  # sys_id IS the ID in ServiceNow
                        break
                if device_sys_id:
                    rel_data = {
                        "parent": device_sys_id,
                        "child": endpoint_sys_id,
                        "type": "Connects to::Connected by",
                    }
                    try:
                        client.create_record("cmdb_rel_ci", rel_data)
                        print(
                            f"✅ Phase 2: Created relationship Device → Endpoint ({endpoint.u_unifi_source_id})"
                        )
                    except Exception as e:
                        print(
                            f"⚠️  Phase 2: Failed to create Device→Endpoint relationship: {e}"
                        )

    return id_mapping
