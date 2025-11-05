#!/usr/bin/env python3
"""Check which ServiceNow tables are available and their plugin/scope requirements.

This script queries the ServiceNow instance to:
1. Check if target CMDB tables exist
2. Get table metadata (scope, plugin, etc.)
3. Identify which tables require ITOM or other plugins
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from beast_dream_snow_loader.servicenow.api_client import ServiceNowAPIClient


def main():
    """Check table availability and requirements."""
    # Initialize client (uses env vars or 1Password)
    client = ServiceNowAPIClient()

    # Tables we want to check
    target_tables = [
        "cmdb_ci_network_gateway",
        "cmdb_location",
        "cmdb_ci_network_gear",
        "cmdb_endpoint",
        "cmdb_ci",  # Base table (should always exist)
    ]

    print("🔍 Checking ServiceNow table availability and requirements...\n")

    results = {}
    for table_name in target_tables:
        print(f"Checking {table_name}...")
        exists = client.table_exists(table_name)
        info = client.get_table_info(table_name) if exists else None

        results[table_name] = {
            "exists": exists,
            "info": info,
        }

        if exists:
            print("  ✅ Table exists")
            if info:
                print(f"  📋 Label: {info.get('label', 'N/A')}")
                print(f"  📦 Scope: {info.get('scope', 'N/A')}")
                print(f"  🔗 Super class: {info.get('super_class', 'N/A')}")
                print(f"  📝 Class: {info.get('sys_class_name', 'N/A')}")
        else:
            print("  ❌ Table does not exist or is not accessible")

        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()

    existing_tables = [t for t, r in results.items() if r["exists"]]
    missing_tables = [t for t, r in results.items() if not r["exists"]]

    print(f"✅ Available tables ({len(existing_tables)}):")
    for table in existing_tables:
        info = results[table]["info"]
        scope = info.get("scope", "N/A") if info else "N/A"
        print(f"  - {table} (scope: {scope})")

    print()
    print(f"❌ Missing tables ({len(missing_tables)}):")
    for table in missing_tables:
        print(f"  - {table}")

    print()
    print("=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print()

    if "cmdb_ci" in existing_tables:
        print("✅ Base cmdb_ci table is available - can use as fallback")
        print("   Use sys_class_name field to categorize CIs")
        print()

    if missing_tables:
        print("⚠️  Missing tables may require:")
        print("   - ITOM (IT Operations Management) plugin")
        print("   - Discovery plugin")
        print("   - Custom table creation")
        print()
        print("💡 Check ServiceNow KB article KB1691523 for CI type requirements")
        print("   Or query sys_plugin table for installed plugins")
        print()

    # Check installed plugins
    print("Checking installed plugins...")
    try:
        plugins = client.query_records(
            "sys_plugin",
            query="active=true",
        )
        if plugins:
            print(f"  Found {len(plugins)} active plugins")
            # Filter for ITOM/Discovery related
            itom_plugins = [
                p
                for p in plugins
                if "itom" in p.get("name", "").lower()
                or "discovery" in p.get("name", "").lower()
            ]
            if itom_plugins:
                print("  ITOM/Discovery related plugins:")
                for plugin in itom_plugins:
                    print(
                        f"    - {plugin.get('name', 'N/A')} (v{plugin.get('version', 'N/A')})"
                    )
            else:
                print("  ⚠️  No ITOM/Discovery plugins found")
        else:
            print("  ⚠️  Could not query plugins")
    except Exception as e:
        print(f"  ⚠️  Error querying plugins: {e}")

    print()


if __name__ == "__main__":
    main()
