# beast-dream-snow-loader

![PyPI - Version](https://img.shields.io/pypi/v/beast-dream-snow-loader.svg)

**UniFi Dream Machine → ServiceNow CMDB Data Loader**

> Loading raw UniFi network infrastructure data into ServiceNow CMDB for network asset management and discovery.

## Overview

beast-dream-snow-loader transforms and loads UniFi network data (hosts, sites, devices, clients) from the UniFi API into ServiceNow CMDB tables. This enables ServiceNow to serve as the source of truth for network infrastructure.

**Purpose:** Complete the integration loop: UniFi API → Data Transformation → ServiceNow CMDB

## What It Does

1. **Transforms Data:** Maps UniFi schema to ServiceNow CMDB schema
   - UniFi hosts → ServiceNow network gateway CIs
   - UniFi sites → ServiceNow locations
   - UniFi devices → ServiceNow network device CIs
   - UniFi clients → ServiceNow endpoints
2. **Loads Data:** Syncs transformed data to ServiceNow CMDB via REST API
   - Multi-phase batch relationship linking
   - Batch loading with dependency resolution
   - Supports specific CI type tables or base `cmdb_ci` table fallback

**Note:** Currently assumes ServiceNow tables exist. Table creation feature planned for future release.

## Project Status

✅ **MVP COMPLETE** - All core features implemented, tested, and published
📦 **Version 0.2.3** (Stable Release) - Published to PyPI
🗓️ **Release Cadence:** Monthly stable releases with interim patches as needed
📋 **Features:** See [docs/MVP_FEATURES.md](docs/MVP_FEATURES.md) for complete feature list
🎉 **Status:** See [docs/MVP_COMPLETE.md](docs/MVP_COMPLETE.md) for MVP completion summary

See [Known Limitations](docs/MVP_FEATURES.md#known-limitations) before using.

## Source Data Schema

UniFi data structure (from `docs/unifi_schema.sql`):
- **hosts** - Gateway devices (Dream Machines, etc.)
- **sites** - UniFi sites/organizations
- **devices** - Network devices (switches, access points, etc.)
- **clients** - Network clients (computers, phones, TVs, thermostats, etc.)

## ServiceNow Integration

- **Target:** ServiceNow CMDB
- **Method:** REST API (direct API calls, MID server support planned)
- **Tables:** 
  - Preferred: Specific CI type tables (`cmdb_ci_network_gateway`, `cmdb_ci_network_gear`, etc.)
  - Fallback: Base `cmdb_ci` table with `sys_class_name` (works without plugin)
- **Plugin Requirement:** CMDB CI Class Models (`sn_cmdb_ci_class`) for full table support
  - Free in PDIs, included with ITOM Visibility in production
  - See [docs/pdi_activation_guide.md](docs/pdi_activation_guide.md) for activation
- **Authentication:** API key (preferred), OAuth token, Basic Auth (fallback)
- **1Password Integration:** Optional 1Password CLI support for credential management

## Quick Start

1. **Install:**
   ```bash
   pip install beast-dream-snow-loader
   # Or with uv:
   uv pip install beast-dream-snow-loader
   ```

2. **Configure ServiceNow:**
   ```bash
   export SERVICENOW_INSTANCE="your-instance.service-now.com"
   export SERVICENOW_USERNAME="your-username"
   export SERVICENOW_API_KEY="your-api-key"  # or use 1Password
   ```

3. **Run Complete Example:**
   ```bash
   python examples/complete_workflow.py
   ```

4. **Or Run Smoke Test:**
   ```bash
   python examples/smoke_test.py
   ```

See [docs/pdi_activation_guide.md](docs/pdi_activation_guide.md) for ServiceNow plugin setup.

## Dependencies

- `pydantic` - Data validation and models
- `requests` - HTTP client for ServiceNow REST API
- `beast-unifi-integration` - UniFi API clients (planned, not yet available)

## Installation

```bash
pip install beast-dream-snow-loader
```

Or with `uv`:
```bash
uv pip install beast-dream-snow-loader
```

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[MVP Features](docs/MVP_FEATURES.md)** - Complete feature list
- **[Release Notes](RELEASE_NOTES.md)** - What's new and what's planned
- **[Deployment Guide](docs/DEPLOYMENT.md)** - PyPI and SonarCloud setup
- **[ServiceNow Setup](docs/pdi_setup.md)** - REST API and plugin activation
- **[Table Requirements](docs/table_requirements.md)** - Plugin dependencies and verification
- **[Constraints & Assumptions](docs/servicenow_constraints.md)** - ServiceNow integration details

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Project:** Part of the Beastmaster framework ecosystem  
**Repository:** `nkllon/beast-dream-snow-loader` (GitHub)

# Test workflow trigger
