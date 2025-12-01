# Session Management Guide

This document explains how session management works in the application and how to handle various scenarios.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  SessionProvider                     │
│  - Wraps entire app (app/layout.tsx)                │
│  - Creates SessionContext                           │
│  - Provides centralized session state               │
└─────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                    ▼
┌──────────────────┐              ┌──────────────────┐
│  useSession()    │              │   Manual Refresh │
│  - Fetches once  │              │   update()       │
│  - Auto-polls    │              └──────────────────┘
│    when blocked  │
└──────────────────┘
        │
        ▼ Auto-polling (5s) if is_block === true
┌─────────────────────────────┐
│   /api/auth/session         │
│   (with cookie auth)        │
└─────────────────────────────┘
```

## Key Components

### 1. SessionProvider (`@/providers/SessionProvider.tsx`)

Client-only provider that:
- Manages global session state via React Context
- Wraps the base `useSession()` hook
- Exposes session via context to all child components

**Location in app:** Wraps entire app in `app/layout.tsx`

### 2. useSession hooks

#### `useSession()` from `@/hooks/useSession`
**Direct access to session data with auto-polling**
```tsx
const { session, loading, error, refetch } = useSession()

// Automatically polls every 5s when session.user.is_block === true
// Stops polling when user becomes unblocked
```

#### `useSession()` from `@/hooks/useAuth.compat`
**Next-auth compatible API (recommended)**
```tsx
const { data, status, update } = useSession()
// status: 'loading' | 'authenticated' | 'unauthenticated'
// data: session object or null
// update(): Promise<SessionData | null> - manual refresh
```

## Common Scenarios

### Scenario 1: User logs in

**What happens:**
1. User connects wallet
2. `useConnectHandler` calls `/api/auth/login`
3. Server sets session cookie
4. Handler calls `update()` immediately
5. Session refreshes without page reload ✅

**Code location:** `src/hooks/useConnectHandler.ts:60-61`

### Scenario 2: User completes quest and gets unblocked

**What happens:**
1. User completes quest in Camunda
2. Backend updates `is_block` status in database
3. `useSession` is auto-polling (every 5s) because `is_block === true`
4. Next poll detects `is_block === false`
5. Polling stops automatically ✅
6. Components re-render with unblocked state

**No extra code needed!** Just use `useSession()` normally.

### Scenario 3: User is blocked and waiting

**Automatic handling:**
```tsx
const { data: session } = useSession()

// Automatically polls when session.user.is_block === true
// No configuration needed
```

**Manual refresh (if needed):**
```tsx
const { update } = useSession()

async function handleQuestComplete() {
  // Force immediate refresh
  await update()
}
```

## Session Refresh Methods

| Method | When to Use | Automatic? |
|--------|-------------|-----------|
| **Auto-polling** | Blocked users | ✅ Yes (built into useSession) |
| **Manual `update()`** | After login or on-demand | ❌ No (call manually) |

## Best Practices

### ✅ DO

- Use `useSession()` from `@/hooks/useAuth.compat` for consistency
- Call `update()` after login or manual operations
- Trust auto-polling for blocked users (it's automatic!)
- Keep SessionProvider at the app root level

### ❌ DON'T

- Don't manually implement polling (it's built-in)
- Don't create multiple SessionProviders
- Don't bypass session management with direct API calls

## Debugging

Console logs to watch for:
- `[useSession] User is blocked, starting auto-polling...`
- `[useSession] Polling for unblock status...`
- `[useSession] User unblocked or unmounted, stopping polling`

## Migration Notes

### From old session system:

**Before:**
```tsx
import { useSession } from 'next-auth/react'
```

**After:**
```tsx
import { useSession } from '@/hooks/useAuth.compat'
// API is compatible, but now has working update() method
```

## API Reference

### SessionData Type
```typescript
interface SessionData {
  user?: {
    id: string
    webapp_user_id: string
    is_admin: boolean
    is_block: boolean  // ⚠️ This is what we sync!
    camunda_user_id?: string
    // ... other fields
  }
  access_token?: string
  refresh_token?: string
  expires: string
}
```

### useSession() Return Type
```typescript
{
  data: SessionData | null
  status: 'loading' | 'authenticated' | 'unauthenticated'
  update: () => Promise<SessionData | null>
}
```

## Testing

When writing tests that use session:

```tsx
import { SessionProvider } from '@/providers/SessionProvider'

// Mock the underlying useSession hook
jest.mock('@/hooks/useSession', () => ({
  useSession: () => ({
    session: { user: { ... } },
    loading: false,
    error: null,
    refetch: jest.fn(),
  })
}))

// Wrap component in provider
render(
  <SessionProvider>
    <YourComponent />
  </SessionProvider>
)
```
