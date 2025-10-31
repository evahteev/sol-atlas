# SOL Atlas API Reference

Complete API documentation for building custom integrations, bots, and tools on top of SOL Atlas.

---

## 🔑 Authentication

All API requests require authentication using a Bearer token or API key.

```bash
# Get your API key from the admin portal
API_KEY="your_api_key_here"

# Include in requests
curl -H "Authorization: Bearer ${API_KEY}" \
     https://api.your-atlas-instance.com/v1/users
```

---

## 📑 Table of Contents

1. [Users API](#users-api)
2. [Quests API](#quests-api)
3. [Points & Rewards](#points--rewards)
4. [Leaderboards](#leaderboards)
5. [Analytics](#analytics)
6. [Webhooks](#webhooks)
7. [BPMN Process API](#bpmn-process-api)

---

## 👤 Users API

### Get User Profile

```http
GET /v1/users/:user_id
```

**Response:**
```json
{
  "id": 12345,
  "telegram_id": 987654321,
  "username": "crypto_enthusiast",
  "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
  "total_points": 1250,
  "level": 5,
  "current_streak": 7,
  "badges": [
    {
      "id": 1,
      "name": "Early Adopter",
      "image_url": "https://...",
      "earned_at": "2025-10-15T10:30:00Z"
    }
  ],
  "quests_completed": 12,
  "referrals": 5,
  "joined_at": "2025-10-01T08:20:00Z",
  "last_active": "2025-10-30T14:45:00Z"
}
```

### Get User by Telegram ID

```http
GET /v1/users/telegram/:telegram_id
```

### Get User by Wallet

```http
GET /v1/users/wallet/:wallet_address
```

### Update User Profile

```http
PATCH /v1/users/:user_id
```

**Request Body:**
```json
{
  "wallet_address": "new_wallet_address",
  "preferences": {
    "notifications": true,
    "public_profile": true
  }
}
```

### Link Wallet to User

```http
POST /v1/users/:user_id/wallet
```

**Request Body:**
```json
{
  "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
  "signature": "base64_encoded_signature",
  "message": "signed_message"
}
```

---

## 🎯 Quests API

### List All Quests

```http
GET /v1/quests
```

**Query Parameters:**
- `type` — Filter by quest type (social, onchain, learning, etc.)
- `active` — Only active quests (true/false)
- `limit` — Number of results (default: 50)
- `offset` — Pagination offset

**Response:**
```json
{
  "quests": [
    {
      "id": 1,
      "name": "Welcome Quest",
      "description": "Complete your profile and connect wallet",
      "type": "onboarding",
      "points_reward": 100,
      "badge_reward": {
        "id": 1,
        "name": "Newcomer"
      },
      "steps": [
        {
          "id": 1,
          "description": "Complete your profile",
          "order": 1
        },
        {
          "id": 2,
          "description": "Connect your wallet",
          "order": 2
        }
      ],
      "active": true,
      "created_at": "2025-10-01T00:00:00Z"
    }
  ],
  "total": 24,
  "limit": 50,
  "offset": 0
}
```

### Get Quest Details

```http
GET /v1/quests/:quest_id
```

### Create Quest

```http
POST /v1/quests
```

**Request Body:**
```json
{
  "name": "First Swap Quest",
  "description": "Make your first swap on Jupiter",
  "type": "onchain",
  "points_reward": 200,
  "badge_reward_id": 5,
  "requirements": {
    "protocol": "jupiter",
    "action": "swap",
    "min_amount_usd": 10
  },
  "steps": [
    {
      "description": "Connect your wallet",
      "verification_type": "wallet_connected",
      "order": 1
    },
    {
      "description": "Complete a swap of at least $10",
      "verification_type": "onchain",
      "verification_config": {
        "protocol": "jupiter",
        "min_amount": 10
      },
      "order": 2
    }
  ],
  "active": true
}
```

### Update Quest

```http
PATCH /v1/quests/:quest_id
```

### Delete Quest

```http
DELETE /v1/quests/:quest_id
```

### Get User's Quest Progress

```http
GET /v1/users/:user_id/quests
```

**Response:**
```json
{
  "quests": [
    {
      "quest_id": 1,
      "quest_name": "Welcome Quest",
      "status": "completed",
      "progress": {
        "current_step": 2,
        "total_steps": 2,
        "completed_steps": [1, 2]
      },
      "started_at": "2025-10-15T10:00:00Z",
      "completed_at": "2025-10-15T10:30:00Z"
    },
    {
      "quest_id": 2,
      "quest_name": "First Swap",
      "status": "in_progress",
      "progress": {
        "current_step": 1,
        "total_steps": 2,
        "completed_steps": [1]
      },
      "started_at": "2025-10-20T14:00:00Z",
      "completed_at": null
    }
  ]
}
```

### Start Quest

```http
POST /v1/users/:user_id/quests/:quest_id/start
```

### Complete Quest Step

```http
POST /v1/users/:user_id/quests/:quest_id/steps/:step_id/complete
```

**Request Body:**
```json
{
  "verification_data": {
    "transaction_signature": "...",
    "timestamp": "2025-10-30T12:00:00Z"
  }
}
```

---

## 🏆 Points & Rewards

### Get User Points History

```http
GET /v1/users/:user_id/points
```

**Query Parameters:**
- `from_date` — Filter by date range
- `to_date` — Filter by date range
- `limit` — Number of results
- `offset` — Pagination offset

**Response:**
```json
{
  "total_points": 1250,
  "history": [
    {
      "id": 123,
      "points": 100,
      "reason": "Completed Welcome Quest",
      "quest_id": 1,
      "timestamp": "2025-10-15T10:30:00Z"
    },
    {
      "id": 124,
      "points": 50,
      "reason": "Daily login streak (7 days)",
      "timestamp": "2025-10-22T00:01:00Z"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

### Award Points

```http
POST /v1/users/:user_id/points
```

**Request Body:**
```json
{
  "points": 100,
  "reason": "Custom reward for exceptional contribution",
  "quest_id": null
}
```

### Get User Badges

```http
GET /v1/users/:user_id/badges
```

**Response:**
```json
{
  "badges": [
    {
      "id": 1,
      "name": "Early Adopter",
      "description": "Joined in the first week",
      "image_url": "https://...",
      "rarity": "legendary",
      "earned_at": "2025-10-01T08:20:00Z"
    }
  ]
}
```

### Award Badge

```http
POST /v1/users/:user_id/badges/:badge_id
```

---

## 📊 Leaderboards

### Get Leaderboard

```http
GET /v1/leaderboards/:timeframe
```

**Path Parameters:**
- `timeframe` — daily, weekly, monthly, all_time

**Query Parameters:**
- `limit` — Number of results (default: 100)
- `metric` — Ranking metric (points, quests_completed, referrals)

**Response:**
```json
{
  "timeframe": "weekly",
  "metric": "points",
  "updated_at": "2025-10-30T15:00:00Z",
  "leaderboard": [
    {
      "rank": 1,
      "user_id": 12345,
      "username": "crypto_whale",
      "value": 2500,
      "badge": "👑 Champion"
    },
    {
      "rank": 2,
      "user_id": 67890,
      "username": "degen_trader",
      "value": 2100,
      "badge": "🥈 Runner-up"
    }
  ],
  "user_rank": {
    "rank": 42,
    "value": 850
  }
}
```

### Get User Rank

```http
GET /v1/leaderboards/:timeframe/users/:user_id
```

**Response:**
```json
{
  "timeframe": "weekly",
  "rank": 42,
  "value": 850,
  "total_users": 1247,
  "percentile": 96.6
}
```

---

## 📈 Analytics

### Get Community Stats

```http
GET /v1/analytics/community
```

**Response:**
```json
{
  "total_users": 5432,
  "active_users_7d": 1247,
  "active_users_30d": 3891,
  "new_users_7d": 234,
  "total_quests_completed": 12453,
  "avg_quests_per_user": 2.3,
  "retention_7d": 0.61,
  "retention_30d": 0.42,
  "engagement_rate": 0.52,
  "community_health_score": 87
}
```

### Get Quest Analytics

```http
GET /v1/analytics/quests
```

**Response:**
```json
{
  "quests": [
    {
      "quest_id": 1,
      "name": "Welcome Quest",
      "started": 892,
      "completed": 794,
      "completion_rate": 0.89,
      "avg_completion_time_minutes": 15,
      "drop_off_points": [
        {
          "step": 2,
          "drop_rate": 0.11
        }
      ]
    }
  ]
}
```

### Get User Analytics

```http
GET /v1/analytics/users/:user_id
```

**Response:**
```json
{
  "user_id": 12345,
  "engagement_score": 92,
  "activity_pattern": {
    "most_active_hour": 14,
    "most_active_day": "wednesday",
    "avg_daily_actions": 4.2
  },
  "contribution_breakdown": {
    "quests": 0.45,
    "social": 0.30,
    "referrals": 0.15,
    "other": 0.10
  },
  "predicted_churn_risk": "low"
}
```

---

## 🔔 Webhooks

Register webhooks to receive real-time events.

### Register Webhook

```http
POST /v1/webhooks
```

**Request Body:**
```json
{
  "url": "https://your-domain.com/webhook",
  "events": [
    "quest.completed",
    "user.joined",
    "points.awarded",
    "badge.earned"
  ],
  "secret": "your_webhook_secret"
}
```

### Webhook Events

#### Quest Completed
```json
{
  "event": "quest.completed",
  "timestamp": "2025-10-30T15:30:00Z",
  "data": {
    "user_id": 12345,
    "quest_id": 5,
    "quest_name": "First Swap",
    "points_earned": 200,
    "badge_earned": {
      "id": 3,
      "name": "Trader"
    }
  }
}
```

#### User Joined
```json
{
  "event": "user.joined",
  "timestamp": "2025-10-30T15:30:00Z",
  "data": {
    "user_id": 99999,
    "telegram_id": 123456789,
    "username": "new_user",
    "referred_by": 12345
  }
}
```

#### Points Awarded
```json
{
  "event": "points.awarded",
  "timestamp": "2025-10-30T15:30:00Z",
  "data": {
    "user_id": 12345,
    "points": 100,
    "reason": "Completed Welcome Quest",
    "new_total": 1350
  }
}
```

### Webhook Signature Verification

```python
import hmac
import hashlib

def verify_webhook(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature"""
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)
```

---

## 🔄 BPMN Process API

Interact with Camunda BPMN processes directly.

### Start Process Instance

```http
POST /engine-rest/process-definition/key/:process_key/start
```

**Request Body:**
```json
{
  "variables": {
    "user_id": {"value": 12345, "type": "Long"},
    "quest_id": {"value": 5, "type": "Long"}
  },
  "businessKey": "quest_5_user_12345"
}
```

### Get Process Instance

```http
GET /engine-rest/process-instance/:instance_id
```

### Get Process Variables

```http
GET /engine-rest/process-instance/:instance_id/variables
```

### Complete External Task

```http
POST /engine-rest/external-task/:task_id/complete
```

**Request Body:**
```json
{
  "workerId": "worker_123",
  "variables": {
    "verification_passed": {"value": true, "type": "Boolean"},
    "result": {"value": "Success", "type": "String"}
  }
}
```

---

## 💻 SDK Examples

### Python SDK

```python
# pip install sol-atlas-sdk

from sol_atlas import AtlasClient

client = AtlasClient(api_key="your_api_key")

# Get user
user = client.users.get(user_id=12345)
print(f"User {user.username} has {user.total_points} points")

# Start quest
client.quests.start(user_id=12345, quest_id=5)

# Award points
client.points.award(
    user_id=12345,
    points=100,
    reason="Custom reward"
)

# Get leaderboard
leaderboard = client.leaderboards.get(timeframe="weekly", limit=10)
for entry in leaderboard:
    print(f"{entry.rank}. {entry.username}: {entry.value} points")
```

### JavaScript/TypeScript SDK

```typescript
// npm install @sol-atlas/sdk

import { AtlasClient } from '@sol-atlas/sdk';

const client = new AtlasClient({ apiKey: 'your_api_key' });

// Get user
const user = await client.users.get(12345);
console.log(`User ${user.username} has ${user.totalPoints} points`);

// Start quest
await client.quests.start({ userId: 12345, questId: 5 });

// Award points
await client.points.award({
  userId: 12345,
  points: 100,
  reason: 'Custom reward'
});

// Get leaderboard
const leaderboard = await client.leaderboards.get({
  timeframe: 'weekly',
  limit: 10
});
```

---

## 🎓 Rate Limits

- **Standard:** 1000 requests/hour per API key
- **Pro:** 10,000 requests/hour per API key
- **Enterprise:** Unlimited

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1635724800
```

---

## 🔗 Next Steps

- **[Integration Guide →](INTEGRATIONS.md)** — Connect external services
- **[Architecture →](ARCHITECTURE.md)** — Understand the system
- **[Features →](FEATURES.md)** — Explore capabilities

---

[← Back to Main README](../README.md)
