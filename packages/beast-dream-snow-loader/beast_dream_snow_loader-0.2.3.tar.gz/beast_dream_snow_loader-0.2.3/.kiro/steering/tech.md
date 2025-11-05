# Technology Stack

## Core Technologies

### Language & Runtime
- **Python 3.10+** - Primary language
- **UV** - Package management (recommended) or pip

### Libraries & Frameworks
- **beast-unifi-integration** - UniFi API clients (dependency)
- **requests** - HTTP client for ServiceNow REST API
- **pydantic** / **dataclasses** - Data models for transformation
- **python-dotenv** - Environment variable management
- **1Password CLI** - Credential management

### ServiceNow Integration
- **ServiceNow REST API** - CMDB table creation and data loading
- **MID Server** - Secure, authenticated access (via beast-unifi-integration)
- **Table API** - Create/modify ServiceNow tables
- **Import Set API** - Batch data loading
- **CMDB API** - Configuration item management

### Development Tools
- **Black** - Code formatting (88 char line length)
- **Ruff** - Linting (E, W, F, I, B, C4, UP rules)
- **MyPy** - Type checking (strict mode)
- **pytest** - Testing framework

## Architecture Patterns

### Package Structure
```
beast-dream-snow-loader/
├── src/
│   └── beast_dream_snow_loader/
│       ├── servicenow/           # ServiceNow integration
│       │   ├── tables.py          # Table creation/management
│       │   ├── loader.py          # Data loading
│       │   └── api_client.py     # REST API client
│       ├── transformers/          # Data transformation
│       │   ├── unifi_to_snow.py  # UniFi → ServiceNow mapping
│       │   └── schema_mapper.py # Schema mapping logic
│       └── models/                # Data models
│           ├── unifi.py          # UniFi data models
│           └── servicenow.py    # ServiceNow data models
```

### Data Flow

```
UniFi API (beast_unifi)
    ↓
Raw UniFi Data (hosts, sites, devices, clients)
    ↓
Transformation Layer (schema mapping)
    ↓
ServiceNow Data Model
    ↓
ServiceNow REST API
    ↓
ServiceNow CMDB Tables
```

### Transformation Pattern

1. **Read:** Fetch UniFi data using `beast_unifi` clients
2. **Transform:** Map UniFi schema to ServiceNow schema
3. **Validate:** Ensure data meets ServiceNow requirements
4. **Create Tables:** Define ServiceNow tables if needed
5. **Load:** Insert/update records in ServiceNow CMDB

### ServiceNow Integration Pattern

- **Authentication:** Via MID server (credentials from 1Password)
- **Table Creation:** Use ServiceNow Table API
- **Data Loading:** Use Import Set API or direct REST API
- **Error Handling:** Retry logic, validation, rollback
- **Logging:** Structured logging with enum serialization support
- **Operational Resilience:** Circuit breakers, retry policies, health checks, metrics collection

## Quality Standards

- **Type Safety:** All functions typed, MyPy strict mode, include type stubs (`types-requests`, `types-psutil`)
- **Code Style:** Black formatting, Ruff linting (use `[tool.ruff.lint]` configuration)
- **Testing:** pytest with unit and integration tests, verify test expectations match implementation
- **Documentation:** Docstrings for all public APIs
- **OSS:** MIT License, PyPI publishing, SonarCloud quality
- **CI/CD:** Use `SonarSource/sonarcloud-github-action@master`, proper coverage configuration, systematic issue resolution
- **Immutability:** NEVER delete/modify artifacts (tags, commits, configs) without understanding origin, dependencies, and having explicit authorization - see `.kiro/steering/immutability-principle.md`

