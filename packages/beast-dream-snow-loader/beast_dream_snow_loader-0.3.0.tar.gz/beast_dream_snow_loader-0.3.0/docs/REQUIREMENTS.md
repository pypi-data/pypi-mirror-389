# Requirements: beast-dream-snow-loader

**Version:** 1.0  
**Date:** 2025-11-04  
**Status:** Implemented (Backward Pass Documentation)

## Overview

This document defines the functional and non-functional requirements for the beast-dream-snow-loader system, derived from the implemented solution. This is a backward pass from implementation to requirements.

## 1. Functional Requirements

### 1.1 Data Transformation

#### FR-1.1: UniFi Host to ServiceNow Gateway CI Transformation
**Requirement:** The system SHALL transform UniFi Host data into ServiceNow Gateway CI format.

**Details:**
- Map UniFi host fields to ServiceNow `cmdb_ci_netgear` table schema
- Extract nested fields from `reportedState.*` structure
- Preserve source identifier in `u_unifi_source_id` field
- Store raw UniFi data in `u_unifi_raw_data` for audit/reconciliation
- Handle missing/null fields gracefully with fallbacks
- Map hardware information (MAC, serial number) from nested structures

**Acceptance Criteria:**
- All required ServiceNow fields are populated
- Source data is preserved for audit trail
- Nested JSON structures are flattened appropriately
- Validation passes using Pydantic models

---

#### FR-1.2: UniFi Site to ServiceNow Location Transformation
**Requirement:** The system SHALL transform UniFi Site data into ServiceNow Location format.

**Details:**
- Map UniFi site to `cmdb_ci_site` class (via `cmdb_ci` table with `sys_class_name`)
- Extract site metadata (name, description, timezone)
- Preserve relationship source IDs (`host_id`) for Phase 2 relationship linking
- Store raw UniFi data in `u_unifi_raw_data`

**Acceptance Criteria:**
- Location records created with correct `sys_class_name`
- Relationship source IDs preserved for linking
- Source data preserved for audit

---

#### FR-1.3: UniFi Device to ServiceNow Network Device CI Transformation
**Requirement:** The system SHALL transform UniFi Device data into ServiceNow Network Device CI format.

**Details:**
- Map UniFi device to `cmdb_ci_network_node` class (via `cmdb_ci` table with `sys_class_name`)
- Extract device identifiers (MAC address, hostname)
- Preserve relationship source IDs (`host_id`, `site_id`) for Phase 2 linking
- Store raw UniFi data in `u_unifi_raw_data`

**Acceptance Criteria:**
- Network device records created with correct `sys_class_name`
- MAC address and identifiers properly extracted
- Relationship source IDs preserved

---

#### FR-1.4: UniFi Client to ServiceNow Endpoint Transformation
**Requirement:** The system SHALL transform UniFi Client data into ServiceNow Endpoint format.

**Details:**
- Map UniFi client to base `cmdb_ci` table
- Extract endpoint information (IP address, MAC address, hostname)
- Preserve relationship source IDs (`site_id`, `device_id`) for Phase 2 linking
- Store raw UniFi data in `u_unifi_raw_data`

**Acceptance Criteria:**
- Endpoint records created in base `cmdb_ci` table
- Network identifiers properly extracted
- Relationship source IDs preserved

---

### 1.2 ServiceNow Integration

#### FR-2.1: ServiceNow REST API Client
**Requirement:** The system SHALL provide a ServiceNow REST API client with authentication support.

**Details:**
- Support multiple authentication methods:
  - API key authentication (preferred)
  - OAuth token authentication
  - Basic authentication (username/password fallback)
- Support 1Password CLI integration for credential retrieval
- Gracefully degrade when 1Password not available (OSS use case)
- Read credentials from environment variables as fallback

**Acceptance Criteria:**
- All authentication methods work correctly
- 1Password integration works when available
- Falls back to environment variables when 1Password unavailable
- Clear error messages for authentication failures

---

#### FR-2.2: Record CRUD Operations
**Requirement:** The system SHALL support Create, Read, Update, and Query operations on ServiceNow records.

**Details:**
- Create records via REST API
- Read individual records by `sys_id`
- Update existing records
- Query records with filters and ordering
- Handle ServiceNow table vs. class distinction:
  - Direct tables (e.g., `cmdb_ci_netgear`) can be used directly
  - Classes (e.g., `cmdb_ci_site`, `cmdb_ci_network_node`) must use base `cmdb_ci` table with `sys_class_name`

**Acceptance Criteria:**
- All CRUD operations work correctly
- Table vs. class distinction handled properly
- Proper error handling for invalid operations

---

#### FR-2.3: ServiceNow Instance Hibernation Handling
**Requirement:** The system SHALL detect and handle ServiceNow PDI hibernation with automatic retry.

**Details:**
- Detect hibernation by checking response content type and HTML indicators
- Implement exponential backoff retry strategy:
  - Base delay: 2.0 seconds
  - Maximum delay: 60.0 seconds
  - Exponential base: 1.5
  - Maximum attempts: 8
