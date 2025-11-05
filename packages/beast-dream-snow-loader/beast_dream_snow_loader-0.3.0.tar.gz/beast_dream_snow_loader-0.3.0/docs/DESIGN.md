# Design: beast-dream-snow-loader

**Version:** 1.0  
**Date:** 2025-11-04  
**Status:** Implemented (Backward Pass Documentation)

## Overview

This document describes the system design for beast-dream-snow-loader, derived from the implemented solution. This is a backward pass from implementation to design.

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────┐
│  UniFi Data │
│  (Source)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Transformation Layer                │
│  - UniFi Models (Pydantic)          │
│  - Transformers (unifi_to_snow.py)  │
│  - Schema Mapper                    │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  ServiceNow Models (Pydantic)        │
│  - ServiceNowGatewayCI              │
│  - ServiceNowLocation               │
│  - ServiceNowNetworkDeviceCI        │
│  - ServiceNowEndpoint               │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  ServiceNow Integration Layer       │
│  - API Client (api_client.py)       │
│    - Authentication                  │
│    - Hibernation Detection          │
│    - Exponential Backoff            │
│    - CRUD Operations                │
│  - Loader (loader.py)               │
│    - Individual Entity Loading       │
│    - Batch Loading                   │
│    - Multi-Phase Batch Relationship Linking  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────┐
│ ServiceNow  │
│   CMDB      │
└─────────────┘
```

### 1.2 Component Overview

**1. Transformation Layer:**
- **Purpose:** Transform UniFi data models to ServiceNow data models
- **Components:**
  - `models/unifi.py`: UniFi data models (Pydantic)
  - `models/servicenow.py`: ServiceNow data models (Pydantic)
  - `transformers/unifi_to_snow.py`: Transformation functions
  - `transformers/schema_mapper.py`: Field mapping configuration

**2. ServiceNow Integration Layer:**
- **Purpose:** Interact with ServiceNow REST API
- **Components:**
  - `servicenow/api_client.py`: REST API client with authentication, hibernation handling, retry logic
  - `servicenow/loader.py`: Data loading functions with relationship management

**3. Operations Layer:**
- **Purpose:** Operational concerns (retry, logging, metrics, etc.)
- **Components:**
  - `operations/retry.py`: Retry logic with exponential backoff
  - `operations/logger.py`: Structured logging
  - `operations/metrics.py`: Metrics collection
  - `operations/config.py`: Configuration management

---

## 2. Data Flow

### 2.1 Entity Loading Flow

```
1. UniFi Data (JSON/dict)
   ↓
2. UniFi Model (Pydantic validation)
   ↓
3. Transformer Function
   - Field mapping
   - Nested field extraction
   - Source ID preservation
   - Raw data preservation
   ↓
4. ServiceNow Model (Pydantic validation)
   ↓
5. Loader Function
   - Table/class selection
   - sys_id exclusion
   - API call
   ↓
6. ServiceNow Record Created
   - sys_id returned
   ↓
7. sys_id captured for Phase 2
```

### 2.2 Multi-Phase Batch Relationship Linking Flow

```
PHASE 1: Record Creation
─────────────────────────
1. Create Gateways
   ↓ sys_ids captured
2. Create Locations
   ↓ sys_ids captured
3. Create Devices
   ↓ sys_ids captured
4. Create Endpoints
   ↓ sys_ids captured

Mapping: {table: {source_id: sys_id}}

PHASE 2: Relationship Creation
────────────────────────────────
5. For each Location:
   - Find Gateway sys_id by source_id
   - Create cmdb_rel_ci record:
     parent=gateway_sys_id
     child=location_sys_id
     type="Managed by::Manages"

6. For each Device:
   - Find Gateway sys_id by source_id
   - Create cmdb_rel_ci record (Gateway → Device)
   - Find Location sys_id by source_id
   - Create cmdb_rel_ci record (Location → Device)

7. For each Endpoint:
   - Find Location sys_id by source_id
   - Create cmdb_rel_ci record (Location → Endpoint)
   - Find Device sys_id by source_id
   - Create cmdb_rel_ci record (Device → Endpoint)
