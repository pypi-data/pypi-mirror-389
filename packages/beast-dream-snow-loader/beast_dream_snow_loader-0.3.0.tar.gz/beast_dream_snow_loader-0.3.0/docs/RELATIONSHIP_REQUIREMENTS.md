# Relationship Requirements: ServiceNow CMDB CI Relationships

**Version:** 1.0  
**Date:** 2025-11-04  
**Status:** Implemented (Backward Pass Documentation)

## Overview

This document defines the requirements and design for managing relationships between Configuration Items (CIs) in ServiceNow CMDB. This was a critical discovery during implementation: ServiceNow uses the `cmdb_rel_ci` table for relationships, not fields on CI records.

## 1. Problem Statement

### Initial Assumption (Incorrect)
We initially assumed that relationships could be established by setting fields on CI records, such as:
- `location.host_id = gateway.sys_id`
- `device.site_id = location.sys_id`
- `endpoint.device_id = device.sys_id`

### Reality (Discovered)
- ServiceNow's `cmdb_ci` is an abstract base class
- Custom relationship fields don't exist on CI records
- Even if set, they don't persist
- Relationships must be created in the separate `cmdb_rel_ci` table

## 2. Requirements

### REQ-1: Relationship Table Usage
**Requirement:** The system SHALL create relationships using the `cmdb_rel_ci` table, not by updating fields on CI records.

**Rationale:** ServiceNow uses a separate table for CI relationships. Attempting to store relationships as fields on CI records fails because:
1. The `cmdb_ci` base class is abstract and doesn't have these fields
2. ServiceNow's data model requires relationships in `cmdb_rel_ci`
3. Field updates appear to succeed but don't persist

**Acceptance Criteria:**
- All relationships created in `cmdb_rel_ci` table
- No attempts to update relationship fields on CI records
- Relationships persist correctly

---

### REQ-2: Multi-Phase Batch Relationship Linking
**Requirement:** The system SHALL implement a multi-phase batch processing approach for relationship linking.

**Phase 1:** Batch create all CI records, capture returned `sys_id` values.

**Phase 2:** Batch create relationship records in `cmdb_rel_ci` using captured `sys_id` values.

**Rationale:** This is a performance optimization for batch operations through the REST API Table API. ServiceNow requires `sys_id` values for relationships, which are only available after record creation. By batching creates in phases, we optimize for speed compared to sequential one-by-one processing.

**Alternative (not implemented):** A single web service call that accepts a tree structure and processes everything in one operation would be slower but potentially transactional. This is not implemented here as it would be slower for small updates, especially through the Table API.

**Acceptance Criteria:**
- Phase 1 completes before Phase 2 begins
- All `sys_id` values captured in Phase 1
- All relationships created in Phase 2 using captured `sys_id` values

---

### REQ-3: Source ID to sys_id Mapping
**Requirement:** The system SHALL maintain a mapping from UniFi source IDs to ServiceNow `sys_id` values for relationship linking.

**Mapping Structure:**
```python
{
    "table_name": {
        "unifi_source_id": "servicenow_sys_id",
        ...
    },
    ...
}
```

**Example:**
```python
{
    "cmdb_ci_netgear": {
        "udm-pro-001": "305cdd49c38532106618304d0501312b",
        ...
    },
    "cmdb_ci_site": {
        "site-001": "b45cdd49c38532106618304d0501312f",
        ...
    },
    ...
}
```

**Acceptance Criteria:**
- Mapping maintained for all created records
- Mapping used correctly in Phase 2
- Missing mappings handled gracefully

---

### REQ-4: Relationship Types
**Requirement:** The system SHALL use standard ServiceNow relationship types.

**Supported Relationship Types:**

1. **"Managed by::Manages"**
   - Used for: Gateway → Location, Gateway → Device
   - Meaning: Gateway manages the Location/Device

2. **"Located in::Contains"**
   - Used for: Location → Device, Location → Endpoint
   - Meaning: Device/Endpoint is located at the Location

3. **"Connects to::Connected by"**
   - Used for: Device → Endpoint
   - Meaning: Endpoint connects through the Device

**Acceptance Criteria:**
- Correct relationship types used for each relationship
- Relationship types match ServiceNow standards

---

## 3. Relationship Mappings

### 3.1 Location → Gateway

**Source:** UniFi Site has `hostId` (UniFi Gateway ID)

