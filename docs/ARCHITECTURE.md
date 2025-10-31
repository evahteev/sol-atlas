# SOL Atlas Architecture

Technical deep dive into the SOL Atlas platform — understanding how Telegram communities, BPMN automation, AI agents, and Solana blockchain come together.

---

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         SOL ATLAS                                │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Telegram   │  │     Web      │  │   Solana     │          │
│  │    Users     │  │   Portal     │  │  Blockchain  │          │
│  └───────┬──────┘  └───────┬──────┘  └───────┬──────┘          │
│          │                  │                  │                  │
│          ├──────────────────┴──────────────────┤                │
│          │                                      │                  │
│  ┌───────▼────────────────────────────────────▼──────┐          │
│  │              Bot Gateway Layer                     │          │
│  │    (Telegram Bot API + Web Socket Server)         │          │
│  └────────────────────┬──────────────────────────────┘          │
│                       │                                           │
│  ┌────────────────────▼───────────────────────────────┐         │
│  │            GURU Framework Core                      │         │
│  │  ┌─────────────┐ ┌────────────┐ ┌──────────────┐  │         │
│  │  │   Camunda   │ │  MindsDB   │ │   Workers    │  │         │
│  │  │    BPMN     │ │  AI Layer  │ │  (Python)    │  │         │
│  │  └─────────────┘ └────────────┘ └──────────────┘  │         │
│  └────────────────────┬───────────────────────────────┘         │
│                       │                                           │
│  ┌────────────────────▼───────────────────────────────┐         │
│  │               Data Layer                            │         │
│  │  ┌─────────────┐ ┌────────────┐ ┌──────────────┐  │         │
│  │  │ PostgreSQL  │ │   Redis    │ │   MindsDB    │  │         │
│  │  │  (Primary)  │ │  (Cache)   │ │   (Skills)   │  │         │
│  │  └─────────────┘ └────────────┘ └──────────────┘  │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Architecture

### 1. Bot Gateway Layer

**Purpose:** Handle all user interactions from Telegram and Web

**Technologies:**
- Telegram Bot API (Python)
- WebSocket Server (Node.js)
- Next.js (Web Portal)

**Key Components:**

```python
# bot/luka_bot/main.py
class AtlasBot:
    def __init__(self, token: str):
        self.bot = telegram.Bot(token=token)
        self.flow_client = FlowClient()  # BPMN integration
        self.ai_copilot = CoPilotSteward()  # AI assistant

    async def handle_message(self, update: Update):
        """Route user messages to appropriate handler"""
        user = self.get_or_create_user(update.user)

        # Check if AI CoPilot should respond
        if self.should_use_copilot(update.message):
            response = await self.ai_copilot.respond(
                user=user,
                message=update.message.text
            )
            return await self.send_message(user, response)

        # Check if message triggers a quest step
        quest_update = await self.flow_client.process_user_action(
            user_id=user.id,
            action='message_sent',
            data={'text': update.message.text}
        )

        if quest_update:
            await self.notify_quest_progress(user, quest_update)

    async def handle_callback(self, update: Update):
        """Handle button clicks and inline actions"""
        callback = update.callback_query
        action, data = self.parse_callback(callback.data)

        # Route to appropriate handler
        if action == 'quest_start':
            await self.start_quest(callback.from_user, data['quest_id'])
        elif action == 'wallet_connect':
            await self.initiate_wallet_connection(callback.from_user)
```

---

### 2. GURU Framework Core

**Purpose:** Orchestrate workflows, manage state, and coordinate services

#### 2.1 Camunda BPMN Engine

**Purpose:** Visual workflow automation and process orchestration

**Location:** `engine/`

