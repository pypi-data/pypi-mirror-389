# ServiceNow Table Requirements & Plugin Dependencies

## Overview

This document tracks which ServiceNow tables are available and which plugins/modules are required for them.

## Table Availability Check

Run `scripts/check_table_requirements.py` to verify table availability on your ServiceNow instance.

## Target Tables

### Required Tables

1. **`cmdb_ci_network_gateway`** - Network gateway CI
   - **Status:** ❌ Not available on PDI (requires plugin activation)
   - **Plugin Required:** **CMDB CI Class Models** (`sn_cmdb_ci_class`)
   - **Action:** Activate plugin in PDI (see Activation Instructions below)

2. **`cmdb_location`** - Location records
   - **Status:** ❌ Not available on PDI (needs verification)
   - **Plugin Required:** Unknown (may be standard CMDB or require plugin)

3. **`cmdb_ci_network_gear`** - Network device CI
   - **Status:** ❌ Not available on PDI (requires plugin activation)
   - **Plugin Required:** **CMDB CI Class Models** (`sn_cmdb_ci_class`)
   - **Note:** `cmdb_ci_netgear` exists but not `cmdb_ci_network_gear`
   - **Action:** Activate plugin in PDI (see Activation Instructions below)

4. **`cmdb_endpoint`** - Endpoint/client records
   - **Status:** ❌ Not available on PDI (needs verification)
   - **Plugin Required:** Unknown (may be custom table)

### Base Table (Fallback)

5. **`cmdb_ci`** - Base Configuration Item table
   - **Status:** ✅ Available on all instances
   - **Plugin Required:** None (core CMDB)
   - **Usage:** Can use with `sys_class_name` field to categorize CIs

## Plugin Requirements

### CMDB CI Class Models Plugin (REQUIRED)

**Plugin ID:** `sn_cmdb_ci_class`  
**Plugin Name:** CMDB CI Class Models

This plugin provides all new class models provided by ServiceNow, including:
- `cmdb_ci_network_gateway`
- `cmdb_ci_network_gear`
- Other network device CI types

**Activation Required:** This plugin must be activated to access these specific CI type tables.

**Cost & Availability:**
- **PDIs:** Free to activate (no cost)
- **Production:** Included with **ITOM Visibility** subscription (typically ~$9,000/year)
- **If doing CMDB work:** You likely already have ITOM Visibility, which includes this plugin
- **If just testing:** PDIs allow free activation - this is often one of the first plugins enabled for CMDB work

**Note:** This plugin is included with ITOM Visibility. If you're doing CMDB work, you likely already have access. If you're just kicking tires, PDIs make it free to activate.

### ITOM (IT Operations Management)

ITOM may be required for certain CI types depending on licensing/subscription, but the **CMDB CI Class Models** plugin is what provides the table definitions.

**Reference:** ServiceNow KB article KB1691523 lists CI types requiring ITOM subscription (for licensing, not table availability).

## Verification Methods

1. **Run script:** `python scripts/check_table_requirements.py`
   - Checks table existence via API
   - Queries `sys_db_object` table for metadata (scope, plugin info)
   - Lists installed plugins (if accessible)

2. **Check ServiceNow Documentation:**
   - KB article KB1691523: CI types requiring ITOM subscription
   - ServiceNow product documentation for table requirements

3. **Query ServiceNow Instance:**
   - `sys_db_object` table: Table metadata including scope/plugin
   - `sys_plugin` table: Installed plugins (may require admin access)

## Workarounds

### Option 1: Use Base `cmdb_ci` Table

Use base `cmdb_ci` table with `sys_class_name` field:

```python
data = {
    "sys_class_name": "cmdb_ci_network_gateway",
    "name": "Gateway Name",
    # ... other fields
}
client.create_record("cmdb_ci", data)
```

**Pros:**
- Works on all instances (no plugin required)
- Standard ServiceNow pattern

**Cons:**
- Less type-specific validation
- May not have all CI type-specific fields

### Option 2: Install ITOM Plugin

Install/activate ITOM plugin on ServiceNow instance to get specific CI type tables.

**Pros:**
- Full CI type support with all fields
- Better validation and relationships

**Cons:**
- Requires ITOM license/subscription
- May not be available on all instances

### Option 3: Create Custom Tables

Create custom tables with `u_*` prefix for UniFi-specific entities.

**Pros:**
- Full control over schema
- No plugin dependencies

**Cons:**
- More setup/maintenance
- Not standard ServiceNow pattern
- May not integrate well with standard CMDB workflows

## Current Implementation

The loader currently:
1. Attempts to use specific CI type tables first
2. Falls back to base `cmdb_ci` table if specific table doesn't exist (see `examples/smoke_test.py`)

This allows the tool to work on instances without ITOM while still supporting ITOM-enabled instances.

## Activation Instructions for PDI

Since this is a development instance (PDI), you can activate the required plugin:

### Activate CMDB CI Class Models Plugin

1. **Log into your PDI:** `https://dev212392.service-now.com` (or your instance URL)
2. **Navigate to Plugins:**
   - Go to **System Definition** > **Plugins**
   - Or search for "Plugins" in the filter navigator
3. **Search for Plugin:**
   - Search for **"CMDB CI Class Models"** or plugin ID `sn_cmdb_ci_class`
4. **Activate Plugin:**
   - Click on the plugin
   - Click **Activate** button
   - Wait for activation to complete (may take a few minutes)
5. **Verify Tables Exist:**
   - Run `scripts/check_table_requirements.py` to verify tables are now available
   - Or query the tables directly via REST API

After activation, the following tables should become available:
- `cmdb_ci_network_gateway`
- `cmdb_ci_network_gear`
- Other network CI type tables

### Alternative: Use Base Table (No Plugin Required)

If you don't want to activate the plugin, the tool can use the base `cmdb_ci` table with `sys_class_name` field. This is already implemented as a fallback.

## Next Steps

1. **Activate Plugin in PDI:**
   - Follow instructions above to activate `sn_cmdb_ci_class`
   - Verify tables are available after activation

2. **Update Loader:**
   - Update loader to use specific CI type tables once plugin is activated
   - Remove fallback to base table (or keep as optional)

3. **Document Production Requirements:**
   - Document that production instances need `sn_cmdb_ci_class` plugin activated
   - Or document that users can use base `cmdb_ci` table as fallback

