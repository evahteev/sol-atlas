# Backend Bug Fix: CopilotKit Route Handler

## TL;DR for Backend Developer

**File**: `src/app/api/copilotkit/[integrationId]/route.ts`  
**Issue**: Route handler fails to parse `integrationId` when query parameters are present  
**Impact**: All CopilotKit requests return 404  
**Fix**: Use URL parser instead of string split  

---

## The Bug

### Current Code (Broken)
```typescript
export async function POST(request: NextRequest) {
  const integrationId = request.url.split("/").pop();  // ❌ BUG HERE
  
  const integration = agentsIntegrations.find((i) => i.id === integrationId);
  if (!integration) {
    return new Response("Integration not found", { status: 404 });
  }
  // ...
}
```

### What's Wrong
- Request URL: `/api/copilotkit/bot-api?locale=en`
- Extracted value: `"bot-api?locale=en"` ← includes query params
- Expected value: `"bot-api"`
- Result: 404 because `"bot-api?locale=en" !== "bot-api"`

---

## The Fix

### Option 1: URL Parser (Recommended)
```typescript
export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const integrationId = url.pathname.split("/").pop();
  
  const integration = agentsIntegrations.find((i) => i.id === integrationId);
  if (!integration) {
    return new Response("Integration not found", { status: 404 });
  }
  const agents = await integration.agents({ request });
  const runtime = new CopilotRuntime({
    // @ts-ignore for now
    agents,
  });
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: `/api/copilotkit/${integrationId}`,
  });

  return handleRequest(request);
}
```

### Option 2: Next.js Context Params (Cleaner)
```typescript
export async function POST(
  request: NextRequest,
  context: { params: Promise<{ integrationId: string }> }
) {
  const { integrationId } = await context.params;  // Next.js handles URL parsing
  
  const integration = agentsIntegrations.find((i) => i.id === integrationId);
  if (!integration) {
    return new Response("Integration not found", { status: 404 });
  }
  const agents = await integration.agents({ request });
  const runtime = new CopilotRuntime({
    // @ts-ignore for now
    agents,
  });
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: `/api/copilotkit/${integrationId}`,
  });

  return handleRequest(request);
}
```

---

## Testing

### Manual Testing
```bash
# 1. Apply the fix
# 2. Restart dev server
pnpm run dev

# 3. Check browser console - should see no 404s
# 4. Verify CopilotKit connection works
```

### Integration Testing
```typescript
// Test case to add:
describe('CopilotKit route handler', () => {
  it('should extract integrationId from URL with query params', () => {
    const url = '/api/copilotkit/bot-api?locale=en';
    const parsed = new URL(url, 'http://localhost');
    const integrationId = parsed.pathname.split('/').pop();
    expect(integrationId).toBe('bot-api');
  });
});
```

---

## Why This Happened

The original implementation used naive string manipulation:
```typescript
request.url.split("/").pop()  // Gets last segment INCLUDING query string
```

Next.js App Router doesn't automatically parse dynamic route params in the same way as Pages Router, so we need to either:
1. Use the `context.params` object (cleaner, Next.js recommended)
2. Parse the URL properly with `new URL()` (more explicit)

---

## Deployment Checklist

- [ ] Apply fix to `src/app/api/copilotkit/[integrationId]/route.ts`
- [ ] Run `pnpm run lint` (ensure no linting errors)
- [ ] Test locally with query parameters
- [ ] Verify backend service is running on port 8000 (or `BOT_API_URL`)
- [ ] Check production build: `pnpm run build`
- [ ] Update tests if integration tests exist

---

## Related Configuration

### Environment Variables
```bash
BOT_API_URL=http://localhost:8000  # Backend service URL
```

### Registered Integrations
See `src/agents.ts`:
```typescript
export const agentsIntegrations: AgentIntegrationConfig[] = [
  {
    id: "bot-api",  // Must match exactly (without query params)
    agents: async ({ request }) => { /* ... */ }
  }
];
```

---

## Questions?

- **Why not use string manipulation?** - Query parameters, fragments, and trailing slashes break it
- **Why Option 2 is better?** - Next.js handles edge cases (trailing slashes, encoding, etc.)
- **Will this break other integrations?** - No, fix applies to all integrations uniformly

**Recommendation**: Use Option 2 (context params) for consistency with Next.js App Router patterns.

