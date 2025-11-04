# ServiceNow CI Class Selection Guide

> **Note:** This is the detailed guide for class selection. See [ADR-0001](../adr/0001-servicenow-ci-class-selection.md) for the architectural decision record.

## Overview

ServiceNow CIs can be queried from multiple class tables due to inheritance hierarchies. This document explains how to choose the "best" class for creating CIs.

## Class Hierarchy & Queryability

**Key Principle:** A CI created in a specific class table can be queried from all parent class tables, but NOT from child/subclass tables.

**Example:**
- A CI created in `cmdb_ci_netgear` can be queried from:
  - ✅ `cmdb_ci_netgear` (its own class)
  - ✅ `cmdb_ci_hardware` (parent class)
  - ✅ `cmdb_ci` (grandparent/base class)
  - ❌ `cmdb_ci_network_node` (child class - cannot query)

## Class Selection Strategy

**Goal:** Use the most specific appropriate class that matches the device type.

**Considerations:**
1. **Physical vs Virtual:** 
   - Physical hardware → `cmdb_ci_hardware` or subclasses
   - Virtual appliances → `cmdb_ci_vm_object` or subclasses

2. **Device Type:**
   - Network devices → `cmdb_ci_netgear` or `cmdb_ci_network_node`
   - Gateway/routers → `cmdb_ci_netgear` (physical) or gateway classes (virtual)
   - Locations → `cmdb_ci_site`

3. **Specificity:**
   - More specific = better validation and fields
   - Too specific = may not exist on all instances
   - Too generic = works everywhere but less useful

## Current Class Mappings

### Gateway (UniFi Dream Machine)

**Selected:** `cmdb_ci_netgear`

**Detailed Rationale:**

**1. Device Type: Physical Network Hardware**
- UniFi Dream Machine is a **physical network appliance** (router/gateway hardware)
- Not a virtual appliance or software service
- Physically installed network infrastructure device

**2. Class Hierarchy Analysis:**
- **Virtual Gateway Classes (Rejected):**
  - `cmdb_ci_nat_gateway` → `cmdb_ci_vm_object` (Virtual Machine Object)
  - `cmdb_ci_internet_gateway` → `cmdb_ci_vm_object` (Virtual Machine Object)
  - These are for virtual/cloud appliances (AWS NAT Gateway, etc.), not physical devices
  - UniFi Dream Machine is not a VM object - it's physical hardware

**3. Physical Hardware Classes (Considered):**
- `cmdb_ci_netgear` → `cmdb_ci_hardware` → `cmdb_ci` (Selected)
  - Specifically designed for physical network gear/hardware
  - Matches UniFi Dream Machine device type
  - Provides appropriate fields for network hardware (ports, interfaces, etc.)
  
