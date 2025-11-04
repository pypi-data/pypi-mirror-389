# Requirements: ServiceNow CMDB Table Creation

**Feature:** servicenow-table-creation  
**Status:** Planned  
**Created:** 2025-11-03

## Requirements (EARS Format)

### WHEN the system needs to load UniFi data THEN it SHALL create ServiceNow CMDB tables if they don't exist.

**Rationale:** ServiceNow tables must exist before data can be loaded.

**Acceptance:**
- Check if tables exist before creating
- Create tables via ServiceNow REST API Table API
- Handle table creation errors appropriately
- Support idempotent operations (create if not exists)

---

### WHEN creating ServiceNow tables THEN the system SHALL map UniFi schema to ServiceNow CMDB schema.

**Rationale:** ServiceNow CMDB has different schema conventions than raw UniFi data.

**Acceptance:**
- Map UniFi `hosts` → ServiceNow network gateway CI table
- Map UniFi `sites` → ServiceNow location/group tables
- Map UniFi `devices` → ServiceNow network device CI table
- Map UniFi `clients` → ServiceNow endpoint/client table
- Handle nested fields (e.g., `reportedState.hostname` → flat ServiceNow field)

---

### IF ServiceNow table creation fails THEN the system SHALL provide clear error messages and rollback if possible.

**Rationale:** Failures should be recoverable and informative.

**Acceptance:**
- Detailed error messages including table name and error reason
- Rollback created tables if subsequent creation fails
- Log all table creation operations

---

### WHERE credentials are needed THEN the system SHALL use 1Password CLI and environment variable fallback.

**Rationale:** Secure credential management without hardcoding.

**Acceptance:**
- Try 1Password CLI first (Beastmaster vault)
- Falls back to environment variables (~/.env)
- Never hardcodes credentials in code

---

### WHEN tables are created THEN the system SHALL document the table structure and field mappings.

**Rationale:** Documentation enables maintenance and troubleshooting.

**Acceptance:**
- Generate table schema documentation
- Document field mappings (UniFi → ServiceNow)
- Include in project documentation

