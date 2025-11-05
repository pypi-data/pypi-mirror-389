# ServiceNow Integration Constraints & Assumptions

**Purpose:** Document explicit assumptions and constraints for ServiceNow integration. These may be modified or violated in future revisions.

**Last Updated:** 2025-11-03

## Critical Cluster-Wide Constraints

### Environment Variables: User's Home Directory Only

**Constraint:** All environment variables must be in the home directory of the executing user. No exceptions.

**For beast nodes/participants:** Environment variables can go nowhere else. This is a hard constraint.

**Enforcement:**
- Never create `.env` files in project directories (cluster-wide policy violation)
- Never use `python-dotenv` or any library to load `.env` files
- **Execution context detection & graceful degradation:**
  - **Beast node**: Has access to beast services (1Password, etc.) or they are provisionable
  - **OSS user**: No beast services required - this is the **public-facing default** for this repo
- Code detects available services (1Password CLI, etc.) and uses them if present
- Code gracefully degrades when beast services aren't available (OSS user case)
- Code reads from system environment via `os.getenv()` only - automatically uses executing user's environment
- The executing user/system is responsible for making environment variables available in the system environment

**Can Violate:** No - this is a cluster-wide policy constraint.

**See:** `docs/env_var_rules.md` for detailed rules.

## Assumptions

### 1. Custom Fields Available ✅

**Assumption:** ServiceNow instance allows creating custom fields with `u_*` prefix.

**Fields We Assume Available:**
- `u_unifi_source_id` (string) - Stores UniFi source identifier
- `u_unifi_raw_data` (JSON/string) - Stores raw UniFi JSON for audit/reconciliation
- `u_unifi_registration_time` (datetime) - UniFi registration timestamp
- `u_unifi_last_connection_change` (datetime) - Last connection state change

**Rationale:** Standard ServiceNow custom field pattern. If unavailable, we'll need to use standard fields or different approach.

**Impact if Violated:** Would need to use standard fields only or different identifier strategy.

---

### 2. Standard CMDB Tables Available ⚠️

**Assumption:** Standard ServiceNow CMDB tables are available and can be used.

