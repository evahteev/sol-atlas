# AG-UI Gateway API

> REST + WebSocket API Gateway for Luka Bot with AG-UI protocol support

**Version:** 1.0.0  
**Status:** Development  

---

## Overview

The AG-UI Gateway exposes all Luka Bot capabilities via standard web protocols, enabling web applications and Telegram Mini Apps to interact with the bot's LLM, workflows, tasks, and knowledge bases.

### Key Features

- **🔐 Authentication:** Telegram Mini App auth + Guest mode
- **💬 Real-time Chat:** WebSocket with LLM streaming
- **🛠️ Tool Execution:** Visible RAG search and tool invocations
- **📋 Task Management:** Camunda workflow task rendering as forms
- **📚 Knowledge Base Catalog:** Public/private KB discovery
- **👤 Profile Management:** User settings and preferences
- **📁 File Upload:** S3/R2 integration for attachments
- **🎯 Command Routing:** Commands → Optional BPMN workflows

### Architecture

```
Client (Web/Mini App)
    ↓
AG-UI Gateway (FastAPI)
    ↓
Luka Bot Services (Reused)
    ↓
Infrastructure (Redis, Postgres, ES, Camunda)
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for frontend development)

### Installation

1. **Clone repository:**
   ```bash
   cd /path/to/dexguru/bot/ag_ui_gateway
   ```

2. **Copy environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Check health:**
   ```bash
   curl http://localhost:8000/health
   ```

5. **View API docs:**
   - OpenAPI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Development Setup

#### Backend

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run development server:**
   ```bash
   # Make sure you're in the parent 'bot' directory so luka_bot is accessible
   cd /path/to/dexguru/bot
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   uvicorn ag_ui_gateway.ag_ui_gateway.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Run tests:**
   ```bash
   pytest ag_ui_gateway/tests/ -v --cov
   ```

#### Frontend

1. **Navigate to web_app:**
   ```bash
   cd web_app
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run development server:**
   ```bash
   npm run dev  # Runs on port 3000 with proxy
   ```

4. **Build for production:**
   ```bash
   npm run build  # Creates dist/ folder
   ```

#### Full Stack Development

Run both servers simultaneously:

```bash
# Terminal 1 - Backend (from parent bot directory)
cd /path/to/dexguru/bot
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
source ag_ui_gateway/venv/bin/activate
uvicorn ag_ui_gateway.ag_ui_gateway.main:app --reload --port 8000

