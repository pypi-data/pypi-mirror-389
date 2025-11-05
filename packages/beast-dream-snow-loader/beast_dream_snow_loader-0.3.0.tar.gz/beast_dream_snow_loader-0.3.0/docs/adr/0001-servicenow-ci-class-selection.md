# ADR-0001: ServiceNow CI Class Selection for UniFi Dream Machine Integration

**Status:** Accepted  
**Date:** 2025-11-03  
**Deciders:** Development Team  
**Tags:** servicenow, cmdb, class-selection, architecture, mvp-constraint

## Context

ServiceNow CMDB uses a hierarchical class structure where Configuration Items (CIs) can be queried from multiple parent class tables due to inheritance. When integrating UniFi Dream Machine network data into ServiceNow, we need to select the appropriate CI classes for:

1. **UniFi Gateways (Dream Machine)** - Physical network gateway appliances
2. **UniFi Sites** - Geographic/network locations
3. **UniFi Network Devices** - Switches, access points, etc.
4. **UniFi Clients** - Network endpoints (devices connecting to network)

**Key Challenge:** ServiceNow has multiple class options, and the "best" class selection is complicated because:
- CIs can be queried from all parent class tables (inheritance hierarchy)
- Virtual appliance classes exist but are for software/cloud services, not physical hardware
- Some expected classes don't exist (e.g., `cmdb_ci_network_gateway`, `cmdb_location`)
- Plugin activation provides additional classes that may not match initial expectations

**Discovery Findings:**
- CMDB CI Class Models plugin (`sn_cmdb_ci_class`) is installed and activated
- Virtual gateway classes (`cmdb_ci_nat_gateway`, `cmdb_ci_internet_gateway`) inherit from `cmdb_ci_vm_object` (virtual appliances)
- Physical hardware classes (`cmdb_ci_netgear`, `cmdb_ci_network_node`) inherit from `cmdb_ci_hardware` (physical hardware)
- `cmdb_location` table doesn't exist; `cmdb_ci_site` is the standard location class
- `cmdb_endpoint` table doesn't exist; base `cmdb_ci` table must be used

## Decision

We selected the following CI classes for UniFi Dream Machine integration:

### 1. Gateway: `cmdb_ci_netgear`

**Rationale:**
- UniFi Dream Machine is **physical network hardware**, not a virtual appliance
- `cmdb_ci_netgear` is specifically designed for physical network gear/hardware
- Virtual gateway classes (`cmdb_ci_nat_gateway`, `cmdb_ci_internet_gateway`) are for virtual/cloud appliances (AWS NAT Gateway, etc.)
- Hierarchy: `cmdb_ci_netgear` → `cmdb_ci_hardware` → `cmdb_ci` → `cmdb`
- Provides appropriate fields for network hardware (ports, interfaces, etc.)

**Alternatives Considered:**
- `cmdb_ci_network_node` - Subclass of `cmdb_ci_netgear`, but more specific for nodes than gateways
- `cmdb_ci_nat_gateway` / `cmdb_ci_internet_gateway` - Rejected (virtual appliances, inherit from `cmdb_ci_vm_object`)
- `cmdb_ci_hardware` - Too generic (includes all hardware, not just network)
- `cmdb_ci_network_gateway` - Doesn't exist (verified)

### 2. Location: `cmdb_ci_site`

**Rationale:**
- Standard ServiceNow class for site locations
- `cmdb_location` doesn't exist (verified via API queries)
- Hierarchy: `cmdb_ci_site` → `cmdb_ci` → `cmdb`
- Provides location-specific fields and validation

**Alternatives Considered:**
- `cmdb_location` - Doesn't exist
- `cmdb_ci` - Too generic, loses location-specific fields

### 3. Network Device: `cmdb_ci_network_node`

