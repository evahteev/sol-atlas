# API Specification: AG-UI Gateway REST API

**Version:** 1.0  
**Base URL:** `https://api.your-domain.com`  
**Protocol:** HTTPS  
**Format:** JSON  

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Authentication Endpoints](#authentication-endpoints)
6. [Catalog Endpoints](#catalog-endpoints)
7. [Profile Endpoints](#profile-endpoints)
8. [File Upload Endpoints](#file-upload-endpoints)
9. [Command Endpoints](#command-endpoints)
10. [Health Check Endpoints](#health-check-endpoints)

---

## Overview

The AG-UI Gateway REST API provides access to Luka Bot's features via standard HTTP protocols. All endpoints return JSON responses and follow REST conventions.

### Base URL

```
Production: https://api.your-domain.com
Development: http://localhost:8000
```

### Content Type

All requests and responses use `application/json` unless otherwise specified (e.g., file uploads use `multipart/form-data`).

### Versioning

Currently v1 (no version prefix in URL). Future versions will use path versioning: `/v2/api/...`

---

## Authentication

### Authorization Header

Most endpoints require authentication via Bearer token:

```http
Authorization: Bearer <token>
```

**Token Types:**
- **Guest Token:** `guest_<random>` - Limited permissions
- **JWT Token:** Standard JWT format - Full permissions

### Guest vs Authenticated Access

| Access Level | Token Type | Permissions |
|-------------|-----------|-------------|
| Anonymous | None | Public catalog view only |
| Guest | Guest token | Public KB search, limited chat |
| Authenticated | JWT | Full access |

---

## Error Handling

### Standard Error Response

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "additional context"
  },
  "timestamp": "2025-10-18T14:30:00Z"
}
```

### HTTP Status Codes

| Code | Status | Usage |
|------|--------|-------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request body/parameters |
| 401 | Unauthorized | Missing/invalid auth token |
| 403 | Forbidden | No permission for resource |
| 404 | Not Found | Resource doesn't exist |
| 413 | Payload Too Large | File > 20MB |
| 415 | Unsupported Media Type | Invalid file type |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | Upstream service unavailable |
| 503 | Service Unavailable | Maintenance mode |

### Error Codes

| Code | Description |
|------|-------------|
| `AUTH_INVALID_TOKEN` | JWT token invalid or expired |
| `AUTH_INVALID_SIGNATURE` | Telegram signature validation failed |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `PERMISSION_DENIED` | No access to resource |
| `UPGRADE_REQUIRED` | Guest users need to authenticate |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `WORKFLOW_ERROR` | Camunda workflow error |
| `UPSTREAM_UNAVAILABLE` | Flow API or Warehouse unavailable |
| `VALIDATION_ERROR` | Request validation failed |

---

## Rate Limiting

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1697642400
```

### Limits by Tier

| Endpoint Pattern | Guest | Authenticated |
|-----------------|-------|---------------|
| `/api/auth/*` | 10/min | N/A |
| `/api/catalog` | 20/min | 60/min |
| `/api/kb/*` (GET) | 30/min | 120/min |
| `/api/kb/*` (PATCH) | N/A | 10/min |
| `/api/search` | 10/min | 30/min |
| `/api/profile` | N/A | 30/min |
| `/api/files/upload` | N/A | 5/min |
| `/api/commands/*` | N/A | 60/min |

### Rate Limit Exceeded Response

```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again later.",
  "details": {
    "limit": 20,
    "window": 60,
    "retry_after": 45
  }
}
```

---

## Authentication Endpoints

### POST /api/auth/telegram-miniapp

Authenticate user via Telegram Mini App initData.

**Request:**

```http
POST /api/auth/telegram-miniapp HTTP/1.1
Content-Type: application/json

{
  "initData": "query_id=xxx&user=%7B%22id%22%3A123456789...&auth_date=1697640000&hash=abc123..."
}
```

**Response (200 OK):**

```json
{
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "telegram_user_id": 123456789,
    "username": "pavel",
    "first_name": "Pavel",
    "last_name": "Ivanov",
    "camunda_user_id": "user_123456789",
    "webapp_user_id": 42
  }
}
```

**Errors:**
- `401` - Invalid signature or expired initData
- `500` - Flow API unavailable

---

### POST /api/auth/guest

Create guest session for anonymous browsing.

**Request:**

```http
POST /api/auth/guest HTTP/1.1
Content-Type: application/json
```

No body required.

**Response (201 Created):**

```json
{
  "token": "guest_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "token_type": "guest",
  "expires_in": 3600,
  "message": "Guest session created. Sign in for full features.",
  "upgrade_url": "/api/auth/telegram-miniapp",
  "permissions": [
    "read:public_kb",
    "chat:ephemeral",
    "search:public_kb"
  ]
}
```

**Note:** Guest sessions expire after 1 hour of inactivity.

---

### POST /api/auth/refresh

Refresh expired JWT token.

**Request:**

```http
POST /api/auth/refresh HTTP/1.1
Authorization: Bearer <expired_or_valid_jwt_token>
```

**Response (200 OK):**

```json
{
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

**Errors:**
- `401` - Token completely invalid (not just expired)
- `500` - Flow API unavailable

---

### POST /api/auth/upgrade

Upgrade guest session to authenticated.

**Request:**

```http
POST /api/auth/upgrade HTTP/1.1
Authorization: Bearer <guest_token>
Content-Type: application/json

{
  "initData": "query_id=xxx&user=...&hash=..."
}
```

**Response (200 OK):**

```json
{
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "message": "Upgraded to authenticated user",
  "user": {
    "telegram_user_id": 123456789,
    "username": "pavel"
  }
}
```

**Errors:**
- `400` - Not a guest token
- `401` - Invalid Telegram signature

---

## Catalog Endpoints

### GET /api/catalog

List knowledge bases in catalog with filters.

**Request:**

```http
GET /api/catalog?visibility=public&category=crypto&limit=50&offset=0 HTTP/1.1
Authorization: Bearer <token>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `visibility` | string | No | Filter: `public`, `private`, `unlisted`, `all` |
| `category` | string | No | Filter: `crypto`, `web3`, `tech`, `gaming`, etc. |
| `status` | string | No | Filter: `enabled`, `disabled`, `indexing` |
| `featured` | boolean | No | Show only featured KBs |
| `search` | string | No | Search in name/description |
| `limit` | integer | No | Max results (default: 50, max: 100) |
| `offset` | integer | No | Pagination offset (default: 0) |

**Response (200 OK):**

```json
{
  "total": 156,
  "limit": 50,
  "offset": 0,
  "results": [
    {
      "id": "crypto-signals-vip",
      "name": "Crypto Signals VIP",
      "description": "Premium crypto trading signals and analysis",
      "icon": "💰",
      "visibility": "public",
      "status": "enabled",
      "categories": ["crypto", "trading"],
      "tags": ["bitcoin", "ethereum", "signals"],
      "stats": {
        "messages": 15420,
        "contributors": 234,
        "searches": 1250
      },
      "featured": true,
      "verified": true,
      "quality_score": 92.5,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-10-18T14:22:00Z"
    }
  ],
  "categories": {
    "crypto": 45,
    "web3": 32,
    "tech": 28,
    "gaming": 15
  }
}
```

**Errors:**
- `401` - Invalid/missing token (if filtering by private)
- `429` - Rate limit exceeded

---

### GET /api/kb/{kb_id}

Get detailed information about a knowledge base.

**Request:**

```http
GET /api/kb/crypto-signals-vip HTTP/1.1
Authorization: Bearer <token>
```

**Response (200 OK):**

```json
{
  "id": "crypto-signals-vip",
  "name": "Crypto Signals VIP",
  "description": "Premium crypto trading signals and analysis",
  "icon": "💰",
  "banner_url": "https://cdn.example.com/banners/crypto-signals.jpg",
  "visibility": "public",
  "status": "enabled",
  "categories": ["crypto", "trading"],
  "tags": ["bitcoin", "ethereum", "signals", "technical-analysis"],
  "owner_id": 123456,
  "source_type": "group",
  "source_id": -1001234567890,
  "source_name": "Crypto Signals VIP Group",
  "language": "en",
  "stats": {
    "messages": 15420,
    "contributors": 234,
    "searches": 1250,
    "members": 567
  },
  "featured": true,
  "verified": true,
  "quality_score": 92.5,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-10-18T14:22:00Z",
  "last_indexed": "2025-10-18T14:20:00Z",
  "sample_messages": [
    {
      "text": "BTC breaking $65k resistance, strong bullish momentum...",
      "sender": "TraderJoe",
      "date": "2025-10-18T12:00:00Z"
    }
  ],
  "access": {
    "can_read": true,
    "can_edit": false,
    "can_manage": false
  }
}
```

**Errors:**
- `404` - KB not found
- `403` - No access to private KB (guest or not member)

**Upgrade Required Response (403):**

```json
{
  "error": "UPGRADE_REQUIRED",
  "message": "This knowledge base is private. Sign in to access.",
  "details": {
    "upgrade_url": "/api/auth/telegram-miniapp",
    "kb_id": "private-kb-123"
  }
}
```

---

### PATCH /api/kb/{kb_id}

Update knowledge base metadata (owner only).

**Request:**

```http
PATCH /api/kb/crypto-signals-vip HTTP/1.1
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "visibility": "public",
  "description": "Updated description with more details",
  "categories": ["crypto", "trading", "analysis"],
  "tags": ["bitcoin", "ethereum", "signals", "technical-analysis", "day-trading"]
}
```

**Response (200 OK):**

```json
{
  "message": "Knowledge base updated successfully",
  "kb": {
    "id": "crypto-signals-vip",
    "name": "Crypto Signals VIP",
    "visibility": "public",
    "updated_at": "2025-10-18T15:00:00Z"
  }
}
```

**Errors:**
- `403` - Not owner
- `404` - KB not found
- `400` - Invalid visibility or category

---

## Profile Endpoints

### GET /api/profile

Get current user's profile.

**Request:**

```http
GET /api/profile HTTP/1.1
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**

```json
{
  "user_id": 123456789,
  "telegram_user_id": 123456789,
  "username": "pavel",
  "first_name": "Pavel",
  "language": "en",
  "created_at": "2025-01-10T08:00:00Z",
  "stats": {
    "messages_sent": 523,
    "tasks_completed": 42,
    "groups_managed": 3,
    "kb_size_mb": 125.5
  },
  "settings": {
    "llm_provider": "ollama",
    "llm_model": "llama3.2",
    "streaming_enabled": true,
    "language": "en"
  },
  "active_processes": [
    {
      "id": "proc-789",
      "name": "Community Audit",
      "process_definition_key": "community_audit",
      "started": "2025-10-18T10:00:00Z",
      "status": "running"
    }
  ]
}
```

**Errors:**
- `401` - Not authenticated (guest token not allowed)
- `403` - Upgrade required

---

### PATCH /api/profile/settings

Update user settings.

**Request:**

```http
PATCH /api/profile/settings HTTP/1.1
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "language": "ru",
  "llm_provider": "openai",
  "llm_model": "gpt-4-turbo",
  "streaming_enabled": false
}
```

**Response (200 OK):**

```json
{
  "message": "Settings updated successfully",
  "settings": {
    "llm_provider": "openai",
    "llm_model": "gpt-4-turbo",
    "streaming_enabled": false,
    "language": "ru"
  }
}
```

**Errors:**
- `401` - Not authenticated
- `400` - Invalid setting value

---

## File Upload Endpoints

### POST /api/files/upload

Upload file for task variable or chat attachment.

**Request:**

```http
POST /api/files/upload HTTP/1.1
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="document.pdf"
Content-Type: application/pdf

<binary file data>
------WebKitFormBoundary
Content-Disposition: form-data; name="task_id"

task-123
------WebKitFormBoundary
Content-Disposition: form-data; name="variable_name"

s3_document
------WebKitFormBoundary
Content-Disposition: form-data; name="context"

task
------WebKitFormBoundary--
```

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | File to upload |
| `task_id` | string | No | Task ID (for task uploads) |
| `variable_name` | string | No | Variable name (for task uploads) |
| `context` | string | Yes | `task` or `chat` |

**Response (200 OK):**

```json
{
  "file_url": "https://cdn.example.com/uploads/a1b2c3d4-document.pdf",
  "file_name": "document.pdf",
  "file_size": 2048576,
  "mime_type": "application/pdf",
  "uploaded_at": "2025-10-18T14:30:00Z"
}
```

**Errors:**
- `413` - File > 20MB
- `415` - Unsupported file type
- `401` - Not authenticated (guest not allowed)

---

## Command Endpoints

### POST /api/commands/{command}

Execute a command (alternative to WebSocket).

**Request:**

```http
POST /api/commands/search HTTP/1.1
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "args": {
    "kb_ids": ["crypto-kb", "defi-kb"],
    "query": "DeFi lending protocols",
    "max_results": 10
  }
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "command": "search",
  "result": {
    "results": [
      {
        "text": "Aave is a decentralized lending protocol...",
        "score": 0.92,
        "source": "crypto-kb",
        "sender": "CryptoPro",
        "date": "2025-10-15T12:00:00Z"
      }
    ],
    "total": 15,
    "kb_searched": ["crypto-kb", "defi-kb"]
  }
}
```

**Available Commands:**
- `start` - Main menu
- `tasks` - List tasks
- `search` - Search KBs
- `profile` - View profile
- `chat` - Manage threads
- `groups` - Manage groups
- `catalog` - Browse catalog

**Errors:**
- `404` - Unknown command
- `403` - Command requires authentication (guest not allowed)
- `400` - Invalid command arguments

---

## Health Check Endpoints

### GET /health

Health check endpoint for load balancers.

**Request:**

```http
GET /health HTTP/1.1
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-18T14:30:00Z",
  "dependencies": {
    "redis": "healthy",
    "postgres": "healthy",
    "elasticsearch": "healthy",
    "camunda": "healthy",
    "flow_api": "healthy"
  }
}
```

**Degraded Response (200 OK):**

```json
{
  "status": "degraded",
  "redis": true,
  "postgres": true,
  "elasticsearch": false,
  "camunda": true
}
```

---

### GET /metrics

Prometheus metrics endpoint.

**Request:**

```http
GET /metrics HTTP/1.1
```

**Response (200 OK):**

```text
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/catalog",status="200"} 1234

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/catalog",le="0.1"} 900
http_request_duration_seconds_bucket{method="GET",endpoint="/api/catalog",le="0.5"} 1200
```

---

## Common Patterns

### Pagination

List endpoints support offset-based pagination:

```http
GET /api/catalog?limit=50&offset=0  # First page
GET /api/catalog?limit=50&offset=50  # Second page
```

**Response includes:**
```json
{
  "total": 156,
  "limit": 50,
  "offset": 0,
  "results": [...]
}
```

### Filtering

Use query parameters for filtering:

```http
GET /api/catalog?visibility=public&category=crypto&status=enabled
```

### Searching

Use `search` query parameter:

```http
GET /api/catalog?search=DeFi%20protocols
```

### Sorting

Not yet implemented. Will be added in v1.1.

---

## Rate Limiting Best Practices

1. **Check headers:** Monitor `X-RateLimit-Remaining`
2. **Implement exponential backoff:** Wait longer between retries
3. **Cache responses:** Reduce API calls
4. **Authenticate:** Get higher limits
5. **Batch requests:** Combine when possible

---

## CORS Policy

**Allowed Origins:**
- `https://your-domain.com`
- `https://t.me` (Telegram Mini App)

**Allowed Methods:** All

**Allowed Headers:** All

**Credentials:** Allowed

---

## Changelog

**v1.0 (2025-10-18)**
- Initial API release
- Authentication endpoints
- Catalog endpoints
- Profile endpoints
- File upload
- Commands
- Guest mode support

---

**Related Documents:**
- [WebSocket Protocol](./WEBSOCKET_PROTOCOL.md)
- [Authentication Guide](./AUTHENTICATION.md)
- [Data Models](./DATA_MODELS.md)
- [PRD](./PRD.md)