```xml
<!-- Example: Quest Workflow -->
<bpmn:process id="welcome_quest" name="Welcome Quest">
  <bpmn:startEvent id="start" name="Quest Started" />

  <bpmn:serviceTask id="check_profile"
                    name="Check Profile Complete"
                    camunda:type="external"
                    camunda:topic="check_user_profile" />

  <bpmn:exclusiveGateway id="profile_complete" name="Profile Complete?" />

  <bpmn:serviceTask id="award_points"
                    name="Award 100 Points"
                    camunda:type="external"
                    camunda:topic="award_points" />

  <bpmn:serviceTask id="send_badge"
                    name="Send Welcome Badge"
                    camunda:type="external"
                    camunda:topic="send_badge" />

  <bpmn:endEvent id="end" name="Quest Complete" />

  <!-- Sequence flows -->
  <bpmn:sequenceFlow sourceRef="start" targetRef="check_profile" />
  <bpmn:sequenceFlow sourceRef="check_profile" targetRef="profile_complete" />
  <bpmn:sequenceFlow sourceRef="profile_complete" targetRef="award_points">
    <bpmn:conditionExpression>${profileComplete == true}</bpmn:conditionExpression>
  </bpmn:sequenceFlow>
  <bpmn:sequenceFlow sourceRef="award_points" targetRef="send_badge" />
  <bpmn:sequenceFlow sourceRef="send_badge" targetRef="end" />
</bpmn:process>
```

#### 2.2 External Workers

**Purpose:** Execute business logic for BPMN tasks

**Location:** `worker/`

```python
# worker/quest_worker.py
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

# Worker that handles point awards
def award_points_worker(task: ExternalTask) -> TaskResult:
    user_id = task.get_variable("user_id")
    points = task.get_variable("points")
    reason = task.get_variable("reason")

    try:
        # Update database
        db.execute(
            "INSERT INTO points_log (user_id, points, reason, timestamp) "
            "VALUES (%s, %s, %s, NOW())",
            (user_id, points, reason)
        )

        # Update user total
        db.execute(
            "UPDATE users SET total_points = total_points + %s WHERE id = %s",
            (points, user_id)
        )

        # Check for milestone badges
        user_points = db.fetchone(
            "SELECT total_points FROM users WHERE id = %s",
            (user_id,)
        )

        badges_earned = check_milestones(user_points['total_points'])

        # Return success with variables for next step
        return task.complete({
            "points_awarded": points,
            "new_total": user_points['total_points'],
            "badges_earned": badges_earned
        })

    except Exception as e:
        return task.failure(
            error_message=str(e),
            error_details=f"Failed to award {points} points to user {user_id}"
        )

# Register worker
worker = ExternalTaskWorker(
    worker_id="points_worker",
    base_url="http://engine:8080/engine-rest"
)
worker.subscribe("award_points", award_points_worker)
```

#### 2.3 MindsDB AI Layer

**Purpose:** Skilled agents and knowledge bases

```sql
-- Create a knowledge base from docs
CREATE MODEL community_knowledge
FROM postgres (
  SELECT * FROM documentation
)
PREDICT answer
USING
  engine = 'langchain',
  embeddings_model = 'sentence-transformers/all-MiniLM-L6-v2',
  model_name = 'gpt-4o-mini';

-- Create a sentiment analysis model
CREATE MODEL sentiment_analyzer
FROM postgres (
  SELECT message_text, sentiment FROM labeled_messages
)
PREDICT sentiment
USING
  engine = 'huggingface',
  task = 'text-classification',
  model_name = 'cardiffnlp/twitter-roberta-base-sentiment';

-- Query from bot
SELECT answer
FROM community_knowledge
WHERE question = 'How do I connect my wallet?';
```

---

### 3. Data Layer

#### 3.1 PostgreSQL Schema

