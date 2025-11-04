#!/usr/bin/env python3
"""Check parent classes for ServiceNow CI classes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from beast_dream_snow_loader.servicenow.api_client import ServiceNowAPIClient


def get_class_hierarchy(
    client: ServiceNowAPIClient, table_name: str, depth: int = 0
) -> list[str]:
    """Get class hierarchy for a table."""
    info = client.get_table_info(table_name)
    if not info:
        return []

    result = [f"{'  ' * depth}{table_name}: {info.get('label', 'N/A')}"]

    super_class_link = info.get("super_class", {})
    super_class_id = (
        super_class_link.get("value") if isinstance(super_class_link, dict) else None
    )

    if super_class_id and depth < 5:
        super_class_info = client.query_records(
            "sys_db_object", query=f"sys_id={super_class_id}", limit=1
        )
        if super_class_info:
            super_class_name = super_class_info[0].get("name")
            result.extend(get_class_hierarchy(client, super_class_name, depth + 1))

    return result


def main():
    """Check parent classes for gateway classes."""
    client = ServiceNowAPIClient()

    tables = [
        "cmdb_ci_nat_gateway",
        "cmdb_ci_internet_gateway",
        "cmdb_ci_site",
        "cmdb_ci_network_node",
    ]

    for table in tables:
        print(f"\n{table} class hierarchy:")
        print("\n".join(get_class_hierarchy(client, table)))


if __name__ == "__main__":
    main()
