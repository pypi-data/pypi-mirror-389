"""UniFi API data models using Pydantic for validation."""

from pydantic import BaseModel, ConfigDict, Field


class ReportedState(BaseModel):
    """Nested model for reportedState fields from UniFi API."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    controller_uuid: str = Field(..., description="Controller UUID")
    host_type: int = Field(..., description="Host type")
    hostname: str = Field(..., description="Hostname")
    mgmt_port: int = Field(..., description="Management port")
    name: str = Field(..., description="Device name")
    state: str = Field(..., description="Device state")
    version: str = Field(..., description="Software version")
    firmware_version: float | None = Field(None, description="Firmware version")
    hardware_id: str | None = Field(None, description="Hardware ID")
    inform_port: float | None = Field(None, description="Inform port")
    override_inform_host: str | None = Field(None, description="Override inform host")
    release_channel: str | None = Field(None, description="Release channel")
    anonid: str | None = Field(None, description="Anonymous ID")


class UserData(BaseModel):
    """Nested model for userData fields from UniFi API."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    status: str = Field(..., description="User status")
    email: str | None = Field(None, description="User email")
    fullName: str | None = Field(None, description="Full name")
    localId: str | None = Field(None, description="Local ID")
    role: str | None = Field(None, description="User role")
    roleId: str | None = Field(None, description="Role ID")


class UniFiHost(BaseModel):
    """UniFi gateway/host data model."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    id: str = Field(..., description="Unique host identifier")
    hardwareId: str = Field(..., description="Hardware identifier")
    type: str = Field(..., description="Host type")
    ipAddress: str = Field(..., description="IP address")
    owner: bool = Field(..., description="Owner flag")
    isBlocked: bool = Field(..., description="Blocked flag")
    registrationTime: str = Field(..., description="Registration timestamp")
    lastConnectionStateChange: str = Field(
        ..., description="Last connection state change timestamp"
    )
    latestBackupTime: str = Field(..., description="Latest backup timestamp")
    reportedState: ReportedState = Field(..., description="Reported state data")
    userData: UserData = Field(..., description="User data")


class SiteCounts(BaseModel):
    """Nested model for statistics.counts fields from UniFi API."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    criticalNotification: int = Field(..., description="Critical notifications count")
    gatewayDevice: int = Field(..., description="Gateway device count")
    guestClient: int = Field(..., description="Guest client count")
    lanConfiguration: int = Field(..., description="LAN configuration count")
    offlineDevice: int = Field(..., description="Offline device count")
    offlineGatewayDevice: int = Field(..., description="Offline gateway device count")
    offlineWifiDevice: int = Field(..., description="Offline WiFi device count")
    offlineWiredDevice: int = Field(..., description="Offline wired device count")
    pendingUpdateDevice: int = Field(..., description="Pending update device count")
    totalDevice: int = Field(..., description="Total device count")
    wanConfiguration: int = Field(..., description="WAN configuration count")
    wifiClient: int = Field(..., description="WiFi client count")
    wifiConfiguration: int = Field(..., description="WiFi configuration count")
    wifiDevice: int = Field(..., description="WiFi device count")
    wiredClient: int = Field(..., description="Wired client count")
    wiredDevice: int = Field(..., description="Wired device count")


class SiteGateway(BaseModel):
    """Nested model for statistics.gateway fields from UniFi API."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    hardwareId: str | None = Field(None, description="Gateway hardware ID")
    inspectionState: str | None = Field(None, description="Inspection state")
    ipsMode: str | None = Field(None, description="IPS mode")
    shortname: str | None = Field(None, description="Gateway shortname")


class SitePercentages(BaseModel):
    """Nested model for statistics.percentages fields from UniFi API."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    txRetry: float | None = Field(None, description="TX retry percentage")
    wanUptime: float | None = Field(None, description="WAN uptime percentage")


class SiteStatistics(BaseModel):
    """Nested model for statistics fields from UniFi API."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    counts: SiteCounts = Field(..., description="Site counts statistics")
    gateway: SiteGateway | None = Field(None, description="Gateway statistics")
    percentages: SitePercentages | None = Field(
        None, description="Percentage statistics"
    )


class SiteMeta(BaseModel):
    """Nested model for meta fields from UniFi API."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    desc: str = Field(..., description="Site description")
    name: str = Field(..., description="Site name")
    timezone: str = Field(..., description="Site timezone")
    gatewayMac: str | None = Field(None, description="Gateway MAC address")


class UniFiSite(BaseModel):
    """UniFi site/organization data model."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    siteId: str = Field(..., description="Unique site identifier")
    hostId: str = Field(..., description="Host identifier")
    permission: str = Field(..., description="Permission level")
    isOwner: bool = Field(..., description="Owner flag")
    meta: SiteMeta = Field(..., description="Site metadata")
    statistics: SiteStatistics = Field(..., description="Site statistics")


class UniFiDevice(BaseModel):
    """UniFi network device data model."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    hostId: str = Field(..., description="Host identifier")
    updatedAt: str = Field(..., description="Last update timestamp")


class UniFiClient(BaseModel):
    """UniFi client/endpoint data model."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields from API

    hostname: str = Field(..., description="Client hostname")
    ip: str = Field(..., description="Client IP address")
    mac: str = Field(..., description="Client MAC address")
    deviceType: str | None = Field(
        None, description="Device type (computer, phone, IoT, etc.)"
    )
    siteId: str | None = Field(None, description="Site identifier")
    deviceId: str | None = Field(None, description="Device identifier")