**Rationale:**
- Specifically designed for network nodes (switches, APs, etc.)
- More specific than parent `cmdb_ci_netgear` class
- Distinguishes network nodes from gateways semantically
- Hierarchy: `cmdb_ci_network_node` → `cmdb_ci_netgear` → `cmdb_ci_hardware` → `cmdb_ci` → `cmdb`

**Alternatives Considered:**
- `cmdb_ci_netgear` - Could work but less specific (we use this for gateways)
- `cmdb_ci_network_gear` - Doesn't exist (typo - actual table is `cmdb_ci_netgear`)

### 4. Endpoint: `cmdb_ci` (base table with `sys_class_name`)

**Rationale:**
- `cmdb_endpoint` table doesn't exist (verified)
- Base table always available (no plugin dependencies)
- `sys_class_name` field allows categorization and filtering
- Flexible enough to handle diverse endpoint types (computers, phones, IoT, etc.)

**Alternatives Considered:**
- `cmdb_endpoint` - Doesn't exist
- `cmdb_ci_computer` - Too specific (clients are diverse)
- `cmdb_ci_hardware` - Could work but endpoints may not be hardware

## Consequences

### Positive

1. **Correct Device Representation:**
   - Physical devices use physical hardware classes (not virtual appliance classes)
   - Semantic alignment with ServiceNow's class model
   - Appropriate fields and validation for each device type

2. **Queryability:**
   - CIs can be queried from all parent class tables
   - Enables flexible querying strategies
   - Maintains compatibility with ServiceNow's inheritance model

3. **Flexibility:**
   - Base `cmdb_ci` table works on all instances (no plugin dependencies)
   - Can upgrade to specific classes later if needed
   - Graceful degradation for instances without plugins

4. **Documentation:**
   - Clear rationale for each class selection
   - Future developers can understand the decisions
   - Can be referenced when similar decisions are needed

### Negative

1. **Class Selection Complexity:**
   - Requires understanding of ServiceNow class hierarchies
   - Virtual vs physical distinction may not be obvious
   - Multi-class queryability adds complexity

2. **Potential Confusion:**
   - Gateway classes exist but are for virtual appliances
   - Expected class names don't always match actual tables
   - Plugin dependencies may not be obvious

3. **Maintenance:**
   - If ServiceNow adds new classes, may need to re-evaluate
   - Class selection may need updates for different device types

## Implementation

**Location:** `src/beast_dream_snow_loader/servicenow/loader.py`

**Table Mappings:**
```python
TABLE_GATEWAY_CI = "cmdb_ci_netgear"  # Physical network hardware
TABLE_LOCATION = "cmdb_ci_site"  # Site/location
TABLE_NETWORK_DEVICE_CI = "cmdb_ci_network_node"  # Network nodes
TABLE_ENDPOINT = "cmdb_ci"  # Base table with sys_class_name
```

**Documentation:**
- `docs/class_selection.md` - Detailed class selection guide
- `docs/servicenow_constraints.md` - Updated with actual classes
- `scripts/check_class_hierarchy.py` - Tool for inspecting class hierarchies

## References

- ServiceNow CMDB Class Hierarchy Documentation
- `docs/class_selection.md` - Detailed rationale and examples
- `scripts/check_class_hierarchy.py` - Class hierarchy inspection tool
- `docs/table_requirements.md` - Table availability and plugin requirements

## Notes

- This decision was made after plugin activation and verification of available classes
- Class selection considers both queryability (parent classes) and specificity (appropriate level)
- Virtual appliance classes are explicitly rejected for physical hardware devices
- Base `cmdb_ci` table provides fallback for endpoints (no standard endpoint class exists)

## MVP Constraint

**This is an MVP constraint** - the selected classes are fixed for the MVP release. Future versions may:
- Support configuration of class mappings per device type
- Add support for additional class hierarchies
- Allow dynamic class selection based on device characteristics
- Support custom class mappings via configuration

For MVP, these class selections are hardcoded and represent the best-fit classes for UniFi Dream Machine integration.

