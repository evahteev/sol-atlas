# Setup & Configuration

The Luka Bot runtime targets Python 3.11+ and depends on Redis, Elasticsearch, and the wider SOL Atlas services when advanced features are enabled. This guide walks through local development setup and highlights configuration knobs for staging and production.

## Prerequisites
- Python 3.11 or newer.
- Redis 7+ (FSM storage and caching).
- Optional but recommended:
  - Elasticsearch 8.x + S3-compatible storage for knowledge base synchronization.
  - Camunda 7 (REST API enabled) for workflow automation.
  - Flow API (FastAPI service) for session management and JWT issuance.
  - Ollama (local LLM inference) if running without OpenAI credentials.

Install system packages:
```bash
# macOS (Homebrew)
brew install redis elasticsearch

# Debian/Ubuntu
sudo apt-get install redis-server
```

## Environment Variables
Copy `.env.example` into `.env` and adjust per environment.

### Core Bot
- `BOT_TOKEN` – Telegram bot token.
- `BOT_NAME`, `RATE_LIMIT`, `DEBUG` – runtime tuning.
- `USE_WEBHOOK`, `WEBHOOK_HOST/PORT/BASE_URL/PATH/SECRET` – enable webhook mode.

### Storage & Cache
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASS`, `REDIS_DATABASE`.
- `ELASTICSEARCH_URL`, `ELASTICSEARCH_AUTH`, `ELASTICSEARCH_CA_PATH` (see `luka_bot/services/elasticsearch_service.py` for supported options).
- `S3_*` – access credentials, bucket, endpoint, and region for attachments.

### Integrations
- `FLOW_API_URL`, `FLOW_API_SYS_KEY` – Flow API lookup and JWT exchange.
- `ENGINE_URL`, `ENGINE_USERNAME`, `ENGINE_PASSWORD`, `ENGINE_USERS_GROUP_ID` – Camunda REST access.
- `DEFAULT_LOCALE`, `AVAILABLE_LOCALES` – i18n defaults (see `core/config.py` for extended options).
- `LUKA_COMMANDS_ENABLED` – comma-separated list of optional commands (`chat`, `tasks`, etc.).
- `OLLAMA_URL`, `OLLAMA_MODEL_NAME`, `OPENAI_API_KEY`, `OPENAI_MODEL_NAME` – LLM providers.
- `SENTRY_DSN`, `AMPLITUDE_API_KEY`, `POSTHOG_API_KEY` – observability integrations.

### Metrics & Ops
- `METRICS_ENABLED`, `METRICS_HOST`, `METRICS_PORT` – Prometheus endpoint configuration.
- `PROMETHEUS_PORT`, `GRAFANA_PORT`, `GRAFANA_ADMIN_*` – docker-compose monitoring stack.

## Local Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Start dependencies
redis-server --daemonize yes                      # or `docker compose up -d redis`
ollama serve                                      # optional, for local LLM usage

# Run Luka Bot in polling mode
python -m luka_bot
```
The bot logs startup milestones (LLM provider availability, middleware registration, metrics server status). Watch for `✅ luka_bot starting...` and `✅ Metrics server started...` messages.

### Docker Compose
Use the reference stack to launch all services:
```bash
docker compose up -d --build
```
Available services after startup:
- `bot` – Luka Bot container (mounts `./luka_bot` for live reload).
- `redis` – Redis cache/FSM storage.
- Optional monitoring containers (commented out by default) for Prometheus/Grafana.

Run Alembic migrations when enabling the admin gateway or other DB-backed components:
```bash
docker compose exec bot alembic upgrade head
```

## Locale Management
Compile locale files whenever strings change:
```bash
pybabel compile -d luka_bot/locales -D messages
```
The Babel configuration lives in `luka_bot/babel.cfg`. Add new languages by creating `<lang>/LC_MESSAGES/messages.po` and recompiling.

## Knowledge Base Setup
1. Configure `ELASTICSEARCH_URL` and S3 credentials.
2. Enable group knowledge indexing via bot settings (`/groups` → “Knowledge Base” toggle).
3. Use `luka_bot/scripts/backfill_group_links.py` or custom scripts to seed historical content.

## Workflow Synchronization
Ensure Camunda definitions are reachable at `ENGINE_URL`. The workflow discovery service caches definitions and toolchains; warm the cache by calling `/processes` handlers or by running:
```python
from luka_bot.services.workflow_service import get_workflow_service
import asyncio

async def main():
    service = get_workflow_service()
    await service.initialize()

asyncio.run(main())
```

Proceed to the [Operations Guide](operations.md) once your environment is bootstrapped.
