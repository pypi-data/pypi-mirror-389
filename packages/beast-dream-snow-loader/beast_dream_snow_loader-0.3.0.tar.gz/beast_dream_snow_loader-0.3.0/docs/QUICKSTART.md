# Quick Start Guide

Get up and running with `beast-dream-snow-loader` in 5 minutes.

## Prerequisites

1. **Python 3.10+** and `uv` package manager
2. **ServiceNow Instance** with REST API enabled
3. **ServiceNow Credentials** (API key preferred, or username/password)

## Installation

```bash
# Clone the repository
git clone https://github.com/nkllon/beast-dream-snow-loader.git
cd beast-dream-snow-loader

# Install dependencies
uv sync
```

## ServiceNow Setup

### 1. Enable REST API (if not already enabled)

Your admin user needs the `rest_api_explorer` role:

1. Log into ServiceNow
2. Search for "Users" in filter navigator
3. Open your user (or admin user)
4. Go to "Roles" tab
5. Add `rest_api_explorer` role
6. Save

See [docs/pdi_setup.md](pdi_setup.md) for detailed instructions.

### 2. Configure Authentication

**Option A: API Key (Recommended for Production)**

1. Create a service account user in ServiceNow (no UI login)
2. Generate an API key for that user
3. Set environment variables:

```bash
export SERVICENOW_INSTANCE="your-instance.service-now.com"
export SERVICENOW_USERNAME="your-service-account"
export SERVICENOW_API_KEY="your-api-key"
```

**Option B: Basic Auth (Development/Testing)**

```bash
export SERVICENOW_INSTANCE="your-instance.service-now.com"
export SERVICENOW_USERNAME="admin"
export SERVICENOW_PASSWORD="your-password"
```

**Option C: 1Password (Beast Cluster)**

If you have 1Password CLI available and signed in, credentials are automatically retrieved from:
- Vault: "Beastmaster"
- Item: "ServiceNow Dev Account"
- Fields: `instance`, `username`, `api_key` or `password`

See [docs/1password_usage.md](1password_usage.md) for details.

### 3. (Optional) Activate CMDB CI Class Models Plugin

For full table support (`cmdb_ci_network_gateway`, etc.):

1. Go to **System Definition** > **Plugins**
2. Search for **"CMDB CI Class Models"** (or `sn_cmdb_ci_class`)
3. Click **Activate**
4. Wait for activation (may take a few minutes)

**Note:** Plugin is free in PDIs. If not activated, the tool falls back to base `cmdb_ci` table.

See [docs/pdi_activation_guide.md](pdi_activation_guide.md) for details.

## Verify Setup

### 1. Check Table Availability

```bash
uv run python scripts/check_table_requirements.py
```

This will show:
- Which tables are available
- Which plugin is required
- Recommended next steps

### 2. Run Smoke Test

```bash
uv run python examples/smoke_test.py
```

This will:
- Test ServiceNow connectivity
- Attempt to create a test record
- Verify authentication works

## Basic Usage

### Transform UniFi Data to ServiceNow

```python
from beast_dream_snow_loader.models.unifi import UniFiHost
from beast_dream_snow_loader.transformers.unifi_to_snow import transform_host
from beast_dream_snow_loader.servicenow.api_client import ServiceNowAPIClient
from beast_dream_snow_loader.servicenow.loader import load_gateway_ci

# 1. Create UniFi host model (from API data)
unifi_host = UniFiHost(
    id="test-host-123",
    hardwareId="UDM-Pro",
    ipAddress="192.168.1.1",
    # ... other fields
)

# 2. Transform to ServiceNow model
snow_gateway = transform_host(unifi_host)

# 3. Load into ServiceNow
client = ServiceNowAPIClient()  # Uses env vars or 1Password
result = load_gateway_ci(client, snow_gateway)

print(f"Created record with sys_id: {result['sys_id']}")
```

### Batch Load with Relationships

```python
from beast_dream_snow_loader.servicenow.loader import load_entities_with_relationships

# Transform your UniFi data
gateways = [transform_host(h) for h in unifi_hosts]
locations = [transform_site(s) for s in unifi_sites]
devices = [transform_device(d) for d in unifi_devices]
endpoints = [transform_client(c) for c in unifi_clients]

# Load all with automatic relationship linking
client = ServiceNowAPIClient()
id_mapping = load_entities_with_relationships(
    client,
    gateways=gateways,
    locations=locations,
    devices=devices,
    endpoints=endpoints,
)

# id_mapping contains {table_name: {source_id: sys_id}}
```

## Next Steps

- **Full Documentation:** See [docs/](docs/) directory
- **API Reference:** See code docstrings
- **Examples:** See [examples/](examples/) directory
- **Troubleshooting:** See [docs/servicenow_constraints.md](servicenow_constraints.md)

## Troubleshooting

### "401 Unauthorized" Error

- Check your credentials are correct
- Verify REST API is enabled (see Setup step 1)
- Ensure `rest_api_explorer` role is assigned

### "Invalid table" Error

- Specific CI type tables may not exist (plugin not activated)
- Tool automatically falls back to base `cmdb_ci` table
- To get specific tables, activate CMDB CI Class Models plugin

### "Table does not exist" Error

- Run `scripts/check_table_requirements.py` to verify table availability
- Activate required plugin if needed
- Tool will use base `cmdb_ci` table as fallback

## Support

- **Issues:** [GitHub Issues](https://github.com/nkllon/beast-dream-snow-loader/issues)
- **Documentation:** See [docs/](docs/) directory
- **Release Notes:** See [RELEASE_NOTES.md](../RELEASE_NOTES.md)

