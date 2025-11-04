# Product Vision: beast-dream-snow-loader

**Project:** beast-dream-snow-loader  
**Purpose:** Load UniFi Dream Machine network data into ServiceNow CMDB  
**Status:** Spec-driven development phase

## Product Overview

beast-dream-snow-loader completes the integration between UniFi network infrastructure and ServiceNow CMDB. It transforms raw UniFi API data into ServiceNow CMDB records, enabling ServiceNow to serve as the authoritative source for network asset management.

## Core Value Propositions

1. **Network Asset Discovery:** Automatically load UniFi devices, sites, hosts, and clients into ServiceNow
2. **CMDB Population:** Create and maintain ServiceNow CMDB tables for network infrastructure
3. **Data Transformation:** Map UniFi schema to ServiceNow CMDB schema
4. **Integration Completion:** Completes the beast-unifi-integration → ServiceNow pipeline

## Target Users

- **ServiceNow Administrators:** Need network infrastructure in CMDB
- **Network Administrators:** Want network devices cataloged in ServiceNow
- **IT Operations:** Need unified asset management across systems

## Key Features (Planned)

1. **ServiceNow Table Creation**
   - Define CMDB tables for UniFi entities
   - Create tables via ServiceNow REST API
   - Schema mapping from UniFi to ServiceNow

2. **Data Transformation**
   - Map UniFi hosts → ServiceNow CMDB records
   - Map UniFi sites → ServiceNow locations/groups
   - Map UniFi devices → ServiceNow CI records
   - Map UniFi clients → ServiceNow client/endpoint records

3. **Data Loading**
   - Batch loading of transformed data
   - Incremental updates (only changed records)
   - Error handling and retry logic
   - Sync status tracking

4. **Integration**
   - Uses `beast_unifi` API clients for source data
   - ServiceNow REST API for destination
   - MID server for secure authentication

## Product Principles

- **OSS First:** MIT licensed, publicly available
- **Deliver while you sell:** Working code demonstrates capability
- **ServiceNow Best Practices:** Follow CMDB data model standards
- **Transformation Focus:** Clean mapping between UniFi and ServiceNow schemas

