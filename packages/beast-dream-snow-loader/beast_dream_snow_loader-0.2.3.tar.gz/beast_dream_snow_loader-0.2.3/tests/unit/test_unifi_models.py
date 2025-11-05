"""Unit tests for UniFi data models."""

import pytest

from beast_dream_snow_loader.models.unifi import (
    UniFiClient,
    UniFiDevice,
    UniFiHost,
    UniFiSite,
)


class TestUniFiHost:
    """Test UniFiHost model validation and structure."""

    def test_host_validates_with_minimal_data(self):
        """Test that UniFiHost validates with minimal required fields."""
        # RED: This test will fail until model is implemented
        host_data = {
            "id": "test-host-id",
            "hardwareId": "test-hardware-id",
            "type": "gateway",
            "ipAddress": "192.168.1.1",
            "owner": True,
            "isBlocked": False,
            "registrationTime": "2025-01-01T00:00:00Z",
            "lastConnectionStateChange": "2025-01-01T00:00:00Z",
            "latestBackupTime": "2025-01-01T00:00:00Z",
            "userData": {"status": "active"},
            "reportedState": {
                "controller_uuid": "test-uuid",
                "host_type": 1,
                "hostname": "test-hostname",
                "mgmt_port": 8443,
                "name": "Test Host",
                "state": "online",
                "version": "1.0.0",
            },
        }
        host = UniFiHost(**host_data)
        assert host.id == "test-host-id"
        assert host.hardwareId == "test-hardware-id"
        assert host.type == "gateway"
        assert host.ipAddress == "192.168.1.1"

    def test_host_validates_nested_reported_state(self):
        """Test that nested reportedState fields are properly structured."""
        host_data = {
            "id": "test-host-id",
            "hardwareId": "test-hardware-id",
            "type": "gateway",
            "ipAddress": "192.168.1.1",
            "owner": True,
            "isBlocked": False,
            "registrationTime": "2025-01-01T00:00:00Z",
            "lastConnectionStateChange": "2025-01-01T00:00:00Z",
            "latestBackupTime": "2025-01-01T00:00:00Z",
            "userData": {"status": "active"},
            "reportedState": {
                "controller_uuid": "test-uuid",
                "host_type": 1,
                "hostname": "test-hostname",
                "mgmt_port": 8443,
                "name": "Test Host",
                "state": "online",
                "version": "1.0.0",
                "firmware_version": 1.5,
                "hardware_id": "UDM-Pro",
            },
        }
        host = UniFiHost(**host_data)
        assert host.reportedState.hostname == "test-hostname"
        assert host.reportedState.firmware_version == 1.5
        assert host.reportedState.hardware_id == "UDM-Pro"

    def test_host_validates_nested_user_data(self):
        """Test that nested userData fields are properly structured."""
        host_data = {
            "id": "test-host-id",
            "hardwareId": "test-hardware-id",
            "type": "gateway",
            "ipAddress": "192.168.1.1",
            "owner": True,
            "isBlocked": False,
            "registrationTime": "2025-01-01T00:00:00Z",
            "lastConnectionStateChange": "2025-01-01T00:00:00Z",
            "latestBackupTime": "2025-01-01T00:00:00Z",
            "userData": {
                "status": "active",
                "email": "test@example.com",
                "fullName": "Test User",
                "role": "admin",
            },
            "reportedState": {
                "controller_uuid": "test-uuid",
                "host_type": 1,
                "hostname": "test-hostname",
                "mgmt_port": 8443,
                "name": "Test Host",
                "state": "online",
                "version": "1.0.0",
            },
        }
        host = UniFiHost(**host_data)
        assert host.userData.status == "active"
        assert host.userData.email == "test@example.com"
        assert host.userData.fullName == "Test User"

    def test_host_handles_missing_optional_fields(self):
        """Test that missing optional fields are handled gracefully."""
        host_data = {
            "id": "test-host-id",
            "hardwareId": "test-hardware-id",
            "type": "gateway",
            "ipAddress": "192.168.1.1",
            "owner": True,
            "isBlocked": False,
            "registrationTime": "2025-01-01T00:00:00Z",
            "lastConnectionStateChange": "2025-01-01T00:00:00Z",
            "latestBackupTime": "2025-01-01T00:00:00Z",
            "userData": {"status": "active"},
            "reportedState": {
                "controller_uuid": "test-uuid",
                "host_type": 1,
                "hostname": "test-hostname",
                "mgmt_port": 8443,
                "name": "Test Host",
                "state": "online",
                "version": "1.0.0",
            },
        }
        host = UniFiHost(**host_data)
        # Optional fields should be None or have defaults
        assert host.reportedState.firmware_version is None or isinstance(
            host.reportedState.firmware_version, float
        )

    def test_host_rejects_invalid_data(self):
        """Test that invalid data raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UniFiHost(
                id="test-id",
                # Missing required fields
            )


class TestUniFiSite:
    """Test UniFiSite model validation and structure."""

    def test_site_validates_with_minimal_data(self):
        """Test that UniFiSite validates with minimal required fields."""
        site_data = {
            "siteId": "test-site-id",
            "hostId": "test-host-id",
            "permission": "read",
            "isOwner": True,
            "meta": {
                "desc": "Test site description",
                "name": "Test Site",
                "timezone": "America/New_York",
            },
            "statistics": {
                "counts": {
                    "criticalNotification": 0,
                    "gatewayDevice": 1,
                    "guestClient": 0,
                    "lanConfiguration": 0,
                    "offlineDevice": 0,
                    "offlineGatewayDevice": 0,
                    "offlineWifiDevice": 0,
                    "offlineWiredDevice": 0,
                    "pendingUpdateDevice": 0,
                    "totalDevice": 5,
                    "wanConfiguration": 1,
                    "wifiClient": 10,
                    "wifiConfiguration": 1,
                    "wifiDevice": 3,
                    "wiredClient": 2,
                    "wiredDevice": 2,
                },
            },
        }
        site = UniFiSite(**site_data)
        assert site.siteId == "test-site-id"
        assert site.hostId == "test-host-id"
        assert site.permission == "read"
        assert site.isOwner is True

    def test_site_validates_nested_meta(self):
        """Test that nested meta fields are properly structured."""
        site_data = {
            "siteId": "test-site-id",
            "hostId": "test-host-id",
            "permission": "read",
            "isOwner": True,
            "meta": {
                "desc": "Test site description",
                "name": "Test Site",
                "timezone": "America/New_York",
                "gatewayMac": "00:11:22:33:44:55",
            },
            "statistics": {
                "counts": {
                    "criticalNotification": 0,
                    "gatewayDevice": 1,
                    "guestClient": 0,
                    "lanConfiguration": 0,
                    "offlineDevice": 0,
                    "offlineGatewayDevice": 0,
                    "offlineWifiDevice": 0,
                    "offlineWiredDevice": 0,
                    "pendingUpdateDevice": 0,
                    "totalDevice": 5,
                    "wanConfiguration": 1,
                    "wifiClient": 10,
                    "wifiConfiguration": 1,
                    "wifiDevice": 3,
                    "wiredClient": 2,
                    "wiredDevice": 2,
                },
            },
        }
        site = UniFiSite(**site_data)
        assert site.meta.name == "Test Site"
        assert site.meta.desc == "Test site description"
        assert site.meta.timezone == "America/New_York"
        assert site.meta.gatewayMac == "00:11:22:33:44:55"

    def test_site_validates_nested_statistics(self):
        """Test that nested statistics fields are properly structured."""
        site_data = {
            "siteId": "test-site-id",
            "hostId": "test-host-id",
            "permission": "read",
            "isOwner": True,
            "meta": {
                "desc": "Test site description",
                "name": "Test Site",
                "timezone": "America/New_York",
            },
            "statistics": {
                "counts": {
                    "criticalNotification": 5,
                    "gatewayDevice": 1,
                    "guestClient": 3,
                    "lanConfiguration": 2,
                    "offlineDevice": 1,
                    "offlineGatewayDevice": 0,
                    "offlineWifiDevice": 1,
                    "offlineWiredDevice": 0,
                    "pendingUpdateDevice": 2,
                    "totalDevice": 10,
                    "wanConfiguration": 1,
                    "wifiClient": 15,
                    "wifiConfiguration": 1,
                    "wifiDevice": 5,
                    "wiredClient": 5,
                    "wiredDevice": 5,
                },
                "gateway": {
                    "hardwareId": "UDM-Pro",
                    "shortname": "udm-pro",
                },
                "percentages": {
                    "txRetry": 0.5,
                    "wanUptime": 99.9,
                },
            },
        }
        site = UniFiSite(**site_data)
        assert site.statistics.counts.totalDevice == 10
        assert site.statistics.counts.criticalNotification == 5
        assert site.statistics.gateway.hardwareId == "UDM-Pro"
        assert site.statistics.percentages.wanUptime == 99.9

    def test_site_handles_missing_optional_fields(self):
        """Test that missing optional fields are handled gracefully."""
        site_data = {
            "siteId": "test-site-id",
            "hostId": "test-host-id",
            "permission": "read",
            "isOwner": True,
            "meta": {
                "desc": "Test site description",
                "name": "Test Site",
                "timezone": "America/New_York",
            },
            "statistics": {
                "counts": {
                    "criticalNotification": 0,
                    "gatewayDevice": 1,
                    "guestClient": 0,
                    "lanConfiguration": 0,
                    "offlineDevice": 0,
                    "offlineGatewayDevice": 0,
                    "offlineWifiDevice": 0,
                    "offlineWiredDevice": 0,
                    "pendingUpdateDevice": 0,
                    "totalDevice": 5,
                    "wanConfiguration": 1,
                    "wifiClient": 10,
                    "wifiConfiguration": 1,
                    "wifiDevice": 3,
                    "wiredClient": 2,
                    "wiredDevice": 2,
                },
            },
        }
        site = UniFiSite(**site_data)
        # Optional fields should be None or have defaults
        assert site.meta.gatewayMac is None or isinstance(site.meta.gatewayMac, str)

    def test_site_rejects_invalid_data(self):
        """Test that invalid data raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UniFiSite(
                siteId="test-id",
                # Missing required fields
            )