**Tables We Use (Actual Available Classes):**
- `cmdb_ci_netgear` - Network gear CI (physical hardware - for UniFi Dream Machine gateway)
- `cmdb_ci_site` - Site/location records (`cmdb_location` doesn't exist)
- `cmdb_ci_network_node` - Network node CI (subclass of `cmdb_ci_netgear` for network devices)
- `cmdb_ci` - Base CI table (for endpoints/clients with `sys_class_name`)

**Note on Class Selection:**
- ServiceNow CIs can be queried from multiple parent class tables (inheritance hierarchy)
- We use the most specific appropriate class for each device type
- See `docs/class_selection.md` for detailed class selection rationale and hierarchy documentation

**PDI Finding (Verified):** Specific CI type tables (e.g., `cmdb_ci_network_gateway`) do not exist on PDI.
- **Verified via:** `scripts/check_table_requirements.py` - confirms tables don't exist
- **Plugin Required:** **CMDB CI Class Models** (`sn_cmdb_ci_class`) plugin must be activated
- **Plugin Dependency:** Plugin states "Expanded model and asset classes will be installed" - may require CMDB subscription/licensing
- **Action for PDI:** Activate plugin via System Definition > Plugins > "CMDB CI Class Models"
- **Base Table Available:** Base `cmdb_ci` table exists and works for smoke testing (fallback option)
- **Workaround:** Use base `cmdb_ci` table with `sys_class_name` field to categorize CIs, or activate plugin
- **Documentation:** See `docs/pdi_activation_guide.md` for activation instructions
- **For Production:** Plugin should be activated. If not available, users can use base table fallback or request plugin activation.
- **Minimal Install Option:** Backlog item - support for instances without CMDB subscription, using only base `cmdb_ci` table (no plugin required)

**Rationale:** Standard ServiceNow CMDB structure. If custom tables needed, we'll adjust.
**Smoke Test Result:** Base `cmdb_ci` table works. Specific CI type tables not found on PDI.
**Verification Method:** Script queries `sys_db_object` table and attempts table access to verify existence.

**Impact if Violated:** Would need to create custom tables or use different table names or base `cmdb_ci` table.

---

### 3. Required Fields Minimal ✅

**Assumption:** ServiceNow tables have minimal required fields beyond standard CMDB fields.

**Required Fields We Assume:**
- `name` - Required for all CI tables
- `class_name` - May be auto-populated or optional
- `classification` - May be auto-populated or optional
- Standard fields: `sys_id` (auto-generated), `sys_created_on`, etc.

**Rationale:** Conservative assumption - start minimal, add fields as needed.

**Impact if Violated:** Would need to add required fields to models and transformations.

---

### 4. Direct REST API (Not Import Sets) ✅

**Assumption:** We use ServiceNow REST API Table API directly for record creation/updates.

**Rationale:** Simpler for initial implementation, more control. Import Sets can be added later if needed.

**Impact if Violated:** Would need to refactor to use Import Set API instead.

---

### 5. Authentication: Service Account with API Key (Production) ✅

**Assumption:** ServiceNow instance uses a **named service account user** for API operations:
- Service account user has a name/identity (for audit logs)
- Service account user has specific role/permissions for API operations
- Service account user **cannot log into UI** (no UI access)
- Service account uses **API key** (not password) for authentication

**Authentication Methods:**
1. **API Key** (Primary for production) - `SERVICENOW_API_KEY` + `SERVICENOW_USERNAME` env vars
   - Basic Auth with API key as password
   - Service account user (no UI login)
   - Named user for audit trail
2. **OAuth Token** (Optional) - `SERVICENOW_OAUTH_TOKEN` env var
   - Bearer token authentication
   - Can be tied to service account user
3. **Username/Password** (Development/testing only) - `SERVICENOW_USERNAME` + `SERVICENOW_PASSWORD`
   - Basic Auth with actual password
   - **NOT recommended for production**
   - Only for dev/testing with regular user accounts

**Rationale:** 
- Service account pattern provides audit trail (named user) without exposing UI credentials
- API keys are simpler than OAuth for system-to-system integrations
- Never use normal user credentials in production (except dev/testing)
- Service account user should not have UI login capability

**Impact if Violated:** Would need to use regular user credentials (not recommended for production).

---

### 6. Upsert Strategy: Query by Source ID ✅

**Assumption:** For upserts (create or update), we:
1. Query by `u_unifi_source_id` to find existing record
2. If found, update by `sys_id`
3. If not found, create new record

**Rationale:** Standard upsert pattern. Alternative: use Import Sets with transform maps.

**Impact if Violated:** Would need different upsert strategy (e.g., Import Sets, external ID field).

---

### 7. Relationship Linking: Multi-Phase Batch Processing ✅

**Assumption:** We link relationships using multi-phase batch processing:
1. **Phase 1:** Create all records (without relationships), capture returned `sys_id`s
2. **Phase 2:** Update records with relationship references using captured `sys_id`s

**Rationale:** ServiceNow requires `sys_id` for relationships. Cannot use source IDs. REST API doesn't support transactional/batch operations.

**Current Implementation:** REST API with multi-phase batch processing approach (implemented and tested).

**Alternative Approaches (To Investigate):**
- **GraphQL API**: May support batch mutations and transactional semantics (single-phase approach)
  - ServiceNow GraphQL API available since Quebec release
  - Need to verify: batch mutations, transactional semantics, inline relationship references
  - If supported, could eliminate multi-phase batch processing complexity
  - Investigation needed before switching
- **Change Management**: Standard/Regular Changes could track entire batch operation
- **Import Sets**: Could use Import Sets with transform maps (different approach)

**Impact if Violated:** Would need single-phase approach (e.g., GraphQL batch mutations, pre-create placeholder records, or Import Sets).

**Discovery Tasks:**
1. **GraphQL API**: Investigate batch mutations and transactional semantics before considering switch from REST
2. **Changesets**: Investigate if we can:
   - Initiate/start a changeset before writing records
   - Detect if we're already in a changeset context
   - Include both schema and data changes in changeset
   - Changesets can wrap CMDB data modifications for transactional behavior

---

### 8. Field Naming Convention ✅

**Assumption:** 
- ServiceNow fields use snake_case (e.g., `ip_address`, `mac_address`)
- Custom fields use `u_*` prefix (e.g., `u_unifi_source_id`)
- Relationships use standard ServiceNow reference fields (e.g., `host_id` → sys_id reference)

**Rationale:** Standard ServiceNow conventions.

**Impact if Violated:** Would need different field naming strategy.

---

## Constraints

### 1. sys_id Handling

**Constraint:** `sys_id` is auto-generated by ServiceNow and cannot be provided on create.

**Implementation:**
- `sys_id` is optional in models (for updates only)
- Do not provide `sys_id` when creating records
- Use `sys_id` from created records for relationships

**Can Violate:** No - this is a ServiceNow platform constraint.

---

### 2. Relationship References

**Constraint:** Relationships must reference ServiceNow `sys_id` values, not source identifiers.

**Implementation:**
- Store mapping: `{unifi_source_id: servicenow_sys_id}`
- Use `sys_id` values for all relationship fields
- Multi-phase batch processing: create records → link relationships

**Can Violate:** No - this is a ServiceNow platform constraint.

---

### 3. Field Extraction

**Constraint:** Must flatten nested UniFi fields to flat ServiceNow schema.

**Implementation:**
- Extract nested fields (e.g., `reportedState.hostname` → `hostname`)
- Store raw data in `u_unifi_raw_data` for preservation
- Map to ServiceNow-compatible field names

**Can Violate:** Yes - can preserve more nested structure if ServiceNow supports it.

---

## Revision History

| Date | Change | Reason |
|------|--------|--------|
| 2025-11-03 | Initial assumptions | First implementation |

## Future Revision Considerations

When modifying constraints/assumptions:
1. Document the change in this file
2. Update affected code (models, transformations, loaders)
3. Update tests to reflect new constraints
4. Update smoke test if needed

## Questions That May Need Answers Later

1. **Custom fields available?** → Assumed YES, verified in smoke test
2. **Standard tables or custom?** → **PDI Finding:** Specific CI type tables (e.g., `cmdb_ci_network_gateway`) may not exist on all instances. May need to use base `cmdb_ci` table or create custom tables.
   - **ITOM Required?** Specific CI type tables may require ITOM (IT Operations Management) plugin to be installed/activated.
   - **Workaround:** Use base `cmdb_ci` table with `sys_class_name` field to categorize CIs.
3. **Required fields?** → Assumed MINIMAL, may need more
4. **Import Sets vs direct API?** → Assumed DIRECT API, may switch to Import Sets
5. **OAuth vs Basic Auth?** → Using BASIC AUTH (username/password), API key for production
6. **GraphQL vs REST API?** → Currently using REST, GraphQL may support batch/transactional operations
7. **Change Management?** → Not currently using, but Standard/Regular Changes could track batch operations

## Alternative Approaches (Future Considerations)

### GraphQL API (Alternative to REST)

**Potential Benefits:**
- **Batch Mutations**: Create multiple records in a single GraphQL mutation
- **Transactional Semantics**: Mutations may support all-or-nothing behavior
- **Dynamic Operations**: Build mutations programmatically based on data
- **Simplified Relationship Linking**: May be able to reference created records within same mutation

**ServiceNow Support:**
- ServiceNow supports GraphQL API (since Quebec release)
- GraphQL Table API available for CMDB operations
- Dynamic GraphQL schema generation from table definitions

**Impact:**
- Could eliminate multi-phase batch relationship linking
- Single GraphQL mutation could create all records and set relationships
- May require ServiceNow GraphQL API client implementation

**Current Status:** Using REST API (multi-phase batch processing approach). GraphQL could be future enhancement.

---

### Change Management (Alternative to Direct API)

**Potential Benefits:**
- **Standard Change**: For batch sync operations (pre-approved, fast-track)
- **Regular/Normal Change**: For updates that need approval workflow
- **Audit Trail**: All operations tracked under Change Request
- **Rollback Capability**: Change can be rolled back if needed
- **Workflow Integration**: Changes go through normal ServiceNow approval process

**Use Cases:**
- **Full Sync**: Standard Change for entire UniFi sync operation
- **Incremental Updates**: Standard or Regular Change depending on scope
- **Bulk Operations**: All record creations/updates tracked under one Change

**Implementation Pattern:**
1. Create Change Request (Standard or Regular)
2. Associate all record operations with Change Request
3. Change Request provides unit of work for entire sync
4. Approval workflow (if Regular Change) or auto-approval (if Standard Change)

**Impact:**
- Better audit trail and compliance
- Operations tracked as managed changes
- Supports rollback and change tracking
- May require Change Management configuration

**Current Status:** Not using Change Management. Could be future enhancement for production operations.

