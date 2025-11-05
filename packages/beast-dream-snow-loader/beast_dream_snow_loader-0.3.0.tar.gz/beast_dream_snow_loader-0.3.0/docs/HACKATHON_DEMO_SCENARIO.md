# Hackathon/Demo Scenario: Temporary ServiceNow PDI

## Use Case

**Scenario:** Public-facing demo/showcase for hackathons or Observatory projects
- **Observatory**: Public demo environment at `observatory.nkllon.com`
- **Hackathon**: Temporary demo instance for hackathon duration
- **Lab**: nkllon lab infrastructure with Cloudflare endpoints

**Requirements:**
- Fresh ServiceNow PDI booted on-demand
- Template-based deployment (push button)
- Publicly accessible via Cloudflare endpoint
- Secure for public access during hackathon
- Temporary (bootstrap for hackathon, tear down after)

## Why This Makes Sense

### ServiceNow PDIs are Perfect for This

1. **Free for Development**: PDIs are free, no cost concerns
2. **Quick Setup**: Can be booted in minutes
3. **Fresh Instance**: Clean slate for each demo/hackathon
4. **No Production Risk**: Completely isolated from production
5. **Full Features**: Can activate plugins (CMDB CI Class Models, etc.) for demo

### Observatory Pattern

The Observatory is a public-facing showcase environment:
- **Purpose**: Demonstrate beast projects to the community
- **Access**: Public via `observatory.nkllon.com` (Cloudflare)
- **Security**: Public access but secure (API keys, rate limiting)
- **Infrastructure**: Temporary, on-demand, ephemeral

### Hackathon Scenario

Perfect for hackathon demos:
1. **Day 1**: Push button → Fresh PDI boots → Configure → Demo ready
2. **During Hackathon**: Public API endpoint via Cloudflare → Hackathon participants can use it
3. **Post Hackathon**: Tear down → No lingering costs

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Observatory / Hackathon                                 │
│  observatory.nkllon.com (Cloudflare)                     │
└──────────────┬────────────────────────────────────────────┘
               │
               │ Public API (with API keys)
               ▼
┌─────────────────────────────────────────────────────────┐
│  Cloudflare Workers / API Gateway                        │
│  - Rate limiting (public access protection)              │
│  - API key authentication                               │
│  - Request routing                                       │
└──────────────┬────────────────────────────────────────────┘
               │
               │ Secure credentials (managed)
               ▼