class TestUniFiDevice:
    """Test UniFiDevice model validation and structure."""

    def test_device_validates_with_minimal_data(self):
        """Test that UniFiDevice validates with minimal required fields."""
        device_data = {
            "hostId": "test-host-id",
            "updatedAt": "2025-01-01T00:00:00Z",
        }
        device = UniFiDevice(**device_data)
        assert device.hostId == "test-host-id"
        assert device.updatedAt == "2025-01-01T00:00:00Z"

    def test_device_handles_extra_fields(self):
        """Test that UniFiDevice accepts additional fields (extensible)."""
        device_data = {
            "hostId": "test-host-id",
            "updatedAt": "2025-01-01T00:00:00Z",
            "mac": "00:11:22:33:44:55",
            "model": "USW-Pro-48",
            "serial": "ABC123",
        }
        device = UniFiDevice(**device_data)
        assert device.hostId == "test-host-id"
        assert device.updatedAt == "2025-01-01T00:00:00Z"
        # Extra fields should be accessible via model_dump or __pydantic_fields__
        assert hasattr(device, "mac") or "mac" in device.model_dump()

    def test_device_rejects_invalid_data(self):
        """Test that invalid data raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UniFiDevice(
                hostId="test-id",
                # Missing required updatedAt field
            )


class TestUniFiClient:
    """Test UniFiClient model validation and structure."""

    def test_client_validates_with_minimal_data(self):
        """Test that UniFiClient validates with minimal required fields."""
        client_data = {
            "hostname": "test-client",
            "ip": "192.168.1.100",
            "mac": "00:11:22:33:44:55",
        }
        client = UniFiClient(**client_data)
        assert client.hostname == "test-client"
        assert client.ip == "192.168.1.100"
        assert client.mac == "00:11:22:33:44:55"

    def test_client_identifies_device_type(self):
        """Test that device type classification works."""
        client_data = {
            "hostname": "test-phone",
            "ip": "192.168.1.101",
            "mac": "00:11:22:33:44:56",
            "deviceType": "phone",
        }
        client = UniFiClient(**client_data)
        assert client.deviceType == "phone"

    def test_client_handles_optional_fields(self):
        """Test that optional fields are handled gracefully."""
        client_data = {
            "hostname": "test-client",
            "ip": "192.168.1.100",
            "mac": "00:11:22:33:44:55",
            "siteId": "test-site-id",
            "deviceId": "test-device-id",
        }
        client = UniFiClient(**client_data)
        assert client.hostname == "test-client"
        assert client.siteId is None or isinstance(client.siteId, str)

    def test_client_rejects_invalid_data(self):
        """Test that invalid data raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UniFiClient(
                hostname="test",
                # Missing required ip and mac fields
            )
