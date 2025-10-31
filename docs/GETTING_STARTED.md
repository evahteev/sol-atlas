# Getting Started with SOL Atlas

Launch your Telegram community in under 5 minutes and start building believers, not just followers.

---

## 📋 Prerequisites

Before you begin, make sure you have:

- **Docker & Docker Compose** installed ([Get Docker](https://docs.docker.com/get-docker/))
- **Telegram Bot Token** from [@BotFather](https://t.me/botfather)
- **Basic knowledge** of Telegram and community management
- **(Optional)** Solana wallet for testing on-chain integrations

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/dex-guru/sol-atlas
cd sol-atlas
```

### Step 2: Configure Your Bot

Create a `.env` file in the root directory:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_NAME=YourBotName

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=sol_atlas

# GURU Engine Configuration
CAMUNDA_USER=demo
CAMUNDA_PASSWORD=demo

# Optional: Solana RPC
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

### Step 3: Launch the Platform

```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps
```

You should see:
```
NAME                    STATUS              PORTS
sol-atlas-engine        Up                  0.0.0.0:8080->8080/tcp
sol-atlas-bot           Up
sol-atlas-workers       Up
sol-atlas-gui           Up                  0.0.0.0:3000->3000/tcp
sol-atlas-db            Up                  5432/tcp
```

### Step 4: Access Your Dashboard

Open your browser and navigate to:
- **Bot Launcher:** [http://localhost:3000](http://localhost:3000)
- **GURU Engine:** [http://localhost:8080](http://localhost:8080) (login: demo/demo)

### Step 5: Connect Your Bot to Telegram

1. Open your Telegram and search for your bot name
2. Click "Start" to initiate the bot
3. You should receive a welcome message!

🎉 **Congratulations!** Your SOL Atlas bot is live.

---

## 🎮 Creating Your First Quest

Now let's create a simple quest to engage your community:

### Option 1: Using the Visual Builder (No Code)

1. Navigate to the **Quest Builder** in your dashboard ([http://localhost:3000/quests](http://localhost:3000/quests))
2. Click **"Create New Quest"**
3. Select a template:
   - **Welcome Quest** — Perfect for onboarding
   - **Social Quest** — Twitter/Discord engagement
   - **Trading Quest** — On-chain activity tracking
   - **Custom Quest** — Build from scratch

4. Configure your quest:
   ```
   Quest Name: Welcome to Our Community
   Description: Complete these steps to become a verified member

   Steps:
   ✅ Join our Telegram group
   ✅ Follow us on Twitter
   ✅ Connect your Solana wallet

   Reward: 100 points + "Early Adopter" badge
   ```

5. Click **"Publish Quest"**

### Option 2: Using BPMN (Low-Code)

For more complex workflows, use the Camunda Modeler:

1. Download [Camunda Modeler](https://camunda.com/download/modeler/)
2. Open the modeler and create a new BPMN diagram
3. Design your quest flow:

```
[Start Event] → [Join Telegram Task] → [Follow Twitter Task] →
[Connect Wallet Task] → [Award Points] → [Send Badge] → [End Event]
```

4. Save the BPMN file to `engine/resources/quests/welcome-quest.bpmn`
5. Restart the engine: `docker-compose restart engine`
6. The quest is now available in your bot!

---

## 🏆 Setting Up Leaderboards

Leaderboards drive competition and engagement. Here's how to set them up:

### 1. Navigate to Leaderboard Configuration

Go to [http://localhost:3000/leaderboards](http://localhost:3000/leaderboards)

### 2. Create a New Leaderboard

```yaml
Name: Weekly Top Contributors
Metric: Total Points
Time Period: Weekly (resets every Monday)
Display: Top 10 users
Rewards:
  - 1st Place: 1000 bonus points + "Champion" badge
  - 2nd Place: 500 bonus points + "Runner-up" badge
  - 3rd Place: 250 bonus points + "Bronze Medal" badge
```

### 3. Enable Automatic Announcements

Configure your bot to post leaderboard updates:
- **Daily snapshot:** Every day at 12:00 UTC
- **Weekly winners:** Every Monday at 9:00 UTC
- **Monthly champions:** First day of month

---

## 🤖 Configuring the AI CoPilot Steward

The CoPilot helps new members navigate your community and complete quests.

### 1. Enable CoPilot in Settings

```yaml
# config/copilot.yaml
enabled: true
model: gpt-4o-mini
personality: friendly_and_helpful
knowledge_base: ./knowledge/community_docs.md

greeting_message: |
  Hey there! 👋 I'm your Atlas CoPilot.
  I'm here to help you get started and find your way around.

  What would you like to do?
  🎯 Start a quest
  🏆 Check the leaderboard
  💡 Learn about our project
  ❓ Ask a question
```

### 2. Add Knowledge Base Content

Create a markdown file with your project info:

```bash
mkdir -p knowledge
nano knowledge/community_docs.md
```

Add content about your project:
```markdown
# About Our Project

We're building [your project description]...

## Getting Started
...

## Token Information
...

## How to Earn Rewards
...
```

### 3. Test the CoPilot

Send a message to your bot:
```
/help
```

The CoPilot will respond with contextual guidance!

---

## 🔗 Connecting to Solana

SOL Atlas can track on-chain activities and reward users for their actions.

### 1. Configure Solana RPC

Add your RPC endpoint to `.env`:
```bash
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
# Or use a premium RPC like Helius, QuickNode, or Triton
```

### 2. Create an On-Chain Quest

Example: Reward users for staking tokens

1. Go to Quest Builder
2. Create new quest: **"Stake 100 Tokens"**
3. Add an on-chain verification step:

```javascript
// Quest validation (in BPMN external worker)
async function validateStaking(userId, walletAddress) {
  const connection = new Connection(process.env.SOLANA_RPC_URL);
  const stakingAccount = await getStakingAccount(walletAddress);

  if (stakingAccount.amount >= 100) {
    await awardPoints(userId, 500);
    await sendBadge(userId, 'staker');
    return true;
  }
  return false;
}
```

4. Users can now complete the quest by staking!

---

## 📊 Understanding Analytics

Monitor your community's health through the Analytics Dashboard.

### Key Metrics to Track

1. **Engagement Rate**
   - Daily active users (DAU)
   - Messages per user
   - Quest completion rate

2. **Retention**
   - 7-day retention
   - 30-day retention
   - Churn rate

3. **Growth**
   - New members per day
   - Referral conversion rate
   - Viral coefficient

4. **Community Health**
   - Sentiment score (from message analysis)
   - Top contributors
   - Engagement distribution

### Accessing Analytics

Navigate to: [http://localhost:3000/analytics](http://localhost:3000/analytics)

Or query directly via API:
```bash
curl http://localhost:8080/api/analytics/community/summary
```

---

## 🚀 Going to Production

Ready to launch? Follow these steps:

### 1. Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Enable HTTPS for all endpoints
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Enable bot anti-spam filters
- [ ] Set up backup schedule

### 2. Infrastructure Setup

**Option A: Cloud Deployment (Recommended)**

Deploy to your preferred cloud provider:
- **AWS:** Use ECS or EKS
- **Google Cloud:** Use Cloud Run or GKE
- **DigitalOcean:** Use App Platform or Kubernetes

**Option B: VPS Deployment**

Requirements:
- 4GB RAM minimum
- 2 CPU cores
- 50GB storage
- Ubuntu 22.04 LTS

### 3. Domain & SSL

```bash
# Install Nginx
sudo apt install nginx

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

### 4. Monitoring Setup

Install monitoring tools:
```bash
# Prometheus for metrics
docker-compose -f docker-compose.monitoring.yaml up -d

# Grafana for dashboards
# Access at http://localhost:3001
```

### 5. Backup Configuration

Set up automated backups:
```bash
# Add to crontab
0 2 * * * /usr/local/bin/backup-sol-atlas.sh
```

---

## 🆘 Troubleshooting

### Bot Not Responding

1. Check bot token is correct
2. Verify bot is running: `docker-compose logs bot`
3. Test Telegram API: `curl https://api.telegram.org/bot<TOKEN>/getMe`

### Database Connection Errors

```bash
# Check database is running
docker-compose ps sol-atlas-db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### BPMN Workflows Not Executing

1. Verify engine is running: `docker-compose logs engine`
2. Check workflow deployment: Go to http://localhost:8080/camunda
3. Review worker logs: `docker-compose logs workers`

### Performance Issues

```bash
# Check resource usage
docker stats

# Increase resources in docker-compose.yaml
services:
  engine:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
```

---

## 🎓 Next Steps

Now that your bot is running, explore these advanced features:

1. **[Community Pillars Guide](COMMUNITY_PILLARS.md)** — Learn the framework
2. **[Features Deep Dive](FEATURES.md)** — Explore all capabilities
3. **[Architecture Guide](ARCHITECTURE.md)** — Understand the system
4. **[Integration Guide](INTEGRATIONS.md)** — Connect external services
5. **[API Documentation](API.md)** — Build custom integrations

---

## 💬 Need Help?

- **Community:** Join [@SolanaAtlas](https://t.me/SolanaAtlas) on Telegram
- **Issues:** Report bugs on [GitHub](https://github.com/dex-guru/sol-atlas/issues)
- **Docs:** Browse [full documentation](README.md)

---

**Ready to grow your community?** 🚀

[← Back to Main README](../README.md) | [Next: Community Pillars →](COMMUNITY_PILLARS.md)
