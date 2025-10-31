# luka_bot - Standalone Production Telegram Bot

**Status:** Phase 1 Foundation Complete ✅  
**Architecture:** Completely independent from `bot_server` (no imports)

## Overview

luka_bot is a **production-ready Telegram bot** built from scratch using patterns validated in `bot_server/`. It's completely standalone - no dependencies on bot_server code.

### Why Standalone?

- ✅ **Production Ready:** Independent deployment and versioning
- ✅ **Clean Architecture:** Only what's needed, no legacy code
- ✅ **Maintainable:** Clear separation of concerns
- ✅ **Testable:** Isolated unit and integration tests

## Current Status (Phase 1)

### What Works Now ✅

```
✅ Bot startup and shutdown
✅ Redis FSM storage  
✅ I18n (en, ru, uk locales compiled)
✅ /start command with welcome message
✅ Echo handler (placeholder for LLM)
✅ Logging with loguru
✅ Polling mode
```

### Architecture

```
llm_bot/
├── __main__.py              # Entry point (standalone)
├── core/
│   ├── config.py            # Settings (pydantic)
│   └── loader.py            # Bot, dp, redis, i18n
├── handlers/
│   ├── __init__.py          # Router registration
│   ├── start.py             # /start command
│   └── echo.py              # Echo handler
└── locales/
    ├── en/LC_MESSAGES/
    ├── ru/LC_MESSAGES/
    └── uk/LC_MESSAGES/
```

## Setup

### Prerequisites

```bash
# Redis (for FSM state storage)
redis-server

# Python 3.11+
python --version
```

### Configuration

Create `.env` file:

```bash
# Required
BOT_TOKEN=your_telegram_bot_token_here

# Optional (with defaults)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DATABASE=0

# Future phases
ENGINE_URL=http://localhost:8080/engine-rest  # Camunda
OLLAMA_URL=http://localhost:11434             # LLM
FLOW_API_URL=http://localhost:8000            # User auth
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Compile locales (already done)
python -m babel.messages.frontend compile -d luka_bot/locales -D messages

# Run bot
python -m luka_bot
```

## Usage

### Basic Commands

```
/start - Welcome message with Phase 1 status
[any text] - Echo handler (Phase 2 will add LLM)
```

### Testing Locally

```bash
# Start Redis
redis-server

# Run bot
python -m luka_bot

# In Telegram:
# 1. Find your bot (@YourBotName)
# 2. Send: /start
# 3. Send: Hello!
# Expected: Echo response
```

## Development Phases

### Phase 1: Foundation ✅ (Current)

**Goal:** Minimal working bot, completely standalone

- [x] Core infrastructure (config, loader, bot, dp)
- [x] Locales (i18n) compiled
- [x] /start handler
- [x] Echo handler
- [x] Logging
- [x] Redis FSM storage
- [ ] Update documentation

**Lines of code:** ~200  
**Time:** 1 hour

### Phase 2: LLM Streaming (Next)

**Goal:** Basic LLM conversations without threads

**To Copy from bot_server:**
- `services/ollama_client.py` → `llm_bot/services/llm_service.py`
- Adapt streaming logic (simpler, no tools yet)

**New Handlers:**
- Replace echo.py with `streaming_dm.py`
- Add typing indicator

**Estimate:** ~300 lines, 2 hours

### Phase 3: Thread Management

**Goal:** Multiple conversation threads per user

**To Copy/Adapt:**
- `services/context_resolution_service.py` (simplified)
- Thread metadata storage (Redis only, no Camunda yet)

**New Handlers:**
- `/chats` - List threads
- Thread creation/switching
- Thread-scoped context

**Estimate:** ~400 lines, 3 hours

### Phase 4: Camunda Integration

**Goal:** Workflow-driven dialogs

**To Copy/Adapt:**
- Camunda client from `camunda_client/`
- `services/camunda.py` (minimal subset)
- Process instance management

**Estimate:** ~500 lines, 3-4 hours

### Phase 5: Tools & Knowledge Base

**To Copy/Adapt:**
- KB search tool
- Tool execution framework
- YouTube tools

**Estimate:** ~600 lines, 4 hours

### Phase 6-8: Advanced Features

- Onboarding & GURU credits
- Group support
- Voice messages
- Observability & production hardening

## Key Differences from bot_server

### What We're NOT Copying

- ❌ Legacy menu systems
- ❌ Complex service locator pattern (too heavy for MVP)
- ❌ Excessive abstractions
- ❌ Deprecated MindsDB code
- ❌ Warehouse WebSocket (not needed)

### What We're Copying & Simplifying

- ✅ Ollama client → Simple LLM service
- ✅ Streaming logic → Cleaner implementation
- ✅ Context resolution → Redis-first approach
- ✅ Camunda client → Minimal wrapper
- ✅ Thread management → Simpler data model

### Design Principles

1. **YAGNI:** Only implement what Phase needs
2. **Simplicity:** Prefer simple over clever
3. **Testability:** Easy to unit test
4. **Observability:** Log everything clearly
5. **Independence:** Zero bot_server imports

## Configuration Reference

### Environment Variables

```bash
# Bot
BOT_TOKEN=           # Telegram bot token (required)
BOT_NAME=luka_bot     # Bot display name
DEBUG=false          # Debug mode

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASS=          # Optional password
REDIS_DATABASE=0

# Camunda (Phase 4+)
ENGINE_URL=http://localhost:8080/engine-rest
ENGINE_USERNAME=demo
ENGINE_PASSWORD=demo

# LLM (Phase 2+)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL_NAME=llama3.2
OLLAMA_TIMEOUT=60

# Flow API (Phase 3+)
FLOW_API_URL=http://localhost:8000
FLOW_API_SYS_KEY=secret
FLOW_API_JWT_SECRET=your-secret-key-here

# Webhook (Phase 8)
USE_WEBHOOK=false
WEBHOOK_BASE_URL=https://example.ngrok-free.app
WEBHOOK_PATH=/webhook
WEBHOOK_SECRET=change-me
```

## Troubleshooting

### Bot doesn't start

```bash
# Check Redis
redis-cli ping
# Should return: PONG

# Check BOT_TOKEN in .env
cat .env | grep BOT_TOKEN

# Check Python version
python --version
# Should be 3.11+
```

### Locale compilation errors

```bash
# Recompile locales
cd luka_bot
python -m babel.messages.frontend compile -d locales -D messages
```

### "Module not found" errors

```bash
# Install dependencies
pip install -r requirements.txt

# Check you're in project root
pwd
# Should end with: .../bot
```

## Contributing

### Adding a New Handler

1. Create handler file in `llm_bot/handlers/`
2. Import and register in `handlers/__init__.py`
3. Test with `/start` to verify routing

### Adding a New Service

1. Create service file in `llm_bot/services/`
2. Keep it simple - single responsibility
3. Add comprehensive logging
4. No global state

### Code Style

- **Logging:** Use emoji prefixes (👋 🚀 ✅ ❌ 💬)
- **Naming:** Clear, descriptive names
- **Docstrings:** Every function/class
- **Type hints:** Always use them

## Next Steps

1. ✅ **Phase 1 Complete:** Foundation is solid
2. 🔄 **Phase 2 Starting:** Copy LLM streaming service
3. 📋 **Document:** Update IMPLEMENTATION_STATUS.md

## License

See LICENSE.md in project root.

---

**Built from scratch, inspired by bot_server patterns** 🚀
