# Observatory Gateway Experiment

## Purpose

Even without a hackathon, setting up the Observatory gateway pattern provides valuable learning and benchmarking opportunities:

1. **Shared Development Endpoint**: Multiple developers/LLMs can work on same ServiceNow instance
2. **Performance Data**: Benchmark ServiceNow API performance through gateway vs direct
3. **Rate Limiting**: Test ServiceNow's built-in rate limiting vs gateway rate limiting
4. **Monitoring**: Collect metrics on API usage, latency, error rates
5. **Observatory Infrastructure**: Build out observatory.nkllon.com infrastructure
6. **Lab Experimentation**: Test Cloudflare Workers integration with ServiceNow

## Shared Development Use Case

**Problem:** Multiple developers/LLMs working on integration, but each needs ServiceNow access
- Each developer would need their own PDI (or share credentials - not ideal)
- Multiple LLMs working on same problem need shared state
- Tracking who did what is difficult with shared credentials

**Solution:** Observatory gateway with per-developer API keys
- Single PDI instance (shared development environment)
- Each developer/LLM gets their own API key
- Gateway tracks usage per API key (who did what)
- All working on same ServiceNow instance, but isolated via API keys

**Benefits:**
- **Shared State**: All developers/LLMs see same data
- **Isolation**: Each API key tracks separate usage
- **Monitoring**: See which developer/LLM made which changes
- **No Credential Sharing**: Each gets their own API key
- **Easy Onboarding**: New developer? Generate API key, done

**PDI User Limits:**
- PDIs support multiple named users (can create additional users)
- Each user can have their own API key
- All users can access the same PDI instance
- No hard limit on number of users (within reason)

## What We Can Learn

### Performance Benchmarking

**Questions to Answer:**
- What's the latency overhead of going through Cloudflare gateway?
- How does ServiceNow's rate limiting behave under load?
- What's the actual throughput we can achieve?
- How does gateway caching affect performance?

**Metrics to Collect:**
- Request latency (gateway → ServiceNow → response)
- Throughput (requests per second)
- Error rates (429s, timeouts, etc.)
- Rate limit behavior (when do we hit limits?)

### ServiceNow Rate Limiting Behavior

**What to Test:**
- Default rate limits (if any)
- Custom rate limit rules
- HTTP 429 responses with Retry-After headers
- Behavior under sustained load
- Recovery after rate limit

**Gateway vs Direct:**
- Compare gateway rate limiting to ServiceNow's built-in
- Test if gateway adds value or just overhead
- Understand when gateway rate limiting makes sense

### Observatory Infrastructure

**Build Out:**
- Cloudflare Workers deployment for API gateway
- API key management system
- Monitoring and logging
- observatory.nkllon.com endpoint configuration

**Benefits:**
- Reusable infrastructure for future demos
- Public-facing API endpoint for community
- Testing ground for new features

## Experimental Setup

### Phase 1: Basic Gateway (Minimal)

**Goal:** Get basic gateway working, measure overhead

**Steps:**
1. Deploy simple Cloudflare Worker that proxies to ServiceNow
2. Add API key authentication
3. Measure latency overhead (gateway vs direct)
4. Document baseline performance

**Time Estimate:** 2-4 hours

### Phase 2: Rate Limiting & Monitoring

**Goal:** Add rate limiting and collect metrics

**Steps:**
1. Implement rate limiting in gateway
2. Add logging/metrics collection
3. Test rate limit behavior
4. Compare to ServiceNow's built-in limits

**Time Estimate:** 4-6 hours

### Phase 3: Observatory Integration

**Goal:** Integrate with Observatory infrastructure

**Steps:**
1. Configure observatory.nkllon.com endpoint
2. Set up API key management
3. Create public documentation
4. Load demo data into ServiceNow

**Time Estimate:** 4-6 hours

## What We Get

### Data & Insights

