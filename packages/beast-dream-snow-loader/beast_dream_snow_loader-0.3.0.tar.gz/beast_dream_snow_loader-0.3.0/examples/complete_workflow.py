#!/usr/bin/env python3
"""Complete workflow example: Transform and load UniFi data to ServiceNow.

This example demonstrates the complete end-to-end workflow:
1. Load UniFi data (from API or mock data)
2. Transform UniFi models to ServiceNow models
3. Load transformed data into ServiceNow CMDB
4. Handle relationships and dependencies

Usage:
    # Set ServiceNow credentials
    export SERVICENOW_INSTANCE="dev12345.service-now.com"
    export SERVICENOW_USERNAME="admin"
    export SERVICENOW_API_KEY="your-api-key"

    # Run example
    python examples/complete_workflow.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from beast_dream_snow_loader.models.unifi import (
    UniFiClient,
    UniFiDevice,
    UniFiHost,
    UniFiSite,
)
from beast_dream_snow_loader.servicenow.api_client import ServiceNowAPIClient
from beast_dream_snow_loader.servicenow.loader import load_entities_with_relationships
from beast_dream_snow_loader.transformers.unifi_to_snow import (
    transform_client,
    transform_device,
    transform_host,
    transform_site,
)


def create_sample_unifi_data():
    """Create sample UniFi data for demonstration.

    In production, this would come from beast-unifi-integration API.
    """
    # Sample UniFi Host (Gateway)
    host = UniFiHost(
        id="udm-pro-001",
        hardwareId="UDM-Pro",
        type="udm",
        ipAddress="192.168.1.1",
        owner=True,
        isBlocked=False,
        registrationTime="2025-01-01T00:00:00Z",
        lastConnectionStateChange="2025-11-03T10:00:00Z",
        latestBackupTime="2025-11-03T09:00:00Z",
        reportedState={
            "controller_uuid": "test-controller-uuid-001",
            "host_type": 1,
            "hostname": "udm-pro-001",
            "mgmt_port": 8443,
            "name": "UDM Pro",
            "state": "connected",
            "version": "3.0.0",
            "hardware": {"mac": "aa:bb:cc:dd:ee:01"},
            "firmware": {"version": "3.0.0"},
        },
        userData={
            "status": "active",
        },
    )

    # Sample UniFi Site
    site = UniFiSite(
        siteId="site-001",
        hostId="udm-pro-001",
        permission="admin",
        isOwner=True,
        meta={
            "name": "Main Office",
            "desc": "Primary office location",
            "timezone": "America/New_York",
        },
        statistics={
            "counts": {
                "criticalNotification": 0,
                "gatewayDevice": 1,
                "guestClient": 0,
                "lanConfiguration": 1,
                "offlineDevice": 0,
                "offlineGatewayDevice": 0,
                "offlineWifiDevice": 0,
                "offlineWiredDevice": 0,
                "pendingUpdateDevice": 0,
                "totalDevice": 5,
                "wanConfiguration": 1,
                "wifiClient": 15,
                "wifiConfiguration": 1,
                "wifiDevice": 3,
                "wiredClient": 10,
                "wiredDevice": 2,
            }
        },
    )

    # Sample UniFi Device
    device = UniFiDevice(
        hostId="udm-pro-001",
        updatedAt="2025-11-03T10:00:00Z",
        mac="aa:bb:cc:dd:ee:02",
        model="USW-24-POE",
        name="Main Switch",
    )

    # Sample UniFi Client
    client = UniFiClient(
        hostId="udm-pro-001",
        siteId="site-001",
        mac="aa:bb:cc:dd:ee:03",
        hostname="workstation-001",
        ip="192.168.1.100",
        deviceType="computer",
    )

    return host, site, device, client


def main():
    """Run complete workflow example."""
    print("🚀 Complete Workflow Example: UniFi → ServiceNow")
    print("=" * 60)

    try:
        # Step 1: Initialize ServiceNow client
        print("\n1. Initializing ServiceNow API client...")
        client = ServiceNowAPIClient()
        print(f"   ✓ Connected to: {client.instance}")

        # Step 2: Load sample UniFi data
        print("\n2. Loading UniFi data...")
        hosts, sites, devices, clients = create_sample_unifi_data()
        print(
            f"   ✓ Loaded: {len(hosts)} host(s), {len(sites)} site(s), {len(devices)} device(s), {len(clients)} client(s)"
        )

        # Step 3: Transform to ServiceNow models
        print("\n3. Transforming UniFi data to ServiceNow models...")
        gateway_cis = [transform_host(host) for host in hosts]
        locations = [transform_site(site) for site in sites]
        network_devices = [transform_device(device) for device in devices]
        endpoints = [transform_client(client_data) for client_data in clients]
        print("   ✓ Transformation complete")

        # Step 4: Load into ServiceNow with relationships
        print("\n4. Loading into ServiceNow CMDB...")
        print("   (This may take a moment...)")

        id_mapping = load_entities_with_relationships(
            client,
            gateways=gateway_cis,
            locations=locations,
            devices=network_devices,
            endpoints=endpoints,
        )

        # Step 5: Display results
        print("\n5. Results:")
        print("   ✓ Records created successfully!")
        for table_name, mappings in id_mapping.items():
            if mappings:
                print(f"   - {table_name}: {len(mappings)} record(s)")
                for source_id, sys_id in list(mappings.items())[:3]:  # Show first 3
                    print(f"     • {source_id} → {sys_id}")
                if len(mappings) > 3:
                    print(f"     ... and {len(mappings) - 3} more")

        print("\n✅ Complete workflow successful!")
        print("\nNext steps:")
        print("  - Check ServiceNow instance to verify records")
        print("  - Review relationships between records")
        print("  - Load additional data as needed")
        return 0

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease set ServiceNow credentials:")
        print("  export SERVICENOW_INSTANCE='your-instance.service-now.com'")
        print("  export SERVICENOW_USERNAME='your-username'")
        print("  export SERVICENOW_API_KEY='your-api-key'")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
