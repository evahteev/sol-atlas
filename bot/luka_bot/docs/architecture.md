# Architecture

Luka Bot follows a layered architecture that separates transport concerns (Aiogram handlers), domain logic (singleton services), and infrastructure adapters. The design keeps the Telegram runtime stateless where possible while delegating long-lived state to Redis, Elasticsearch, Camunda, and Atlas platform services.

## System Context
```
┌────────────────────┐             ┌────────────────────────┐
│   Telegram Users   │◄────────────┤     Luka Bot (DM)      │
└────────────────────┘             └──────────┬─────────────┘
                                               │
┌────────────────────┐             ┌───────────▼────────────┐
│  Telegram Groups   │◄────────────┤   Luka Bot (Groups)    │
└────────────────────┘             └───────────┬────────────┘
                                               │
                      SOL Atlas Core Services  │
                                               ▼
┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│  Flow API (FastAPI)│  │ Camunda 7 BPM Engine│  │ Atlas UI Gateway   │
└────────────────────┘  └────────────────────┘  └────────────────────┘
           │                     │                      │
┌──────────▼────────┐  ┌─────────▼────────┐  ┌──────────▼─────────┐
│ Redis / Postgres  │  │ Elasticsearch/S3 │  │ Observability Stack │
└───────────────────┘  └──────────────────┘  └─────────────────────┘
```

## Internal Layout
- **Core** (`luka_bot/core/`) – configuration, application bootstrap, dependency wiring for bot, dispatcher, Redis FSM, and i18n.
- **Handlers** (`luka_bot/handlers/`) – Aiogram routers organized by domain (DM threads, groups, moderation, search, workflow processes, metrics). Each handler delegates to services and utilities.
- **Middlewares** (`luka_bot/middlewares/`) – authentication (Flow API JWT), password gating, form routing, localization, and Prometheus instrumentation.
- **Services** (`luka_bot/services/`) – singleton services implementing business logic: LLM provider fallback, thread storage, moderation, workflow orchestration, knowledge ingestion, S3 uploads, messaging helpers, and Camunda/Flow integrations.
- **Agents** (`luka_bot/agents/`) – prompt templates and agent configurations for specialized LLM personas.
- **Models & Schemas** (`luka_bot/models/`, `luka_bot/schemas/`) – shared dataclasses and Pydantic models for configuration, knowledge entries, and workflow payloads.
- **Scripts** (`luka_bot/scripts/`) – maintenance utilities, e.g., backfilling knowledge graph data.

## Message Flow
1. **Inbound update** arrives via Telegram polling/webhook and enters the dispatcher.
2. **Middlewares** enrich the update (Flow API session, language, password gate) and emit Prometheus metrics.
3. The appropriate **handler router** executes, matching commands, inline callbacks, or free-text messages.
4. Handlers call **services**, which coordinate Redis state, workflow status, moderation decisions, and LLM interactions.
5. **LLM service** uses the provider fallback to choose Ollama or OpenAI, augments prompts with RAG snippets through Elasticsearch, and streams responses back to handlers.
6. Outgoing messages are formatted by the **messaging service**, which also updates reply trackers for retrospective moderation.

## State & Storage
- **Redis** – FSM state, thread metadata, transient moderation flags, reply trackers.
- **Elasticsearch + S3** – knowledge base documents, embeddings, uploaded files, and long-form summaries.
- **Camunda** – workflow definitions, form schemas, and task state; accessed via REST through `camunda_client/`.
- **Flow API** – user profiles, session tokens, task updates; Luka obtains JWT tokens using `flow_client/`.
- **Postgres** – primarily used by `ag_ui_gateway` and Flow API; Luka interacts indirectly via APIs.

## Observability & Reliability
- **Prometheus middleware** exposes `/metrics` with handler timings, LLM latency, and queue depth.
- **Loguru** provides structured logging; configure sinks via environment variables or container logging drivers.
- **Sentry** hooks (optional) capture runtime exceptions when `SENTRY_DSN` is configured.
- **Provider Fallback** caches provider health to fail over from Ollama to OpenAI with minimal downtime.

## Extensibility
- Register new handlers in `handlers/__init__.py` or expose them via feature flags in `settings.LUKA_COMMANDS_ENABLED`.
- Add custom tools by extending services (e.g., implement a new knowledge source) and exposing commands or inline UI.
- Integrate additional workflows by synchronizing BPMN definitions through `workflow_discovery_service` and adding user-facing entrypoints.
