# Design: UniFi to ServiceNow Data Transformation

**Feature:** unifi-to-snow-transformation  
**Status:** Design  
**Created:** 2025-11-03  
**Dependencies:** None (foundation feature)

## Overview

This design defines the transformation layer that converts UniFi API data structures into ServiceNow CMDB-compatible formats. The transformation handles nested field flattening, type conversion, and validation.

## Architecture

### Component Structure

```
transformers/
├── unifi_to_snow.py      # Main transformation orchestrator
└── schema_mapper.py      # Field mapping configuration and logic

models/
├── unifi.py              # UniFi data models (Pydantic)
└── servicenow.py         # ServiceNow data models (Pydantic)
```

### Data Flow

```
UniFi API Data (dict/JSON)
    ↓
UniFi Models (Pydantic validation)
    ↓
Transformation Layer (schema mapping)
    ↓
ServiceNow Models (Pydantic validation)
    ↓
ServiceNow-compatible dict/JSON
```

## Data Models

### UniFi Models (`models/unifi.py`)

Type-safe Pydantic models representing UniFi API data structures:

- **UniFiHost**: Represents UniFi gateway/host data
  - Core fields: `id`, `hardwareId`, `type`, `ipAddress`, `owner`, `isBlocked`
  - Nested: `reportedState`, `userData` (sub-models)
  - Timestamps: `registrationTime`, `lastConnectionStateChange`, `latestBackupTime`

- **UniFiSite**: Represents UniFi site/organization data
  - Core fields: `siteId`, `hostId`, `permission`, `isOwner`
  - Nested: `meta`, `statistics` (sub-models)

- **UniFiDevice**: Represents UniFi network device data
  - Core fields: `hostId`, `updatedAt`
  - Note: Schema may need expansion based on actual API response

- **UniFiClient**: Represents UniFi client/endpoint data
  - Core fields: identifiers (hostname, IP, MAC), device type
  - Note: Schema may need expansion based on actual API response

**Principle**: Models use Pydantic for validation and type safety. Optional fields use `Optional[...]` for nullable values.

### ServiceNow Models (`models/servicenow.py`)

Type-safe Pydantic models representing ServiceNow CMDB data structures:

- **ServiceNowGatewayCI**: Network gateway configuration item
  - Fields: `sys_id` (unique), `name`, `ip_address`, `hostname`, `firmware_version`, etc.
  - Flat structure (no nested fields)

- **ServiceNowLocation**: Location/group record
  - Fields: `sys_id`, `name`, `description`, `timezone`, etc.
  - Relationships: `host_id` (FK to gateway)

- **ServiceNowNetworkDeviceCI**: Network device configuration item
  - Fields: `sys_id`, `name`, `mac_address`, `serial_number`, `model`, etc.
  - Relationships: `site_id`, `host_id` (FKs)

- **ServiceNowEndpoint**: Endpoint/client record
  - Fields: `sys_id`, `hostname`, `ip_address`, `mac_address`, `device_type`, etc.
  - Relationships: `site_id`, `device_id` (FKs)

**Principle**: ServiceNow models use flat schemas (no nested objects) per ServiceNow conventions.

## Transformation Layer

### Schema Mapper (`transformers/schema_mapper.py`)

Configuration-driven field mapping system:

- **FieldMappingConfig**: Configuration class defining UniFi → ServiceNow field mappings
  - Source path: `"reportedState.hostname"`
  - Target field: `"hostname"`
  - Transformation function: Optional (e.g., string normalization, type conversion)

- **Mapping Strategies**:
  - Direct mapping: `reportedState.hostname` → `hostname`
  - Nested flattening: `reportedState.hardware.mac` → `hardware_mac_address`
  - Type conversion: `"true"/"false"` → `boolean`
  - Value transformation: `"Dream Machine Pro"` → `"UDM-Pro"`

**Principle**: Mapping configuration is externalized (JSON/YAML) for maintainability. Default mappings are provided.

### Transformation Interface (`transformers/unifi_to_snow.py`)

Core transformation functions:

- **`transform_host(unifi_host: UniFiHost) -> ServiceNowGatewayCI`**
  - Maps UniFi host to ServiceNow gateway CI
  - Flattens `reportedState.*` and `userData.*` fields
  - Validates output using Pydantic model

- **`transform_site(unifi_site: UniFiSite) -> ServiceNowLocation`**
  - Maps UniFi site to ServiceNow location
  - Flattens `meta.*` and `statistics.*` fields
  - Preserves site-to-host relationships

- **`transform_device(unifi_device: UniFiDevice) -> ServiceNowNetworkDeviceCI`**
  - Maps UniFi device to ServiceNow network device CI
  - Extracts device identifiers (MAC, serial, model)
  - Links to sites/hosts via relationships

- **`transform_client(unifi_client: UniFiClient) -> ServiceNowEndpoint`**
  - Maps UniFi client to ServiceNow endpoint
  - Identifies device types (computer, phone, IoT, etc.)
  - Links to sites/devices via relationships

