"""Schema mapping configuration for UniFi → ServiceNow transformation."""

from collections.abc import Callable


class FieldMappingConfig:
    """Configuration class defining UniFi → ServiceNow field mappings."""

    def __init__(self):
        """Initialize default field mappings."""
        self._host_mappings = self._get_default_host_mappings()
        self._site_mappings = self._get_default_site_mappings()
        self._device_mappings = self._get_default_device_mappings()
        self._client_mappings = self._get_default_client_mappings()

    def _get_default_host_mappings(self) -> dict[str, str]:
        """Get default field mappings for hosts → gateway CI."""
        return {
            "id": "u_unifi_source_id",  # Map to source ID, not sys_id
            "hardwareId": "hardware_id",
            "reportedState.hostname": "hostname",
            "ipAddress": "ip_address",
            "reportedState.version": "firmware_version",
            "reportedState.name": "name",
            "reportedState.state": "state",
            "reportedState.hardware.mac": "mac_address",
            "reportedState.hardware.serialno": "serial_number",
        }

    def _get_default_site_mappings(self) -> dict[str, str]:
        """Get default field mappings for sites → location."""
        return {
            "siteId": "u_unifi_source_id",  # Map to source ID, not sys_id
            "meta.name": "name",
            "meta.desc": "description",
            "meta.timezone": "timezone",
            # Note: hostId relationship handled separately (two-phase linking)
        }

    def _get_default_device_mappings(self) -> dict[str, str]:
        """Get default field mappings for devices → network device CI."""
        return {
            "hostId": "u_unifi_source_id",  # Map to source ID, not sys_id
            # Additional fields may come from API
            "mac": "mac_address",
            "serial": "serial_number",
            "model": "model",
            # Note: Relationships (host_id, site_id) handled separately (two-phase linking)
        }

    def _get_default_client_mappings(self) -> dict[str, str]:
        """Get default field mappings for clients → endpoint."""
        return {
            # Generate source ID from hostname or MAC
            "hostname": "hostname",
            "ip": "ip_address",
            "mac": "mac_address",
            "deviceType": "device_type",
            # Note: Relationships (site_id, device_id) handled separately (two-phase linking)
        }

    def get_host_mappings(self) -> dict[str, str]:
        """Get host → gateway CI field mappings."""
        return dict(self._host_mappings)

    def get_site_mappings(self) -> dict[str, str]:
        """Get site → location field mappings."""
        return dict(self._site_mappings)

    def get_device_mappings(self) -> dict[str, str]:
        """Get device → network device CI field mappings."""
        return dict(self._device_mappings)

    def get_client_mappings(self) -> dict[str, str]:
        """Get client → endpoint field mappings."""
        return dict(self._client_mappings)


def flatten_nested_field(field_path: str) -> str:
    """Flatten nested field path to ServiceNow-compatible field name.

    Examples:
        "reportedState.hostname" → "hostname"
        "reportedState.hardware.mac" → "hardware_mac_address"
        "reportedState.autoUpdate.schedule.day" → "auto_update_schedule_day"
    """
    parts = field_path.split(".")
    if len(parts) == 1:
        return parts[0]

    # Common prefixes to drop (reportedState, meta, userData, statistics)
    common_prefixes = ["reportedState", "meta", "userData", "statistics"]

    # If starts with common prefix, drop it
    if parts[0] in common_prefixes:
        parts = parts[1:]

    if len(parts) == 0:
        return field_path  # Fallback

    if len(parts) == 1:
        return parts[0]

    # Convert camelCase to snake_case for each part
    result_parts = []
    for part in parts:
        # Simple camelCase conversion (basic)
        snake = "".join(["_" + c.lower() if c.isupper() else c for c in part]).lstrip(
            "_"
        )
        result_parts.append(snake)

    return "_".join(result_parts)


def get_field_mapping(source_field: str, mappings: dict[str, str]) -> str | None:
    """Get target field name for a source field.

    Returns the mapped target field if found, otherwise returns None.
    """
    return mappings.get(source_field)


def apply_field_mapping(
    source_data: dict,
    mappings: dict[str, str],
    flatten_func: Callable[[str], str] | None = None,
) -> dict:
    """Apply field mappings to source data.

    Args:
        source_data: Source data dictionary
        mappings: Field mappings (source → target)
        flatten_func: Optional function to flatten nested fields

    Returns:
        Dictionary with mapped field names
    """
    if flatten_func is None:
        flatten_func = flatten_nested_field

    result = {}
    for source_path, target_field in mappings.items():
        # Get value from nested path if needed
        value = _get_nested_value(source_data, source_path)
        if value is not None:
            result[target_field] = value

    return result


def _get_nested_value(data: dict, path: str) -> str | None:
    """Get value from nested dictionary path.

    Example:
        data = {"reportedState": {"hostname": "test"}}
        path = "reportedState.hostname"
        returns "test"
    """
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current if isinstance(current, (str, int, float, bool)) else str(current)