┌─────────────────────────────────────────────────────────┐
│  ServiceNow PDI (Temporary)                              │
│  - Fresh instance (booted on-demand)                     │
│  - CMDB CI Class Models plugin activated                 │
│  - Public API access (via gateway)                       │
│  - Demo data loaded                                      │
└─────────────────────────────────────────────────────────┘
```

## Implementation

### 1. PDI Template/Provisioning

**ServiceNow PDI Provisioning:**
- Create PDI via ServiceNow Developer Portal API (if available)
- Or manual: "Create Instance" button → Configure template
- Template includes:
  - CMDB CI Class Models plugin activated
  - REST API enabled
  - Demo user with `rest_api_explorer` role
  - Pre-configured with demo data (optional)

**Automation Options:**
- ServiceNow API for instance creation (if available)
- Terraform/Pulumi for infrastructure as code
- Manual template + runbook for quick setup

### 2. Cloudflare Gateway (Public Access)

**Why Cloudflare Workers/Gateway:**
- **Security**: Public endpoint needs protection (API keys, rate limiting)
- **Access Control**: Don't expose ServiceNow credentials publicly
- **Rate Limiting**: Protect ServiceNow from abuse (public access)
- **Monitoring**: Track usage for hackathon

**Configuration:**
- API key authentication (per hackathon participant)
- Rate limiting (e.g., 100 req/hour per API key)
- Request proxying to ServiceNow PDI
- Logging and monitoring

### 3. Security Considerations

**Public Access Security:**
1. **API Keys**: Each hackathon participant gets API key (not ServiceNow credentials)
2. **Rate Limiting**: Cloudflare rate limits (before ServiceNow)
3. **IP Restrictions**: Optional IP allowlist for hackathon
4. **Time-Limited**: API keys expire after hackathon
5. **Monitoring**: Track all API calls for abuse detection

**ServiceNow PDI Security:**
- Service account with API key (not password)
- Read-only or limited write permissions (CMDB only)
- No admin access via API
- Audit logging enabled

### 4. Observatory Integration

**Observatory Pattern:**
- Public showcase at `observatory.nkllon.com`
- Demonstrates beast projects to community
- Temporary infrastructure for demos
- Secure public access

**Integration Points:**
- Observatory website links to demo ServiceNow instance
- API documentation for hackathon participants
- Example code/scripts for using the API
- Live demo data in ServiceNow

## Workflow

### Hackathon Setup (Day 1)

1. **Provision PDI**:
   ```bash
   # Push button → Fresh PDI boots
   # Or automation:
   curl -X POST "https://developer.servicenow.com/api/pdi/create" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"template": "cmdb-demo"}'
   ```

2. **Configure PDI**:
   - Activate CMDB CI Class Models plugin
   - Create service account with API key
   - Load demo data (UniFi → ServiceNow)
   - Configure REST API access

3. **Deploy Cloudflare Gateway**:
   - Deploy Workers script for API proxying
   - Configure API key authentication
   - Set rate limits
   - Point to PDI instance

4. **Generate API Keys**:
   - Create API keys for hackathon participants
   - Distribute via hackathon registration

### Hackathon Duration

- Participants use API keys to access ServiceNow via Cloudflare gateway
- ServiceNow PDI serves demo data
- Cloudflare provides rate limiting and security
- Monitoring tracks usage

### Hackathon Cleanup

- Revoke all API keys
- Tear down Cloudflare gateway
- Deactivate/delete PDI (or leave for post-hackathon review)
- Archive demo data if needed

## Where This Fits in nkllon Lab

### Observatory Infrastructure

**observatory.nkllon.com:**
- Public-facing showcase environment
- Cloudflare-managed endpoint
- Temporary infrastructure for demos
- Secure public access

**nkllon Lab:**
- Lab infrastructure for beast projects
- Cloudflare endpoints for public access
- Temporary/on-demand resources
- Hackathon/demo support

### Integration with beast-dream-snow-loader

**For Hackathons:**
1. Provision fresh PDI
2. Load demo UniFi data into ServiceNow
3. Expose via Cloudflare gateway at `observatory.nkllon.com`
4. Provide API keys to participants
5. Demonstrate beast-dream-snow-loader integration

**For Observatory:**
1. Live demo of UniFi → ServiceNow integration
2. Public API endpoint for community to try
3. Showcase transformation and loading capabilities
4. Documentation and examples

## Benefits

1. **Quick Setup**: Push button → Demo ready in minutes
2. **No Cost**: PDIs are free, only Cloudflare costs
3. **Fresh Instance**: Clean slate for each demo
4. **Secure**: API gateway protects ServiceNow from abuse
5. **Public Access**: Community can try the integration
6. **Temporary**: Tear down after hackathon, no lingering infrastructure

## Comparison to Production

### Production (Direct Integration)
- Client manages their own ServiceNow instance
- Client manages their own credentials
- Direct ServiceNow access
- Long-term infrastructure

### Hackathon/Demo (Gateway Pattern)
- Temporary ServiceNow PDI
- Public access via Cloudflare gateway
- API keys for participants (not ServiceNow credentials)
- Ephemeral infrastructure

## Next Steps

1. **PDI Provisioning Automation**: Script/API for booting PDIs
2. **Cloudflare Gateway**: Deploy Workers script for API proxying
3. **Template Configuration**: Pre-configured PDI template with plugins
4. **API Key Management**: Generate/revoke keys for participants
5. **Documentation**: Hackathon participant guide

## Conclusion

This is a **legitimate use case for API Gateway**:
- **Public access** requires security layer (not compensating ServiceNow weakness)
- **Multi-tenant** (hackathon participants) need quota allocation
- **Temporary infrastructure** needs easy provisioning/teardown
- **Observatory pattern** supports public-facing demos

The gateway here is for **public access security** and **multi-tenant quota**, not compensating for ServiceNow limitations.

