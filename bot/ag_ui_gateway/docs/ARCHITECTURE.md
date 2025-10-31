# System Architecture: AG-UI Gateway

**Version:** 1.0  
**Date:** October 18, 2025  

---

## Table of Contents

1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Responsibilities](#component-responsibilities)
4. [Data Flow](#data-flow)
5. [Integration Points](#integration-points)
6. [Technology Stack](#technology-stack)
7. [Scalability](#scalability)
8. [Security Architecture](#security-architecture)

---

## Overview

The AG-UI Gateway is a **FastAPI-based API Gateway** that exposes Luka Bot's capabilities via REST + WebSocket APIs. It acts as a bridge between web/mobile clients and the existing Luka Bot service layer, translating between AG-UI protocol events and service calls.

### Design Principles

1. **Service Reuse:** All business logic from `luka_bot/services/` is reused without duplication
2. **Adapter Pattern:** Adapters translate between AG-UI protocol and service calls
3. **Stateless API:** Session state stored in Redis for horizontal scaling
4. **Event-Driven:** Real-time communication via WebSocket events
5. **Security First:** Authentication, authorization, rate limiting at gateway level

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Layer                                  │
├─────────────────────────────────────────────────────────────────────┤
│  • Web App (React + AG-UI Client)                                   │
│  • Telegram Mini App (Telegram WebApp API)                          │
│  • Future: Mobile Apps (React Native), Desktop (Electron)           │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 │ HTTPS (REST) + WSS (WebSocket)
                 │ + Telegram initData Auth
                 │
┌────────────────▼────────────────────────────────────────────────────┐
│              API Gateway Layer (FastAPI)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │  REST Endpoints │  │   WebSocket     │  │   Middleware    │    │
│  │                 │  │    Handlers     │  │                 │    │
│  │  /api/auth      │  │  /ws/chat      │  │  - Auth         │    │
│  │  /api/catalog   │  │  /ws/tasks     │  │  - Rate Limit   │    │
│  │  /api/profile   │  │                 │  │  - CORS         │    │
│  │  /api/files     │  │                 │  │  - Logging      │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      Adapters                                 │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  LLM Adapter    │  Task Adapter   │  Catalog Adapter        │  │
│  │  Command Router │  Profile Adapter │ Tool Adapter            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   Protocol Layer                              │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  Event Dispatcher │ Message Handler │ AG-UI Events           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────┬────────────────┬─────────────────────┬────────────────────────┘
      │                │                     │
      │ Auth           │ Task Events         │ Service Calls
      │                │                     │
┌─────▼────┐  ┌────────▼──────┐  ┌──────────▼─────────────────────────┐
│ Flow API │  │ Warehouse WS  │  │   Luka Bot Service Layer (Reused)  │
│          │  │               │  ├─────────────────────────────────────┤
│  - Auth  │  │ - Task Events │  │  • LLMService (streaming + tools)   │
│  - JWT   │  │ - Real-time   │  │  • CamundaService (workflows)       │
└──────────┘  └───────────────┘  │  • TaskService (rendering)          │
                                  │  • RAGService (KB search)           │
                                  │  • ElasticsearchService (indexing)  │
                                  │  • ProfileService (settings)        │
                                  │  • ThreadService (conversations)    │
                                  │  • S3UploadService (files)          │
                                  │  • GroupService (groups)            │
                                  └──────────┬──────────────────────────┘
                                             │
                              ┌──────────────▼──────────────────────────┐
                              │           Infrastructure                │
                              ├─────────────────────────────────────────┤
                              │  Redis    │  Postgres  │  Elasticsearch │
                              │  Camunda  │  S3/R2     │  Flow API      │
                              └─────────────────────────────────────────┘
```

---

## Component Responsibilities

### 1. API Gateway (FastAPI Application)

**Location:** `ag_ui_gateway/main.py`

**Responsibilities:**
- HTTP request routing
- WebSocket connection management
- Middleware orchestration (auth, rate limiting, CORS)
- Health checks and monitoring
- Startup/shutdown hooks

**Key Features:**
- Async/await support
- Auto-generated OpenAPI docs
- WebSocket support
- Dependency injection

---

### 2. REST Endpoints (`api/`)

**Location:** `ag_ui_gateway/api/`

**Modules:**
- `auth.py` - Authentication endpoints (telegram-miniapp, guest, refresh)
- `catalog.py` - Knowledge base catalog (list, details, update)
- `profile.py` - User profile and settings
- `files.py` - File upload handling
- `health.py` - Health check and metrics

**Pattern:**
```python
@router.get("/api/catalog")
async def list_catalog(
    token_data: dict = Depends(get_optional_token),
    visibility: Optional[str] = "public"
):
    # Route to adapter
    adapter = CatalogAdapter(token_data['user_id'])
    return await adapter.list_catalog(visibility)
```

---

### 3. WebSocket Handlers (`websocket/`)

**Location:** `ag_ui_gateway/websocket/`

**Modules:**
- `chat.py` - AG-UI protocol chat (main interaction)
- `tasks.py` - Task notification forwarding

**Responsibilities:**
- Connection lifecycle management
- Message parsing and validation
- Event dispatching to adapters
- Error handling and reconnection

**Pattern:**
```python
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    session = await authenticate_websocket(websocket)
    
    async for message in websocket.iter_json():
        await handle_message(message, session)
```

---

### 4. Adapters (`adapters/`)

**Location:** `ag_ui_gateway/adapters/`

**Purpose:** Translate between AG-UI protocol and luka_bot services

**Modules:**

#### `llm_adapter.py` - LLM Service → AG-UI Events
- Streams LLM responses as `textStreamDelta` events
- Emits `toolInvocation` / `toolResult` events
- Translates tool notifications to AG-UI format

#### `task_adapter.py` - Task Service → Forms
- Converts Camunda tasks to `formRequest` events
- Maps task variables to form fields
- Handles form submissions

#### `catalog_adapter.py` - KB Catalog Management
- Lists KBs with filters
- Fetches KB details
- Updates KB metadata
- Checks permissions

#### `command_adapter.py` - Command Routing
- Routes commands to workflows (optional)
- Executes command-specific logic
- Returns command results

#### `profile_adapter.py` - Profile Management
- Fetches user profile
- Updates settings
- Lists active processes

---

### 5. Authentication (`auth/`)

**Location:** `ag_ui_gateway/auth/`

**Modules:**

#### `tokens.py` - Token Management
- Guest token generation
- JWT creation and validation
- Token type detection
- Session management

#### `telegram_miniapp.py` - Telegram Auth
- Signature validation (HMAC-SHA256)
- User data extraction
- Auth date verification

#### `flow_auth.py` - Flow API Integration
- User lookup/creation
- JWT token fetching
- Camunda credentials retrieval

#### `permissions.py` - Permission System
- Permission definitions
- Access control checks
- Role-based authorization
- Decorator for endpoints

---

### 6. Protocol Layer (`protocol/`)

**Location:** `ag_ui_gateway/protocol/`

**Modules:**

#### `events.py` - Event Models
- Pydantic models for all AG-UI events
- Validation schemas
- Type definitions

#### `dispatcher.py` - Event Dispatcher
- Emits events to WebSocket clients
- Batching and optimization
- Error handling

#### `handler.py` - Message Handler
- Routes incoming messages to appropriate adapters
- Validates message format
- Error recovery

---

### 7. Middleware (`middleware/`)

**Location:** `ag_ui_gateway/middleware/`

**Modules:**

#### `auth_middleware.py` - Authentication Injection
- Validates tokens (guest or JWT)
- Injects user context into requests
- Handles auth errors

#### `rate_limit.py` - Rate Limiting
- Tiered limits (guest vs authenticated)
- Redis-based token bucket
- Rate limit headers

---

### 8. Configuration (`config/`)

**Location:** `ag_ui_gateway/config/`

**Modules:**

#### `settings.py` - Environment Configuration
- Pydantic BaseSettings
- Environment variable loading
- Defaults and validation

#### `commands.py` - Command-to-Workflow Mapping
- Command registry
- Workflow configuration
- Auto-execute flags

---

## Data Flow

### 1. Authentication Flow

```
Client                        Gateway                      Flow API
  │                              │                              │
  │  1. POST /api/auth/         │                              │
  │     telegram-miniapp        │                              │
  │─────────────────────────────>│                              │
  │                              │                              │
  │                              │  2. Validate signature       │
  │                              │     (HMAC-SHA256)            │
  │                              │                              │
  │                              │  3. GET /api/telegram/users  │
  │                              │────────────────────────────>│
  │                              │                              │
  │                              │  4. User data + credentials  │
  │                              │<────────────────────────────│
  │                              │                              │
  │                              │  5. POST /api/login          │
  │                              │────────────────────────────>│
  │                              │                              │
  │                              │  6. JWT token                │
  │                              │<────────────────────────────│
  │                              │                              │
  │                              │  7. Cache in Redis           │
  │                              │                              │
  │  8. JWT token + user data   │                              │
  │<─────────────────────────────│                              │
```

### 2. Chat Message Flow

```
Client                 Gateway              LLM Service          Elasticsearch
  │                       │                      │                     │
  │  1. WS: user_message │                      │                     │
  │──────────────────────>│                      │                     │
  │                       │                      │                     │
  │                       │  2. stream_response  │                     │
  │                       │─────────────────────>│                     │
  │                       │                      │                     │
  │                       │                      │  3. Tool: search_kb │
  │                       │                      │────────────────────>│
  │                       │                      │                     │
  │  4. WS: toolInvocation│                      │                     │
  │<──────────────────────│                      │                     │
  │                       │                      │  5. Results         │
  │                       │                      │<────────────────────│
  │                       │                      │                     │
  │  6. WS: toolResult    │                      │                     │
  │<──────────────────────│                      │                     │
  │                       │                      │                     │
  │  7. WS: textStreamDelta (multiple chunks)   │                     │
  │<──────────────────────│<─────────────────────│                     │
  │                       │                      │                     │
  │  8. WS: messageComplete│                     │                     │
  │<──────────────────────│                      │                     │
```

### 3. Task Notification Flow

```
Warehouse WS           Gateway              Task Service         Client
  │                       │                      │                     │
  │  1. Task created      │                      │                     │
  │──────────────────────>│                      │                     │
  │                       │                      │                     │
  │                       │  2. render_task()   │                     │
  │                       │─────────────────────>│                     │
  │                       │                      │                     │
  │                       │  3. FormData         │                     │
  │                       │<─────────────────────│                     │
  │                       │                      │                     │
  │                       │  4. Convert to formRequest                │
  │                       │                      │                     │
  │                       │  5. WS: taskNotification                   │
  │                       │────────────────────────────────────────────>│
  │                       │                      │                     │
  │                       │  6. WS: formRequest  │                     │
  │                       │────────────────────────────────────────────>│
```

---

## Integration Points

### 1. Flow API

**Purpose:** User authentication and JWT tokens

**Endpoints Used:**
- `GET /api/telegram/users` - Get user by Telegram ID
- `POST /api/telegram/users` - Create user
- `POST /api/login` - Get JWT token

**Authentication:** System key in headers

---

### 2. Warehouse WebSocket API

**Purpose:** Real-time task notifications

**Connection:** WebSocket with JWT authentication

**Events Received:**
- `task_created`
- `task_updated`
- `task_completed`
- `task_deleted`

**Forwarding:** Events forwarded to client as AG-UI `taskNotification` events

---

### 3. Luka Bot Services

**Purpose:** Business logic execution

**Services Reused:**
- `LLMService` - LLM interactions
- `CamundaService` - Workflow execution
- `TaskService` - Task management
- `RAGService` - Knowledge base search
- `ElasticsearchService` - Indexing
- `ProfileService` - User settings
- `ThreadService` - Conversation threads
- `S3UploadService` - File uploads
- `GroupService` - Group management

**Pattern:** Import directly and call methods

```python
from luka_bot.services.llm_service import get_llm_service

llm_service = get_llm_service()
async for chunk in llm_service.stream_response(...):
    await dispatcher.emit_text_delta(chunk)
```

---

### 4. Camunda Engine

**Purpose:** Workflow execution

**Access:** Via `CamundaService` (reused)

**Operations:**
- Start process instances
- Get user tasks
- Complete tasks
- Get task variables

---

### 5. Elasticsearch

**Purpose:** Knowledge base search

**Access:** Via `ElasticsearchService` (reused)

**Operations:**
- Text search (BM25)
- Vector search (k-NN)
- Hybrid search
- Index messages

---

## Technology Stack

### Core Framework

- **FastAPI 0.104+** - Web framework
- **Uvicorn** - ASGI server
- **websockets 12+** - WebSocket protocol
- **Pydantic v2** - Data validation
- **pydantic-settings** - Configuration

### Authentication

- **python-jose[cryptography]** - JWT handling
- **passlib** - Password hashing (if needed)

### Data Storage

- **redis 5+** - Session cache, rate limiting
- **asyncpg** - PostgreSQL async driver (via SQLAlchemy)

### HTTP Client

- **httpx** - Async HTTP client (Flow API)

### Monitoring

- **loguru** - Structured logging
- **prometheus-client** - Metrics export

### Development

- **pytest** - Testing
- **pytest-asyncio** - Async test support
- **httpx** - Test client

---

## Scalability

### Horizontal Scaling

- **Stateless API:** All state in Redis
- **Load Balancer:** Nginx or cloud LB
- **Multiple Instances:** Docker containers
- **Session Affinity:** Not required (stateless)

### WebSocket Scaling

- **Connection Pooling:** Redis Pub/Sub for broadcasting
- **Sticky Sessions:** Optional for performance
- **Reconnection:** Client-side exponential backoff

### Database Scaling

- **Read Replicas:** PostgreSQL read replicas
- **Connection Pooling:** PgBouncer
- **Cache Layer:** Redis for frequently accessed data

---

## Security Architecture

### Defense in Depth

1. **Network Layer:** TLS/SSL (HTTPS, WSS)
2. **Application Layer:** Auth, rate limiting, validation
3. **Data Layer:** Encrypted at rest, parameterized queries

### Authentication Security

- **Telegram Signature:** HMAC-SHA256 validation
- **JWT Tokens:** HS256, 1-hour expiry
- **Guest Tokens:** Cryptographically secure random
- **Session Storage:** Redis with expiry

### Authorization

- **Permission System:** Role-based access control
- **Resource-Level:** Per-KB, per-task permissions
- **Middleware:** Automatic permission checks

### Rate Limiting

- **Tiered Limits:** Guest vs authenticated
- **Token Bucket:** Redis-based algorithm
- **IP + User:** Combined rate limiting

### Input Validation

- **Pydantic Models:** All requests validated
- **File Upload:** Size and type restrictions
- **XSS Prevention:** Output encoding
- **SQL Injection:** Parameterized queries

---

## Related Documents

- [PRD](./PRD.md)
- [API Specification](./API_SPECIFICATION.md)
- [WebSocket Protocol](./WEBSOCKET_PROTOCOL.md)
- [Authentication](./AUTHENTICATION.md)
- [Deployment](./DEPLOYMENT.md)

---

**Document Version:** 1.0  
**Last Updated:** October 18, 2025

