# SOL Atlas Luka Bot

Luka Bot is the conversational agent that powers the SOL Atlas ecosystem. It delivers LLM-assisted workflows, knowledge base search, and group operations for Discord and Telegram communities while integrating with the rest of the SOL Atlas stack (Camunda process automation, Flow API, and the Atlas UI gateway).

## Core Capabilities
- Streaming conversations with provider failover (Ollama → OpenAI) and thread persistence.
- Knowledge-base ingestion and retrieval backed by Elasticsearch and S3 media storage.
- Group management with reputation, moderation toggles, and localized onboarding.
- Workflow execution through Camunda BPM and Flow API real-time task updates.
- Observability via Prometheus metrics, structured Loguru logging, and Sentry hooks.

## Repository Structure
- `luka_bot/` – production Telegram agent (handlers, services, middlewares, locales, scripts, docs).
- `ag_ui_gateway/` – Flask-based admin and Atlas web gateway for operators.
- `flow_client/`, `camunda_client/` – shared protocol and client libraries used by the bot and UI.
- `docker-compose.yml`, `Dockerfile`, `.env.example` – reference infrastructure for local and staging environments.
- `AGENTS.md` – contributor guidelines for agents and supporting services.

## Quick Start
```bash
# Python 3.11+
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # populate tokens and service URLs
python -m luka_bot          # starts Luka Bot in polling mode
```

Optional services:
- `docker compose up -d redis` – Redis for FSM storage (required).
- `docker compose up -d elasticsearch` – enable KB indexing/search.
- `docker compose up -d` – bring up the full stack (bot, Redis, monitoring scaffolding).

## Documentation
- Updated guides live in `luka_bot/docs/` (start with `README.md` for the table of contents).
- Deployment, operations, and API notes are organized by topic; legacy notes remain under `luka_bot/docs/archive/`.
- For contributor workflow and coding conventions, see `AGENTS.md`.

## License
Released under the LGPL-3.0 license (`LICENSE.md`). Contributions are welcome—open an issue or follow the workflow described in `AGENTS.md`.
