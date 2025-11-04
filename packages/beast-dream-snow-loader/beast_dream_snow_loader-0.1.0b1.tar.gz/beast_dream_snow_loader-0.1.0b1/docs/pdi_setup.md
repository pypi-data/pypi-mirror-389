# Personal Developer Instance (PDI) Setup

**Purpose:** Guide for setting up ServiceNow PDI for REST API access.

## Enabling REST API Access

REST API should be enabled by default on PDIs, but the user may need proper roles.

### Step 1: Check User Roles

The `admin` user needs the `rest_api_explorer` role:

1. **Log into your PDI instance** (e.g., `https://dev212392.service-now.com`)
2. **Navigate to:** User Administration → Users
   - Or search for "Users" in the filter navigator
3. **Find the admin user** and click on it
4. **Check the "Roles" tab** - ensure it has:
   - `rest_api_explorer` - Required for REST API access
   - `admin` - Should already be present
   - `web_service_admin` - Optional but recommended

5. **If `rest_api_explorer` is missing:**
   - Click "Edit" on the user
   - Go to "Roles" tab
   - Click "Edit" on Roles
   - Search for "rest_api_explorer"
   - Add it to the user
   - Save

### Step 2: Verify REST API Explorer Works

1. **Navigate to:** REST API Explorer
   - Search for "REST API Explorer" in the filter navigator
   - Or go to: System Web Services → REST → REST API Explorer
2. **If you can access REST API Explorer**, REST API is enabled
3. **If you get an error**, you need the `rest_api_explorer` role (see Step 1)

### Step 3: Test REST API Access

Once `rest_api_explorer` role is added, test with:

```bash
curl -u "admin:PASSWORD" \
  -H "Accept: application/json" \
  "https://dev212392.service-now.com/api/now/table/sys_user?sysparm_limit=1"
```

Should return JSON data, not 401 error.

## Testing REST API Access

Once enabled, test with:

```bash
curl -u "admin:PASSWORD" \
  -H "Accept: application/json" \
  "https://dev212392.service-now.com/api/now/table/sys_user?sysparm_limit=1"
```

Should return JSON data, not 401 error.

## Common Issues

### 401 Unauthorized - "User is not authenticated"
- **Cause:** REST API not enabled or user lacks permissions
- **Fix:** Enable REST API plugin, grant roles, verify user permissions

### 403 Forbidden
- **Cause:** User lacks required roles
- **Fix:** Grant `rest_api_explorer` and `web_service_admin` roles

### Instance URL Issues
- **PDI Instance URL:** `dev{number}.service-now.com` (e.g., `dev212392.service-now.com`)
- **Not:** `developer.service-now.com` (that's the portal, not the instance)

## References

- [ServiceNow Developer Portal](https://developer.servicenow.com)
- [PDI Guide](https://developer.servicenow.com/dev.do#!/guides/zurich/developer-program/pdi-guide/understanding-pdis)