- Provide user-friendly pacifier/feedback during retries:
  - Streamlit spinner if in Streamlit context
  - Terminal animation with progress indication if in CLI context
- Clear error messages if instance doesn't wake up after max attempts

**Acceptance Criteria:**
- Hibernation detected correctly
- Retry with exponential backoff works
- User receives clear feedback during retries
- Appropriate error messages if instance doesn't wake up

---

### 1.3 Relationship Management

#### FR-3.1: Multi-Phase Batch Relationship Linking
**Requirement:** The system SHALL implement a multi-phase batch processing approach for establishing relationships between CIs.

**Details:**
- **Phase 1:** Batch create all CI records, capture returned `sys_id` values
- **Phase 2:** Batch create relationship records in `cmdb_rel_ci` table using captured `sys_id` values
- Relationships supported:
  - Location → Gateway: "Managed by::Manages"
  - Device → Gateway: "Managed by::Manages"
  - Device → Location: "Located in::Contains"
  - Endpoint → Location: "Located in::Contains"
  - Endpoint → Device: "Connects to::Connected by"

**Rationale:** This is a performance optimization for batch operations through the REST API Table API. ServiceNow requires `sys_id` values for relationships, which are only available after record creation. By batching creates in phases, we optimize for speed compared to sequential one-by-one processing.

**Alternative (not implemented):** A single web service call that accepts a tree structure and processes everything in one operation would be slower but potentially transactional. This is not implemented here as it would be slower for small updates, especially through the Table API.

**Acceptance Criteria:**
- Phase 1 creates all records and captures `sys_id` values
- Phase 2 creates relationship records using `cmdb_rel_ci` table
- All relationships properly established
- Source ID to `sys_id` mapping maintained correctly

---

#### FR-3.2: Relationship Source ID Mapping
**Requirement:** The system SHALL map UniFi source IDs to ServiceNow `sys_id` values for relationship linking.

**Details:**
- Store mapping: `{table_name: {source_id: sys_id}}`
- Use source IDs from UniFi data (`hostId`, `siteId`, etc.) as keys
- Map to ServiceNow `sys_id` values returned from record creation
- Use mapping in Phase 2 to establish relationships

**Acceptance Criteria:**
- Source ID to `sys_id` mapping maintained for all created records
- Mapping used correctly in Phase 2 relationship creation
- Missing mappings handled gracefully with error messages

---

#### FR-3.3: Relationship Creation via cmdb_rel_ci Table
**Requirement:** The system SHALL create relationships using the `cmdb_rel_ci` table, not by updating fields on CI records.

