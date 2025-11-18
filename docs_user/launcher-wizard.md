# Launcher Wizard Guide

Your DevOps steward/conscierge that spins up complete Atlas applications in minutes.

---

## Overview

The **Launcher Wizard** is your DevOps steward/conscierge that spins up complete Atlas applications in minutes.

**What It Does:**

1. **Spins up infrastructure** — Kubernetes namespaces with your own security and sandbox
2. **Deploys microservices** - Bot, AG-UI Gateway, Engine, Elasticsearch, Redis, etc.
3. **Exposes URLs** - Links to engine, components, admin UI
4. **Provides env vars** - Download configuration for local development

**Result:** A fully functional Atlas application running in your own Kubernetes namespace, ready to use in minutes.

---

## Workflow

1. **Go to launcher** - https://atlas.gurunetwork.ai/launcher
2. **Follow wizard** - 4 steps (Identity, Bot Setup, Group Setup, Ready)
3. **Get your app** - Running in k8s namespace, URLs exposed
4. **Fork the repo** - Switch infrastructure to your own fork
5. **Develop locally** - Use env vars from `/admin` command in bot

### The 4 Steps

**Step 1: Community Identity (25%)**
- Define bot name, username, description, and type (Community or Personal)

**Step 2: Connect Your Telegram Bot (50%)**
- Get bot token from [@BotFather](https://t.me/BotFather) (`/newbot`)
- Paste token into launcher

**Step 3: Group Setup (75%)**
- Add bot to your Telegram group
- Grant necessary permissions
- Deployment starts automatically

**Step 4: Ready (100%)**
- Deployment complete
- Access bot, admin UI, and get env vars for local development

---

## What Gets Deployed

### Stateless Microservices

- **bot-app** — Telegram bot + AG-UI Gateway
- **webchatbot-app** — AI assistant for web
- **engine-api** — BPMN workflow engine
- **flowapi-api** — Auth, app config, analytics API
- **warehouse-api** — WebSocket event stream

### Stateful Infrastructure

- **PostgreSQL** (via PgBouncer) — Primary database
- **Redis** — Cache and state management
- **Elasticsearch** — Knowledge bases

### Optional (Enterprise)

- **ClickHouse** — Event bus and analytics
- **RabbitMQ** — Async workloads
- **Workers** — External task workers

**Deployment:** Each application runs in its own Kubernetes namespace (`atlas-{app-id}`) with isolated resources, security policies, and monitoring.

---

## Exposed URLs

After deployment, the launcher UI displays:

- **Bot URL** — `https://t.me/{bot_username}`
- **Engine API** — `https://engine-{app-id}.atlas.gurunetwork.ai`
- **FlowAPI** — `https://flowapi-{app-id}.atlas.gurunetwork.ai`
- **Warehouse API** — `wss://warehouse-{app-id}.atlas.gurunetwork.ai`
- **Admin UI** — `https://admin-{app-id}.atlas.gurunetwork.ai`
- **Webchatbot** — Embeddable widget URL

---

## Development Environment Setup

### Get Environment Variables

1. **In Telegram Bot:**
   - Send `/admin` command
   - Bot responds with download link for env vars

2. **Download Configuration:**
   - Click link to download `.env` file
   - Contains all connection strings and secrets

3. **Use for Local Development:**
   ```bash
   # Copy env vars
   cp .env.local .env
   
   # Run development script
   ./run_development.sh
   ```

**What's Included:**
- Database URLs (PostgreSQL, Redis, Elasticsearch)
- Service URLs (FlowAPI, EngineAPI, warehouse-api)
- API keys and tokens
- Feature flags

---

## Fork and Customize

### Step 1: Fork the Repository

```bash
# Fork on GitHub
https://github.com/evahteev/sol-atlas

# Clone your fork
git clone https://github.com/your-username/sol-atlas
cd sol-atlas
```

### Step 2: Switch Infrastructure

1. **Update Kubernetes Configs:**
   - Point to your own cluster
   - Update namespace references
   - Configure your own ingress

2. **Update Environment Variables:**
   - Use your own database URLs
   - Configure your own service URLs
   - Set your own secrets

3. **Deploy:**
   ```bash
   kubectl apply -f k8s/
   ```

### Step 3: Keep Developing

- **Workflows** — Edit BPMN diagrams or YAML
- **Personas** — Edit Context.md + YAML
- **Tools** — Add [LangGraph](https://github.com/langchain-ai/langgraph) tools or custom code
- **UI** — Customize webchatbot, admin portal

**Benefits:**
- Full control over infrastructure
- Custom deployments
- Keep using launcher for new apps
- Develop against your own fork

---

## Benefits

- **Minutes to production** - Not weeks or months
- **Your own namespace** - Isolated, secure, sandboxed
- **Portable** - Fork repo, switch infra, keep developing
- **Templates** - Pre-built use cases (community bot, personal bot, intercom)

---

## Use Cases

- **Quick start** - Spin up bot, test, iterate
- **Development environment** - Local dev against deployed infra
- **Production deployment** - One-click deploy to your k8s cluster
- **Template customization** - Start from template, customize workflows

### Templates

**Community Bot** — Quest system, leaderboards, wallet integration, analytics dashboard

**Personal Bot** — Daily briefs, custom routines, personal notes, knowledge base

**Intercom Bot** — Webchatbot widget, Telegram support group integration, knowledge base RAG, escalation workflows

---

## Troubleshooting

### Deployment Fails

- Check Kubernetes cluster access and resource availability
- Review launcher logs and Kubernetes events

### Bot Not Responding

- Verify bot token in BotFather
- Re-add bot to group with necessary permissions
- Check bot logs in admin UI

### Can't Access Admin UI

- Verify URL in launcher UI
- Check network connectivity and browser console

---

## Best Practices

**Security:**
- Never share bot tokens or API keys
- Use secrets for sensitive data
- Enable RBAC in Kubernetes

**Performance:**
- Monitor resources (CPU, memory)
- Scale horizontally for stateless services
- Optimize databases for stateful services

**Development:**
- Version control workflows and configs
- Test locally before deploying
- Monitor logs for debugging

---

## Next Steps

- Read the [Getting Started Guide](getting-started.md) for quick setup
- Check the [Architecture Overview](architecture.md) for system design
- Explore the [Components Guide](components.md) for component details
- Review the [Requirements](requirements.md) for deployment requirements

---

## Support

- **Documentation:** https://atlas.gurunetwork.ai/docs
- **Community:** https://t.me/SolanaAtlas
- **Issues:** https://github.com/evahteev/sol-atlas/issues