```

---

## 3. Component Design

### 3.1 ServiceNowAPIClient

**Purpose:** Handle all ServiceNow REST API interactions

**Key Responsibilities:**
- Authentication (API key, OAuth, Basic Auth, 1Password)
- HTTP request/response handling
- Hibernation detection and retry
- Exponential backoff with pacifier
- CRUD operations (create, read, update, query)

**Key Methods:**
- `create_record(table, data)`: Create a record
- `get_record(table, sys_id)`: Get a record by sys_id
- `update_record(table, sys_id, data)`: Update a record
- `query_records(table, query, limit)`: Query records with filters

**Design Decisions:**
- **Hibernation Detection:** Checks response content type and HTML indicators
- **Exponential Backoff:** Base 1.5, max 60s, 8 attempts
- **Pacifier:** Streamlit-aware, falls back to terminal animation
- **Authentication:** Graceful degradation (1Password → env vars)

**Error Handling:**
- Detects hibernation and retries automatically
- Provides clear error messages
- Falls back gracefully when services unavailable

---

### 3.2 Loader Functions

**Purpose:** Load entities into ServiceNow with proper table/class handling

**Key Functions:**
- `load_gateway_ci()`: Load gateway into `cmdb_ci_netgear`
- `load_location()`: Load location into `cmdb_ci` with `sys_class_name=cmdb_ci_site`
- `load_network_device_ci()`: Load device into `cmdb_ci` with `sys_class_name=cmdb_ci_network_node`
- `load_endpoint()`: Load endpoint into base `cmdb_ci`
- `load_entities_with_relationships()`: Batch load with relationship linking

**Design Decisions:**
- **Table vs. Class Distinction:** 
  - Direct tables (e.g., `cmdb_ci_netgear`) used directly
  - Classes (e.g., `cmdb_ci_site`) use base `cmdb_ci` with `sys_class_name`
- **sys_id Handling:** Always excluded from create operations (ServiceNow auto-generates)
- **Fallback Logic:** Falls back to base `cmdb_ci` if specific tables unavailable
- **Multi-Phase Batch Processing:** Performance optimization - batch create records in Phase 1, then batch create relationships in Phase 2. This is faster than sequential one-by-one processing through the REST API Table API.

**Relationship Management:**
- Uses `cmdb_rel_ci` table (not fields on CI records)
- Relationship types:
  - "Managed by::Manages"
  - "Located in::Contains"
  - "Connects to::Connected by"

---

### 3.3 Transformer Functions

**Purpose:** Transform UniFi models to ServiceNow models

**Key Functions:**
- `transform_host()`: UniFi Host → ServiceNow Gateway CI
- `transform_site()`: UniFi Site → ServiceNow Location
- `transform_device()`: UniFi Device → ServiceNow Network Device CI
- `transform_client()`: UniFi Client → ServiceNow Endpoint

**Design Decisions:**
- **Field Mapping:** Uses `schema_mapper.py` for configurable field mappings
- **Nested Field Extraction:** Flattens nested JSON structures
- **Source Data Preservation:** Stores raw UniFi data in `u_unifi_raw_data`
- **Source ID Preservation:** Stores UniFi IDs in `u_unifi_source_id`
- **Relationship Source IDs:** Preserves `host_id`, `site_id`, `device_id` for Phase 2 linking

**Field Mapping Strategy:**
- Configurable via `FieldMappingConfig`
- Handles nested field extraction (e.g., `reportedState.hostname`)
- Fallback values for missing fields
- Validation via Pydantic models

---

## 4. Data Model Design

### 4.1 UniFi Models

**Models:**
- `UniFiHost`: Gateway device (Dream Machine)
- `UniFiSite`: Site/location
- `UniFiDevice`: Network device (switch, AP, etc.)
- `UniFiClient`: Network endpoint (computer, phone, etc.)

**Characteristics:**
- Pydantic BaseModel for validation
- Nested structures (e.g., `reportedState.*`)
- Source identifiers (e.g., `id`, `siteId`, `hostId`)

---

### 4.2 ServiceNow Models

**Models:**
- `ServiceNowGatewayCI`: Gateway CI in `cmdb_ci_netgear`
- `ServiceNowLocation`: Location in `cmdb_ci` with `sys_class_name=cmdb_ci_site`
- `ServiceNowNetworkDeviceCI`: Network device in `cmdb_ci` with `sys_class_name=cmdb_ci_network_node`
- `ServiceNowEndpoint`: Endpoint in base `cmdb_ci`

**Common Fields:**
- `sys_id`: Optional (excluded on create, ServiceNow auto-generates)
- `u_unifi_source_id`: Required (tracks UniFi source)
- `u_unifi_raw_data`: Optional (raw UniFi JSON for audit)

**Relationship Fields (for Phase 2):**
- `host_id`: Source ID of related gateway (not sys_id)
- `site_id`: Source ID of related site (not sys_id)
- `device_id`: Source ID of related device (not sys_id)

**Note:** Relationship fields are source IDs, not sys_ids. They're converted to sys_ids in Phase 2.

---

## 5. Error Handling Design

### 5.1 Hibernation Handling

**Detection:**
- Checks response content type (not `application/json`)
- Checks HTML content for hibernation indicators
- Returns `True` if hibernating, `False` otherwise

**Retry Strategy:**
- Exponential backoff: `base_delay * (exponential_base ^ (attempt - 1))`
- Parameters:
  - Base delay: 2.0 seconds
  - Max delay: 60.0 seconds
  - Exponential base: 1.5
  - Max attempts: 8

**User Feedback:**
- Streamlit spinner if in Streamlit context
- Terminal animation with progress if in CLI context
- Clear error message if instance doesn't wake up

---

### 5.2 Table/Class Fallback

**Strategy:**
- Try specific table first (e.g., `cmdb_ci_netgear`)
- If error (403, 400, "Invalid table"), fallback to base `cmdb_ci` with `sys_class_name`
- Clear error messages for debugging

**Example:**
```python
try:
    return client.create_record("cmdb_ci_netgear", data)
except Exception as e:
    if "Invalid table" in str(e) or "403" in str(e):
        data["sys_class_name"] = "cmdb_ci_netgear"
        return client.create_record("cmdb_ci", data)
    raise
