# Guru Framework · **Engine Module**

> **Status:** Alpha · Actively developed · Contributions welcome  
> The Engine module is the **workflow & event-streaming heart** of the Guru Framework. It fuses [Camunda Platform 7](https://camunda.com/products/camunda-platform/) with AI processors, on-chain triggers, and a high-throughput AMQP event bus—exposing everything **only** through **REST** and **WebSockets**.

---

## ✨ Key Capabilities

| Capability | Description |
|------------|-------------|
| **BPMN 2.0 Runtime** | Executes standard BPMN diagrams with user tasks, timers, DMN, and incident handling. |
| **External Workers** | Language-agnostic job clients (Java / Python / Node) pull work via REST—ideal for GPT calls or on-chain interactions. |
| **Engine Event Bus (AMQP)** | Every history/event is serialised to JSON and published to **RabbitMQ/Kafka** for reactive UIs & data warehousing. |
| **Web3 Triggers** | Listen to ERC-20 transfers, NFT mints, or custom events and start/correlate processes in real time. |
| **Hot-Swap Deployments** | Upload BPMN/DMN/JAR at runtime—latest definition auto-activated with zero downtime. |
| **Vaulted Secrets & Signing** | Integrates HashiCorp-style Vault and Thirdweb wallets for secure key management. |

---

## 🏗️ Architecture Snapshot

```text
┌──────────────────┐          REST           ┌──────────────────┐
│ Front-end (Next) │ ───────────────────────▶│  Engine REST API │
└──────────────────┘                         └──────────────────┘
        ▲                                          │
        │ WebSocket (history stream)               ▼
┌──────────────────┐        AMQP           ┌──────────────────────┐
│  Analytics UI    │◀─────────────────────▶│  Engine Event Bus    │
└──────────────────┘                       │ (RabbitMQ / Kafka)   │
                                           └──────────┬──────────┘
                                                      │ JSON events
                                                      ▼
                                           ┌─────────────────────┐
                                           │ Process Runtime     │
                                           │   (Camunda 7)       │
                                           └────────┬────────────┘
                                                    │ REST jobs
                                                    ▼
                                       ┌───────────────────────────┐
                                       │      External Workers     │
                                       │ (AI, Web3, enrichment)    │
                                       └───────────────────────────┘
```

# 🚀 Quick Start

## Option A — Docker Compose (one-liner)

```bash
# spin up Postgres, RabbitMQ & Engine API
docker compose -f dev/docker-compose.yml up -d
```

*Application UI:* <http://localhost:8080/camunda/app/welcome/default/>  
*REST API:* <http://localhost:8080/engine-rest>

default login: demo

default password: demo

---

## Option B — IntelliJ IDE (hot-reload dev)

1. **Clone** the monorepo and open the *engine* module in IntelliJ.  
2. Set the run configuration to **`CamundaApplication`** (extends `SpringBootServletInitializer`).  
3. Hit&nbsp;▶; Testcontainers will start Postgres and RabbitMQ if enabled.

```bash
# or from CLI
./mvnw spring-boot:run -pl modules/engine
```

---

## Upload a BPMN diagram

```bash
curl -F "data=@./examples/burning-meme.bpmn" \\
     http://localhost:8080/engine-rest/deployment/create
```

## Start a process instance

```bash
curl -X POST -H "Content-Type: application/json" \\
     -d '{"variables":{"telegram_user_id":{"value":"123456"}}}' \\
     http://localhost:8080/engine-rest/process-definition/key/burning-meme/start
```

---

<details>
<summary><strong>Environment Variables (full list)</strong></summary>

```properties
# Logging & history
logging.level.org.springframework=${LOGGING_LEVEL:INFO}
camunda.bpm.history=${HISTORY_LEVEL:full}

# Database
camunda.bpm.datasource.jdbc-url=${BBPA_ENGINE_DB_URL:jdbc:h2:mem:workflow}
camunda.bpm.datasource.username=${BBPA_ENGINE_DB_USER:workflow}
camunda.bpm.datasource.password=${BBPA_ENGINE_DB_PASS:workflow}
camunda.bpm.datasource.driverClassName=${BBPA_ENGINE_DB_DRIVER_CLASS:org.h2.Driver}
camunda.bpm.datasource.driver=${BBPA_ENGINE_DB_DRIVER:postgresql}
camunda.bpm.datasource.hikari.minIdle=10
camunda.bpm.datasource.hikari.idle-timeout=10000
camunda.bpm.datasource.hikari.maximumPoolSize=30

# Ethereum / Web3
ethereum.privateKey=${ETHEREUM_PRIVATEKEY:ETHEREUM_PRIVATEKEY}
ethereum.defaultFundingCommitment=${DEFAULT_FUNDING:1000}
ethereum.rpcUrl=${RPC_URL:https://rpc.ankr.com/polygon_mumbai}
ethereum.factoryAddress=${FACTORY_ADDRESS:0x8E1c92D50c4A9DD7ef46C3d77Db0A7Cb6D300f86}

# Guru Flow API & Warehouse
api.url=${FLOW_API_URL:FLOW_API_URL}
api.key=${FLOW_API_SYS_KEY:FLOW_API_SYS_KEY}
warehouse.url=${WAREHOUSE_API_HOST:WAREHOUSE_API_HOST}
warehouse.key=${WAREHOUSE_API_KEY:secret}

dexguruapi.url=${DEXGURU_API_BASE:https://api.dex.guru}

# Telegram Bot
bot.name=${BOT_NAME:BOT_NAME}
bot.token=${BOT_TOKEN:BOT_TOKEN}
bot.adminGroupId=${BOT_ADMIN_GROUP_ID:-1000000000}

# Application meta
application.name=${APPLICATION_NAME:Guru Network App}
application.token=${APPLICATION_TOKEN:tGURU}
application.url=${APPLICATION_URL:https://miles.gurunetwork.ai}

# RabbitMQ (Engine Event Bus)
spring.rabbitmq.enabled=${RABBITMQ_ENABLED:false}
spring.rabbitmq.host=${RABBITMQ_HOST:localhost}
spring.rabbitmq.port=${RABBITMQ_PORT:5672}
spring.rabbitmq.username=${RABBITMQ_USER:guest}
spring.rabbitmq.password=${RABBITMQ_PASSWORD:guest}
engine.rabbitmq.exchange=${RABBITMQ_EXCHANGE:engine.exchange}
engine.rabbitmq.queue=${RABBITMQ_QUEUE:engine.queue}
engine.rabbitmq.routingkey=${RABBITMQ_ROUTINGKEY:engine.routingkey}
spring.rabbitmq.virtual-host=${RABBITMQ_VIRTUAL_HOST:/}

# Inscriptions (optional)
inscription.enabled=${INSCRIPTIONS_HISTORY_ENABLED:false}
inscription.event.types=${INSCRIPTION_HISTORY_EVENT_TYPES:ALL}
inscription.privateKey=${INSCRIPTIONS_PRIVATEKEY:0000000000000000000000000000}
inscription.rpcUrl=${INSCRIPTIONS_RPC_URL:http://node-canto-testnet-01.dexguru.biz:8545}
inscription.chainId=${INSCRIPTIONS_CHAIN:261}
inscription.max_threads=${INSCRIPTIONS_MAX_THREADS:10}
inscription.maxRetry=${INSCRIPTIONS_MAX_RETRY:3}
inscription.queue.capacity=${INSCRIPTIONS_QUEUE_CAPACITY:3000}
inscription.batch.size=${INSCRIPTIONS_BATCH_SIZE:30}
inscription.block.time=${INSCRIPTIONS_BLOCK_TIME:3000}

# Job Executor
camunda.bpm.job-execution.enabled=${JOB_EXECUTION_ENABLE:true}
camunda.bpm.job-execution.max-pool-size=${JOB_EXECUTION_MAX_POOL_SIZE:10}
camunda.bpm.job-execution.max-jobs-per-acquisition=${JOB_EXECUTION_MAX_JOBS_PER_ACQ:3}
camunda.bpm.job-execution.core-pool-size=${JOB_EXECUTION_CORE_POOL_SIZE:3}

# AI integrations
mindsdb.url=${MINDS_DB_HOST:http://127.0.0.1:47334}
mindsdb.openai.api.key=${OPENAI_API_KEY:sk-key}
openai.api.key=${OPENAI_API_KEY:sk-key}
rapidApi.api.key=${RAPID_API_KEY:rapid-ke}
```
</details>

---
_Apache-2.0 © 2025 DexGuru Inc. & Guru Network contributors_
            