```sql
-- Users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    wallet_address VARCHAR(44),
    total_points INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    joined_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW()
);

-- Quests table
CREATE TABLE quests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    quest_type VARCHAR(50),
    points_reward INTEGER,
    badge_reward VARCHAR(100),
    requirements JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Quest progress tracking
CREATE TABLE quest_progress (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    quest_id INTEGER REFERENCES quests(id),
    status VARCHAR(20), -- 'started', 'in_progress', 'completed', 'failed'
    progress JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    UNIQUE(user_id, quest_id)
);

-- Points log
CREATE TABLE points_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    points INTEGER NOT NULL,
    reason VARCHAR(255),
    quest_id INTEGER REFERENCES quests(id),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Badges
CREATE TABLE badges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    requirement JSONB
);

-- User badges (many-to-many)
CREATE TABLE user_badges (
    user_id BIGINT REFERENCES users(id),
    badge_id INTEGER REFERENCES badges(id),
    earned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, badge_id)
);

-- Leaderboards (materialized view for performance)
CREATE MATERIALIZED VIEW leaderboard_weekly AS
SELECT
    u.id,
    u.telegram_id,
    u.username,
    SUM(pl.points) as weekly_points,
    COUNT(DISTINCT qp.quest_id) as quests_completed,
    ROW_NUMBER() OVER (ORDER BY SUM(pl.points) DESC) as rank
FROM users u
LEFT JOIN points_log pl ON u.id = pl.user_id
    AND pl.timestamp > NOW() - INTERVAL '7 days'
LEFT JOIN quest_progress qp ON u.id = qp.user_id
    AND qp.completed_at > NOW() - INTERVAL '7 days'
GROUP BY u.id, u.telegram_id, u.username
ORDER BY weekly_points DESC;

-- Refresh leaderboard every 5 minutes
CREATE INDEX idx_points_log_timestamp ON points_log(timestamp);
```

#### 3.2 Redis Caching

```python
# Cache frequently accessed data
class CacheManager:
    def __init__(self):
        self.redis = redis.Redis(host='redis', port=6379, decode_responses=True)

    def get_user_points(self, user_id: int) -> int:
        """Get user points with cache"""
        cache_key = f"user:{user_id}:points"

        # Try cache first
        cached = self.redis.get(cache_key)
        if cached:
            return int(cached)

        # Query database
        points = db.fetchone(
            "SELECT total_points FROM users WHERE id = %s",
            (user_id,)
        )['total_points']

        # Cache for 5 minutes
        self.redis.setex(cache_key, 300, points)

        return points

    def get_leaderboard(self, timeframe: str = 'weekly') -> List[Dict]:
        """Get leaderboard with cache"""
        cache_key = f"leaderboard:{timeframe}"

        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Query from materialized view
        leaderboard = db.fetchall(f"SELECT * FROM leaderboard_{timeframe} LIMIT 100")

        # Cache for 5 minutes
        self.redis.setex(cache_key, 300, json.dumps(leaderboard))

        return leaderboard
```

---

## 🔗 Integration Points

### Solana Integration

```python
# worker/solana_worker.py
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from solders.signature import Signature

class SolanaVerifier:
    def __init__(self, rpc_url: str):
        self.client = AsyncClient(rpc_url)

    async def verify_wallet_ownership(
        self,
        wallet_address: str,
        signed_message: str,
        signature: str
    ) -> bool:
        """Verify user owns the wallet"""
        try:
            # Verify signature
            is_valid = verify_signature(
                message=signed_message,
                signature=signature,
                public_key=wallet_address
            )
            return is_valid
        except Exception as e:
            logger.error(f"Wallet verification failed: {e}")
            return False

    async def check_token_balance(
        self,
        wallet_address: str,
        token_mint: str,
        min_balance: int
    ) -> bool:
        """Check if wallet has minimum token balance"""
        try:
            wallet_pubkey = PublicKey(wallet_address)
            token_accounts = await self.client.get_token_accounts_by_owner(
                wallet_pubkey,
                {"mint": PublicKey(token_mint)}
            )

            for account in token_accounts.value:
                balance = int(account.account.data.parsed['info']['tokenAmount']['amount'])
                if balance >= min_balance:
                    return True

            return False
        except Exception as e:
            logger.error(f"Balance check failed: {e}")
            return False

    async def verify_transaction(
        self,
        wallet_address: str,
        tx_type: str,
        min_amount: float = 0
    ) -> Optional[Dict]:
        """Verify a specific transaction occurred"""
        try:
            wallet_pubkey = PublicKey(wallet_address)

            # Get recent transactions
            signatures = await self.client.get_signatures_for_address(
                wallet_pubkey,
                limit=20
            )

            for sig in signatures.value:
                tx = await self.client.get_transaction(
                    Signature.from_string(sig.signature),
                    encoding="jsonParsed"
                )

                # Parse transaction and check if it matches criteria
                if self.matches_criteria(tx, tx_type, min_amount):
                    return {
                        "signature": sig.signature,
                        "timestamp": sig.block_time,
                        "amount": self.extract_amount(tx)
                    }

            return None
        except Exception as e:
            logger.error(f"Transaction verification failed: {e}")
            return None
```