**Principle**: All transformation functions are pure functions (no side effects). Input validation via Pydantic, output validation via Pydantic.

## Field Mapping Details

### Host → Gateway CI Mapping

| UniFi Field | ServiceNow Field | Notes |
|-------------|------------------|-------|
| `id` | `sys_id` | Unique identifier |
| `hardwareId` | `hardware_id` | Hardware identifier |
| `reportedState.hostname` | `hostname` | Hostname |
| `ipAddress` | `ip_address` | IP address |
| `reportedState.version` | `firmware_version` | Firmware version |
| `reportedState.name` | `name` | Display name |
| `reportedState.state` | `state` | Device state |
| `reportedState.hardware.mac` | `mac_address` | MAC address |
| `reportedState.hardware.serialno` | `serial_number` | Serial number |

### Site → Location Mapping

| UniFi Field | ServiceNow Field | Notes |
|-------------|------------------|-------|
| `siteId` | `sys_id` | Unique identifier |
| `meta.name` | `name` | Site name |
| `meta.desc` | `description` | Site description |
| `meta.timezone` | `timezone` | Timezone |
| `hostId` | `host_id` | FK to gateway |

### Device → Network Device CI Mapping

| UniFi Field | ServiceNow Field | Notes |
|-------------|------------------|-------|
| Device identifier | `sys_id` | Unique identifier |
| MAC address | `mac_address` | MAC address |
| Serial number | `serial_number` | Serial number |
| Model | `model` | Device model |
| `hostId` | `host_id` | FK to host |

### Client → Endpoint Mapping

| UniFi Field | ServiceNow Field | Notes |
|-------------|------------------|-------|
| Client identifier | `sys_id` | Unique identifier |
| Hostname | `hostname` | Hostname |
| IP address | `ip_address` | IP address |
| MAC address | `mac_address` | MAC address |
| Device type | `device_type` | Computer, phone, IoT, etc. |

## Error Handling

### Validation Errors

- **Input Validation**: UniFi models validate input data. Invalid data raises `ValidationError` with details.
- **Output Validation**: ServiceNow models validate transformed data. Invalid transformation raises `ValidationError`.

### Missing Fields

- **Optional Fields**: Use `Optional[...]` in models for nullable fields.
- **Default Values**: Provide sensible defaults where appropriate (e.g., empty string, None).
- **Field Mapping**: Missing source fields result in `None` in target (unless default provided).

### Nested Field Handling

- **Flattening Strategy**: Use underscore notation for nested fields (e.g., `reportedState.hostname` → `hostname`, `reportedState.hardware.mac` → `hardware_mac_address`).
- **Deep Nesting**: Handle deeply nested fields (e.g., `reportedState.autoUpdate.schedule.day` → `auto_update_schedule_day`).

## Type Safety

- **Input Types**: All transformation functions accept Pydantic models (not raw dicts).
- **Output Types**: All transformation functions return Pydantic models (not raw dicts).
- **Type Hints**: All functions have complete type hints (MyPy strict mode).
- **Runtime Validation**: Pydantic validates at runtime (catches type mismatches).

## Configuration

### Field Mapping Configuration

Default mappings provided in `transformers/schema_mapper.py`. Custom mappings can be provided via:
- JSON configuration file
- YAML configuration file
- Programmatic configuration (dict)

**Principle**: Configuration is optional - sensible defaults provided. Custom mappings override defaults.

## Integration Points

### Input: `beast-unifi-integration`

- **API**: Uses `beast_unifi` API clients to fetch UniFi data
- **Data Format**: Expects dict/JSON from API (validated via Pydantic models)
- **Dependency**: `beast-unifi-integration` package (external dependency)

### Output: ServiceNow REST API

- **Data Format**: ServiceNow-compatible dict/JSON (from Pydantic models via `.dict()` or `.model_dump()`)
- **Usage**: Transformed data ready for ServiceNow REST API calls

## Testing Strategy

### Unit Tests

- Test each transformation function with sample UniFi data
- Verify field mappings are correct
- Test error handling (missing fields, invalid data)
- Test nested field flattening

### Integration Tests

- Test end-to-end: UniFi API data → Transformation → ServiceNow-compatible format
- Test with real UniFi API responses (mocked)
- Verify Pydantic validation at each stage

## Design Principles

1. **Type Safety**: Pydantic models throughout for compile-time and runtime validation
2. **Separation of Concerns**: Models separate from transformation logic
3. **Configuration-Driven**: Field mappings externalized for maintainability
4. **Pure Functions**: Transformation functions have no side effects
5. **Validation at Boundaries**: Validate input (UniFi) and output (ServiceNow) data
6. **Flat Schemas**: ServiceNow models use flat structures (no nesting)
7. **Error Handling**: Clear error messages with validation details

## Next Steps

1. Implement UniFi models (`models/unifi.py`)
2. Implement ServiceNow models (`models/servicenow.py`)
3. Implement schema mapper (`transformers/schema_mapper.py`)
4. Implement transformation functions (`transformers/unifi_to_snow.py`)
5. Write unit tests for each component
6. Write integration tests for end-to-end flow


