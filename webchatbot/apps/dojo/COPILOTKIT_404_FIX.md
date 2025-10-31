# CopilotKit API 404 Error - Diagnostic Report

## Issue Summary

**Error**: `Failed to load resource: the server responded with a status of 404 (Not Found)` when accessing `/api/copilotkit/bot-api?locale=en`

**Root Cause**: Backend route parsing bug

**Severity**: High - Blocks all CopilotKit functionality

---

## Analysis

### Problem Location

File: `apps/dojo/src/app/api/copilotkit/[integrationId]/route.ts`

The issue occurs in the POST handler:

```typescript
export async function POST(request: NextRequest) {
  const integrationId = request.url.split("/").pop();
  
  const integration = agentsIntegrations.find((i) => i.id === integrationId);
  if (!integration) {
    return new Response("Integration not found", { status: 404 });
  }
  // ...
}
```

### Why It Fails

1. Frontend calls: `/api/copilotkit/bot-api?locale=en`
2. The route handler extracts: `integrationId = "bot-api?locale=en"` (includes query params)
3. Registered integration ID is: `"bot-api"` (exact match required)
4. String comparison fails: `"bot-api?locale=en" !== "bot-api"`
5. Result: 404 response

### Expected Behavior

The `integrationId` should be `"bot-api"` without query parameters.

---

## Solution

### Fix #1: Using URL Parser (Recommended)

```typescript
export async function POST(request: NextRequest) {
  // Extract integrationId from URL path, ignoring query parameters
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

### Fix #2: Using Next.js Context Params (Alternative)

```typescript
export async function POST(
  request: NextRequest,
  context: { params: Promise<{ integrationId: string }> }
) {
  const { integrationId } = await context.params;

  const integration = agentsIntegrations.find((i) => i.id === integrationId);
  if (!integration) {
    return new Response("Integration not found", { status: 404 });
  }
  // ... rest remains the same
}
```

---

## Additional Checks

### Verify Backend Service is Running

The frontend also needs the Bot API backend service to be available:

**Configuration**: `apps/dojo/src/env.ts`
```typescript
botApiUrl: process.env.BOT_API_URL || 'http://localhost:8000'
```

**Required endpoints** (from `BotApiAgent`):
- `POST /api/agent/luka` - Main agent endpoint
- `POST /api/auth/guest` - Guest authentication
- `POST /api/auth/telegram-miniapp` - Telegram auth
- `GET /api/agent/luka/health` - Health check
- `GET /api/agent/luka/info` - Agent info

### Environment Variables

Check these are set correctly:
- `BOT_API_URL` - URL of the bot API backend (default: `http://localhost:8000`)

---

## Implementation Steps

1. **Apply the fix** to `apps/dojo/src/app/api/copilotkit/[integrationId]/route.ts`
2. **Restart the Next.js dev server** (`pnpm run dev`)
3. **Verify the Bot API backend is running** on port 8000 (or configured port)
4. **Test the integration** by accessing the bot-api feature in the UI

---

## Testing

After applying the fix, verify:

1. ✅ No 404 errors in browser console
2. ✅ CopilotKit successfully connects: Check for `RUN_STARTED` events
3. ✅ Messages are exchanged with the bot
4. ✅ Query parameters (like `?locale=en`) are properly preserved

---

## Related Files

- **Route Handler**: `apps/dojo/src/app/api/copilotkit/[integrationId]/route.ts`
- **Integration Config**: `apps/dojo/src/agents.ts`
- **Bot API Agent**: `apps/dojo/src/agents/bot-api-agent.ts`
- **Frontend Component**: `apps/dojo/src/components/bot-api-chat-panel.tsx`
- **Environment Config**: `apps/dojo/src/env.ts`

---

## Notes

- This is a **backend issue**, not a frontend configuration problem
- The frontend request is correct: `/api/copilotkit/bot-api?locale=en`
- The backend route parsing needs to handle query parameters properly
- Consider adding URL parsing unit tests to prevent regression