### Telegram Deep Linking

```python
# Referral system using Telegram deep links
def generate_referral_link(user_id: int, bot_username: str) -> str:
    """Generate unique referral link"""
    referral_code = base64.urlsafe_b64encode(str(user_id).encode()).decode()
    return f"https://t.me/{bot_username}?start=ref_{referral_code}"

def parse_referral_code(start_param: str) -> Optional[int]:
    """Extract referrer ID from start parameter"""
    if not start_param.startswith('ref_'):
        return None

    try:
        code = start_param[4:]  # Remove 'ref_' prefix
        referrer_id = int(base64.urlsafe_b64decode(code).decode())
        return referrer_id
    except:
        return None

# In bot handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    start_param = context.args[0] if context.args else None

    # Check if referred
    if start_param:
        referrer_id = parse_referral_code(start_param)
        if referrer_id:
            await process_referral(referrer_id, user.id)

    await send_welcome_message(user)
```

---

## 🚀 Deployment Architecture

### Docker Compose Setup

```yaml
# docker-compose.yaml
version: '3.8'

services:
  # Camunda BPMN Engine
  engine:
    build: ./engine
    container_name: sol-atlas-engine
    environment:
      - POSTGRES_HOST=db
      - POSTGRES_DB=sol_atlas
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "8080:8080"
    depends_on:
      - db
    networks:
      - atlas-network

  # Telegram Bot
  bot:
    build: ./bot
    container_name: sol-atlas-bot
    environment:
      - TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
      - CAMUNDA_URL=http://engine:8080/engine-rest
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/sol_atlas
      - REDIS_URL=redis://redis:6379
      - SOLANA_RPC_URL=${SOLANA_RPC_URL}
    depends_on:
      - engine
      - db
      - redis
    networks:
      - atlas-network

  # External Workers
  workers:
    build: ./worker
    container_name: sol-atlas-workers
    environment:
      - CAMUNDA_URL=http://engine:8080/engine-rest
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/sol_atlas
      - SOLANA_RPC_URL=${SOLANA_RPC_URL}
    depends_on:
      - engine
      - db
    networks:
      - atlas-network

  # Web GUI
  gui:
    build: ./gui
    container_name: sol-atlas-gui
    environment:
      - NEXT_PUBLIC_API_URL=http://engine:8080
    ports:
      - "3000:3000"
    depends_on:
      - engine
    networks:
      - atlas-network

  # PostgreSQL Database
  db:
    image: postgres:15
    container_name: sol-atlas-db
    environment:
      - POSTGRES_DB=sol_atlas
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - atlas-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: sol-atlas-redis
    volumes:
      - redis_data:/data
    networks:
      - atlas-network

volumes:
  postgres_data:
  redis_data:

networks:
  atlas-network:
    driver: bridge
```

### Production Deployment (Kubernetes)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sol-atlas-bot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sol-atlas-bot
  template:
    metadata:
      labels:
        app: sol-atlas-bot
    spec:
      containers:
      - name: bot
        image: sol-atlas-bot:latest
        env:
        - name: TELEGRAM_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: telegram-token
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 📊 Performance Considerations

### Scalability

- **Horizontal scaling:** Bot and worker services are stateless
- **Database connection pooling:** PgBouncer for PostgreSQL
- **Redis caching:** Reduce database load
- **CDN:** Static assets and images
- **Rate limiting:** Prevent abuse

### Monitoring

```yaml
# Prometheus metrics
metrics:
  - messages_processed_total
  - quest_completions_total
  - wallet_verifications_total
  - api_response_time_seconds
  - database_query_duration_seconds
  - cache_hit_rate
```

---

## 🎓 Next Steps

- **[Integration Guide →](INTEGRATIONS.md)** — Connect external services
- **[API Reference →](API.md)** — Developer documentation

---

[← Back to Main README](../README.md)