```

---

### 5.3 Relationship Creation Errors

**Strategy:**
- Continue processing if relationship creation fails
- Log error with context (which entities, which relationship type)
- Don't fail entire batch if one relationship fails

**Error Messages:**
- Clear indication of which relationship failed
- Include source IDs for debugging
- Include relationship type

---

## 6. Authentication Design

### 6.1 Authentication Methods (Priority Order)

1. **1Password CLI** (if available)
   - Checks for `op` command availability
   - Retrieves credentials from 1Password vault
   - Graceful degradation if not available

2. **Environment Variables** (fallback)
   - `SERVICENOW_INSTANCE`
   - `SERVICENOW_USERNAME`
   - `SERVICENOW_PASSWORD` or `SERVICENOW_API_KEY`
   - `SERVICENOW_OAUTH_TOKEN`

3. **Basic Auth** (username/password)
4. **OAuth Token** (if provided)

### 6.2 Credential Flow

```
1. Check 1Password CLI availability
   ↓ (if available)
2. Retrieve from 1Password vault
   ↓ (if not available)
3. Read from environment variables
   ↓ (if not available)
4. Error: Credentials required
```

---

## 7. Relationship Design

### 7.1 Relationship Types

**Standard ServiceNow Relationship Types:**
- `"Managed by::Manages"`: Gateway manages Location/Device
- `"Located in::Contains"`: Location/Device contains Location/Device/Endpoint
- `"Connects to::Connected by"`: Device connects to Endpoint

### 7.2 Relationship Table Structure

**Table:** `cmdb_rel_ci`

**Fields:**
- `parent`: sys_id of parent CI
- `child`: sys_id of child CI
- `type`: Relationship type (e.g., "Managed by::Manages")

**Note:** Relationships are NOT stored as fields on CI records. They're stored in the separate `cmdb_rel_ci` table.

### 7.3 Relationship Mapping

**Source ID to sys_id Mapping:**
```python
id_mapping = {
    "cmdb_ci_netgear": {"unifi_host_id_1": "sys_id_1", ...},
    "cmdb_ci_site": {"unifi_site_id_1": "sys_id_2", ...},
    ...
}
```

**Phase 2 Process:**
1. Look up source ID in `id_mapping`
2. Get corresponding `sys_id`
3. Create `cmdb_rel_ci` record with `parent` and `child` sys_ids

---

## 8. Performance Considerations

### 8.1 Batch Loading

**Current Implementation:**
- Sequential record creation (one at a time)
- No parallelization
- No batching of API calls

**Future Optimization Opportunities:**
- Parallel record creation (with rate limiting)
- Batch API calls (if ServiceNow supports)
- Import Sets for bulk loading

### 8.2 Retry Strategy

**Exponential Backoff:**
- Prevents overwhelming ServiceNow instance
- Respects rate limits
- Provides good user experience with pacifier

**Parameters Tuned For:**
- PDI hibernation wake-up time
- Network latency
- ServiceNow API response time

---

## 9. Security Design

### 9.1 Credential Management

**1Password Integration:**
- Credentials stored in 1Password vault
- Retrieved via CLI (secure)
- No credentials in code or logs

**Environment Variables:**
- Fallback for OSS users
- Standard practice for CI/CD
- Clear documentation of required variables

**No Hardcoded Credentials:**
- Never in code
- Never in logs
- Never in version control

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Coverage:**
- Model validation (Pydantic)
- Transformation functions
- Field mapping
- Error handling

### 10.2 Integration Tests

**Smoke Tests:**
- Basic connectivity
- Record creation
- Relationship linking

**Test Data:**
- Sample UniFi data
- ServiceNow PDI for testing

---

## 11. Deployment Considerations

### 11.1 Dependencies

**Required:**
- Python 3.10+
- ServiceNow instance with REST API access
- User with appropriate roles

**Optional:**
- 1Password CLI (for credential management)
- Streamlit (for interactive UI)
- `sn_cmdb_ci_class` plugin (for full table support)

### 11.2 Configuration

**Environment Variables:**
- ServiceNow instance URL
- Authentication credentials
- Optional retry/timeout settings

**No Configuration Files:**
- All configuration via environment variables
- Keeps deployment simple
- Works well with containers/cloud

---

## 12. Future Design Considerations

### 12.1 Scalability

**Current Limitations:**
- Sequential processing
- No parallelization
- No batching

**Future Options:**
- Parallel processing with rate limiting
- Batch API calls
- Import Sets for bulk operations
- GraphQL API for transactional operations

### 12.2 Reliability

**Current:**
- Basic error handling
- Hibernation retry
- Fallback mechanisms

**Future:**
- Circuit breaker pattern
- More comprehensive retry logic
- Better error recovery
- Transaction support (changesets)

---

## References

- [Requirements Document](REQUIREMENTS.md)
- [ADR-0001: ServiceNow CI Class Selection](adr/0001-servicenow-ci-class-selection.md)
- [ServiceNow Constraints](servicenow_constraints.md)
- [Table Requirements](table_requirements.md)

