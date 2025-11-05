# Batch Processing Architecture: Multi-Phase Batch Loading

**Version:** 1.0  
**Date:** 2025-11-04  
**Status:** Corrected Terminology

## Overview

This document describes the correct architecture and terminology for the batch processing solution used in beast-dream-snow-loader. The solution uses **multi-phase batch processing** for performance optimization, NOT a two-phase commit.

## Correct Terminology

### ❌ INCORRECT Terms (Do Not Use)
- "Two-phase commit"
- "Two-phase transaction"
- "Transaction commit"
- "Database transaction"

### ✅ CORRECT Terms (Use These)
- "Multi-phase batch processing"
- "Multi-phase batch loading"
- "Sequential batch processing"
- "Batch processing optimization"

## Solution Architecture

### What It Is

**Multi-phase batch processing** is a performance optimization strategy for loading data through the ServiceNow REST API Table API.

**How It Works:**
1. **Phase 1:** Batch create all CI records, capture returned `sys_id` values
2. **Phase 2:** Batch create relationship records in `cmdb_rel_ci` table using captured `sys_id` values

**Why It's Faster:**
- Batching creates in Phase 1 is faster than sequential one-by-one processing
- Batching relationship creates in Phase 2 is faster than sequential one-by-one processing
- Optimized for REST API Table API performance characteristics

### What It Is NOT

**NOT a Transaction:**
- This is NOT a database transaction
- This is NOT a two-phase commit protocol
- There is NO transactional guarantee (all-or-nothing)
- Operations are sequential and independent

**NOT Atomic:**
- If Phase 1 succeeds but Phase 2 fails, Phase 1 records remain
- No rollback mechanism
- No transactional integrity

## Why This Architecture?

### Performance Optimization

**Through REST API Table API:**
- Small updates are faster when batched
- Multiple creates in one phase is faster than sequential creates
- Optimized for the Table API's performance characteristics

**For Small Updates:**
- Especially beneficial for small updates
- Avoids overhead of transactional operations
- Maximizes throughput

### ServiceNow Constraints

**sys_id Requirement:**
- ServiceNow requires `sys_id` values for relationships
- `sys_id` values are only available after record creation
- Cannot create relationships during record creation
- Must create records first, then create relationships

**REST API Table API:**
- Table API doesn't support transactional batch operations
- Each create is independent
- No native support for atomic multi-record operations

## Alternative Approaches

### Alternative 1: Single Web Service Call (Not Implemented)

**How It Would Work:**
- Create a custom JavaScript web service in ServiceNow
- Accept a tree structure of all records and relationships
- Process everything in one operation server-side

**Characteristics:**
- **Slower** for small updates (service overhead)
- **Potentially transactional** (could use GlideRecord transactions)
- **More complex** (requires custom web service development)
- **One-phase operation** (not multi-phase)

**Why Not Implemented:**
- Slower for small updates, especially through the Table API
- Requires custom ServiceNow development
- More complex to maintain
- Performance penalty doesn't justify transactional benefits for our use case

### Alternative 2: Sequential One-by-One Processing (Not Used)

**How It Would Work:**
- Create record 1
- Create relationship for record 1
- Create record 2
- Create relationship for record 2
- etc.

**Characteristics:**
- **Slower** (sequential processing)
- **Simpler** (no batching)
- **More API calls** (higher overhead)

**Why Not Used:**
- Too slow for batch operations
- Doesn't optimize for REST API performance
- Higher API call overhead

## Current Implementation

### Phase 1: Batch Record Creation

```python
# Batch create all gateways
for gateway in gateways:
    result = load_gateway_ci(client, gateway)
    sys_id = result.get("sys_id")
    id_mapping[TABLE_GATEWAY_CI][gateway.u_unifi_source_id] = sys_id

# Batch create all locations
for location in locations:
    result = load_location(client, location)
    sys_id = result.get("sys_id")
    id_mapping[TABLE_LOCATION][location.u_unifi_source_id] = sys_id

# ... etc for devices and endpoints
```

**Characteristics:**
- All records of one type created before moving to next type
- `sys_id` values captured in mapping
- Optimized for batch processing

### Phase 2: Batch Relationship Creation

```python
# Batch create relationships using captured sys_ids
for location in locations:
    location_sys_id = id_mapping[TABLE_LOCATION].get(location.u_unifi_source_id)
    gateway_sys_id = id_mapping[TABLE_GATEWAY_CI].get(location.host_id)
    
    rel_data = {
        "parent": gateway_sys_id,
        "child": location_sys_id,
        "type": "Managed by::Manages",
    }
    client.create_record("cmdb_rel_ci", rel_data)
```

**Characteristics:**
- Uses `sys_id` values from Phase 1
- Creates relationships in `cmdb_rel_ci` table
- Optimized for batch processing

## Performance Characteristics

### Throughput Optimization

**Batch Processing:**
- Multiple creates in sequence (same connection, same session)
- Reduced API overhead per record
- Optimized for REST API Table API

**Compared to Sequential:**
- Faster than one-by-one processing
- Better throughput for small updates
- Lower API call overhead

### Trade-offs

**Performance:**
- ✅ Faster than sequential processing
- ✅ Optimized for REST API Table API
- ✅ Better for small updates

**Reliability:**
- ⚠️ Not transactional (no rollback)
- ⚠️ Phase 1 records remain if Phase 2 fails
- ⚠️ No atomic guarantee

## Industry Standard Terminology

### Correct Terms

1. **Batch Processing:** Processing multiple items together
2. **Multi-Phase Processing:** Processing in multiple sequential phases
3. **Sequential Processing:** Processing one phase after another
4. **Performance Optimization:** Optimizing for speed/throughput

### Incorrect Terms (Database Transaction Concepts)

1. **Two-Phase Commit:** Database protocol for distributed transactions
2. **Transaction:** Database concept for atomic operations
3. **Commit:** Database concept for finalizing transactions
4. **Rollback:** Database concept for undoing transactions

**Why They're Wrong:**
- This solution is NOT a database transaction
- This solution is NOT using two-phase commit protocol
- This solution is NOT transactional
- This solution is a performance optimization strategy

## Summary

### What We Have

**Multi-phase batch processing** for performance optimization:
- Phase 1: Batch create CI records
- Phase 2: Batch create relationships
- Optimized for REST API Table API
- Faster than sequential one-by-one processing

### What We Don't Have

**Transactional guarantees:**
- No two-phase commit
- No transaction rollback
- No atomic operations
- No all-or-nothing guarantee

### Why This Is Correct

**Performance optimization:**
- Optimized for REST API Table API performance
- Faster for small updates
- Better throughput

**ServiceNow constraints:**
- sys_ids required for relationships
- sys_ids only available after creation
- REST API doesn't support transactional batch operations

**Industry standard:**
- Uses correct terminology for batch processing
- Not confusing with database transaction concepts
- Clear about performance vs. transactional trade-offs

---

## References

- [Requirements Document](REQUIREMENTS.md) - FR-3.1: Multi-Phase Batch Relationship Linking
- [Design Document](DESIGN.md) - Section 2.2: Multi-Phase Batch Relationship Linking Flow
- [Relationship Requirements](RELATIONSHIP_REQUIREMENTS.md) - REQ-2: Multi-Phase Batch Relationship Linking

