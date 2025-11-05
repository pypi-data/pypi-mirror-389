# Transformation Analysis: Issues & Fixes

## Current Issues

### 1. Information Preservation ❌

**Problem:** Only subset of fields mapped, losing data:
- Nested `reportedState.*` fields (many not extracted)
- `userData.*` fields (not extracted)
- `statistics.*` fields (not extracted)
- Timestamps and metadata

**Impact:** Data loss, cannot audit or reconcile

### 2. Relationship Preservation ❌

**Problem:** Relationships broken:
- Using `hostId` as `sys_id` for devices (conflicts with ServiceNow auto-generation)
- Relationships reference source IDs, not ServiceNow sys_ids
- Cannot link records after creation

**Impact:** Broken referential integrity, orphaned records

### 3. ServiceNow Best Practices ❌

**Problems:**
- `sys_id` should NOT be provided (ServiceNow auto-generates)
- Missing source identifier field to track UniFi origin
- Missing required ServiceNow fields (e.g., `class_name`, `classification`)
- Relationships should use sys_id references, not custom IDs

**Impact:** Won't work with standard ServiceNow tables, violates CMDB practices

## Required Fixes

### Fix 1: Make sys_id Optional, Add Source Identifier

**ServiceNow Models:**
```python
class ServiceNowGatewayCI(BaseModel):
    # sys_id: str = Field(..., ...)  # ❌ Remove - ServiceNow generates
    sys_id: str | None = Field(None, ...)  # ✅ Optional, for updates only
    u_unifi_source_id: str = Field(..., description="UniFi source identifier")  # ✅ Add
    name: str = Field(..., ...)
    # ... rest of fields
```

**Transformation:**
- Map UniFi `id` → `u_unifi_source_id` (not `sys_id`)
- Don't provide `sys_id` on create (let ServiceNow generate)
- Use `sys_id` only for updates (upsert by source ID)

### Fix 2: Preserve Source Data

**Add Source Data Preservation:**
- Store raw UniFi JSON in `u_unifi_raw_data` (JSON field)
- Extract ALL nested fields, not just mapped ones
- Preserve timestamps: `u_unifi_registration_time`, etc.

### Fix 3: Multi-Phase Batch Relationship Linking

**Phase 1: Create Records**
- Create all records, capture returned `sys_id`s
- Store mapping: `{unifi_source_id: servicenow_sys_id}`

**Phase 2: Link Relationships**
- Update records with relationship references
- Use `sys_id` values from Phase 1
- Example: `location.host_id = gateway.sys_id` (not source ID)

### Fix 4: ServiceNow CMDB Requirements

**Required Fields for CI Tables:**
- `class_name`: Table name (e.g., "cmdb_ci_network_gateway")
- `classification`: CI classification (e.g., "Network Gateway")
- `category`: CI category
- `asset`: Link to asset record (if applicable)

**Standard Field Naming:**
- Use ServiceNow standard fields where possible
- Custom fields: `u_*` prefix (e.g., `u_unifi_source_id`)
- Relationships: Use standard reference fields

## Recommended Implementation Order

1. **Fix sys_id handling** (Critical - blocks smoke testing)
   - Make sys_id optional in models
   - Add `u_unifi_source_id` field
   - Update transformations

2. **Add source data preservation** (Important)
   - Store raw UniFi data
   - Extract all nested fields

3. **Implement multi-phase batch relationship linking** (Critical)
   - Create records first, capture sys_ids
   - Update relationships second

4. **Add ServiceNow required fields** (Important)
   - Add `class_name`, `classification`, etc.
   - Update transformations

## Questions for ServiceNow Instance

Before implementing fixes, need to know:
1. Are custom fields allowed? (for `u_unifi_source_id`, `u_unifi_raw_data`)
2. Which standard tables are available? (or need custom tables)
3. What are required fields for each table?
4. Can we use Import Sets or must use direct API?