# Terminal 2 - Frontend  
cd ag_ui_gateway/web_app && npm run dev
```

Open http://localhost:3000 in browser (proxies API calls to :8000)

---

## Project Structure

```
ag_ui_gateway/
├── docs/                          # Documentation
│   ├── PRD.md                     # Product requirements
│   ├── API_SPECIFICATION.md       # REST API reference
│   ├── WEBSOCKET_PROTOCOL.md      # WebSocket events
│   ├── ARCHITECTURE.md            # System architecture
│   ├── AUTHENTICATION.md          # Auth flows
│   ├── GUEST_MODE.md              # Guest mode spec
│   ├── DATA_MODELS.md             # Pydantic schemas
│   ├── FRONTEND_INTEGRATION.md    # Frontend setup & serving
│   ├── IMPLEMENTATION_ROADMAP.md  # Development plan
│   ├── DEPLOYMENT.md              # Deployment guide
│   └── TESTING_STRATEGY.md        # Testing approach
├── web_app/                       # React Frontend (port 3000)
│   ├── public/                    # Static assets
│   ├── src/
│   │   ├── components/            # UI components
│   │   ├── pages/                 # Page components (Home, Catalog, Chat)
│   │   ├── services/              # API & WebSocket clients
│   │   ├── hooks/                 # Custom React hooks
│   │   └── App.tsx                # Main app
│   ├── package.json               # Node dependencies
│   ├── vite.config.ts             # Vite configuration (dev proxy)
│   └── Dockerfile                 # Frontend container (nginx)
├── ag_ui_gateway/                 # Backend API (port 8000)
│   ├── main.py                    # FastAPI app
│   ├── api/                       # REST endpoints
│   │   ├── auth.py                # Authentication
│   │   ├── catalog.py             # KB catalog
│   │   ├── profile.py             # User profile
│   │   ├── files.py               # File upload
│   │   └── health.py              # Health checks
│   ├── websocket/                 # WebSocket handlers
│   │   └── chat.py                # AG-UI chat
│   ├── adapters/                  # Service adapters
│   │   ├── llm_adapter.py         # LLM → AG-UI events
│   │   ├── task_adapter.py        # Task → forms
│   │   ├── catalog_adapter.py     # KB catalog
│   │   ├── command_adapter.py     # Command routing
│   │   └── profile_adapter.py     # Profile management
│   ├── auth/                      # Authentication
│   │   ├── tokens.py              # Token management
│   │   ├── telegram_miniapp.py    # Telegram auth
│   │   ├── flow_auth.py           # Flow API integration
│   │   └── permissions.py         # Permission system
│   ├── protocol/                  # AG-UI protocol
│   │   ├── events.py              # Event models
│   │   ├── dispatcher.py          # Event dispatcher
│   │   └── handler.py             # Message handler
│   ├── models/                    # Pydantic models
│   │   ├── api_models.py          # API schemas
│   │   ├── websocket_models.py    # WebSocket events
│   │   └── kb_models.py           # KB models
│   ├── middleware/                # Middleware
│   │   ├── rate_limit.py          # Rate limiting
│   │   └── auth_middleware.py     # Auth injection
│   ├── config/                    # Configuration
│   │   ├── settings.py            # Pydantic settings
│   │   └── commands.py            # Command mapping
│   └── monitoring/                # Observability
│       ├── metrics.py             # Prometheus metrics
│       └── logging_config.py      # Loguru config
├── tests/                         # Test suite
│   ├── test_auth.py
│   ├── test_catalog.py
│   └── integration/
├── pyproject.toml                 # Poetry config
├── Dockerfile                     # Docker build
├── docker-compose.yml             # Local development
├── .env.example                   # Environment template
└── README.md                      # This file
```

---

## API Endpoints

### Authentication

- `POST /api/auth/telegram-miniapp` - Authenticate via Telegram
- `POST /api/auth/guest` - Create guest session
- `POST /api/auth/refresh` - Refresh JWT token

### Catalog

- `GET /api/catalog` - List knowledge bases
- `GET /api/kb/{kb_id}` - KB details
- `PATCH /api/kb/{kb_id}` - Update KB metadata

### Profile

- `GET /api/profile` - User profile
- `PATCH /api/profile/settings` - Update settings

### Files

- `POST /api/files/upload` - Upload file

### Health

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### WebSocket

- `/ws/chat` - AG-UI protocol chat

**Full API documentation:** [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md)

---

## WebSocket Protocol

### Client → Server Events

- `auth` - Authentication
- `user_message` - Chat message
- `command` - Execute command
- `form_submit` - Submit form
- `search_kb` - Search KB

### Server → Client Events

- `auth_success` - Auth completed
- `textStreamDelta` - Streaming text
- `toolInvocation` - Tool started
- `toolResult` - Tool completed
- `formRequest` - Render form
- `stateUpdate` - State change
- `taskNotification` - Task event
- `error` - Error occurred

**Full protocol documentation:** [docs/WEBSOCKET_PROTOCOL.md](docs/WEBSOCKET_PROTOCOL.md)

---

## Environment Variables

See `.env.example` for all available configuration options.

### Required

- `BOT_TOKEN` - Telegram bot token
- `AUTHJWT_SECRET_KEY` - JWT signing secret (min 32 chars, reuses luka_bot's auth key)
- `POSTGRES_PASSWORD` - Database password (optional, only if POSTGRES_ENABLED=True)
- `FLOW_API_URL` - Flow API endpoint
- `WAREHOUSE_WS_URL` - Warehouse WebSocket URL

### Optional

- `DEBUG` - Enable debug mode (default: true)
- `ALLOWED_ORIGINS` - CORS origins (default: localhost + t.me)
- `LOG_LEVEL` - Logging level (default: INFO)

---

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# All tests
pytest ag_ui_gateway/tests/

# With coverage
pytest ag_ui_gateway/tests/ --cov=ag_ui_gateway

# Specific test
pytest ag_ui_gateway/tests/test_auth.py -v
```

