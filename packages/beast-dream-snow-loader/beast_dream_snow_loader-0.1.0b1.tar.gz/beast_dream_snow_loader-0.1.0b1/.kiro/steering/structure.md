# Project Organization

## Directory Structure

```
beast-dream-snow-loader/
├── src/
│   └── beast_dream_snow_loader/
│       ├── servicenow/           # ServiceNow integration
│       │   ├── __init__.py
│       │   ├── api_client.py     # REST API client
│       │   ├── tables.py          # Table creation/management
│       │   └── loader.py          # Data loading logic
│       ├── transformers/          # Data transformation
│       │   ├── __init__.py
│       │   ├── unifi_to_snow.py  # Main transformation
│       │   └── schema_mapper.py  # Schema mapping
│       └── models/                # Data models
│           ├── __init__.py
│           ├── unifi.py          # UniFi data models
│           └── servicenow.py    # ServiceNow data models
│
├── notebooks/                     # Jupyter notebooks
│   └── servicenow_loader.ipynb   # Loader notebook (as mentioned)
│
├── tests/                         # Test suite
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
│
├── docs/                          # Documentation
│   ├── agents.md                  # Agent communication patterns
│   └── unifi_schema.sql          # Source data schema
│
├── examples/                      # Example usage
└── .kiro/                         # BeastSpec/Kiro specs
```

## Package Organization

### beast_dream_snow_loader
Core library for ServiceNow data loading:
- `servicenow/` - ServiceNow REST API integration, table creation, data loading
- `transformers/` - Data transformation from UniFi to ServiceNow schema
- `models/` - Data models for both UniFi and ServiceNow formats

## Naming Conventions

- **Package:** `beast_dream_snow_loader` (snake_case)
- **Modules:** Descriptive, lowercase (e.g., `unifi_to_snow.py`)
- **Classes:** PascalCase (e.g., `ServiceNowLoader`)
- **Functions:** snake_case (e.g., `load_devices()`)
- **Constants:** UPPER_SNAKE_CASE

## File Patterns

- **API Clients:** `servicenow/api_client.py`
- **Transformers:** `transformers/{source}_to_{target}.py`
- **Models:** `models/{source}.py`
- **Tests:** `tests/{type}/test_{module}.py`

## Dependencies

- **beast-unifi-integration** - UniFi API clients (external dependency)
- **requests** - ServiceNow REST API calls
- **pydantic** - Data validation and models

