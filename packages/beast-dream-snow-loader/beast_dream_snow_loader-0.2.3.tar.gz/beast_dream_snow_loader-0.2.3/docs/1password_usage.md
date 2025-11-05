# 1Password CLI Usage Guide

**Purpose:** Secure credential management for beast-dream-snow-loader using 1Password CLI.

**Vault:** "Beastmaster" (standard beast project vault)

**Reference:** [1Password CLI Documentation](https://developer.1password.com/docs/cli)

## Prerequisites

1. **1Password CLI installed** ✅
   ```bash
   op --version  # Should show version (e.g., 2.32.0)
   ```

2. **Signed in to 1Password account**
   ```bash
   op account list  # Should show your account
   ```

3. **Item created in "Beastmaster" vault** with ServiceNow credentials

## Basic Usage

### Sign In to 1Password CLI

```bash
# Sign in (first time or after session expires)
op signin

# Or sign in to specific account
op signin <account>
```

### List Items in Vault

```bash
# List all items in Beastmaster vault
op item list --vault "Beastmaster"

# List items matching pattern
op item list --vault "Beastmaster" --tags servicenow
```

### Read Item Fields

```bash
# Read entire item (JSON)
op item get "ServiceNow Dev Account" --vault "Beastmaster"

# Read specific field
op item get "ServiceNow Dev Account" --vault "Beastmaster" --fields label=username
op item get "ServiceNow Dev Account" --vault "Beastmaster" --fields label=password
op item get "ServiceNow Dev Account" --vault "Beastmaster" --fields label=api_key
```

### Read Password Field (Most Common)

```bash
# Read password field (most common)
op read "op://Beastmaster/ServiceNow Dev Account/password"

# Read username field
op read "op://Beastmaster/ServiceNow Dev Account/username"

# Read API key field
op read "op://Beastmaster/ServiceNow Dev Account/api_key"
```

## ServiceNow Credential Structure

Recommended item structure in "Beastmaster" vault:

**Item Name:** `ServiceNow Dev Account` (or similar)

**Fields:**
- `username` - Service account username
- `password` - Service account password (dev/testing only)
- `api_key` - Service account API key (production)
- `instance` - ServiceNow instance URL (e.g., `dev12345.service-now.com`)
- `oauth_token` - OAuth token (optional)

**Example Item Structure:**
```
ServiceNow Dev Account
├── username: service-account-username
├── api_key: abc123xyz... (recommended for production)
├── password: dev-password (dev/testing only)
├── instance: dev12345.service-now.com
└── oauth_token: optional-token (optional)
```

## Python Integration

### Using 1Password CLI in Python

```python
import subprocess
import os

def get_1password_credential(item_name: str, field: str, vault: str = "Beastmaster") -> str:
    """Get credential from 1Password CLI.
    
    Args:
        item_name: 1Password item name (e.g., "ServiceNow Dev Account")
        field: Field name (e.g., "username", "api_key", "password")
        vault: Vault name (default: "Beastmaster")
    
    Returns:
        Credential value as string
    
    Raises:
        subprocess.CalledProcessError: If 1Password CLI command fails
        FileNotFoundError: If 1Password CLI not installed
    """
    try:
        # Use op:// URL format
        op_url = f"op://{vault}/{item_name}/{field}"
        result = subprocess.run(
            ["op", "read", op_url],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to read 1Password credential: {e.stderr}")
    except FileNotFoundError:
        raise FileNotFoundError("1Password CLI not found. Install from https://developer.1password.com/docs/cli")

# Example usage
instance = get_1password_credential("ServiceNow Dev Account", "instance")
username = get_1password_credential("ServiceNow Dev Account", "username")
api_key = get_1password_credential("ServiceNow Dev Account", "api_key")
```

### Fallback Pattern

```python
def get_credential(item_name: str, field: str, env_var: str | None = None) -> str | None:
    """Get credential from 1Password CLI or environment variable.
    
    Priority:
    1. Environment variable (if provided)
    2. 1Password CLI (if available)
    3. None (if neither available)
    
    Args:
        item_name: 1Password item name
        field: Field name
        env_var: Environment variable name (optional)
    
    Returns:
        Credential value or None
    """
    # Try environment variable first
    if env_var:
        value = os.getenv(env_var)
        if value:
            return value
    
    # Try 1Password CLI
    try:
        return get_1password_credential(item_name, field)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
```

## Integration with ServiceNowAPIClient

The `ServiceNowAPIClient` should support 1Password CLI as a credential source:

```python
# Priority order:
# 1. Function arguments (highest priority)
# 2. Environment variables
# 3. 1Password CLI (if available)
```

**Implementation Status:** TODO (currently supports env vars and function args)

## Troubleshooting

### "1Password CLI not found"
- Install 1Password CLI: https://developer.1password.com/docs/cli
- Ensure `op` is in PATH: `which op`

### "Not signed in"
- Sign in: `op signin`
- Check account: `op account list`

### "Item not found"
- Verify item name: `op item list --vault "Beastmaster"`
- Check vault name: `op vault list`

### "Permission denied"
- Ensure item exists in "Beastmaster" vault
- Verify you have access to the vault

## Security Best Practices

1. **Never commit credentials** to git
2. **Use service account** with API key (not password) for production
3. **Use 1Password CLI** for credential storage (not env vars in production)
4. **Rotate credentials** regularly
5. **Use separate items** for dev/prod environments

## References

- [1Password CLI Documentation](https://developer.1password.com/docs/cli)
- [1Password CLI Reference](https://developer.1password.com/docs/cli/reference)
- [Beast Projects: Credential Management](docs/agents.md#credential-management)