- `cmdb_ci_network_node` → `cmdb_ci_netgear` → `cmdb_ci_hardware` → `cmdb_ci` (Alternative)
  - Subclass of `cmdb_ci_netgear`, more specific
  - Could work but `cmdb_ci_netgear` is the parent class designed for network gear
  - Less existing records in this class (may indicate it's for specific node types)

- `cmdb_ci_hardware` → `cmdb_ci` (Too Generic)
  - Works but too broad (includes all hardware, not just network)
  - Loses network-specific fields and validation

**4. Why Not `cmdb_ci_network_gateway`:**
- This table doesn't exist in ServiceNow (verified)
- Even with plugin activated, no such table found
- Must use available classes from the CMDB CI Class Models plugin

**5. Queryability Implications:**
- ✅ Can query from `cmdb_ci_netgear` (its own class)
- ✅ Can query from `cmdb_ci_hardware` (parent class)
- ✅ Can query from `cmdb_ci` (base class)
- ❌ Cannot query from `cmdb_ci_network_node` (child class - CI created in parent can't be queried from child)

**Conclusion:** `cmdb_ci_netgear` is the most appropriate class for UniFi Dream Machine because:
1. It's specifically for physical network hardware (not virtual appliances)
2. It's the parent class for network gear (appropriate level of specificity)
3. It's available and verified to work
4. It provides network-specific fields and validation
5. It correctly represents the device type in the CMDB hierarchy

### Location (UniFi Site)

**Selected:** `cmdb_ci_site`

**Detailed Rationale:**

**1. Device Type: Geographic/Site Location**
- UniFi sites represent physical locations or sites
- Could be buildings, offices, data centers, or network sites
- Location/site is a common CMDB concept

**2. Class Hierarchy:**
- `cmdb_ci_site` → `cmdb_ci` → `cmdb`
- Direct subclass of `cmdb_ci` (not hardware-specific)
- Designed for location/site entities

**3. Why Not `cmdb_location`:**
- `cmdb_location` table doesn't exist (verified via API queries)
- ServiceNow uses `cmdb_ci_site` for site locations
- `cmn_location` may exist but is a different table (location management, not CMDB CI)

**4. Why Not `cmdb_ci` (Base Class):**
- Could work but `cmdb_ci_site` is more specific
- Provides location-specific fields and validation
- Better semantic alignment with ServiceNow's location model

**5. Queryability:**
- ✅ Can query from `cmdb_ci_site` (its own class)
- ✅ Can query from `cmdb_ci` (parent class)
- ✅ Can query from `cmdb` (root class)

**Conclusion:** `cmdb_ci_site` is the correct class for UniFi sites because:
1. It's the standard ServiceNow class for site locations
2. `cmdb_location` doesn't exist as a table
3. It provides location-specific fields and validation
4. It correctly represents sites in the CMDB hierarchy

### Network Device (UniFi Devices - Switches, APs, etc.)

**Selected:** `cmdb_ci_network_node`

**Detailed Rationale:**

**1. Device Type: Network Infrastructure Nodes**
- UniFi switches, access points, and other network devices are network nodes
- These are physical network infrastructure components
- Network nodes are more specific than general network gear

**2. Class Hierarchy:**
- `cmdb_ci_network_node` → `cmdb_ci_netgear` → `cmdb_ci_hardware` → `cmdb_ci` → `cmdb`
- More specific than `cmdb_ci_netgear` (parent class)
- Represents network nodes specifically (switches, APs, etc.)

**3. Why Not `cmdb_ci_netgear` (Parent Class):**
- `cmdb_ci_netgear` could work (we use it for gateways)
- But `cmdb_ci_network_node` is more specific for network nodes
- Distinguishes between gateways (netgear) and network nodes (network_node)
- Better semantic alignment: gateways are "gear", nodes are "nodes"

**4. Why Not `cmdb_ci_network_gear`:**
- This table doesn't exist (typo/variant - the actual table is `cmdb_ci_netgear`)

**5. Queryability:**
- ✅ Can query from `cmdb_ci_network_node` (its own class)
- ✅ Can query from `cmdb_ci_netgear` (parent class)
- ✅ Can query from `cmdb_ci_hardware` (grandparent class)
- ✅ Can query from `cmdb_ci` (base class)
- ✅ Can query from `cmdb` (root class)

**Conclusion:** `cmdb_ci_network_node` is appropriate for network devices because:
1. It's specifically designed for network nodes (switches, APs, etc.)
2. It's more specific than the parent `cmdb_ci_netgear` class
3. It correctly distinguishes network nodes from gateways in the hierarchy
4. It provides appropriate fields for network node devices

### Endpoint (UniFi Clients)

**Selected:** `cmdb_ci` (base table with `sys_class_name`)

**Detailed Rationale:**

**1. Device Type: Network Endpoints/Clients**
- UniFi clients are network endpoints (devices connecting to network)
- Could be computers, phones, IoT devices, etc.
- Endpoints are typically leaf nodes in network topology

**2. Why Not `cmdb_endpoint`:**
- `cmdb_endpoint` table doesn't exist (verified via API queries)
- No specific endpoint class found in ServiceNow CMDB
- May be a custom table in some instances, but not standard

**3. Why Base `cmdb_ci` with `sys_class_name`:**
- Base table always available (no plugin required)
- `sys_class_name` field allows categorization
- Can set `sys_class_name="cmdb_endpoint"` or custom value for filtering
- Works on all ServiceNow instances (no dependencies)

**4. Alternative Considerations:**
- Could use `cmdb_ci_computer` if client is a computer
- Could use `cmdb_ci_hardware` if client is hardware device
- But clients are diverse (phones, IoT, computers) - base class is most flexible
- `sys_class_name` can be used to categorize if needed

**5. Queryability:**
- ✅ Can query from `cmdb_ci` (its own class)
- ✅ Can query from `cmdb` (root class)
- Can filter by `sys_class_name` to find endpoints

**Conclusion:** `cmdb_ci` base table is appropriate for endpoints because:
1. `cmdb_endpoint` doesn't exist as a standard table
2. Base table works on all instances (no plugin dependencies)
3. `sys_class_name` field allows categorization and filtering
4. Flexible enough to handle diverse endpoint types (computers, phones, IoT, etc.)
5. Can be upgraded to specific classes if needed later (e.g., `cmdb_ci_computer` for computers)

## Class Hierarchy Examples

### Gateway Classes (Virtual Appliances)
```
cmdb_ci_nat_gateway → cmdb_ci_vm_object → cmdb_ci → cmdb
cmdb_ci_internet_gateway → cmdb_ci_vm_object → cmdb_ci → cmdb
```
**Note:** These are for virtual/software appliances, not physical hardware.

### Network Device Classes (Physical Hardware)
```
cmdb_ci_network_node → cmdb_ci_netgear → cmdb_ci_hardware → cmdb_ci → cmdb
```
**Note:** This is the hierarchy for physical network devices like UniFi Dream Machine.

## Decision Matrix

| Device Type | Physical? | Recommended Class | Alternative Classes |
|------------|-----------|-------------------|---------------------|
| UniFi Dream Machine (Gateway) | ✅ Yes | `cmdb_ci_netgear` | `cmdb_ci_network_node`, `cmdb_ci_hardware` |
| UniFi Network Device | ✅ Yes | `cmdb_ci_network_node` | `cmdb_ci_netgear`, `cmdb_ci_hardware` |
| UniFi Site | N/A | `cmdb_ci_site` | `cmdb_ci` |
| UniFi Client | N/A | `cmdb_ci` (with `sys_class_name`) | Custom table |

## Verification

To check class hierarchies:
```bash
uv run python scripts/check_class_hierarchy.py
```

To check table availability:
```bash
uv run python scripts/check_table_requirements.py
```

## Future Considerations

1. **Multiple Class Support:** ServiceNow may support assigning multiple classes to a CI (needs verification)
2. **Dynamic Class Selection:** Could allow configuration of which class to use per device type
3. **Class Validation:** Could validate that selected class exists and is appropriate before creating CI

## References

- ServiceNow CMDB Class Hierarchy Documentation
- `scripts/check_class_hierarchy.py` - Tool to inspect class hierarchies
- `docs/table_requirements.md` - Table availability and plugin requirements

