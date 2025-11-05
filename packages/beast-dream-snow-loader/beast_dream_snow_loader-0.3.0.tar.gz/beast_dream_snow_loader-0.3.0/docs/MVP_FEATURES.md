# MVP Feature List

## Release 0.1.0 (Initial Release)

### Core Features ✅

1. **UniFi Data Models** ✅
   - UniFi Host (gateway) model
   - UniFi Site model
   - UniFi Device model
   - UniFi Client model
   - Full Pydantic validation

2. **ServiceNow Data Models** ✅
   - ServiceNow Gateway CI model
   - ServiceNow Location model
   - ServiceNow Network Device CI model
   - ServiceNow Endpoint model
   - All models with `sys_id` handling and `u_unifi_source_id` tracking

3. **Data Transformation** ✅
   - UniFi → ServiceNow field mapping
   - Nested field flattening
   - Source data preservation (`u_unifi_raw_data`)
   - Multi-phase batch relationship linking

4. **ServiceNow API Client** ✅
   - REST API client with authentication
   - Support for API key, OAuth token, Basic Auth
   - 1Password CLI integration
   - Table existence checking
   - Record CRUD operations

5. **Data Loading** ✅
   - Individual entity loading functions
   - Multi-phase batch relationship linking
   - Batch loading with dependency resolution
   - Changeset support (detection and association)

### ServiceNow Integration

- **Authentication:** API key (preferred), OAuth token, Basic Auth (fallback)
- **Tables:** Supports specific CI type tables if available, falls back to base `cmdb_ci` table
- **Plugin Requirement:** CMDB CI Class Models (`sn_cmdb_ci_class`) for full table support
- **Fallback:** Base `cmdb_ci` table with `sys_class_name` (works without plugin)

### Testing & Quality

- **Unit Tests:** All models and transformers have unit tests
- **Smoke Test:** Basic connectivity and record creation test
- **Code Quality:** Black, Ruff, MyPy configured and passing

### Documentation

- **Setup Guides:** PDI setup, plugin activation
- **Constraints:** ServiceNow assumptions and constraints documented
- **Table Requirements:** Plugin dependencies and verification methods
- **API Usage:** Examples and integration patterns

## Known Limitations

1. **ServiceNow CI Class Selection (MVP Constraint):**
   - Class mappings are hardcoded for MVP (see ADR-0001)
   - Gateway: `cmdb_ci_netgear` (physical hardware)
   - Location: `cmdb_ci_site`
   - Network Device: `cmdb_ci_network_node`
   - Endpoint: `cmdb_ci` (base table with `sys_class_name`)
   - Future: Configurable class mappings per device type
   - **Reference:** [ADR-0001](../adr/0001-servicenow-ci-class-selection.md)

2. **ServiceNow Plugin Dependency:**
   - Full table support requires CMDB CI Class Models plugin
   - Plugin may require CMDB subscription (needs verification)
   - Fallback to base `cmdb_ci` table available

3. **Table Creation:**
   - Not yet implemented (planned for future release)
   - Currently assumes tables exist or uses base `cmdb_ci`

4. **Incremental Sync:**
   - Not yet implemented (planned for future release)
   - Currently does full loads only

5. **Error Recovery:**
   - Basic error handling implemented
   - Retry logic not yet implemented

## Future Features (Backlog)

1. **Optional Minimal ServiceNow Dependency** 🔄
   - Support for instances without CMDB subscription
   - Use only base `cmdb_ci` table (no plugin required)
   - Document minimal installation requirements

2. **ServiceNow Table Creation**
   - Auto-create tables via REST API
   - Schema validation
   - Idempotent table creation

3. **Incremental Sync**
   - Track last sync timestamp
   - Only load changed records
   - Conflict resolution

4. **Change Management Integration**
   - Create change requests for batch operations
   - Changeset support (full implementation)
   - Audit trail

5. **GraphQL API Support**
   - Investigate GraphQL for batch mutations
   - Transactional semantics
   - Relationship linking simplification

6. **MID Server Integration**
   - Secure authentication via MID server
   - On-premise ServiceNow instances

7. **Import Sets**
   - Alternative to direct REST API
   - Bulk data loading
   - Better error handling for large datasets

8. **Configurable Class Mappings** 🔄
   - Support configuration of ServiceNow CI class mappings per device type
   - Allow dynamic class selection based on device characteristics
   - Support custom class mappings via configuration
   - **MVP Constraint:** Class mappings are hardcoded (see ADR-0001)

9. **Observatory Gateway Experiment** 🔄
   - Cloudflare Workers gateway for public API access
   - Performance benchmarking (gateway vs direct)
   - Rate limiting behavior testing
   - Observatory infrastructure (observatory.nkllon.com)
   - **Purpose:** Learning, benchmarking, lab experimentation
   - **Not blocking:** Experimental enhancement, valuable for data/insights