1. **Performance Metrics:**
   - Gateway latency overhead
   - ServiceNow API performance
   - Rate limiting behavior
   - Throughput capabilities

2. **Architecture Learnings:**
   - When gateway adds value vs overhead
   - Best practices for public API access
   - Multi-tenant quota allocation patterns

3. **Observatory Infrastructure:**
   - Reusable gateway pattern
   - Public API endpoint
   - Monitoring/logging setup
   - Documentation for community

### Benchmarking Results

**Questions We Can Answer:**
- How much latency does gateway add? (probably <50ms)
- What's our actual throughput? (probably 50-100 req/sec)
- When do we hit ServiceNow rate limits? (need to test)
- Does gateway caching help? (probably not for CMDB writes)

**Data to Collect:**
- Request/response times
- Error rates
- Rate limit hits
- Throughput at different load levels

## Implementation

### Cloudflare Worker (Simple Proxy)

```javascript
// Basic proxy worker
export default {
  async fetch(request, env) {
    // Validate API key
    const apiKey = request.headers.get('X-API-Key');
    if (!apiKey || !isValidApiKey(apiKey, env)) {
      return new Response('Unauthorized', { status: 401 });
    }

    // Get ServiceNow credentials from env
    const snInstance = env.SERVICENOW_INSTANCE;
    const snUsername = env.SERVICENOW_USERNAME;
    const snApiKey = env.SERVICENOW_API_KEY;

    // Proxy request to ServiceNow
    const url = new URL(request.url);
    const targetUrl = `https://${snInstance}/api/now${url.pathname}${url.search}`;
    
    const response = await fetch(targetUrl, {
      method: request.method,
      headers: {
        'Authorization': `Basic ${btoa(`${snUsername}:${snApiKey}`)}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: request.body,
    });

    // Log request (for benchmarking)
    await logRequest(apiKey, request.method, url.pathname, response.status, env);

    return response;
  }
}
```

### Rate Limiting (KV Storage)

```javascript
// Rate limiting with KV
async function checkRateLimit(apiKey, env) {
  const key = `rate_limit:${apiKey}`;
  const record = await env.RATE_LIMITS.get(key);
  
  if (record) {
    const { count, resetTime } = JSON.parse(record);
    if (Date.now() < resetTime) {
      if (count >= 100) { // 100 req/hour
        return { allowed: false, resetTime };
      }
      await env.RATE_LIMITS.put(key, JSON.stringify({
        count: count + 1,
        resetTime
      }));
    } else {
      // Reset
      await env.RATE_LIMITS.put(key, JSON.stringify({
        count: 1,
        resetTime: Date.now() + 3600000 // 1 hour
      }));
    }
  } else {
    await env.RATE_LIMITS.put(key, JSON.stringify({
      count: 1,
      resetTime: Date.now() + 3600000
    }));
  }
  
  return { allowed: true };
}
```

## Backlog Item

**Title:** Observatory Gateway Experiment

**Goals:**
1. Deploy Cloudflare Worker gateway for ServiceNow API
2. Benchmark performance (gateway vs direct)
3. Test rate limiting behavior
4. Collect metrics and insights
5. Build Observatory infrastructure

**Value:**
- Performance data for documentation
- Understanding of rate limiting behavior
- Reusable Observatory infrastructure
- Learning/experimentation

**Not Blocking:**
- Can proceed with direct integration for MVP
- Gateway is experimental/enhancement
- Useful for lab/benchmarking even if not needed for production

**When to Do:**
- After MVP is complete
- When we have time for experimentation
- Before hackathon if planning one
- When we want to benchmark ServiceNow performance

## Next Steps

1. **Create Cloudflare Worker** (simple proxy)
2. **Deploy to observatory.nkllon.com**
3. **Run baseline benchmarks** (direct vs gateway)
4. **Add rate limiting** and test behavior
5. **Document findings** for future reference

This is valuable experimentation even if we don't need it for the MVP!