### Code Quality

```bash
# Activate virtual environment
source venv/bin/activate

# Format code
black ag_ui_gateway/

# Lint
ruff check ag_ui_gateway/

# Type checking
mypy ag_ui_gateway/
```

### Database Migrations

```bash
# (If using Alembic)
poetry run alembic upgrade head
```

---

## Deployment

### Docker

**Important:** Docker builds from parent directory to include `luka_bot`:

```bash
# Use the build script (recommended)
./build.sh

# Or build manually from parent directory
cd /path/to/dexguru/bot
docker build -f ag_ui_gateway/Dockerfile -t ag-ui-gateway:latest .

# Run container
docker run -p 8000:8000 --env-file ag_ui_gateway/.env ag-ui-gateway:latest
```

### Docker Compose

```bash
# Start services (builds from parent context automatically)
cd ag_ui_gateway
docker-compose up -d

# View logs
docker-compose logs -f ag_ui_gateway

# Stop services
docker-compose down
```

### Production

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for:
- Nginx reverse proxy configuration
- SSL/TLS setup
- Monitoring & health checks
- Horizontal scaling

---

## Documentation

### Core Documents

- **[PRD](docs/PRD.md)** - Product requirements and goals
- **[API Specification](docs/API_SPECIFICATION.md)** - REST API reference
- **[WebSocket Protocol](docs/WEBSOCKET_PROTOCOL.md)** - WebSocket event schemas
- **[Architecture](docs/ARCHITECTURE.md)** - System design
- **[Authentication](docs/AUTHENTICATION.md)** - Auth flows and security

### Additional Guides

- **[Guest Mode](docs/GUEST_MODE.md)** - Anonymous browsing
- **[Data Models](docs/DATA_MODELS.md)** - Pydantic schemas
- **[Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)** - Development plan
- **[Deployment](docs/DEPLOYMENT.md)** - Deployment guide
- **[Testing Strategy](docs/TESTING_STRATEGY.md)** - Testing approach

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | 0.104+ |
| Server | Uvicorn | 0.24+ |
| WebSocket | websockets | 12+ |
| Validation | Pydantic | 2.4+ |
| Auth | python-jose | 3.3+ |
| HTTP Client | httpx | 0.25+ |
| Cache | Redis | 7+ |
| Database | PostgreSQL | 15+ |
| Logging | Loguru | 0.7+ |
| Metrics | Prometheus | - |

---

## Contributing

### Development Workflow

1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Run quality checks
6. Submit pull request

### Code Style

- Follow PEP 8
- Use Black for formatting
- Type hints required
- Docstrings for public APIs

---

## License

See [LICENSE.md](../LICENSE.md)

---

## Support

- **Documentation:** [docs/](docs/)
- **Issues:** GitHub Issues
- **Discord:** Community Discord channel

---

## Roadmap

### Phase 1: Foundation (Weeks 1-3)
- ✅ Authentication (Telegram + Guest)
- ✅ Basic chat with streaming
- ✅ WebSocket connection

### Phase 2: Commands (Weeks 4-5)
- ⏳ Command routing
- ⏳ Profile management
- ⏳ Settings

### Phase 3: Workflows (Weeks 6-8)
- ⏳ Task rendering
- ⏳ Form handling
- ⏳ File upload

### Phase 4: Tools (Weeks 9-10)
- ⏳ Tool execution visibility
- ⏳ KB search integration

### Phase 5: Catalog (Weeks 11-12)
- ⏳ KB catalog
- ⏳ Group management

### Phase 6: Launch (Weeks 13-14)
- ⏳ Performance optimization
- ⏳ Security audit
- ⏳ Production deployment

**Full roadmap:** [docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md)

---

**Built with ❤️ by the Luka Bot Team**

