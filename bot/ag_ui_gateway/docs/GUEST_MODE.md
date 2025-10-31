# Guest Mode Specification

**Version:** 1.0  
**Date:** October 18, 2025

---

## Overview

Guest Mode allows anonymous users to explore public knowledge bases and try basic chat functionality without authentication. This lowers the barrier to entry while creating clear incentives to upgrade to full authentication.

---

## Capabilities Matrix

| Feature | Guest Mode | Authenticated Mode |
|---------|-----------|-------------------|
| **Knowledge Base** |
| Browse public KB catalog | ✅ | ✅ |
| View public KB details | ✅ | ✅ |
| Search public KBs | ✅ (limited) | ✅ |
| Browse private KBs | ❌ | ✅ (if member) |
| **Chat** |
| Basic chat (no history) | ✅ (20 msgs) | ✅ |
| Streaming LLM responses | ✅ | ✅ |
| Tool execution (KB search) | ✅ (public only) | ✅ |
| Thread management | ❌ | ✅ |
| Conversation history | ❌ | ✅ |
| **Workflows & Tasks** |
| View tasks | ❌ | ✅ |
| Complete tasks | ❌ | ✅ |
| Start workflows | ❌ | ✅ |
| Execute commands | ❌ | ✅ |
| **Profile & Settings** |
| View profile | ❌ | ✅ |
| Change settings | ❌ | ✅ |
| File uploads | ❌ | ✅ |

---

## Guest Token System

### Token Generation

```python
import secrets

def generate_guest_token() -> str:
    return f"guest_{secrets.token_urlsafe(32)}"
```

### Token Storage

```python
# Redis storage with 1-hour expiry
session_data = {
    'token_type': 'guest',
    'created_at': time.time(),
    'message_count': 0,
    'permissions': [
        'read:public_kb',
        'chat:ephemeral',
        'search:public_kb'
    ],
    'rate_limit_tier': 'guest'
}

await redis.setex(
    f"guest_session:{token}",
    3600,  # 1 hour
    json.dumps(session_data)
)
```

---

## Rate Limiting

### Guest Tier Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/catalog` | 20 req | 1 minute |
| `/api/kb/*` (GET) | 30 req | 1 minute |
| `/api/search` | 10 req | 1 minute |
| `/ws/chat` messages | 10 msg | 1 minute |
| Total chat messages | 20 msg | per session |

### Upgrade Prompt After Limit

When guest reaches message limit:

```json
{
  "type": "error",
  "code": "UPGRADE_REQUIRED",
  "message": "Guest limit reached (20 messages). Sign in to continue.",
  "details": {
    "upgrade_url": "/api/auth/telegram-miniapp",
    "messages_used": 20,
    "messages_limit": 20
  }
}
```

---

## Upgrade Flow

### 1. Guest Exploration

User browses catalog and tries chat without sign-in.

### 2. Hit Limitation

User encounters feature restriction or message limit.

### 3. Upgrade Prompt

Show contextual upgrade prompt:

```javascript
// Example upgrade prompt
{
  error: "UPGRADE_REQUIRED",
  message: "This feature requires authentication",
  upgrade_url: "/api/auth/telegram-miniapp",
  feature: "tasks"
}
```

### 4. Authentication

User signs in via Telegram Mini App.

### 5. Session Upgrade

```http
POST /api/auth/upgrade
Authorization: Bearer <guest_token>

{
  "initData": "..."
}
```

### 6. Full Access

User now has authenticated token with full permissions.

---

## Conversion Tracking

### Metrics to Track

```python
# Prometheus metrics
guest_sessions_created = Counter('guest_sessions_created_total')
guest_messages_sent = Counter('guest_messages_sent_total')
guest_kb_searches = Counter('guest_kb_searches_total')
guest_upgrade_initiated = Counter('guest_upgrade_initiated_total')
guest_upgrade_completed = Counter('guest_upgrade_completed_total')
guest_session_duration = Histogram('guest_session_duration_seconds')
```

### Conversion Funnel

```
Guest Session Created
  ↓
Browse Catalog (80%)
  ↓
Search KB (50%)
  ↓
Try Chat (40%)
  ↓
Hit Limit (30%)
  ↓
Click Upgrade (15%)
  ↓
Complete Auth (10%)
```

---

## Frontend Implementation

### Guest Banner Component

```typescript
export function GuestBanner() {
  const { isGuest, signIn } = useAuth();
  
  if (!isGuest) return null;
  
  return (
    <div className="bg-blue-500 text-white p-3">
      <p>You're browsing as a guest</p>
      <button onClick={signIn}>
        Sign In with Telegram
      </button>
    </div>
  );
}
```

### Upgrade Prompt

```typescript
export function UpgradePrompt({ feature }: { feature: string }) {
  return (
    <div className="border p-8 text-center">
      <h3>{feature} Requires Sign In</h3>
      <button onClick={signIn}>
        Sign In with Telegram
      </button>
    </div>
  );
}
```

### Message Counter

```typescript
export function GuestChatCounter({ used, max }: {
  used: number; max: number;
}) {
  const remaining = max - used;
  
  return (
    <div className="bg-yellow-50 p-3">
      <p>Guest Mode - {remaining} messages left</p>
      <progress value={used} max={max} />
    </div>
  );
}
```

---

## Success Metrics

**Acquisition:**
- Guest sessions created: 200+/week
- Guest → Sign In click rate: >30%
- Guest → Authenticated conversion: >15%

**Engagement:**
- Average guest session duration: >3 minutes
- Guest messages sent: 500+/week
- Guest KB searches: 1000+/week

**Retention:**
- Converted users 7-day return rate: >50%

---

## Related Documents

- [Authentication](./AUTHENTICATION.md)
- [API Specification](./API_SPECIFICATION.md)
- [WebSocket Protocol](./WEBSOCKET_PROTOCOL.md)

---

**Document Version:** 1.0  
**Last Updated:** October 18, 2025
