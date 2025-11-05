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

2. **`cmdb_ci_site`** - Site/Location CI records
   - **Status:** ✅ Available as CLASS (not a table)
   - **Type:** CLASS only - must use `cmdb_ci` table with `sys_class_name=cmdb_ci_site`
   - **Plugin Required:** None (class exists in base CMDB)
   - **Note:** `cmn_location` exists but is a different table (location management, not CMDB CI)
   - **Usage:** Use base `cmdb_ci` table with `sys_class_name` field

3. **`cmdb_ci_network_node`** - Network node CI (for switches, APs, etc.)
   - **Status:** ✅ Available as CLASS (not a table)
   - **Type:** CLASS only - must use `cmdb_ci` table with `sys_class_name=cmdb_ci_network_node`
   - **Plugin Required:** None (class exists in base CMDB)
   - **Note:** `cmdb_ci_netgear` exists as a table (parent class), but `cmdb_ci_network_node` is only a class
   - **Usage:** Use base `cmdb_ci` table with `sys_class_name` field

4. **`cmdb_ci_netgear`** - Network gear CI (parent class)
   - **Status:** ✅ Available on PDI (verified with `sn_cmdb_ci_class` activated)
   - **Plugin Required:** **CMDB CI Class Models** (`sn_cmdb_ci_class`)
   - **Note:** `cmdb_ci_netgear` is the actual table name (not `cmdb_ci_network_gear`)

5. **`cmdb_endpoint`** - Endpoint/client records
   - **Status:** ❌ Not available on PDI (does not exist)
   - **Plugin Required:** None (table doesn't exist - use base `cmdb_ci` with `sys_class_name`)

### Base Table (Fallback)

6. **`cmdb_ci`** - Base Configuration Item table
   - **Status:** ✅ Available on all instances
   - **Plugin Required:** None (core CMDB)
   - **Usage:** Can use with `sys_class_name` field to categorize CIs

## Plugin Requirements

### CMDB CI Class Models Plugin (REQUIRED)

**Plugin ID:** `sn_cmdb_ci_class`  
**Plugin Name:** CMDB CI Class Models

This plugin provides some CMDB CI class models, including:
- `cmdb_ci_netgear` ✅ (verified - provides network gear CI)
- Other network device CI types

**⚠️ IMPORTANT:** This plugin does NOT provide:
- `cmdb_ci_site` ❌ (requires **Discovery** plugin)
- `cmdb_ci_network_node` ❌ (requires **Discovery** plugin)

**Activation Required:** This plugin must be activated to access these specific CI type tables.

**Cost & Availability:**
- **PDIs:** Free to activate (no cost)
- **Production:** Included with **ITOM Visibility** subscription (typically ~$9,000/year)
- **If doing CMDB work:** You likely already have ITOM Visibility, which includes this plugin
- **If just testing:** PDIs allow free activation - this is often one of the first plugins enabled for CMDB work

**Note:** This plugin is included with ITOM Visibility. If you're doing CMDB work, you likely already have access. If you're just kicking tires, PDIs make it free to activate.

### Important: Table vs Class Distinction

**Key Discovery:** `cmdb_ci_site` and `cmdb_ci_network_node` are **CLASSES**, not **TABLES**.

**What this means:**
- They can be queried via `cmdb_ci` with `sys_class_name` filter ✅
- They CANNOT be used as direct table endpoints (returns 400 Bad Request) ❌
- They CAN be created via base `cmdb_ci` table with `sys_class_name` field ✅
- No plugin activation required - these classes exist in base CMDB ✅

**Implementation:**
- Use `cmdb_ci` table directly with `sys_class_name=cmdb_ci_site` or `sys_class_name=cmdb_ci_network_node`
- This is NOT a fallback - it's the correct approach for these classes

### ITOM (IT Operations Management)

ITOM may be required for certain CI types depending on licensing/subscription. Some CI tables may require ITOM Discovery or other ITOM plugins.

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

