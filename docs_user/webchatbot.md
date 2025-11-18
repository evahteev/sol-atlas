# Webchatbot: Open Source Intercom

An embeddable, [AG-UI Protocol](https://github.com/ag-ui-protocol/ag-ui) compatible chat interface that provides intercom-style support on your site.

---

## Overview

**Webchatbot** is an embeddable, [AG-UI Protocol](https://github.com/ag-ui-protocol/ag-ui) compatible chat interface that provides intercom-style support on your site.

**Based On:**

- [AG-UI Protocol](https://github.com/ag-ui-protocol/ag-ui) interfaces and protocol
- CopilotKit (from Dojo UI)
- [AG-UI Gateway](https://github.com/ag-ui-protocol/ag-ui) backend

---

## Features

- **Embeddable** - Add to landing page or service with one script tag
- **[AG-UI Protocol](https://github.com/ag-ui-protocol/ag-ui) compatible** - Works with all AG-UI protocol components
- **Forms & tools** - Same capabilities as Telegram bot (forms, buttons, generated interfaces)
- **Real-time** - SSE API for streaming responses via [AG-UI Gateway](https://github.com/ag-ui-protocol/ag-ui)
- **Context-aware** - Shared sessions with Telegram bot
- **Works as a Layer 0 AI agent** - Dynamic self-propelling knowledge base from FAQs and group responses

---

## Configuration

### Minimal Setup

```bash
# Environment variables
AG_UI_GATEWAY_URL=https://your-gateway.atlas.gurunetwork.ai
BOT_TOKEN=your_telegram_bot_token

# Run development
./run_development.sh  # Spins up bot, API, frontend
```

### Get Environment Variables

- Use `/admin` command in Telegram bot
- Download connection strings
- Use for local development against deployed infra

**What's Included:**
- Database URLs (PostgreSQL, Redis, Elasticsearch)
- Service URLs (FlowAPI, EngineAPI, warehouse-api)
- API keys and tokens
- Feature flags

---

## How It Works

- [Webchatbot](https://github.com/evahteev/sol-atlas/tree/main/webchatbot) ([AG-UI Protocol](https://github.com/ag-ui-protocol/ag-ui) compatible) embedded on your site
- Connects to [AG-UI Gateway](https://github.com/evahteev/sol-atlas/tree/main/bot/ag_ui_gateway) (SSE API) for real-time responses
- Works as a Layer 0 AI agent with dynamic self-propelling knowledge base from FAQs and group responses
- Escalates to Telegram support group with full context
- Admins respond in Telegram; replies delivered back to user in web chat

---

## Use Cases

- **Layer 0-1 support** - Deflect tickets with intelligent answers
- **Unified support** - Web + Telegram in one system
- **Self-hosted** - No vendor lock-in
- **Customizable** - Fork, customize, deploy

**Example:** [DexGuru](https://dex.guru/) uses Atlas webchatbot to answer DeFi questions, route to support when needed, and surface on-chain data panels.

---

## Integration

### Embedding on Your Site

The webchatbot can be embedded on any website with a simple script tag, connecting to your deployed AG-UI Gateway instance.

### Shared Context

Webchatbot shares the same context and knowledge base as your Telegram bot, ensuring consistent responses across both interfaces.

---

## Next Steps

- Read the [Architecture Overview](architecture.md) for system design
- Check the [Launcher Wizard Guide](launcher-wizard.md) for deployment
- Explore the [Components Guide](components.md) for component details
