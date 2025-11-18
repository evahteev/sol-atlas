# Getting Started

This guide helps you launch your Atlas bot and explore the platform in minutes.

---

## Try Atlas First

### Demo Bot & Webchatbot

**Try the Demo Bot:**
- **Telegram Bot:** [@SOLAtlasBOT](https://t.me/SOLAtlasBOT)
- **Community Group:** [Join Atlas Community](https://t.me/+BXMz7v3VxKFhMjli)

**See Webchatbot in Action:**
- Visit [DexGuru](https://dex.guru/) to see the webchatbot embedded on their site
- Check out [Burning Meme](https://burning.meme/) for gamification examples

---

## Launch Your Own Bot

### Quick Start (5 Minutes)

1. **Go to Launcher** — [https://atlas.gurunetwork.ai/launcher](https://atlas.gurunetwork.ai/launcher)

2. **Follow the 4-Step Wizard:**

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

![onboarding_flow.png](https://atlas.gurunetwork.ai/docs/onboarding_flow.png)

3. **Your Bot is Live!**
   - Bot is running in your own Kubernetes namespace
   - URLs exposed in launcher UI
   - Ready to use in minutes

---

## Clone the Repo and Start Developing

### Step 1: Fork the Repository

```bash
# Fork on GitHub
https://github.com/evahteev/sol-atlas

# Clone your fork
git clone https://github.com/your-username/sol-atlas
cd sol-atlas
```

### Step 2: Get Environment Variables

1. **In Telegram Bot:**
   - Send `/admin` command to your deployed bot
   - Bot responds with download link for env vars

2. **Download Configuration:**
   - Click link to download `.env` file
   - Contains all connection strings and secrets

3. **Set Up Local Development:**
   ```bash
   # Copy env vars
   cp .env.local .env
   
   # Run development script
   ./run_development.sh  # Spins up bot, API, frontend
   ```

**What's Included:**
- Database URLs (PostgreSQL, Redis, Elasticsearch)
- Service URLs (FlowAPI, EngineAPI, warehouse-api)
- API keys and tokens
- Feature flags

### Step 3: Switch to Your Own Infrastructure

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

---

## What You Get

### Stateless Microservices

- **bot-app** — Telegram bot + [AG-UI Gateway](https://github.com/ag-ui-protocol/ag-ui)
- **webchatbot-app** — AI assistant for web
- **engine-api** — BPMN workflow engine
- **flowapi-api** — Auth, app config, analytics API
- **warehouse-api** — WebSocket event stream

### Stateful Infrastructure

- **PostgreSQL** (via PgBouncer) — Primary database
- **Redis** — Cache and state management
- **Elasticsearch** — Knowledge bases

![architecture.png](https://atlas.gurunetwork.ai/docs/architecture.png)

---

## Next Steps

### Customize Your Bot

- **Workflows** — Edit BPMN diagrams ([Modeler](https://camunda.com/download/modeler/)) or YAML
  - [Example BPMN](onboarding/community_onboarding.bpmn)
  - [Example Workflow](sol_atlas_onboarding/README.md)
- **Personas** — Edit Context.md + YAML
  - [Example Config](sol_atlas_onboarding/config.yaml)
- **Tools** — Add [LangGraph](https://github.com/langchain-ai/langgraph) tools or custom code
- **Forms** — Define in BPMN or generate with AI
  - [Example Forms](onboarding/Community_Onboarding_README.md)
- **UI** — Customize webchatbot, admin portal

### Best Practices

- **Start simple** — Basic bot + RAG (`camunda_enabled=false`)
- **Add workflows** — Enable [Camunda](https://github.com/camunda/camunda-bpm-platform) for orchestration
- **Version control** — Workflows, personas, configs in git
- **Test locally** — Use `run_development.sh` against deployed infra
- **Iterate** — Deploy, test, customize, repeat

---

## Resources

### Documentation

- **Architecture Overview** — [architecture.md](architecture.md)
- **Launcher Wizard Guide** — [launcher-wizard.md](launcher-wizard.md)
- **Webchatbot Guide** — [webchatbot.md](webchatbot.md)
- **Components Guide** — [components.md](components.md)

### Examples

- **BPMN Workflows** — [onboarding/community_onboarding.bpmn](onboarding/community_onboarding.bpmn)
- **Forms** — [onboarding/Community_Onboarding_README.md](onboarding/Community_Onboarding_README.md)
- **Workflow Scenarios** — [sol_atlas_onboarding/](sol_atlas_onboarding/)

### Open Source Projects

- **[Camunda BPMN Platform](https://github.com/camunda/camunda-bpm-platform)** — Workflow orchestration
- **[AG-UI Protocol](https://github.com/ag-ui-protocol/ag-ui)** — Unified interface protocol
- **[LangGraph](https://github.com/langchain-ai/langgraph)** — AI layer for agentic workflows
- **[Elasticsearch](https://www.elastic.co/elasticsearch/)** — Search and analytics engine

---

## Support

- **Documentation:** https://atlas.gurunetwork.ai/docs
- **Community:** https://t.me/SolanaAtlas
- **GitHub Issues:** https://github.com/evahteev/sol-atlas/issues
- **Launcher:** https://atlas.gurunetwork.ai/launcher
