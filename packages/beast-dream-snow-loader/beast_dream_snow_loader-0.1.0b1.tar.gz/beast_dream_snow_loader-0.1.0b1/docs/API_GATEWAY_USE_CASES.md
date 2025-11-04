# API Gateway Use Cases (Cloudflare Workers)

## When Would You Need an API Gateway?

### 1. Managed Service Provider (MSP) Scenario

**Problem:** MSP managing multiple client ServiceNow instances
- Each client has their own ServiceNow instance
- Need to manage credentials for many instances
- Want single entry point for all clients
- Need to track usage per client

**Solution:** API Gateway with multi-tenancy
```
Client A → API Gateway → ServiceNow Instance A
Client B → API Gateway → ServiceNow Instance B
Client C → API Gateway → ServiceNow Instance C
```

**Benefits:**
- Single API endpoint for all clients
- Centralized authentication/authorization
- Usage tracking and billing per client
- Rate limiting per client
- Credential management in one place

### 2. Security & Credential Hiding

**Problem:** Don't want to expose ServiceNow credentials to end users
- End users shouldn't have ServiceNow credentials
- Need to rotate credentials without client changes
- Want audit trail of who accessed what

**Solution:** API Gateway as credential proxy
```
User → API Gateway (with API key) → ServiceNow (with real credentials)
```

**Benefits:**
- Users only get API Gateway keys (not ServiceNow credentials)
- Can rotate ServiceNow credentials without user impact
- Centralized logging and audit trail
- Can revoke access instantly

### 3. Rate Limiting & Throttling

**Note:** ServiceNow has built-in rate limiting and API protection. Using an API gateway for rate limiting is only needed for:
- **Multi-tenant scenarios** where you want to allocate ServiceNow's quota across multiple clients
- **Additional layers** of protection beyond ServiceNow's built-in limits
- **Pre-emptive queuing** before requests hit ServiceNow

**ServiceNow's Built-in Protection:**
- Rate limiting per user/role (configurable)
- API throttling and quota management
- OAuth token-based authentication
- API key authentication with audit trails
- IP restrictions and access controls

**When You'd Still Need Gateway Rate Limiting:**
- MSP allocating ServiceNow quota across clients (fair distribution)
- Want to queue requests before they hit ServiceNow
- Need to implement different rate limits than ServiceNow provides
- Want to track usage separately from ServiceNow's audit logs

**Reality Check:** If ServiceNow's rate limiting is insufficient, that's a ServiceNow problem, not something you should paper over with a gateway. The gateway rate limiting is mainly for multi-tenant quota allocation, not compensating for ServiceNow weaknesses.

### 4. Multi-Instance Aggregation

**Problem:** Data spread across multiple ServiceNow instances
- Company has multiple ServiceNow instances (dev/staging/prod)
- Different regions/departments have separate instances
- Need unified view

**Solution:** API Gateway aggregates results
```
Query → API Gateway → [Instance A, Instance B, Instance C] → Aggregated Results
```

### 5. Transformation & Normalization

**Problem:** Different ServiceNow instances have different schemas
- Custom fields vary by instance
- Need to normalize data before sending to clients
- Want to abstract ServiceNow specifics

**Solution:** API Gateway transforms responses
- Normalize field names
- Map custom fields to standard schema
- Hide ServiceNow-specific details

### 6. Caching & Performance

**Problem:** ServiceNow API can be slow, want to cache responses
- CMDB queries are expensive
- Same data requested multiple times
- Want to reduce ServiceNow load

**Solution:** API Gateway with caching
- Cache frequently accessed data
- Invalidate on updates
- Reduce load on ServiceNow

## When You DON'T Need an API Gateway

### Direct Integration (Current Approach)

**Good for:**
- Single ServiceNow instance
- Direct client-to-ServiceNow access
- Simple deployments
- No multi-tenancy needs
- Client has ServiceNow credentials

**Why it's simpler:**
- No extra infrastructure
- Lower latency (direct connection)
- Fewer moving parts
- Client manages their own credentials
- **ServiceNow's built-in security is sufficient** (API keys, OAuth, rate limiting, audit logs)

**ServiceNow Already Provides:**
- ✅ Rate limiting and throttling
- ✅ API key authentication with service accounts
- ✅ OAuth 2.0 token support
- ✅ Role-based access control
- ✅ Audit logging
- ✅ IP restrictions

**Don't add a gateway to compensate for ServiceNow weaknesses** - use ServiceNow's built-in features properly first.

## Real-World Example: MSP Scenario

**Architecture:**
```
┌─────────────┐
│  MSP Client │
│  (UniFi)    │
└──────┬──────┘
       │ API Key (beast-client-123)
       ▼
┌─────────────────────────────────┐
│  Cloudflare Workers API Gateway │
│  - Auth: Validate API key       │
│  - Route: Find client's SN      │
│  - Proxy: Forward to ServiceNow │
│  - Log: Track usage             │
└──────┬──────────────────────────┘
       │ ServiceNow Credentials (managed by MSP)
       ▼
┌─────────────────────────────────┐
│  Client's ServiceNow Instance    │
│  (dev12345.service-now.com)       │
└─────────────────────────────────┘
```

**MSP Benefits:**
1. **One API Key Per Client**: Easy to revoke/manage
2. **Credential Rotation**: Change ServiceNow password without client impact
3. **Usage Tracking**: See which clients use what
4. **Billing**: Track API calls per client
5. **Multi-Instance**: Each client's data goes to their instance

## Implementation Considerations

### If Building API Gateway:

1. **Authentication**: API key per client (not ServiceNow credentials)
2. **Routing**: Map client → ServiceNow instance
3. **Credential Management**: Store ServiceNow credentials securely (1Password, etc.)
4. **Rate Limiting**: Per-client limits
5. **Logging**: Track all API calls
6. **Error Handling**: Translate ServiceNow errors to client-friendly format

### Technology Options:

- **Cloudflare Workers**: Edge computing, fast, global
- **AWS API Gateway**: Full-featured, more complex
- **Kong**: Self-hosted, more control
- **Simple Python FastAPI**: Quick to build, easy to maintain

## Recommendation

**Build API Gateway IF:**
- You're an MSP managing multiple clients
- You need to hide ServiceNow credentials
- You need multi-tenancy
- You need usage tracking/billing

**Skip API Gateway IF:**
- Single ServiceNow instance
- Direct client access is fine
- Simple deployment
- Client manages their own credentials

**Current Project Status:**
The current implementation (direct ServiceNow access) is perfect for:
- End users loading their own UniFi data into their own ServiceNow
- OSS users who want simple integration
- Direct client-to-ServiceNow access

An API Gateway would be a separate service/product for MSP scenarios.

