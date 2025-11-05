# Environment Variable Rules

**Purpose:** Guidelines for environment variable management in beast-dream-snow-loader.

## Critical Cluster-Wide Rule

**⚠️ NEVER CREATE `.env` FILES IN PROJECT DIRECTORIES**

**Cluster-wide policy:** All environment variables must be in the home directory of the executing user. No exceptions.

**For beast nodes/participants:** Environment variables can go nowhere else. This is a hard constraint.

**Enforcement:** Never create `.env` files (at least without asking). Violates cluster-wide policy.

## Principle: Execution Context Detection & Graceful Degradation

**The code does not assume execution context, but can detect available capabilities and use them if present.**

### Execution Contexts

**Beast Node/Cluster:**
- Has access to beast node services (1Password, etc.) or they are provisionable
- Being part of a cluster (even a beast cluster of 1) has qualities and capabilities
- Code can assume beast services are available or provisionable

**OSS User (Public-Facing Default):**
- No beast node services required
- Works with just system environment variables
- This is the **public-facing stance for this repo**
- Code gracefully degrades when beast services aren't available

### Implementation

The code:
- **Detects** available services (1Password CLI, etc.) and uses them if present
- **Gracefully degrades** when beast services aren't available (OSS user case)
- **Does not assume** execution context - it detects what's available
- **Defaults to OSS user** behavior (works without beast services)

**Key insight:** "All environment variables must be in the home directory of the executing user" - the code reads from `os.getenv()` which automatically uses the executing user's environment. The code detects available services and uses them if present, but works without them.

### Priority Order

1. **Function arguments** (highest priority)
2. **System environment variables** (`os.getenv()` - from system environment)
3. **1Password CLI** (if available and signed in)

**Note:** Code reads from system environment only. The user/system is responsible for making environment variables available in the system environment (via shell config, deployment system, etc.).

## When to Use Each

### Beast Node/Cluster
- **1Password CLI** (preferred) - beast services are available or provisionable
- Code detects available services and uses them if present
- Environment variables in executing user's home directory (cluster-wide policy)

### OSS User (Public-Facing Default)
- **System environment variables** - works without beast services
- Set via shell config, deployment system, CI/CD, etc.
- Code gracefully degrades when beast services aren't available
- This is the **public-facing stance for this repo**

### CI/CD
- CI/CD system sets environment variables in system environment
- Or secrets management (GitHub Secrets, etc.) - CI/CD system injects into environment
- Code reads from `os.getenv()` - does not care how they were set

## Security Best Practices

1. **Never create `.env` files** - Cluster-wide policy violation
2. **Use system environment variables** (from user's home directory)
3. **Use 1Password CLI** for production credentials
4. **Rotate credentials** regularly
5. **Use service accounts** with API keys (not passwords)
6. **Separate credentials** for dev/prod environments

## Configuration

**The user/system is responsible for making environment variables available.**

The code reads from `os.getenv()` (system environment variables only). The user/system must ensure environment variables are set in the system environment before running the code.

**Example (user responsibility):**
```bash
# User sets in shell (via ~/.bashrc, ~/.zshrc, deployment system, etc.)
export SERVICENOW_INSTANCE=dev12345.service-now.com
export SERVICENOW_USERNAME=service-account-username
export SERVICENOW_API_KEY=your-api-key-here
# SERVICENOW_OAUTH_TOKEN=optional-oauth-token
# SERVICENOW_PASSWORD=dev-password-only
```

**Code responsibility:** Only reads from `os.getenv()` - does not manage or load environment variables.

## References

- [Beast Projects: Credential Management](docs/agents.md#credential-management)
- Cluster-wide policy: All env vars in user's home directory

