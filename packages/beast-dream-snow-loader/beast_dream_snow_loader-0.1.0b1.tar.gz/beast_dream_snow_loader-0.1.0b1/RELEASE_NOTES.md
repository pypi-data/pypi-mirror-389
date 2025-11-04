# Release Notes

## [Unreleased]

### Planned for Next Release

- ServiceNow table creation via REST API
- Incremental sync support
- Enhanced error recovery and retry logic

### Backlog

- **Optional Minimal ServiceNow Dependency:** Support for instances without CMDB subscription, using only base `cmdb_ci` table
- GraphQL API support investigation
- MID server integration
- Import Sets support

---

## [0.1.0] - Initial Release (Planned)

### Added

#### Core Functionality

- **UniFi Data Models:** Complete Pydantic models for UniFi hosts, sites, devices, and clients
  - Full validation and type safety
  - Support for nested structures and optional fields

- **ServiceNow Data Models:** Complete Pydantic models for ServiceNow CMDB entities
  - Gateway CI, Location, Network Device CI, Endpoint models
  - Proper `sys_id` handling (auto-generated, not set on create)
  - Source tracking with `u_unifi_source_id`
  - Raw data preservation with `u_unifi_raw_data`

- **Data Transformation:** Comprehensive UniFi → ServiceNow transformation
  - Field mapping configuration
  - Nested field flattening (e.g., `reportedState.hardware.mac` → `hardware_mac`)
  - Source data preservation in `u_unifi_raw_data`
  - Two-phase relationship linking (create records first, then link)

- **ServiceNow API Client:** Full-featured REST API client
  - Multiple authentication methods: API key (preferred), OAuth token, Basic Auth
  - 1Password CLI integration for secure credential management
  - Table existence checking
  - Record CRUD operations (create, read, update, query)
  - Changeset detection and association

- **Data Loading:** Batch loading with dependency resolution
  - Individual entity loading functions
  - Two-phase relationship linking (Phase 1: create all records, Phase 2: link relationships)
  - Dependency-aware ordering (gateways → locations → devices → endpoints)
  - Changeset support (detection and optional association)

#### ServiceNow Integration

- **Authentication:** Flexible authentication supporting:
  - API key with service account (production recommended)
  - OAuth 2.0 token (optional)
  - Basic Auth username/password (development/testing only)
  - 1Password CLI integration with graceful fallback

- **Table Support:** Flexible table handling
  - Attempts to use specific CI type tables (`cmdb_ci_network_gateway`, etc.)
  - Falls back to base `cmdb_ci` table if specific tables unavailable
  - Works with or without CMDB CI Class Models plugin

- **Plugin Requirements:**
  - Full support: CMDB CI Class Models plugin (`sn_cmdb_ci_class`)
  - Plugin included with ITOM Visibility subscription
  - Free to activate in PDIs
  - Fallback available if plugin not activated

#### Testing & Quality

- **Unit Tests:** Comprehensive test coverage for:
  - All UniFi models
  - All ServiceNow models
  - Schema mapping and transformation functions
  - Field flattening logic

- **Smoke Test:** Basic connectivity and record creation verification
  - Tests ServiceNow API connectivity
  - Verifies table availability
  - Creates test records
  - Handles table fallback scenarios

- **Code Quality Tools:**
  - Black for code formatting
  - Ruff for linting
  - MyPy for type checking
  - All configured and passing

#### Documentation

- **Setup Guides:**
  - PDI setup guide for REST API access
  - Plugin activation guide for CMDB CI Class Models
  - 1Password integration guide

- **Technical Documentation:**
  - ServiceNow constraints and assumptions
  - Table requirements and plugin dependencies
  - Transformation analysis
  - Environment variable management rules

- **Examples:**
  - Smoke test script
  - Table requirements checker script

### Changed

- Initial implementation of all core features

### Known Limitations

1. **ServiceNow Plugin Dependency:**
   - Full table support requires CMDB CI Class Models plugin
   - Plugin may require CMDB subscription (needs verification - see "Expanded model and asset classes" dependency)
   - Fallback to base `cmdb_ci` table works without plugin

2. **Table Creation:**
   - Not yet implemented
   - Currently assumes tables exist or uses base `cmdb_ci`
   - Planned for future release

3. **Incremental Sync:**
   - Not yet implemented
   - Currently does full loads only
   - Planned for future release

4. **Error Recovery:**
   - Basic error handling implemented
   - Retry logic not yet implemented
   - Planned for future release

### Notes

- This is the initial release, focused on core data transformation and loading functionality
- The tool is designed to work with minimal ServiceNow dependencies (base `cmdb_ci` table) or full CMDB setup
- All authentication methods support execution context detection and graceful degradation
- 1Password integration is optional and works seamlessly with environment variable fallback

---

## Upgrade Notes

### From Previous Versions

N/A - This is the initial release.

### ServiceNow Instance Requirements

**Minimum:**
- ServiceNow instance with REST API enabled
- Admin user with `rest_api_explorer` role
- Base `cmdb_ci` table (always available)

**Recommended:**
- CMDB CI Class Models plugin (`sn_cmdb_ci_class`) activated
- ITOM Visibility subscription (includes plugin)
- Custom fields available for `u_*` prefixed fields

**Optional:**
- Changeset support for transactional operations
- GraphQL API for batch mutations (future)

