#!/usr/bin/env python3
"""Quick test script to verify ServiceNow REST API access.

This tests if the API is actually awake and responding.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from beast_dream_snow_loader.servicenow.api_client import ServiceNowAPIClient


def main():
    print("Testing ServiceNow REST API Access")
    print("=" * 50)

    try:
        client = ServiceNowAPIClient()
        print(f"\n✓ Connected to: {client.instance}")

        # Try a simple query
        print("\nTesting REST API query...")
        result = client.query_records("sys_user", limit=1)

        print("✓ REST API is AWAKE and working!")
        print(f"✓ Successfully queried {len(result)} record(s)")
        if result:
            print(f"✓ Sample record: {result[0].get('user_name', 'N/A')}")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
