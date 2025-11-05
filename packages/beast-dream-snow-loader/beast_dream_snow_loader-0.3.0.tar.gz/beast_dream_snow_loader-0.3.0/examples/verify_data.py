#!/usr/bin/env python3
"""Verify ServiceNow data by querying the Table API.

This script queries the records we created to verify they exist and have correct data.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from beast_dream_snow_loader.servicenow.api_client import ServiceNowAPIClient


def verify_records(client: ServiceNowAPIClient):
    """Query and display records we created."""
    print("🔍 Verifying ServiceNow Records")
    print("=" * 60)

    # Query Gateway CIs - use sys_id from recent runs
    print("\n1. Gateway CIs (cmdb_ci_netgear):")
    # Query recent records by name to find our test data
    gateways = client.query_records(
        "cmdb_ci_netgear",
        query="name=UDM Pro",
        limit=10,
    )
    print(f"   Found {len(gateways)} record(s) named 'UDM Pro'")
    for gw in gateways[:3]:  # Show first 3
        print(f"   • sys_id: {gw.get('sys_id')}")
        print(f"     name: {gw.get('name', 'N/A')}")
        print(f"     ip_address: {gw.get('ip_address', 'N/A')}")
        print(f"     hostname: {gw.get('hostname', 'N/A')}")
        # Try to get custom field
        unifi_id = gw.get("u_unifi_source_id") or gw.get("u_unifi_source_id") or "N/A"
        print(f"     u_unifi_source_id: {unifi_id}")
        # Show raw data if available
        if "u_unifi_raw_data" in gw:
            print("     (raw data preserved: ✓)")

    # Query Locations - handle 403 permission error
    print("\n2. Locations (cmdb_ci_site):")
    try:
        locations = client.query_records(
            "cmdb_ci_site",
            query="name=Main Office",
            limit=10,
        )
        print(f"   Found {len(locations)} record(s) named 'Main Office'")
        for loc in locations[:3]:
            print(f"   • sys_id: {loc.get('sys_id')}")
            print(f"     name: {loc.get('name', 'N/A')}")
            print(f"     description: {loc.get('description', 'N/A')}")
            unifi_id = loc.get("u_unifi_source_id") or "N/A"
            print(f"     u_unifi_source_id: {unifi_id}")
    except Exception as e:
        if "403" in str(e):
            print("   ⚠️  Permission denied (403) - may need additional roles")
            print("   Trying to query via base cmdb_ci table...")
            try:
                locations = client.query_records(
                    "cmdb_ci",
                    query="sys_class_name=cmdb_ci_site^name=Main Office",
                    limit=10,
                )
                print(f"   Found {len(locations)} record(s) via base table")
                for loc in locations[:3]:
                    print(f"   • sys_id: {loc.get('sys_id')}")
                    print(f"     name: {loc.get('name', 'N/A')}")
            except Exception as e2:
                print(f"   ❌ Could not query: {e2}")
        else:
            raise

    # Query Network Devices
    print("\n3. Network Devices (cmdb_ci_network_node):")
    devices = client.query_records(
        "cmdb_ci_network_node",
        query="name=Main Switch",
        limit=10,
    )
    print(f"   Found {len(devices)} record(s) named 'Main Switch'")
    for dev in devices[:3]:
        print(f"   • sys_id: {dev.get('sys_id')}")
        print(f"     name: {dev.get('name', 'N/A')}")
        print(f"     mac_address: {dev.get('mac_address', 'N/A')}")
        unifi_id = dev.get("u_unifi_source_id") or "N/A"
        print(f"     u_unifi_source_id: {unifi_id}")

    # Query Endpoints
    print("\n4. Endpoints (cmdb_ci):")
    endpoints = client.query_records(
        "cmdb_ci",
        query="hostname=workstation-001",
        limit=10,
    )
    print(f"   Found {len(endpoints)} record(s) with hostname 'workstation-001'")
    for ep in endpoints[:3]:
        print(f"   • sys_id: {ep.get('sys_id')}")
        print(f"     name: {ep.get('name', 'N/A')}")
        print(f"     hostname: {ep.get('hostname', 'N/A')}")
        print(f"     ip_address: {ep.get('ip_address', 'N/A')}")
        print(f"     mac_address: {ep.get('mac_address', 'N/A')}")
        print(f"     sys_class_name: {ep.get('sys_class_name', 'N/A')}")
        unifi_id = ep.get("u_unifi_source_id") or "N/A"
        print(f"     u_unifi_source_id: {unifi_id}")

    # Query all UniFi records (any table with u_unifi_source_id)
    print("\n5. All UniFi Records (any table):")
    all_unifi = client.query_records(
        "cmdb_ci",
        query="u_unifi_source_idISNOTEMPTY",
        limit=20,
    )
    print(f"   Found {len(all_unifi)} total record(s) with u_unifi_source_id")
    for record in all_unifi[:5]:  # Show first 5
        print(
            f"   • {record.get('sys_class_name', 'N/A')}: {record.get('name', 'N/A')} "
            f"(sys_id: {record.get('sys_id', 'N/A')})"
        )
    if len(all_unifi) > 5:
        print(f"   ... and {len(all_unifi) - 5} more")

    print("\n✅ Verification complete!")
    return len(gateways) + len(locations) + len(devices) + len(endpoints)


def main():
    """Run verification."""
    try:
        print("Initializing ServiceNow API client...")
        client = ServiceNowAPIClient()
        print(f"✓ Connected to: {client.instance}\n")

        count = verify_records(client)
        print(f"\n📊 Total records verified: {count}")
        return 0

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease set ServiceNow credentials:")
        print("  export SERVICENOW_INSTANCE='your-instance.service-now.com'")
        print("  export SERVICENOW_USERNAME='your-username'")
        print("  export SERVICENOW_PASSWORD='your-password'")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
