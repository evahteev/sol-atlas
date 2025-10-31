# Authentication & Authorization Guide

**Version:** 1.0  
**Date:** October 18, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Telegram Mini App Authentication](#telegram-mini-app-authentication)
3. [Guest Mode Authentication](#guest-mode-authentication)
4. [JWT Token Management](#jwt-token-management)
5. [Permission System](#permission-system)
6. [Rate Limiting](#rate-limiting)
7. [Security Best Practices](#security-best-practices)

---

## Overview

The AG-UI Gateway supports three authentication modes:

1. **Telegram Mini App** - Primary method for Telegram users
2. **Guest Mode** - Anonymous browsing with limited features
3. **JWT Refresh** - Token renewal for authenticated users

All authenticated requests include a Bearer token in the Authorization header.

---

## Telegram Mini App Authentication

### Flow Diagram

```
User Opens Mini App → Telegram Signs initData → Send to Gateway → 
Validate Signature → Get User from Flow API → Generate JWT → Return Token
```

### Implementation

**Client Side (JavaScript):**

```javascript
// Get Telegram WebApp data
const initData = window.Telegram.WebApp.initData;

// Send to API
const response = await fetch('/api/auth/telegram-miniapp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ initData })
});

const { jwt_token, user } = await response.json();

// Store token
localStorage.setItem('auth_token', jwt_token);
```

**Server Side (Python):**

```python
import hmac
import hashlib
from urllib.parse import parse_qs

def validate_telegram_webapp_data(init_data: str, bot_token: str) -> dict:
    """Validate Telegram Mini App initData signature."""
    parsed = parse_qs(init_data)
    
    # Extract hash
    received_hash = parsed.get('hash', [None])[0]
    if not received_hash:
        raise HTTPException(401, "Missing hash")
    
    # Build data check string
    data_check_string = '\n'.join(
        f"{k}={v[0]}" 
        for k, v in sorted(parsed.items()) 
        if k != 'hash'
    )
    
    # Compute secret key
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256
    ).digest()
    
    # Compute expected hash
    expected_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Verify
    if not hmac.compare_digest(received_hash, expected_hash):
        raise HTTPException(401, "Invalid signature")
    
    # Parse user data
    import json
    user_data = json.loads(parsed['user'][0])
    
    return {
        'telegram_user_id': user_data['id'],
        'username': user_data.get('username'),
        'first_name': user_data.get('first_name')
    }
```

### Security Checks

1. **Signature Validation** - HMAC-SHA256 with bot token
2. **Timestamp Check** - auth_date within 5 minutes
3. **Hash Comparison** - Constant-time comparison

---

## Guest Mode Authentication

### Guest Token Generation

**Endpoint:** `POST /api/auth/guest`

**Response:**

```json
{
  "token": "guest_a1b2c3d4e5f6g7h8i9j0",
  "token_type": "guest",
  "expires_in": 3600,
  "permissions": ["read:public_kb", "chat:ephemeral"]
}
```

**Implementation:**

```python
import secrets

class GuestToken:
    @staticmethod
    def generate() -> str:
        return f"guest_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def is_guest_token(token: str) -> bool:
        return token.startswith("guest_")
```

**Storage:**

```python
# Store in Redis with 1-hour expiry
await redis.setex(
    f"guest_session:{token}",
    3600,
    json.dumps({
        'token_type': 'guest',
        'created_at': time.time(),
        'permissions': ['read:public_kb', 'chat:ephemeral']
    })
)
```

### Guest Limitations

| Feature | Guest | Authenticated |
|---------|-------|---------------|
| Public KB Browse | ✅ | ✅ |
| Chat Messages | 20 max | Unlimited |
| Private KB Access | ❌ | ✅ |
| Tasks & Workflows | ❌ | ✅ |
| Profile | ❌ | ✅ |

---

## JWT Token Management

### Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "123456789",
    "telegram_user_id": 123456789,
    "type": "authenticated",
    "exp": 1697644800,
    "iat": 1697641200
  }
}
```

### Token Creation

```python
from jose import jwt
from datetime import datetime, timedelta

def create_jwt_token(user_id: int, secret: str) -> str:
    payload = {
        'sub': str(user_id),
        'telegram_user_id': user_id,
        'type': 'authenticated',
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, secret, algorithm='HS256')
```

### Token Validation

```python
def validate_jwt_token(token: str, secret: str) -> dict:
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.JWTError:
        raise HTTPException(401, "Invalid token")
```

### Token Refresh

**Endpoint:** `POST /api/auth/refresh`

**Flow:**
1. Client sends expired or valid JWT
2. Server validates token (allows expired < 7 days)
3. Server generates new JWT
4. Return new token to client

---

## Permission System

### Permission Definitions

```python
class Permission(str, Enum):
    # Public (guest allowed)
    READ_PUBLIC_KB = "read:public_kb"
    CHAT_EPHEMERAL = "chat:ephemeral"
    SEARCH_PUBLIC_KB = "search:public_kb"
    
    # Authenticated only
    READ_PRIVATE_KB = "read:private_kb"
    WRITE_KB = "write:kb"
    MANAGE_KB = "manage:kb"
    EXECUTE_WORKFLOWS = "execute:workflows"
    VIEW_TASKS = "view:tasks"
    COMPLETE_TASKS = "complete:tasks"
    VIEW_PROFILE = "view:profile"
    UPLOAD_FILES = "upload:files"
```

### Permission Decorator

```python
from functools import wraps

def require_permission(permission: Permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            token_data = request.state.token_data
            
            if permission.value not in token_data.get('permissions', []):
                raise HTTPException(403, "Permission denied")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@router.get("/api/profile")
@require_permission(Permission.VIEW_PROFILE)
async def get_profile(request: Request):
    pass
```

### Access Control Matrix

| Resource | Anonymous | Guest | Authenticated | Owner |
|----------|-----------|-------|---------------|-------|
| Public KB (view) | ✅ | ✅ | ✅ | ✅ |
| Private KB (view) | ❌ | ❌ | Member only | ✅ |
| KB (edit) | ❌ | ❌ | ❌ | ✅ |
| Chat (ephemeral) | ❌ | ✅ | ✅ | ✅ |
| Chat (history) | ❌ | ❌ | ✅ | ✅ |
| Tasks | ❌ | ❌ | ✅ | ✅ |
| Profile | ❌ | ❌ | ✅ | ✅ |

---

## Rate Limiting

### Tiered Rate Limits

```python
RATE_LIMITS = {
    'guest': {
        '/api/catalog': (20, 60),          # 20 req/min
        '/api/kb/*': (30, 60),             # 30 req/min
        '/api/search': (10, 60),           # 10 searches/min
        '/ws/chat': (10, 60),              # 10 messages/min
    },
    'authenticated': {
        '/api/catalog': (60, 60),
        '/api/kb/*': (120, 60),
        '/api/search': (30, 60),
        '/ws/chat': (30, 60),
        '/api/profile': (30, 60),
        '/api/commands/*': (60, 60),
    }
}
```

### Implementation

```python
import time
from typing import Tuple

async def check_rate_limit(
    user_id: str,
    endpoint: str,
    tier: str
) -> Tuple[bool, int]:
    """
    Check if user has exceeded rate limit.
    
    Returns: (is_allowed, retry_after_seconds)
    """
    limit, window = RATE_LIMITS[tier].get(endpoint, (60, 60))
    
    key = f"rate_limit:{tier}:{user_id}:{endpoint}"
    
    # Get current count
    count = await redis.get(key)
    
    if count is None:
        # First request in window
        await redis.setex(key, window, 1)
        return True, 0
    
    count = int(count)
    
    if count >= limit:
        # Rate limit exceeded
        ttl = await redis.ttl(key)
        return False, ttl
    
    # Increment counter
    await redis.incr(key)
    return True, 0
```

---

## Security Best Practices

### 1. Token Storage

**Client Side:**
- Store JWT in `localStorage` or secure cookie
- Never log tokens to console
- Clear token on logout

**Server Side:**
- Store in Redis with expiry
- Index by user_id for quick lookup
- Encrypt sensitive data

### 2. HTTPS Only

- All endpoints require HTTPS in production
- WebSocket uses WSS (secure)
- HSTS headers enabled

### 3. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-domain.com",
        "https://t.me"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Input Validation

- All requests validated with Pydantic models
- File size limits enforced
- MIME type whitelist
- XSS prevention (output encoding)

### 5. Rate Limiting

- Per-user and per-IP limits
- Exponential backoff on retry
- DDoS protection via Nginx

---

## Related Documents

- [API Specification](./API_SPECIFICATION.md)
- [Guest Mode](./GUEST_MODE.md)
- [WebSocket Protocol](./WEBSOCKET_PROTOCOL.md)
- [Architecture](./ARCHITECTURE.md)

---

**Document Version:** 1.0  
**Last Updated:** October 18, 2025