**Process:**
1. Phase 1: Create Gateway, capture `sys_id`
2. Phase 1: Create Location, capture `sys_id`
3. Phase 2: Look up Gateway `sys_id` by `hostId` (source ID)
4. Phase 2: Create `cmdb_rel_ci` record:
   - `parent`: Gateway `sys_id`
   - `child`: Location `sys_id`
   - `type`: "Managed by::Manages"

**Code Example:**
```python
if location.host_id:  # UniFi hostId
    gateway_sys_id = id_mapping[TABLE_GATEWAY_CI].get(location.host_id)
    if gateway_sys_id:
        rel_data = {
            "parent": gateway_sys_id,
            "child": location_sys_id,
            "type": "Managed by::Manages",
        }
        client.create_record("cmdb_rel_ci", rel_data)
```

---

### 3.2 Device → Gateway

**Source:** UniFi Device has `hostId` (UniFi Gateway ID)

**Process:**
1. Phase 1: Create Gateway, capture `sys_id`
2. Phase 1: Create Device, capture `sys_id`
3. Phase 2: Look up Gateway `sys_id` by `hostId` (source ID)
4. Phase 2: Create `cmdb_rel_ci` record:
   - `parent`: Gateway `sys_id`
   - `child`: Device `sys_id`
   - `type`: "Managed by::Manages"

---

### 3.3 Device → Location

**Source:** UniFi Device may have `siteId` (UniFi Site ID)

**Process:**
1. Phase 1: Create Location, capture `sys_id`
2. Phase 1: Create Device, capture `sys_id`
3. Phase 2: Look up Location `sys_id` by `siteId` (source ID)
4. Phase 2: Create `cmdb_rel_ci` record:
   - `parent`: Location `sys_id`
   - `child`: Device `sys_id`
   - `type`: "Located in::Contains"

**Note:** UniFi Device may not have `siteId` directly - may need to be derived from context.

---

### 3.4 Endpoint → Location

**Source:** UniFi Client has `siteId` (UniFi Site ID)

**Process:**
1. Phase 1: Create Location, capture `sys_id`
2. Phase 1: Create Endpoint, capture `sys_id`
3. Phase 2: Look up Location `sys_id` by `siteId` (source ID)
4. Phase 2: Create `cmdb_rel_ci` record:
   - `parent`: Location `sys_id`
   - `child`: Endpoint `sys_id`
   - `type`: "Located in::Contains"

---

### 3.5 Endpoint → Device

**Source:** UniFi Client may have `deviceId` (UniFi Device ID)

**Process:**
1. Phase 1: Create Device, capture `sys_id`
2. Phase 1: Create Endpoint, capture `sys_id`
3. Phase 2: Look up Device `sys_id` by `deviceId` (source ID)
4. Phase 2: Create `cmdb_rel_ci` record:
   - `parent`: Device `sys_id`
   - `child`: Endpoint `sys_id`
   - `type`: "Connects to::Connected by"

**Note:** UniFi Client may not have `deviceId` directly - may need to be derived from context.

---

## 4. Implementation Details

### 4.1 Phase 1: Record Creation

**Order (Dependency-Based):**
1. Gateways (no dependencies)
2. Locations (depend on gateways - relationships set in Phase 2)
3. Devices (depend on gateways and locations - relationships set in Phase 2)
4. Endpoints (depend on locations and devices - relationships set in Phase 2)

**Mapping Capture:**
```python
id_mapping = {
    TABLE_GATEWAY_CI: {},
    TABLE_LOCATION: {},
    TABLE_NETWORK_DEVICE_CI: {},
    TABLE_ENDPOINT: {},
}

# After creating record:
result = load_gateway_ci(client, gateway)
sys_id = result.get("sys_id")
source_id = gateway.u_unifi_source_id
id_mapping[TABLE_GATEWAY_CI][source_id] = sys_id
```

---

### 4.2 Phase 2: Relationship Creation

**Process:**
1. Iterate through entities with relationships
2. Look up related entity `sys_id` by source ID
3. Create `cmdb_rel_ci` record with `parent`, `child`, `type`
4. Handle missing mappings gracefully (log error, continue)

**Error Handling:**
- If source ID not found in mapping: log warning, continue
- If relationship creation fails: log error, continue
- Don't fail entire batch if one relationship fails

