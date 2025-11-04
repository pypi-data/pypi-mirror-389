# Requirements: UniFi to ServiceNow Data Transformation

**Feature:** unifi-to-snow-transformation  
**Status:** Planned  
**Created:** 2025-11-03  
**Source Schema:** `docs/unifi_schema.sql`

## Requirements (EARS Format)

### WHEN the system receives UniFi hosts data THEN it SHALL transform it to ServiceNow network gateway CI format.

**Rationale:** UniFi hosts are gateway devices (Dream Machines) that map to ServiceNow network gateway CIs.

**Source Schema (from `docs/unifi_schema.sql`):**
- `hosts` table with fields: `id`, `hardwareId`, `type`, `ipAddress`, `reportedState.*`, etc.

**Acceptance:**
- Extract key fields: id, hardwareId, IP address, hostname, firmware version
- Map nested fields (e.g., `reportedState.hostname` → `hostname`)
- Handle missing/null fields appropriately
- Validate transformed data against ServiceNow requirements

---

### WHEN the system receives UniFi sites data THEN it SHALL transform it to ServiceNow location/group format.

**Rationale:** UniFi sites are organizational units that map to ServiceNow locations or groups.

**Source Schema:**
- `sites` table with fields: `siteId`, `hostId`, `meta.name`, `meta.desc`, `statistics.*`, etc.

**Acceptance:**
- Map site metadata to ServiceNow location/group fields
- Include site statistics if relevant
- Handle site-to-host relationships

---

### WHEN the system receives UniFi devices data THEN it SHALL transform it to ServiceNow network device CI format.

**Rationale:** UniFi devices (switches, APs, etc.) map to ServiceNow network device CIs.

**Source Schema:**
- `devices` table (minimal in current schema - may need expansion from API)

**Acceptance:**
- Extract device identifiers (MAC, serial, model)
- Map device metadata to ServiceNow CI fields
- Link devices to sites/hosts

---

### WHEN the system receives UniFi clients data THEN it SHALL transform it to ServiceNow endpoint/client format.

**Rationale:** UniFi clients (computers, phones, TVs, thermostats) map to ServiceNow endpoint/client records.

**Acceptance:**
- Extract client identifiers (hostname, IP, MAC)
- Map client metadata to ServiceNow endpoint fields
- Identify device types (computer, phone, IoT device, etc.)
- Link clients to sites/devices

---

### IF source data has nested fields THEN the system SHALL flatten them for ServiceNow schema.

**Rationale:** ServiceNow prefers flat schemas; UniFi has nested JSON structures.

**Acceptance:**
- Flatten `reportedState.*` fields
- Flatten `userData.*` fields
- Flatten `statistics.*` fields
- Use field naming that makes sense in ServiceNow context

---

### WHERE field names differ between UniFi and ServiceNow THEN the system SHALL provide clear mapping documentation.

**Rationale:** Field mapping should be documented and maintainable.

**Acceptance:**
- Document all field mappings
- Use configuration-driven mapping where possible
- Support custom field mappings via configuration