**Details:**
- Create relationship records in `cmdb_rel_ci` table
- Use `parent`, `child`, and `type` fields
- Do NOT attempt to update relationship fields directly on CI records (these fields don't exist on abstract base `cmdb_ci` class)

**Rationale:** ServiceNow uses the `cmdb_rel_ci` table for CI relationships. Custom relationship fields on CI records don't exist and won't persist.

**Acceptance Criteria:**
- All relationships created in `cmdb_rel_ci` table
- No attempts to update non-existent fields on CI records
- Relationship types correctly specified

---

### 1.4 Data Loading

#### FR-4.1: Individual Entity Loading
**Requirement:** The system SHALL provide functions to load individual entities (gateways, locations, devices, endpoints) into ServiceNow.

**Details:**
- `load_gateway_ci()`: Load gateway into `cmdb_ci_netgear` table
- `load_location()`: Load location into `cmdb_ci` table with `sys_class_name=cmdb_ci_site`
- `load_network_device_ci()`: Load device into `cmdb_ci` table with `sys_class_name=cmdb_ci_network_node`
- `load_endpoint()`: Load endpoint into base `cmdb_ci` table
- All functions exclude `sys_id` from create operations (ServiceNow auto-generates)
- Fallback to base `cmdb_ci` table if specific tables unavailable

**Acceptance Criteria:**
- All entity types can be loaded individually
- Proper table/class distinction handled
- `sys_id` excluded from create operations
- Fallback logic works correctly

---

#### FR-4.2: Batch Loading with Relationships
**Requirement:** The system SHALL provide a batch loading function that creates entities and establishes relationships.

**Details:**
- `load_entities_with_relationships()` function accepts lists of entities
- Loads entities in dependency order:
  1. Gateways (no dependencies)
  2. Locations (depend on gateways)
  3. Devices (depend on gateways and locations)
  4. Endpoints (depend on locations and devices)
- Implements multi-phase batch relationship linking
- Returns mapping of source IDs to `sys_id` values

**Acceptance Criteria:**
- All entity types loaded in correct dependency order
- Relationships established correctly
- Source ID to `sys_id` mapping returned
- Error handling for missing dependencies

---

### 1.5 Error Handling

#### FR-5.1: Graceful Error Handling
**Requirement:** The system SHALL handle errors gracefully with informative messages.

**Details:**
- Handle ServiceNow API errors (403, 400, etc.)
- Provide fallback mechanisms when specific tables unavailable
- Clear error messages for authentication failures
- Informative messages for relationship creation failures
- Log errors appropriately

**Acceptance Criteria:**
- Errors don't crash the system
- Clear error messages provided
- Fallback mechanisms work
- Appropriate logging

---

## 2. Non-Functional Requirements

### 2.1 Type Safety

#### NFR-1.1: Pydantic Model Validation
**Requirement:** The system SHALL use Pydantic models for type-safe data validation.

**Details:**
- All data models use Pydantic BaseModel
- Field validation at model boundaries
- Type checking with MyPy

**Acceptance Criteria:**
- All models pass Pydantic validation
- Type checking passes with MyPy
- Invalid data rejected with clear error messages

---

### 2.2 Reliability

#### NFR-2.1: ServiceNow PDI Hibernation Resilience
**Requirement:** The system SHALL automatically handle ServiceNow PDI hibernation without user intervention when possible.

**Details:**
- Automatic detection and retry
- Exponential backoff to avoid overwhelming instance
- Clear user feedback during retries
- Graceful failure if instance doesn't wake up

**Acceptance Criteria:**
- Hibernation handled automatically
- User receives clear feedback
- System doesn't fail silently

---

### 2.3 Usability

#### NFR-3.1: User-Friendly Feedback
**Requirement:** The system SHALL provide clear, user-friendly feedback during operations.

**Details:**
- Progress indicators during retries (pacifier)
- Clear success/failure messages
- Informative error messages
- Context-aware feedback (Streamlit vs. CLI)

**Acceptance Criteria:**
- Users understand what's happening
- Feedback is clear and actionable
- No silent failures

---

### 2.4 Maintainability

#### NFR-4.1: Documentation
**Requirement:** The system SHALL be well-documented with requirements, design, and implementation documentation.

**Details:**
- Requirements documented (this document)
- Design decisions documented (ADRs)
- Implementation documented (code comments, docstrings)
- Usage examples provided

**Acceptance Criteria:**
- All documentation complete and accurate
- Examples work correctly
- Design decisions traceable

---

## 3. Data Requirements

### 3.1 Source Data (UniFi)

**Required Fields:**
- Host: `id`, `ipAddress`, `reportedState.*`
- Site: `siteId`, `hostId`, `meta.*`
- Device: `hostId`, `mac`, identifiers
- Client: `hostname`, `ip`, `mac`, `siteId`

### 3.2 Target Data (ServiceNow)

**Required Fields:**
- Gateway: `name`, `ip_address`, `u_unifi_source_id`
- Location: `name`, `sys_class_name=cmdb_ci_site`, `u_unifi_source_id`
- Network Device: `name`, `mac_address`, `sys_class_name=cmdb_ci_network_node`, `u_unifi_source_id`
- Endpoint: `hostname`, `ip_address`, `mac_address`, `u_unifi_source_id`

**Optional but Recommended:**
- `u_unifi_raw_data`: Raw UniFi JSON for audit/reconciliation
- `firmware_version`: For gateways/devices
- `description`: For locations

---

## 4. Integration Requirements

### 4.1 ServiceNow Instance Requirements

**Minimum Requirements:**
- ServiceNow instance with REST API access
- User with appropriate roles:
  - `rest_api_explorer`
  - `web_service_admin`
  - `itil`
- Base `cmdb_ci` table available (always present)

**Optional Requirements:**
- `sn_cmdb_ci_class` plugin for full table support (not required)
- CMDB subscription (not required for basic functionality)

---

## 5. Constraints

### 5.1 ServiceNow Constraints

- **Table vs. Class Distinction:** Some CI classes (e.g., `cmdb_ci_site`, `cmdb_ci_network_node`) are classes, not direct tables. Must use base `cmdb_ci` table with `sys_class_name`.
- **Relationship Management:** Relationships must use `cmdb_rel_ci` table, not fields on CI records.
- **sys_id Generation:** ServiceNow auto-generates `sys_id` values - must not be provided on create.
- **PDI Hibernation:** ServiceNow PDIs hibernate after inactivity - must handle gracefully.

### 5.2 Implementation Constraints

- **Class Selection:** Fixed for MVP (see ADR-0001)
- **Batch Loading:** Multi-phase batch processing for performance optimization (not transactional)
- **Error Handling:** Basic error handling - no automatic recovery for all error types

---

## 6. Out of Scope (Future)

- Table creation automation
- Incremental sync
- GraphQL API support
- Import Sets integration
- Configurable class mappings (MVP constraint)
- Advanced retry logic for all error types
- Changeset automation

---

## References

- [ADR-0001: ServiceNow CI Class Selection](adr/0001-servicenow-ci-class-selection.md)
- [MVP Definition](MVP_DEFINITION.md)
- [ServiceNow Constraints](servicenow_constraints.md)
- [Table Requirements](table_requirements.md)