---

## 5. Data Model

### 5.1 ServiceNow Model Fields

**Relationship Source ID Fields (for Phase 2):**
- `host_id`: Source ID of related gateway (UniFi `hostId`)
- `site_id`: Source ID of related site (UniFi `siteId`)
- `device_id`: Source ID of related device (UniFi `deviceId`)

**Note:** These are NOT sys_ids. They're UniFi source IDs that are mapped to sys_ids in Phase 2.

### 5.2 cmdb_rel_ci Table Structure

**Table:** `cmdb_rel_ci`

**Required Fields:**
- `parent`: sys_id of parent CI (reference)
- `child`: sys_id of child CI (reference)
- `type`: Relationship type (e.g., "Managed by::Manages")

**Optional Fields:**
- `sys_id`: Auto-generated by ServiceNow
- `sys_created_on`: Timestamp
- Other metadata fields

---

## 6. Error Handling

### 6.1 Missing Source ID Mapping

**Scenario:** Entity references a source ID that doesn't exist in mapping.

**Handling:**
- Log warning: `"⚠️ Phase 2: Gateway {host_id} not found in id_mapping for location {location_id}"`
- Continue processing other relationships
- Don't fail entire batch

### 6.2 Relationship Creation Failure

**Scenario:** `cmdb_rel_ci` record creation fails.

**Handling:**
- Log error: `"⚠️ Phase 2: Failed to create relationship for location {location_id}: {error}"`
- Continue processing other relationships
- Don't fail entire batch

### 6.3 Missing Relationship Source ID

**Scenario:** Entity has no `host_id`, `site_id`, or `device_id` set.

**Handling:**
- Log warning: `"⚠️ Phase 2: Location {location_id} has no host_id set"`
- Skip relationship creation for that entity
- Continue processing other relationships

---

## 7. Design Decisions

### 7.1 Why Multi-Phase Batch Processing?

**Rationale:**
- ServiceNow requires `sys_id` values for relationships
- `sys_id` values are only available after record creation
- Cannot create relationships during record creation
- Performance optimization: Batch create records in Phase 1, then batch create relationships in Phase 2
- Faster than sequential one-by-one processing through the REST API Table API

**Alternatives Considered:**
- Update records after creation with relationship fields
  - **Rejected:** Fields don't exist on CI records, won't persist
- Single web service call with tree structure
  - **Not implemented:** Would be slower for small updates, especially through the Table API
  - **Note:** This alternative would be transactional but slower

### 7.2 Why cmdb_rel_ci Table?

**Rationale:**
- ServiceNow standard mechanism for CI relationships
- Works with all CI types (abstract base class)
- Persists correctly
- Supports standard relationship types

**Alternative Considered:**
- Custom fields on CI records
- **Rejected:** Fields don't exist, won't persist

### 7.3 Why Source ID Mapping?

**Rationale:**
- UniFi data uses UniFi IDs (e.g., `hostId`, `siteId`)
- ServiceNow uses `sys_id` values
- Need to map between them for relationship linking
- Mapping maintained during Phase 1, used in Phase 2

---

## 8. Testing

### 8.1 Unit Tests

**Test Cases:**
- Source ID to sys_id mapping creation
- Relationship record creation
- Missing mapping handling
- Relationship type validation

### 8.2 Integration Tests

**Test Cases:**
- Multi-phase batch relationship linking end-to-end
- Relationship persistence verification
- Error handling for missing mappings
- Error handling for relationship creation failures

---

## 9. Future Enhancements

### 9.1 Transactional Support

**Current:** Multi-phase batch processing (not transactional, optimized for performance)

**Future:** 
- Changeset support for transactional behavior
- Alternative: Single web service call with tree structure (slower but transactional)

### 9.2 Relationship Validation

**Current:** Basic error handling

**Future:**
- Validate relationship types exist
- Validate parent/child CI types are compatible
- Pre-validate before creation

### 9.3 Relationship Querying

**Current:** Create relationships only

**Future:**
- Query existing relationships
- Update relationships
- Delete relationships

---

## References

- [Requirements Document](REQUIREMENTS.md)
- [Design Document](DESIGN.md)
- [ADR-0001: ServiceNow CI Class Selection](adr/0001-servicenow-ci-class-selection.md)
- [ServiceNow Constraints](servicenow_constraints.md)

