# PDI Plugin Activation Guide

## Required Plugin for CMDB CI Type Tables

To use the specific CI type tables (`cmdb_ci_network_gateway`, `cmdb_ci_network_gear`, etc.), you need to activate the **CMDB CI Class Models** plugin.

**Note on Cost:**
- **PDIs:** Plugin activation is free - no cost to activate
- **Production:** Plugin is included with **ITOM Visibility** subscription (typically ~$9,000/year)
- **If you're doing CMDB work:** You likely already have ITOM Visibility, which includes this plugin
- **If you're just testing:** PDIs allow free plugin activation - this is often one of the first plugins enabled for CMDB work

## Quick Activation Steps

1. **Log into your PDI:**
   ```
   https://dev212392.service-now.com
   ```

2. **Navigate to Plugins:**
   - Go to **System Definition** > **Plugins**
   - Or search for "Plugins" in the filter navigator (top left)

3. **Search for Plugin:**
   - Search for: **"CMDB CI Class Models"**
   - Or plugin ID: `sn_cmdb_ci_class`

4. **Activate Plugin:**
   - Click on the plugin in the list
   - Click the **Activate** button
   - Wait for activation to complete (may take 1-2 minutes)

5. **Verify Activation:**
   - Run the verification script:
     ```bash
     export SERVICENOW_INSTANCE="dev212392.service-now.com"
     export SERVICENOW_USERNAME="admin"
     export SERVICENOW_PASSWORD="your-password"
     uv run python scripts/check_table_requirements.py
     ```
   - You should see `cmdb_ci_network_gateway` and `cmdb_ci_network_gear` as ✅ available

## What This Plugin Provides

The **CMDB CI Class Models** plugin (`sn_cmdb_ci_class`) provides:
- `cmdb_ci_network_gateway` - Network gateway CI table
- `cmdb_ci_network_gear` - Network device CI table
- Other network CI type tables

## Alternative: Use Base Table (No Activation Needed)

If you don't want to activate the plugin, the loader can use the base `cmdb_ci` table with `sys_class_name` field. This works without any plugin activation but provides less type-specific validation.

## For Production Instances

Production instances should have the **CMDB CI Class Models** plugin activated. If it's not available, users can:
1. Request plugin activation from their ServiceNow administrator
2. Use the base `cmdb_ci` table fallback (already implemented)
3. Create a feature request on our repo if they need custom table support

