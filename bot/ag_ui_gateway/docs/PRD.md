# Product Requirements Document (PRD): AG-UI Gateway API

**Product Name:** Luka Bot AG-UI Gateway API  
**Version:** 1.0  
**Date:** October 18, 2025  
**Status:** Planning Phase  
**Owner:** Engineering Team  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Overview](#product-overview)
3. [Goals & Success Metrics](#goals--success-metrics)
4. [User Personas & Use Cases](#user-personas--use-cases)
5. [Feature Specifications](#feature-specifications)
6. [Technical Requirements](#technical-requirements)
7. [Non-Functional Requirements](#non-functional-requirements)
8. [Success Criteria](#success-criteria)
9. [Out of Scope](#out-of-scope)
10. [Open Questions](#open-questions)

---

## Executive Summary

### Problem Statement

Luka Bot currently operates exclusively through Telegram's Bot API, limiting user access to:
- Users who have Telegram installed
- Chat-based interface only
- No cross-platform accessibility
- Limited discoverability of knowledge bases

### Solution

Build a **REST + WebSocket API Gateway** that:
- Exposes all Luka Bot capabilities via standard web protocols
- Supports web app and Telegram Mini App clients
- Implements AG-UI protocol for standardized agent-UI communication
- Enables knowledge base discovery and promotion
- Maintains feature parity with Telegram bot
- Supports guest mode for anonymous exploration

### Business Value

- **Market Expansion:** Reach users beyond Telegram ecosystem
- **Knowledge Discovery:** Monetize public knowledge bases through exposure
- **Enterprise Adoption:** Web interface for corporate users
- **Multi-Platform:** Same backend serves web, mobile, desktop
- **API-First:** Enable third-party integrations
- **Lower Barrier:** Guest mode increases user acquisition

### Key Metrics

| Metric | Target (3 months) | Target (6 months) |
|--------|------------------|------------------|
| API Uptime | 99.5% | 99.9% |
| Avg Response Time | <200ms | <150ms |
| WebSocket Connection Success | >95% | >98% |
| Daily Active Users (Web) | 100 | 500 |
| Public KB Searches | 1,000/day | 5,000/day |
| Guest → Auth Conversion | >15% | >20% |

---

## Product Overview

### What We're Building

A **FastAPI-based API Gateway** that:

1. **Bridges AG-UI Protocol ↔ Luka Bot Services**
   - Translates AG-UI events to service calls
   - Emits AG-UI events from service responses
   - Maintains bidirectional real-time communication

2. **Authenticates Users**
   - Telegram Mini App signature validation
   - JWT token management
   - Guest mode for anonymous users
   - Flow API integration

3. **Streams LLM Responses**
   - Real-time text streaming
   - Tool execution visibility
   - Progress indicators

4. **Renders Camunda Tasks**
   - Dynamic form generation
   - File upload support
   - Action buttons

5. **Forwards WebSocket Events**
   - Real-time task notifications from Warehouse API
   - Live updates in chat interface

6. **Manages Knowledge Base Catalog**
   - Public/private KB discovery
   - Category organization
   - Search and filtering
   - Quality scoring

7. **Routes Commands to Workflows**
   - Configurable command-to-BPMN mapping
   - Auto-execute or manual triggers
   - Parameter passing

### What We're NOT Building (v1)

- ❌ Native mobile apps (web-responsive only)
- ❌ Custom LLM models (reuse existing Ollama/OpenAI)
- ❌ New Camunda workflows (reuse existing)
- ❌ Separate database (shares Redis, Postgres, ES)
- ❌ Payment processing (future)
- ❌ Admin dashboard (future)
- ❌ Email/password authentication (Telegram only)

### Technical Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Web Framework | FastAPI 0.104+ | Async, WebSocket support, auto docs |
| Protocol | AG-UI + Custom | Standardized + domain-specific |
| Auth | Telegram Mini App + JWT | Secure, no password management |
| WebSocket | websockets 12+ | Native Python async support |
| Validation | Pydantic v2 | Type safety, validation |
| Cache | Redis 7+ | Shared with bot, session cache |
| Logging | Loguru | Consistent with bot |
| Deployment | Docker + Docker Compose | Containerized, easy scaling |

---

## Goals & Success Metrics

### Primary Goals

**Goal 1: Feature Parity**
- ✅ All Telegram bot commands accessible via web
- ✅ Streaming chat with tool execution
- ✅ Task management (inbox, next, waiting, scheduled)
- ✅ Knowledge base search across multiple KBs
- ✅ File upload for task variables
- ✅ Profile management
- ✅ Group management

**Goal 2: Performance**
- ✅ <200ms average API response time
- ✅ <2s for task form rendering
- ✅ <500ms for streaming first token
- ✅ 99.5% uptime

**Goal 3: Security**
- ✅ Telegram Mini App signature validation
- ✅ JWT token expiry and refresh
- ✅ Rate limiting per user
- ✅ Access control for private KBs

**Goal 4: User Acquisition**
- ✅ Guest mode for anonymous browsing
- ✅ Public KB catalog for SEO
- ✅ >15% guest → authenticated conversion

### Success Metrics

**Adoption Metrics:**
- Weekly Active Users (Web): 50+ (Month 1), 200+ (Month 3)
- Web vs Telegram Ratio: 10% web usage
- Session Duration: >5 minutes average
- Return Rate: >40% week-over-week
- Guest Sessions: 200+/week
- Guest Conversion: >15%

**Performance Metrics:**
- P50 Response Time: <150ms
- P95 Response Time: <500ms
- P99 Response Time: <1000ms
- WebSocket Connection Success: >95%
- WebSocket Reconnection Time: <5s

**Quality Metrics:**
- Error Rate: <1%
- Client-side Error Rate: <2%
- Support Tickets Related to API: <5/week

---

## User Personas & Use Cases

### Primary Persona: "Power User Pavel"

**Demographics:**
- Age: 28-35
- Tech-savvy, uses multiple devices daily
- Active in 5-10 crypto/tech communities

**Needs:**
- Quick access from desktop browser (no Telegram app needed)
- Search across multiple group KBs simultaneously
- Manage workflows from web interface
- Share KB links with colleagues

**Use Cases:**
1. Browse public KB catalog → search for "DeFi tutorials"
2. Open web app during work hours (Telegram blocked at office)
3. Execute `/tasks` command → complete forms inline
4. Upload documents for task completion
5. Try as guest → convert to authenticated user

### Secondary Persona: "Community Manager Carlos"

**Demographics:**
- Age: 30-40
- Manages 3-5 Telegram communities
- Needs analytics and visibility

**Needs:**
- Promote group knowledge bases publicly
- Monitor KB search activity
- Manage group settings from web
- Export group statistics

**Use Cases:**
1. Set group KB to "public" visibility
2. Add categories and tags to KB
3. View KB search analytics dashboard
4. Share KB catalog link for promotion

### Tertiary Persona: "Guest User Gina"

**Demographics:**
- Age: 25-45
- Exploring knowledge resources
- Not yet committed to sign-up

**Needs:**
- Browse public knowledge without commitment
- Try chat functionality before authenticating
- See value before sign-up

**Use Cases:**
1. Land on catalog page from Google
2. Search public KB without account
3. Try 5-10 chat messages with AI
4. See upgrade prompts → convert to authenticated

---

## Feature Specifications

### 1. Authentication & Authorization

**1.1 Telegram Mini App Authentication**
- Validate Telegram initData signature (HMAC-SHA256)
- Extract user information from signed data
- Fetch user from Flow API
- Generate JWT token (1-hour expiry)
- Store session in Redis
- Support token refresh

**1.2 Guest Mode**
- Generate anonymous guest tokens
- Allow public KB browsing without auth
- Allow limited chat (20 messages)
- Show upgrade prompts contextually
- Track guest → authenticated conversion

**1.3 Permission System**
- Role-based access control
- Per-resource permissions (KB, tasks, profile)
- Guest vs authenticated capabilities matrix
- Owner/member/collaborator roles for KBs

### 2. Knowledge Base Catalog

**2.1 Catalog Browsing**
- List public KBs with pagination
- Filter by category (crypto, tech, gaming, etc.)
- Filter by visibility (public/private/unlisted)
- Filter by status (enabled/disabled/indexing)
- Featured KB promotion
- Search by name/description

**2.2 KB Details**
- View KB metadata (name, description, stats)
- Sample messages preview
- Contributor count
- Search activity
- Quality score
- Access control display

**2.3 KB Management (Owners)**
- Update visibility (public/private/unlisted)
- Edit metadata (description, categories, tags)
- View analytics
- Manage collaborators

### 3. Chat & LLM Streaming

**3.1 Chat Interface**
- WebSocket-based real-time chat
- Streaming LLM responses (AG-UI protocol)
- Thread management (authenticated only)
- Tool execution visibility
- Ephemeral chat for guests

**3.2 Tool Execution**
- KB search during chat
- YouTube transcript extraction
- Support ticket creation
- Real-time tool status updates

**3.3 Command Routing**
- Command-to-workflow mapping
- Auto-execute vs manual workflows
- Parameter passing to workflows

### 4. Workflows & Tasks

**4.1 Task Management**
- List user tasks (inbox, next, waiting, scheduled)
- Real-time task notifications via WebSocket
- Task form rendering (text, file, action buttons)
- File upload for task variables
- Task completion with variables

**4.2 Workflow Execution**
- Start BPMN processes via commands
- Pass variables to workflows
- Track process instances
- View active workflows in profile

**4.3 Start Forms**
- Render start forms before workflow execution
- Variable collection dialog
- Confirmation before execution

### 5. Profile & Settings

**5.1 User Profile**
- View statistics (messages, tasks, groups)
- Active workflows display
- Language preference
- LLM provider/model settings

**5.2 Settings Management**
- Change interface language
- Select LLM provider (Ollama/OpenAI)
- Select LLM model
- Notification preferences

### 6. File Uploads

**6.1 Task File Upload**
- Upload files for S3 task variables
- Size limit: 20MB
- Progress tracking
- MIME type validation
- UUID-based naming

**6.2 Chat Attachments (Future)**
- Send files in chat
- Image preview
- Document sharing

---

## Technical Requirements

### API Endpoints

See [API_SPECIFICATION.md](./API_SPECIFICATION.md) for complete details.

**Authentication:**
- `POST /api/auth/telegram-miniapp` - Authenticate via Telegram
- `POST /api/auth/guest` - Create guest session
- `POST /api/auth/refresh` - Refresh JWT token

**Catalog:**
- `GET /api/catalog` - List KBs with filters
- `GET /api/kb/{kb_id}` - KB details
- `PATCH /api/kb/{kb_id}` - Update KB metadata

**Profile:**
- `GET /api/profile` - User profile
- `PATCH /api/profile/settings` - Update settings

**Files:**
- `POST /api/files/upload` - Upload file

**Commands:**
- `POST /api/commands/{command}` - Execute command

**WebSocket:**
- `/ws/chat` - AG-UI protocol chat
- `/ws/tasks` - Task notifications

### WebSocket Protocol

See [WEBSOCKET_PROTOCOL.md](./WEBSOCKET_PROTOCOL.md) for complete details.

**Client → Server Events:**
- `auth` - Authentication
- `user_message` - Chat message
- `command` - Execute command
- `form_submit` - Submit form
- `search_kb` - Search KB

**Server → Client Events:**
- `auth_success` - Auth completed
- `textStreamDelta` - Streaming text
- `toolInvocation` - Tool started
- `toolResult` - Tool completed
- `formRequest` - Render form
- `stateUpdate` - Agent state change
- `taskNotification` - Task event
- `error` - Error occurred

### Data Models

See [DATA_MODELS.md](./DATA_MODELS.md) for complete schemas.

**Core Models:**
- `KnowledgeBase` - KB metadata
- `AuthResponse` - Authentication response
- `FormData` - Task/start form data
- `AgUiEvent` - WebSocket event base
- `Permission` - Permission enum

### Rate Limiting

**Guest Tier:**
- 20 req/min for catalog
- 30 req/min for KB details
- 10 req/min for search
- 10 msg/min for chat (20 total)

**Authenticated Tier:**
- 60 req/min for catalog
- 120 req/min for KB details
- 30 req/min for search
- 30 msg/min for chat (unlimited)

### Security

**Telegram Signature Validation:**
- HMAC-SHA256 with bot token as secret
- Verify auth_date within 5 minutes
- Validate hash against computed signature

**JWT Security:**
- HS256 algorithm
- 1-hour expiry
- Stored in Redis with user_id mapping
- Refresh mechanism

**CORS:**
- Allow origins: web domain, t.me
- Allow credentials: true
- Allow methods: all
- Allow headers: all

**Input Validation:**
- Pydantic models for all requests
- File size limits (20MB)
- MIME type whitelist
- XSS prevention (sanitize HTML)

---

## Non-Functional Requirements

### Performance

- API response time P95 < 500ms
- WebSocket message delivery < 100ms
- Task form rendering < 2s
- File upload throughput > 5MB/s
- Support 1000 concurrent WebSocket connections

### Scalability

- Horizontal scaling via Docker containers
- Stateless API (session in Redis)
- WebSocket connection pooling
- Database connection pooling

### Reliability

- 99.5% uptime target
- Automatic reconnection for WebSocket
- Graceful degradation if services unavailable
- Circuit breaker for external APIs

### Observability

- Prometheus metrics export
- Structured logging with Loguru
- Health check endpoints
- Error tracking with Sentry (optional)

### Security

- Rate limiting per user and IP
- DDoS protection via Nginx
- SQL injection prevention (parameterized queries)
- XSS prevention (output encoding)
- CSRF protection (JWT tokens)

---

## Success Criteria

### Launch Criteria (v1.0)
- [ ] All Telegram bot features accessible via web
- [ ] <200ms P95 API response time
- [ ] 99.5% uptime over 7 days
- [ ] 10+ beta users successfully complete tasks
- [ ] No critical security vulnerabilities
- [ ] Documentation complete (API docs, user guide)
- [ ] Guest mode functional with conversion tracking

### Post-Launch (Month 1)
- [ ] 50+ weekly active users
- [ ] <1% error rate
- [ ] 100+ KB searches per day
- [ ] <5 support tickets related to API
- [ ] 200+ guest sessions
- [ ] >15% guest conversion rate

### Post-Launch (Month 3)
- [ ] 200+ weekly active users
- [ ] 99.9% uptime
- [ ] 1000+ KB searches per day
- [ ] 10% web vs Telegram ratio
- [ ] 5 public KB owners promoting their catalogs

---

## Out of Scope

**v1.0 will NOT include:**
- Native mobile apps (iOS/Android)
- Email/password authentication
- Payment processing for premium KBs
- Admin dashboard
- Custom LLM training
- Voice message support
- Video message support
- Multi-user collaboration in real-time
- KB subscription/notification system
- GraphQL API
- Webhook support for third-party integrations

**Future Considerations:**
- Premium KB monetization (Phase 2)
- Admin analytics dashboard (Phase 2)
- Email notifications (Phase 3)
- Mobile apps (Phase 3)
- Public API for third-party developers (Phase 4)

---

## Open Questions

### Technical Decisions

**Q1: Should we support polling as fallback to WebSocket?**
- **Decision:** Start with WebSocket only, add polling if needed

**Q2: Should we cache catalog in Redis or query DB every time?**
- **Decision:** Cache in Redis with 5-minute TTL

**Q3: Should we support GraphQL instead of REST?**
- **Decision:** REST for v1, evaluate GraphQL later

### Product Decisions

**Q1: Should public KBs be searchable without authentication?**
- **Decision:** Require guest token (anonymous) for basic rate limiting

**Q2: Should we support KB subscriptions (notifications)?**
- **Decision:** Not in v1, add in Phase 6

**Q3: Should we allow KB owners to monetize (paid access)?**
- **Decision:** Not in v1, design for extensibility

### Business Questions

**Q1: What's the pricing model for premium features?**
- **TBD:** Define in Phase 2 after user validation

**Q2: How do we handle GDPR/data privacy for EU users?**
- **TBD:** Legal review required

**Q3: What's the support model for API users?**
- **TBD:** Community Discord + docs for v1

---

## Appendices

### A. Related Documents

- [API Specification](./API_SPECIFICATION.md)
- [WebSocket Protocol](./WEBSOCKET_PROTOCOL.md)
- [Architecture](./ARCHITECTURE.md)
- [Authentication](./AUTHENTICATION.md)
- [Guest Mode](./GUEST_MODE.md)
- [Data Models](./DATA_MODELS.md)
- [Implementation Roadmap](./IMPLEMENTATION_ROADMAP.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Testing Strategy](./TESTING_STRATEGY.md)

### B. Glossary

- **AG-UI:** Agent-User Interaction protocol for standardized agent-UI communication
- **KB:** Knowledge Base (Elasticsearch index with group/user messages)
- **Flow API:** Authentication backend providing JWT tokens and user data
- **Warehouse API:** WebSocket service for real-time task notifications
- **Camunda:** BPMN workflow engine for process orchestration
- **JWT:** JSON Web Token for authentication
- **initData:** Signed data from Telegram Mini App containing user info

---

**Document Status:** Draft → Review → Approved  
**Last Updated:** October 18, 2025  
**Next Review:** After Phase 1 implementation

