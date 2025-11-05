# Shared Development Endpoint via Observatory Gateway

## Why Turn It On Now?

**Use Case:** Multiple developers/LLMs working on the same ServiceNow integration

**Benefits:**
1. **Shared State**: All developers/LLMs work on same ServiceNow instance
2. **No Credential Sharing**: Each gets their own API key
3. **Usage Tracking**: See who made which changes (per API key)
4. **Easy Onboarding**: New developer? Generate API key, done
5. **Isolation**: Each API key tracked separately, but same data

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Developer 1 (LLM/Person)                                │
│  API Key: dev-1-abc123                                   │
└──────────────┬────────────────────────────────────────────┘
               │
┌──────────────▼────────────────────────────────────────────┐
│  Developer 2 (LLM/Person)                                  │
│  API Key: dev-2-xyz789                                   │
└──────────────┬────────────────────────────────────────────┘
            │
┌───────────▼───────────────────────────────────────────────┐
│  Developer 3 (LLM/Person)                                  │
│  API Key: dev-3-def456                                   │
└──────────────┬────────────────────────────────────────────┘
               │
               │ All use same endpoint
               ▼
┌─────────────────────────────────────────────────────────┐
│  Observatory Gateway (observatory.nkllon.com)            │
│  - API key authentication                               │
│  - Rate limiting per API key                            │
│  - Usage tracking per API key                           │
│  - Request logging                                       │
└──────────────┬────────────────────────────────────────────┘
               │
               │ Single ServiceNow instance
               ▼
┌─────────────────────────────────────────────────────────┐
│  ServiceNow PDI (Shared Development Instance)           │
│  - Multiple named users (dev-1, dev-2, dev-3)           │
│  - Each user has API key                                 │
│  - All users see same data                               │
│  - Shared state for all developers                       │
└─────────────────────────────────────────────────────────┘
```

## PDI User Configuration

### Creating Multiple Users in PDI

**ServiceNow PDI supports multiple named users:**

1. **Create Additional Users:**
   - Go to User Administration → Users
   - Create new user for each developer/LLM
   - Assign appropriate roles (`rest_api_explorer`, etc.)

2. **Generate API Keys:**
   - Each user can have their own API key
   - Go to User → Security → API Keys
   - Generate key for each user

3. **Configure Gateway:**
   - Map API key → ServiceNow user credentials
   - Gateway authenticates with user's API key
   - All requests use same PDI instance

### User Limits

**PDI Limitations:**
- No hard limit on number of users (within reason)
- Each user can log in (UI access)
- Each user can have API key (API access)
- All users share same PDI instance and data

**Practical Limits:**
- 5-10 developers: No problem
- 10-20 developers: Should be fine
- 20+ developers: May need to consider instance limits

## Implementation

### Gateway API Key Management

**Store API Key → ServiceNow User Mapping:**

```javascript
// Cloudflare KV or Workers KV
const API_KEY_MAP = {
  'dev-1-abc123': {
    servicenow_user: 'dev1',
    servicenow_api_key: 'key-for-dev1',
  },
  'dev-2-xyz789': {
    servicenow_user: 'dev2',
    servicenow_api_key: 'key-for-dev2',
  },
  // ...
};
```

**Gateway Authentication:**

```javascript
async function authenticateRequest(request, env) {
  const apiKey = request.headers.get('X-API-Key');
  if (!apiKey) {
    return { error: 'Missing API key', status: 401 };
  }
  
  const userConfig = await env.API_KEYS.get(apiKey);
  if (!userConfig) {
    return { error: 'Invalid API key', status: 401 };
  }
  
  const { servicenow_user, servicenow_api_key } = JSON.parse(userConfig);
  return { servicenow_user, servicenow_api_key };
}
```

### Usage Tracking

**Track requests per API key:**

```javascript
async function trackUsage(apiKey, request, response, env) {
  const usage = {
    api_key: apiKey,
    method: request.method,
    path: new URL(request.url).pathname,
    status: response.status,
    timestamp: Date.now(),
  };
  
  // Log to KV or analytics
  await env.USAGE_LOGS.put(`usage:${Date.now()}:${apiKey}`, JSON.stringify(usage));
}
```

## Benefits for Multi-Developer/LLM Work

### Shared State

**All developers see same data:**
- Developer 1 creates a gateway CI
- Developer 2 sees it immediately
- Developer 3 can query it
- All working on same ServiceNow instance

### Isolation & Tracking

**Each API key tracked separately:**
- See which developer made which changes
- Track usage per developer
- Debug issues by API key
- Rate limit per developer

### Easy Onboarding

**New developer:**
1. Create ServiceNow user in PDI (or use existing)
2. Generate API key for user
3. Add API key to gateway configuration
4. Developer gets API key, can start immediately

### Multi-LLM Collaboration

**Multiple LLMs working on same problem:**
- Each LLM gets its own API key
- All LLMs see same ServiceNow state
- Can coordinate work (LLM 1 creates, LLM 2 reads, etc.)
- Track which LLM made which changes

## Why Turn It On Now?

**Immediate Benefits:**
1. **Shared Development**: Multiple people/LLMs can work simultaneously
2. **No Setup Per Developer**: Gateway handles authentication
3. **Usage Visibility**: See who's doing what
4. **Observatory Infrastructure**: Build it now, use it later

**Low Effort, High Value:**
- Simple gateway (basic proxy)
- Reusable for hackathon later
- Valuable for current development
- Learning/experimentation opportunity

**Can Start Simple:**
- Phase 1: Basic proxy + API keys (2-4 hours)
- Add rate limiting/monitoring later
- Iterate based on needs

## Setup Steps

1. **Create PDI Users** (if needed):
   - Create user for each developer/LLM
   - Generate API key for each user

2. **Deploy Gateway**:
   - Simple Cloudflare Worker
   - API key → ServiceNow user mapping
   - Basic proxy functionality

3. **Configure API Keys**:
   - Store API key mappings in KV
   - Generate keys for developers
   - Distribute keys

4. **Test**:
   - Verify each API key works
   - Test shared state (create with one, read with another)
   - Monitor usage

## Conclusion

**Why not turn it on?**
- Low effort to get basic version working
- Immediate value for multi-developer work
- Reusable for hackathon/observatory later
- Learning and experimentation opportunity
- Shared development endpoint beats individual PDIs

**Start Simple:**
- Basic gateway (proxy + API keys)
- Add features as needed
- Iterate based on usage

**Especially Valuable When:**
- Multiple developers working on same thing
- Short timelines ("get it done now")
- Global team (time zones, coordination)
- Lab manager managing cross-cutting concerns
- Need to move fast but securely

**See:** [LAB_MANAGEMENT_USE_CASE.md](LAB_MANAGEMENT_USE_CASE.md) for operational benefits

This is a good use case for turning it on now!

