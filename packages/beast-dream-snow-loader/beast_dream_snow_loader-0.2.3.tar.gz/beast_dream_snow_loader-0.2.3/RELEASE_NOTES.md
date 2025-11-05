# Release Notes

## [Unreleased]

### Planned for Next Release

- ServiceNow table creation via REST API
- Incremental sync support
- Enhanced ServiceNow API client integration

---

## [0.2.0] - 2025-11-04 - Operational Resilience Release

### Added

#### Operational Resilience & Error Handling

- **Comprehensive Error Handling:** Complete error classification and context capture
  - Structured error contexts with operation details, timing, and environment info
  - ServiceNow-specific error parsing with detailed API response analysis
  - Error aggregation and pattern detection for troubleshooting
  - Secure error messaging without credential exposure

- **Retry Management:** Intelligent retry logic with exponential backoff
  - Configurable retry policies with jitter to prevent thundering herd
  - Rate limit detection and automatic delay handling
  - Retryable error classification (network, timeout, server errors)
  - ServiceNow rate limit header parsing and respect

- **Circuit Breaker Pattern:** Fault tolerance and cascading failure prevention
  - Configurable failure thresholds and recovery timeouts
  - State management (CLOSED → OPEN → HALF_OPEN → CLOSED)
  - Thread-safe implementation with proper state transitions
  - Automatic recovery testing and circuit closing

- **Health Monitoring:** Comprehensive system and dependency health checks
  - ServiceNow API connectivity monitoring with response time tracking
  - System resource monitoring (CPU, memory, disk usage)
  - Credential availability checking (1Password CLI, environment variables)
  - Overall health status calculation and alerting

- **Metrics Collection:** Performance tracking and trend analysis
  - Operation-level metrics (response times, success rates, error rates)
  - System-level metrics (resource usage, uptime, connection counts)
  - Percentile calculations (P95, P99 response times)
  - Historical trend analysis and performance bottleneck identification

- **Structured Logging:** Production-ready logging with operational context
  - JSON-formatted logs with structured data for analysis
  - Multiple output targets (console, file) with configurable levels
  - Operational event tracking (errors, retries, circuit breaker events)
  - Postmortem-ready logging with correlation IDs and context preservation

#### Configuration Management

- **Environment Detection:** Automatic deployment environment detection
  - Development, testing, staging, production environment detection
  - Environment-specific configuration defaults and behaviors
  - Platform and process information collection for debugging

- **Configuration Validation:** Comprehensive Pydantic-based configuration
  - Type-safe configuration with validation and error reporting
  - Environment variable integration with secure credential handling
  - Configuration file support with environment override capabilities
  - Beast-compliant configuration patterns and quality standards

#### Beast Project Compliance

- **Security & Credentials:** Enhanced credential management following beast principles
  - 1Password CLI as canonical source with environment variable fallback
  - Secure credential access logging without sensitive data exposure
  - Multiple authentication method prioritization and fallback handling

- **Quality Standards:** Full integration with beast quality gates
  - Structured logging compatible with beast monitoring standards
  - Quality gate enforcement preventing bypass of checks
  - Beast naming conventions and repository pattern compliance

### Enhanced

#### ServiceNow API Client (Planned Integration)

- **Operational Capabilities:** Enhanced API client with resilience features
  - Integrated error handling, retry logic, and circuit breaker patterns
  - Performance metrics collection for all API operations
  - Enhanced error parsing for ServiceNow-specific responses
  - Operation timing and success/failure tracking

#### Testing & Quality

- **Comprehensive Test Coverage:** 125+ unit tests covering all operational components
  - Error handling scenarios and edge cases
  - Retry logic with simulated failures and rate limits
  - Circuit breaker state transitions and recovery patterns
  - Health monitoring and metrics collection validation
  - Configuration management and environment detection

- **Integration Testing:** End-to-end operational resilience testing
  - Simulated ServiceNow API failures and recovery
  - Network timeout and connection error handling
  - Rate limit simulation and backoff verification

### Technical Improvements

- **Performance:** Optimized metrics collection with minimal overhead
- **Memory Management:** Bounded queues and automatic cleanup for long-running processes
- **Thread Safety:** Thread-safe implementations for concurrent operations
- **Scalability:** Designed for horizontal scaling of monitoring components

### Known Limitations

1. **ServiceNow API Integration:** Enhanced API client integration pending
   - Current API client works but doesn't yet integrate operational features
   - Full integration planned for next release

2. **Graceful Degradation:** Partial implementation
   - Table fallback logic implemented
   - Full graceful degradation patterns pending

3. **Advanced Monitoring:** Basic implementation complete
   - Health check endpoints not yet exposed
   - Advanced alerting and notification systems pending

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

