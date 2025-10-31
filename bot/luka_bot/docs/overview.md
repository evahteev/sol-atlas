# Overview

Luka Bot is the conversational automation layer inside SOL Atlas. It bridges LLM-powered assistance with the operational tooling that keeps Atlas communities healthy—surfacing knowledge, routing work to BPM workflows, and giving moderators a control panel directly inside Telegram.

## Product Goals
- **Guide community members** through Atlas knowledge spaces, surfacing answers from indexed documents and contextual snippets.
- **Coordinate operations staff** by pushing Camunda workflow tasks into chat, collecting structured inputs, and syncing status back to Flow API.
- **Safeguard public channels** with localized onboarding, moderation toggles, and reputation dashboards so stewards keep signal high.
- **Keep conversations grounded** through multi-turn thread memories, knowledge base retrieval, and automatic summarization of long-running chats.

## Primary Personas
- **Community members** interact with Luka in direct messages to ask questions, request tasks, or browse curated topics.
- **Group stewards and moderators** manage group settings, moderation level, and knowledge-base indexing directly from inline menus.
- **Operations agents** run Camunda-powered workflows (profile checks, grants, onboarding) without leaving Telegram, with Atlas UI as the companion surface.
- **Platform engineers** extend Luka with new agents, prompts, and tools so SOL Atlas can address emerging community programs.

## Feature Highlights
- **LLM Dialog Engine** – Supports streaming responses, provider fallback (Ollama → OpenAI), and multi-thread conversations with context recall.
- **Knowledge Hub** – Writes message excerpts and files into Elasticsearch/S3, enabling scoped retrieval across groups, topics, and locales.
- **Workflow Bridge** – Synchronizes Camunda process definitions, launches guided forms, and streams task updates through Flow API sockets.
- **Group Operations** – Inline menus for moderation, rules, localization, and analytics; reputation viewer and KB contribution flows.
- **Security & Compliance** – Multi-tenant configuration, per-command enablement, optional password gate, rate limiting, audit logging hooks.

## Documentation Map
If you are new to Luka Bot, review the documents in this order:
1. **Setup & Configuration** (`setup.md`) – spin up Redis, configure `.env`, and run the bot locally.
2. **Architecture** (`architecture.md`) – learn how handlers, services, and integrations cooperate.
3. **Operations Guide** (`operations.md`) – understand deployment modes, monitoring, and playbooks.
4. **Development Workflow** (`development.md`) – follow the conventions for extending or testing Luka.

Refer to `archive/` when you need the history behind specific moderation or workflow changes. All instructions in the refreshed docs reflect the current SOL Atlas stack (2025).
