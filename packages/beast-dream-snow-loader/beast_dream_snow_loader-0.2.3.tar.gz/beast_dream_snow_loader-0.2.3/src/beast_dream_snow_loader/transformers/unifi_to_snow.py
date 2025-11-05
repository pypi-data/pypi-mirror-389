"""UniFi to ServiceNow transformation functions."""

from beast_dream_snow_loader.models.servicenow import (
    ServiceNowEndpoint,
    ServiceNowGatewayCI,
    ServiceNowLocation,
    ServiceNowNetworkDeviceCI,
)
from beast_dream_snow_loader.models.unifi import (
    UniFiClient,
    UniFiDevice,
    UniFiHost,
    UniFiSite,
)
from beast_dream_snow_loader.transformers.schema_mapper import (
    FieldMappingConfig,
    apply_field_mapping,
)


def transform_host(unifi_host: UniFiHost) -> ServiceNowGatewayCI:
    """Transform UniFi host to ServiceNow gateway CI.

    Args:
        unifi_host: UniFi host data model

    Returns:
        ServiceNow gateway CI model with flattened fields
    """
    config = FieldMappingConfig()
    mappings = config.get_host_mappings()

    # Convert Pydantic model to dict for mapping (includes nested structures)
    host_dict = unifi_host.model_dump()

    # Apply field mappings (handles nested field extraction)
    mapped_data = apply_field_mapping(host_dict, mappings)

    # Ensure required fields are present (fallbacks)
    if "u_unifi_source_id" not in mapped_data:
        mapped_data["u_unifi_source_id"] = unifi_host.id
    if "ip_address" not in mapped_data:
        mapped_data["ip_address"] = unifi_host.ipAddress
    if "hostname" not in mapped_data and unifi_host.reportedState:
        mapped_data["hostname"] = unifi_host.reportedState.hostname
    if "name" not in mapped_data and unifi_host.reportedState:
        mapped_data["name"] = unifi_host.reportedState.name

    # Handle deeply nested hardware fields
    if unifi_host.reportedState and hasattr(unifi_host.reportedState, "model_dump"):
        reported_state = unifi_host.reportedState.model_dump()
        if "hardware" in reported_state and isinstance(
            reported_state["hardware"], dict
        ):
            hardware = reported_state["hardware"]
            if "mac" in hardware and "mac_address" not in mapped_data:
                mapped_data["mac_address"] = hardware["mac"]
            if "serialno" in hardware and "serial_number" not in mapped_data:
                mapped_data["serial_number"] = hardware["serialno"]

    # Preserve raw source data for audit/reconciliation
    if "u_unifi_raw_data" not in mapped_data:
        mapped_data["u_unifi_raw_data"] = unifi_host.model_dump()

    # Validate and return ServiceNow model
    return ServiceNowGatewayCI(**mapped_data)


def transform_site(unifi_site: UniFiSite) -> ServiceNowLocation:
    """Transform UniFi site to ServiceNow location.

    Args:
        unifi_site: UniFi site data model

    Returns:
        ServiceNow location model with flattened fields
    """
    config = FieldMappingConfig()
    mappings = config.get_site_mappings()

    # Convert Pydantic model to dict for mapping (includes nested structures)
    site_dict = unifi_site.model_dump()

    # Apply field mappings (handles nested field extraction)
    mapped_data = apply_field_mapping(site_dict, mappings)

    # Ensure required fields are present (fallbacks)
    if "u_unifi_source_id" not in mapped_data:
        mapped_data["u_unifi_source_id"] = unifi_site.siteId
    if "name" not in mapped_data and unifi_site.meta:
        mapped_data["name"] = unifi_site.meta.name
    if "description" not in mapped_data and unifi_site.meta:
        mapped_data["description"] = unifi_site.meta.desc
    if "timezone" not in mapped_data and unifi_site.meta:
        mapped_data["timezone"] = unifi_site.meta.timezone

    # Relationships (host_id, site_id, device_id) are handled in Phase 2 of two-phase linking
    # Do NOT set relationship fields during transformation - they will be None until Phase 2
    # The loader will set these using sys_ids after all records are created

    # Preserve raw source data for audit/reconciliation
    if "u_unifi_raw_data" not in mapped_data:
        mapped_data["u_unifi_raw_data"] = unifi_site.model_dump()

    # Validate and return ServiceNow model
    return ServiceNowLocation(**mapped_data)


def transform_device(unifi_device: UniFiDevice) -> ServiceNowNetworkDeviceCI:
    """Transform UniFi device to ServiceNow network device CI.

    Args:
        unifi_device: UniFi device data model

    Returns:
        ServiceNow network device CI model
    """
    config = FieldMappingConfig()
    mappings = config.get_device_mappings()

    # Convert Pydantic model to dict for mapping
    device_dict = unifi_device.model_dump()

    # Apply field mappings
    mapped_data = apply_field_mapping(device_dict, mappings)

    # Ensure required fields are present
    if "u_unifi_source_id" not in mapped_data:
        mapped_data["u_unifi_source_id"] = unifi_device.hostId
    if "name" not in mapped_data:
        mapped_data["name"] = unifi_device.hostId  # Fallback to hostId if no name
    if "mac_address" not in mapped_data:
        # Try to get from extra fields or use fallback
        device_dict = unifi_device.model_dump()
        if "mac" in device_dict:
            mapped_data["mac_address"] = device_dict["mac"]
        else:
            # Required field - use placeholder if not available
            mapped_data["mac_address"] = "unknown"

    # Relationships (host_id, site_id, device_id) are handled in Phase 2 of two-phase linking
    # Do NOT set relationship fields during transformation - they will be None until Phase 2
    # The loader will set these using sys_ids after all records are created

    # Preserve raw source data for audit/reconciliation
    if "u_unifi_raw_data" not in mapped_data:
        mapped_data["u_unifi_raw_data"] = unifi_device.model_dump()

    # Validate and return ServiceNow model
    return ServiceNowNetworkDeviceCI(**mapped_data)


def transform_client(unifi_client: UniFiClient) -> ServiceNowEndpoint:
    """Transform UniFi client to ServiceNow endpoint.

    Args:
        unifi_client: UniFi client data model

    Returns:
        ServiceNow endpoint model
    """
    config = FieldMappingConfig()
    mappings = config.get_client_mappings()

    # Convert Pydantic model to dict for mapping
    client_dict = unifi_client.model_dump()

    # Apply field mappings
    mapped_data = apply_field_mapping(client_dict, mappings)

    # Ensure required fields are present
    if "u_unifi_source_id" not in mapped_data:
        # Generate source ID from hostname or MAC if needed
        mapped_data["u_unifi_source_id"] = unifi_client.hostname or unifi_client.mac
    if "hostname" not in mapped_data:
        mapped_data["hostname"] = unifi_client.hostname
    if "ip_address" not in mapped_data:
        mapped_data["ip_address"] = unifi_client.ip
    if "mac_address" not in mapped_data:
        mapped_data["mac_address"] = unifi_client.mac

    # Relationships (host_id, site_id, device_id) are handled in Phase 2 of two-phase linking
    # Do NOT set relationship fields during transformation - they will be None until Phase 2
    # The loader will set these using sys_ids after all records are created

    # Preserve raw source data for audit/reconciliation
    if "u_unifi_raw_data" not in mapped_data:
        mapped_data["u_unifi_raw_data"] = unifi_client.model_dump()

    # Validate and return ServiceNow model
    return ServiceNowEndpoint(**mapped_data)
