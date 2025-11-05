# Tasks: UniFi to ServiceNow Data Transformation

**Feature:** unifi-to-snow-transformation  
**Status:** Tasks  
**Created:** 2025-11-03  
**Design:** `design.md`

## Task Breakdown

### 1. Data Models Implementation

#### 1.1 Implement UniFi Host Model
**Capability:** System can validate and represent UniFi host/gateway data with type safety.

**Tasks:**
- Create `models/unifi.py` module
- Implement `UniFiHost` Pydantic model with core fields (`id`, `hardwareId`, `type`, `ipAddress`, etc.)
- Implement nested `ReportedState` Pydantic sub-model for `reportedState.*` fields
- Implement nested `UserData` Pydantic sub-model for `userData.*` fields
- Handle timestamp fields (`registrationTime`, `lastConnectionStateChange`, `latestBackupTime`)
- Add type hints and validation rules
- Write unit tests (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- `UniFiHost` validates sample UniFi API host data
- Nested fields are properly structured
- Missing optional fields are handled gracefully
- Type validation catches invalid data

#### 1.2 Implement UniFi Site Model
**Capability:** System can validate and represent UniFi site/organization data with type safety.

**Tasks:**
- Implement `UniFiSite` Pydantic model with core fields (`siteId`, `hostId`, `permission`, `isOwner`)
- Implement nested `SiteMeta` Pydantic sub-model for `meta.*` fields
- Implement nested `SiteStatistics` Pydantic sub-model for `statistics.*` fields
- Add type hints and validation rules
- Write unit tests (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- `UniFiSite` validates sample UniFi API site data
- Nested fields are properly structured
- Missing optional fields are handled gracefully

#### 1.3 Implement UniFi Device Model
**Capability:** System can validate and represent UniFi network device data with type safety.

**Tasks:**
- Implement `UniFiDevice` Pydantic model with core fields (`hostId`, `updatedAt`)
- Add fields based on actual API response (may need expansion)
- Add type hints and validation rules
- Write unit tests (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- `UniFiDevice` validates sample UniFi API device data
- Model is extensible for additional fields

#### 1.4 Implement UniFi Client Model
**Capability:** System can validate and represent UniFi client/endpoint data with type safety.

**Tasks:**
- Implement `UniFiClient` Pydantic model with identifiers (hostname, IP, MAC)
- Add device type classification
- Add type hints and validation rules
- Write unit tests (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- `UniFiClient` validates sample UniFi API client data
- Device types are properly identified

#### 1.5 Implement ServiceNow Models
**Capability:** System can validate and represent ServiceNow CMDB data structures with type safety.

**Tasks:**
- Create `models/servicenow.py` module
- Implement `ServiceNowGatewayCI` Pydantic model (flat schema, no nesting)
- Implement `ServiceNowLocation` Pydantic model (flat schema)
- Implement `ServiceNowNetworkDeviceCI` Pydantic model (flat schema)
- Implement `ServiceNowEndpoint` Pydantic model (flat schema)
- Add type hints and validation rules
- Write unit tests (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- All ServiceNow models have flat schemas (no nested objects)
- Models validate sample ServiceNow-compatible data
- Foreign key relationships are represented as string IDs

### 2. Schema Mapping Implementation

#### 2.1 Implement Field Mapping Configuration
**Capability:** System can define and manage field mappings between UniFi and ServiceNow schemas.

**Tasks:**
- Create `transformers/schema_mapper.py` module
- Implement `FieldMappingConfig` configuration class
- Define default field mappings for hosts → gateway CI
- Define default field mappings for sites → location
- Define default field mappings for devices → network device CI
- Define default field mappings for clients → endpoint
- Support nested field flattening (e.g., `reportedState.hostname` → `hostname`)
- Write unit tests (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- Field mappings are configurable and documented
- Nested fields are properly flattened
- Default mappings cover core fields from requirements

#### 2.2 Implement Field Flattening Logic
**Capability:** System can flatten nested UniFi fields into flat ServiceNow-compatible fields.

**Tasks:**
- Implement nested field flattening function (e.g., `reportedState.hardware.mac` → `hardware_mac_address`)
- Handle deeply nested fields (e.g., `reportedState.autoUpdate.schedule.day`)
- Use underscore notation for flat field names
- Write unit tests for various nesting scenarios (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- Nested fields are correctly flattened
- Field naming follows ServiceNow conventions
- Deep nesting is handled appropriately

### 3. Transformation Functions Implementation

#### 3.1 Implement Host Transformation
**Capability:** System can transform UniFi host data into ServiceNow gateway CI format.

**Tasks:**
- Create `transformers/unifi_to_snow.py` module
- Implement `transform_host(unifi_host: UniFiHost) -> ServiceNowGatewayCI` function
- Apply field mappings from schema mapper
- Flatten nested `reportedState.*` and `userData.*` fields
- Handle missing/null fields appropriately
- Validate output using `ServiceNowGatewayCI` model
- Write unit tests with sample data (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- Function transforms sample UniFi host to ServiceNow gateway CI
- All required fields are mapped correctly
- Output validates against ServiceNow model
- Missing fields are handled gracefully

#### 3.2 Implement Site Transformation
**Capability:** System can transform UniFi site data into ServiceNow location format.

**Tasks:**
- Implement `transform_site(unifi_site: UniFiSite) -> ServiceNowLocation` function
- Apply field mappings from schema mapper
- Flatten nested `meta.*` and `statistics.*` fields
- Preserve site-to-host relationships (`hostId` → `host_id`)
- Handle missing/null fields appropriately
- Validate output using `ServiceNowLocation` model
- Write unit tests with sample data (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- Function transforms sample UniFi site to ServiceNow location
- Relationships are preserved
- Output validates against ServiceNow model

#### 3.3 Implement Device Transformation
**Capability:** System can transform UniFi device data into ServiceNow network device CI format.

**Tasks:**
- Implement `transform_device(unifi_device: UniFiDevice) -> ServiceNowNetworkDeviceCI` function
- Apply field mappings from schema mapper
- Extract device identifiers (MAC, serial, model)
- Link devices to sites/hosts via relationships
- Handle missing/null fields appropriately
- Validate output using `ServiceNowNetworkDeviceCI` model
- Write unit tests with sample data (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- Function transforms sample UniFi device to ServiceNow network device CI
- Device identifiers are correctly extracted
- Relationships are preserved
- Output validates against ServiceNow model

#### 3.4 Implement Client Transformation
**Capability:** System can transform UniFi client data into ServiceNow endpoint format.

**Tasks:**
- Implement `transform_client(unifi_client: UniFiClient) -> ServiceNowEndpoint` function
- Apply field mappings from schema mapper
- Extract client identifiers (hostname, IP, MAC)
- Identify device types (computer, phone, IoT device, etc.)
- Link clients to sites/devices via relationships
- Handle missing/null fields appropriately
- Validate output using `ServiceNowEndpoint` model
- Write unit tests with sample data (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- Function transforms sample UniFi client to ServiceNow endpoint
- Device types are correctly identified
- Relationships are preserved
- Output validates against ServiceNow model

### 4. Error Handling and Validation

#### 4.1 Implement Input Validation
**Capability:** System validates UniFi input data and provides clear error messages for invalid data.

**Tasks:**
- Ensure UniFi models validate input data (Pydantic validation)
- Handle `ValidationError` exceptions with clear messages
- Test with invalid data scenarios (missing fields, wrong types, etc.)
- Write unit tests for validation errors (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- Invalid UniFi data raises `ValidationError` with details
- Error messages are clear and actionable
- Required fields are enforced

#### 4.2 Implement Output Validation
**Capability:** System validates transformed ServiceNow data and provides clear error messages for invalid transformations.

**Tasks:**
- Ensure ServiceNow models validate transformed data (Pydantic validation)
- Handle `ValidationError` exceptions with clear messages
- Test with invalid transformation scenarios
- Write unit tests for validation errors (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- Invalid ServiceNow data raises `ValidationError` with details
- Error messages indicate which transformation failed
- Required fields are enforced

#### 4.3 Implement Missing Field Handling
**Capability:** System handles missing optional fields gracefully without errors.

**Tasks:**
- Ensure all optional fields use `Optional[...]` type hints
- Provide sensible defaults where appropriate
- Test with missing optional fields
- Write unit tests for missing field scenarios (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- Missing optional fields result in `None` (or default value)
- No errors are raised for missing optional fields
- Required fields still enforce presence

### 5. Integration and Testing

#### 5.1 Write Integration Tests
**Capability:** System correctly transforms end-to-end from UniFi API data to ServiceNow-compatible format.

**Tasks:**
- Create integration test: UniFi API response (dict) → UniFi model → Transformation → ServiceNow model → dict
- Test with sample UniFi API responses (mocked)
- Verify Pydantic validation at each stage
- Test all entity types (hosts, sites, devices, clients)
- Write integration tests (TDD: RED-GREEN-REFACTOR)

**Acceptance:**
- End-to-end transformation works correctly
- All validation stages pass
- Output is ServiceNow-compatible

#### 5.2 Document Field Mappings
**Capability:** Field mappings are documented for maintainability and troubleshooting.

**Tasks:**
- Document all field mappings in code (docstrings)
- Create field mapping reference documentation
- Include examples in documentation
- Update design.md with actual mappings if they differ

**Acceptance:**
- Field mappings are documented
- Documentation is clear and examples are provided
- Documentation is accessible to developers

## Implementation Order

1. **Data Models** (1.1-1.5): Foundation for everything else
2. **Schema Mapping** (2.1-2.2): Needed for transformations
3. **Transformation Functions** (3.1-3.4): Core functionality
4. **Error Handling** (4.1-4.3): Quality and robustness
5. **Integration and Testing** (5.1-5.2): Validation and documentation

## TDD Approach

All tasks follow RED-GREEN-REFACTOR:
- **RED**: Write failing test first
- **GREEN**: Implement minimal code to pass test
- **REFACTOR**: Improve code while keeping tests green

## Dependencies

- **beast-unifi-integration**: For understanding UniFi API data format (external dependency)
- **pydantic**: For data models and validation (already in dependencies)
- **python-dotenv**: For configuration (already in dependencies)


