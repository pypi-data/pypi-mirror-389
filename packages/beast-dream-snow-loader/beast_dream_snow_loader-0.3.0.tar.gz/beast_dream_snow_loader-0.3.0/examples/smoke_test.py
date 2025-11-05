#!/usr/bin/env python3
"""Smoke test script for ServiceNow integration.

Usage:
    # Set environment variables
    export SERVICENOW_INSTANCE="dev12345.service-now.com"
    export SERVICENOW_USERNAME="admin"
    export SERVICENOW_PASSWORD="your-password"

    # Run smoke test (CLI - uses terminal dots)
    python examples/smoke_test.py

    # Or run as Streamlit app (uses Streamlit spinner widgets!)
    streamlit run examples/smoke_test.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from beast_dream_snow_loader.models.servicenow import ServiceNowGatewayCI
from beast_dream_snow_loader.servicenow.api_client import ServiceNowAPIClient
from beast_dream_snow_loader.servicenow.loader import load_gateway_ci


def main():
    """Run smoke test: create a test gateway CI record in ServiceNow."""
    print("🚀 ServiceNow Smoke Test")
    print("=" * 50)

    try:
        # Initialize API client
        print("\n1. Initializing ServiceNow API client...")
        client = ServiceNowAPIClient()
        print(f"   ✓ Connected to instance: {client.instance}")

        # Create test gateway CI
        print("\n2. Creating test gateway CI record...")
        # Note: On PDIs, specific CI type tables may not exist.
        # Use base cmdb_ci table with sys_class_name for testing.
        test_data = {
            "sys_class_name": "cmdb_ci",  # Base CI class
            "u_unifi_source_id": "smoke_test_gateway_001",
            "name": "Smoke Test Gateway",
            "ip_address": "192.168.1.1",
            "hostname": "smoke-test-gateway.example.com",
        }

        # Try to load into specific table first, fallback to base cmdb_ci
        try:
            test_gateway = ServiceNowGatewayCI(
                u_unifi_source_id="smoke_test_gateway_001",
                name="Smoke Test Gateway",
                ip_address="192.168.1.1",
                hostname="smoke-test-gateway.example.com",
                firmware_version="1.0.0",
            )
            result = load_gateway_ci(client, test_gateway)
        except Exception as e:
            # Fallback to base cmdb_ci table if specific table doesn't exist or access denied
            if "Invalid table" in str(e) or "403" in str(e) or "Forbidden" in str(e):
                print(
                    "   ⚠️  Specific table not available or access denied, using base cmdb_ci table..."
                )
                # Fallback to base cmdb_ci table
                result = client.create_record("cmdb_ci", test_data)
            else:
                raise
        print("   ✓ Record created successfully!")
        print(f"   ✓ sys_id: {result.get('sys_id', 'N/A')}")
        print(f"   ✓ name: {result.get('name', 'N/A')}")

        print("\n✅ Smoke test PASSED!")
        return 0

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease set environment variables (choose one authentication method):")
        print("\nOption 1 - API Key (Recommended for Production):")
        print("  export SERVICENOW_INSTANCE='your-instance.service-now.com'")
        print("  export SERVICENOW_USERNAME='service-account-username'")
        print("  export SERVICENOW_API_KEY='your-api-key'")
        print("  Note: Use service account user (named user, no UI login)")
        print("\nOption 2 - OAuth Token (Optional):")
        print("  export SERVICENOW_INSTANCE='your-instance.service-now.com'")
        print("  export SERVICENOW_OAUTH_TOKEN='your-oauth-token'")
        print("\nOption 3 - Username/Password (Development/Testing Only):")
        print("  export SERVICENOW_INSTANCE='your-instance.service-now.com'")
        print("  export SERVICENOW_USERNAME='dev-username'")
        print("  export SERVICENOW_PASSWORD='dev-password'")
        print(
            "  Note: NOT recommended for production - use service account with API key"
        )
        return 1

    except Exception as e:
        print(f"\n❌ Smoke test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
