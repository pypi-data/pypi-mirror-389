"""ServiceNow CMDB data models using Pydantic for validation."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ServiceNowGatewayCI(BaseModel):
    """ServiceNow network gateway configuration item model.

    Note: sys_id is optional and should NOT be provided on create.
    ServiceNow auto-generates sys_id. Use u_unifi_source_id for tracking source.
    See docs/servicenow_constraints.md for assumptions.
    """

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    sys_id: str | None = Field(
        None,
        description="ServiceNow system identifier (auto-generated, for updates only)",
    )
    u_unifi_source_id: str = Field(
        ..., description="UniFi source identifier (required, for tracking)"
    )
    u_unifi_raw_data: dict[str, Any] | None = Field(
        None, description="Raw UniFi source data (JSON) for audit/reconciliation"
    )
    name: str = Field(..., description="Gateway name")
    ip_address: str = Field(..., description="IP address")
    hostname: str = Field(..., description="Hostname")
    firmware_version: str | None = Field(None, description="Firmware version")
    hardware_id: str | None = Field(None, description="Hardware identifier")
    mac_address: str | None = Field(None, description="MAC address")
    serial_number: str | None = Field(None, description="Serial number")
    state: str | None = Field(None, description="Device state")


class ServiceNowLocation(BaseModel):
    """ServiceNow location/group record model.

    Note: sys_id is optional and should NOT be provided on create.
    ServiceNow auto-generates sys_id. Use u_unifi_source_id for tracking source.
    See docs/servicenow_constraints.md for assumptions.
    """

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    sys_id: str | None = Field(
        None,
        description="ServiceNow system identifier (auto-generated, for updates only)",
    )
    u_unifi_source_id: str = Field(
        ..., description="UniFi source identifier (required, for tracking)"
    )
    u_unifi_raw_data: dict[str, Any] | None = Field(
        None, description="Raw UniFi source data (JSON) for audit/reconciliation"
    )
    name: str = Field(..., description="Location name")
    description: str = Field(..., description="Location description")
    timezone: str = Field(..., description="Timezone")
    host_id: str | None = Field(
        None,
        description="Foreign key to gateway (sys_id reference). Note: Custom field must exist in ServiceNow (e.g., u_host_id)",
    )


class ServiceNowNetworkDeviceCI(BaseModel):
    """ServiceNow network device configuration item model.

    Note: sys_id is optional and should NOT be provided on create.
    ServiceNow auto-generates sys_id. Use u_unifi_source_id for tracking source.
    See docs/servicenow_constraints.md for assumptions.
    """

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    sys_id: str | None = Field(
        None,
        description="ServiceNow system identifier (auto-generated, for updates only)",
    )
    u_unifi_source_id: str = Field(
        ..., description="UniFi source identifier (required, for tracking)"
    )
    u_unifi_raw_data: dict[str, Any] | None = Field(
        None, description="Raw UniFi source data (JSON) for audit/reconciliation"
    )
    name: str = Field(..., description="Device name")
    mac_address: str = Field(..., description="MAC address")
    serial_number: str | None = Field(None, description="Serial number")
    model: str | None = Field(None, description="Device model")
    site_id: str | None = Field(
        None,
        description="Foreign key to site (sys_id reference). Note: Custom field must exist in ServiceNow (e.g., u_site_id)",
    )
    host_id: str | None = Field(
        None,
        description="Foreign key to host (sys_id reference). Note: Custom field must exist in ServiceNow (e.g., u_host_id)",
    )


class ServiceNowEndpoint(BaseModel):
    """ServiceNow endpoint/client record model.

    Note: sys_id is optional and should NOT be provided on create.
    ServiceNow auto-generates sys_id. Use u_unifi_source_id for tracking source.
    See docs/servicenow_constraints.md for assumptions.
    """

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    sys_id: str | None = Field(
        None,
        description="ServiceNow system identifier (auto-generated, for updates only)",
    )
    u_unifi_source_id: str = Field(
        ..., description="UniFi source identifier (required, for tracking)"
    )
    u_unifi_raw_data: dict[str, Any] | None = Field(
        None, description="Raw UniFi source data (JSON) for audit/reconciliation"
    )
    hostname: str = Field(..., description="Hostname")
    ip_address: str = Field(..., description="IP address")
    mac_address: str = Field(..., description="MAC address")
    device_type: str | None = Field(
        None, description="Device type (computer, phone, IoT, etc.)"
    )
    site_id: str | None = Field(
        None,
        description="Foreign key to site (sys_id reference). Note: Custom field must exist in ServiceNow (e.g., u_site_id)",
    )
    device_id: str | None = Field(
        None,
        description="Foreign key to device (sys_id reference). Note: Custom field must exist in ServiceNow (e.g., u_device_id)",
    )
