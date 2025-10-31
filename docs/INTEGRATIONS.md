# SOL Atlas Integration Guide

Connect SOL Atlas with external services, APIs, and Solana protocols to supercharge your community.

---

## 📑 Table of Contents

1. [Solana Protocols](#solana-protocols)
2. [Wallet Providers](#wallet-providers)
3. [Social Platforms](#social-platforms)
4. [Analytics Services](#analytics-services)
5. [Payment & Token Distribution](#payment--token-distribution)
6. [Custom Integrations](#custom-integrations)

---

## ⛓️ Solana Protocols

### Jupiter Aggregator

Track and reward swaps through Jupiter.

```python
# worker/jupiter_integration.py
from jupiter_python_sdk.jupiter import Jupiter

class JupiterIntegration:
    def __init__(self, rpc_url: str):
        self.jupiter = Jupiter(rpc_url)

    async def verify_swap(
        self,
        wallet_address: str,
        min_amount_usd: float,
        time_window_hours: int = 24
    ) -> Optional[Dict]:
        """Verify user completed a swap on Jupiter"""

        # Get user's recent transactions
        transactions = await self.get_recent_transactions(
            wallet_address,
            time_window_hours
        )

        for tx in transactions:
            # Check if transaction is a Jupiter swap
            if self.is_jupiter_swap(tx):
                swap_details = self.parse_swap(tx)

                if swap_details['usd_value'] >= min_amount_usd:
                    return {
                        'signature': tx['signature'],
                        'amount': swap_details['usd_value'],
                        'from_token': swap_details['from_token'],
                        'to_token': swap_details['to_token'],
                        'timestamp': tx['timestamp']
                    }

        return None

    def is_jupiter_swap(self, transaction: Dict) -> bool:
        """Check if transaction is a Jupiter swap"""
        # Jupiter program IDs
        JUPITER_V6 = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"

        for instruction in transaction['instructions']:
            if instruction['programId'] == JUPITER_V6:
                return True

        return False

# Quest configuration
"""
quest:
  name: "First Jupiter Swap"
  type: "onchain"
  verification:
    protocol: "jupiter"
    action: "swap"
    min_amount_usd: 10
  reward:
    points: 200
    badge: "Degen Swapper"
"""
```

### Raydium / Orca (AMMs)

```python
# worker/amm_integration.py
class AMMIntegration:
    # Raydium Program IDs
    RAYDIUM_LIQUIDITY_V4 = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
    RAYDIUM_AMM_V4 = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"

    # Orca Program IDs
    ORCA_SWAP_V1 = "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP"
    ORCA_SWAP_V2 = "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"

    async def verify_liquidity_provision(
        self,
        wallet_address: str,
        protocol: str = "raydium",
        min_amount_usd: float = 100
    ) -> Optional[Dict]:
        """Verify user added liquidity"""
        # Implementation similar to Jupiter
        pass

# Quest configuration
"""
quest:
  name: "Provide Liquidity"
  type: "onchain"
  verification:
    protocol: "raydium"
    action: "add_liquidity"
    min_amount_usd: 100
  reward:
    points: 500
    badge: "Liquidity Provider"
"""
```

### Solana NFT Marketplaces

```python
# worker/nft_marketplace_integration.py
class NFTMarketplaceIntegration:
    # Magic Eden
    MAGIC_EDEN_V2 = "M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K"

    # Tensor
    TENSOR = "TSWAPaqyCSx2KABk68Shruf4rp7CxcNi8hAsbdwmHbN"

    async def verify_nft_purchase(
        self,
        wallet_address: str,
        collection_address: Optional[str] = None
    ) -> Optional[Dict]:
        """Verify NFT purchase on marketplace"""

        transactions = await self.get_recent_transactions(wallet_address)

        for tx in transactions:
            if self.is_nft_purchase(tx):
                nft_details = self.parse_nft_transaction(tx)

                # If specific collection required
                if collection_address:
                    if nft_details['collection'] != collection_address:
                        continue

                return {
                    'signature': tx['signature'],
                    'nft_mint': nft_details['mint'],
                    'price_sol': nft_details['price'],
                    'marketplace': nft_details['marketplace'],
                    'timestamp': tx['timestamp']
                }

        return None

# Quest configuration
"""
quest:
  name: "Collect Our NFT"
  type: "onchain"
  verification:
    protocol: "magic_eden"
    action: "nft_purchase"
    collection: "OUR_COLLECTION_ADDRESS"
  reward:
    points: 1000
    badge: "True Collector"
    unlock: "nft_holder_channel"
"""
```

---

## 💳 Wallet Providers

### Phantom Wallet

```javascript
// bot/wallet_integrations/phantom.js
class PhantomIntegration {
  constructor() {
    this.deepLinkUrl = "https://phantom.app/ul/v1/";
  }

  generateConnectLink(callbackUrl, nonce) {
    const params = new URLSearchParams({
      dapp_encryption_public_key: process.env.DAPP_PUBLIC_KEY,
      cluster: "mainnet-beta",
      app_url: "https://yourdomain.com",
      redirect_link: callbackUrl,
    });

    return `${this.deepLinkUrl}connect?${params.toString()}`;
  }

  async verifyConnection(signature, nonce, publicKey) {
    // Verify signature
    const message = `Sign this message to prove you own wallet: ${nonce}`;
    const isValid = await verifySignature(message, signature, publicKey);

    if (isValid) {
      // Store wallet connection in database
      await db.query(
        "UPDATE users SET wallet_address = $1, wallet_verified = true WHERE telegram_id = $2",
        [publicKey, userId]
      );
    }

    return isValid;
  }
}

// Telegram bot usage
bot.onText(/\/wallet/, async (msg) => {
  const userId = msg.from.id;
  const nonce = generateNonce();

  // Store nonce temporarily
  await redis.setex(`wallet_nonce:${userId}`, 300, nonce);

  const connectLink = phantom.generateConnectLink(
    `https://yourdomain.com/wallet/callback?user=${userId}`,
    nonce
  );

  await bot.sendMessage(
    userId,
    `Click the button to connect your Phantom wallet:`,
    {
      reply_markup: {
        inline_keyboard: [
          [{ text: "🦊 Connect Phantom", url: connectLink }]
        ]
      }
    }
  );
});
```

### Solflare Wallet

```javascript
// Similar implementation to Phantom
class SolflareIntegration {
  // Solflare uses similar deep linking protocol
  // Implementation details...
}
```

---

## 📱 Social Platforms

### Twitter/X Integration

Track mentions, likes, retweets for social quests.

```python
# worker/twitter_integration.py
import tweepy

class TwitterIntegration:
    def __init__(self, bearer_token: str):
        self.client = tweepy.Client(bearer_token=bearer_token)

    async def verify_tweet(
        self,
        username: str,
        must_mention: List[str],
        must_include_hashtags: List[str],
        min_length: int = 100
    ) -> Optional[Dict]:
        """Verify user posted qualifying tweet"""

        # Get user's recent tweets
        user = self.client.get_user(username=username)
        tweets = self.client.get_users_tweets(
            id=user.data.id,
            max_results=10,
            tweet_fields=['created_at', 'public_metrics']
        )

        for tweet in tweets.data:
            # Check all requirements
            if not all(mention in tweet.text for mention in must_mention):
                continue

            if not all(f"#{tag}" in tweet.text for tag in must_include_hashtags):
                continue

            if len(tweet.text) < min_length:
                continue

            # Tweet qualifies!
            return {
                'tweet_id': tweet.id,
                'text': tweet.text,
                'likes': tweet.public_metrics['like_count'],
                'retweets': tweet.public_metrics['retweet_count'],
                'created_at': tweet.created_at
            }

        return None

    async def get_engagement_score(self, tweet_id: str) -> int:
        """Calculate engagement score for bonus points"""
        tweet = self.client.get_tweet(
            id=tweet_id,
            tweet_fields=['public_metrics']
        )

        metrics = tweet.data.public_metrics
        score = (
            metrics['like_count'] * 1 +
            metrics['retweet_count'] * 3 +
            metrics['reply_count'] * 2 +
            metrics['quote_count'] * 5
        )

        return score

# Quest configuration
"""
quest:
  name: "Twitter Amplifier"
  type: "social"
  platform: "twitter"
  requirements:
    must_mention: ["@YourProject"]
    must_include_hashtags: ["Solana", "YourTag"]
    min_length: 100
  reward:
    base_points: 100
    bonus_points_per_engagement: 1
    max_bonus: 500
    badge: "Amplifier"
"""
```

### Discord Integration

```python
# worker/discord_integration.py
import discord
from discord.ext import commands

class DiscordBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def verify_server_membership(
        self,
        discord_id: int,
        guild_id: int
    ) -> bool:
        """Verify user is member of Discord server"""
        guild = self.get_guild(guild_id)
        if not guild:
            return False

        member = guild.get_member(discord_id)
        return member is not None

    async def assign_role_after_quest(
        self,
        discord_id: int,
        guild_id: int,
        role_name: str
    ):
        """Assign Discord role after quest completion"""
        guild = self.get_guild(guild_id)
        member = guild.get_member(discord_id)
        role = discord.utils.get(guild.roles, name=role_name)

        if member and role:
            await member.add_roles(role)

# Quest configuration
"""
quest:
  name: "Join Our Discord"
  type: "social"
  platform: "discord"
  requirements:
    action: "join_server"
    guild_id: "YOUR_GUILD_ID"
  reward:
    points: 50
    badge: "Discord Member"
    discord_role: "Community Member"
"""
```

---

## 📊 Analytics Services

### Dune Analytics

```python
# worker/dune_integration.py
from dune_client.client import DuneClient

class DuneIntegration:
    def __init__(self, api_key: str):
        self.dune = DuneClient(api_key)

    async def get_wallet_activity_score(
        self,
        wallet_address: str,
        query_id: int
    ) -> Dict:
        """Get wallet activity score from Dune query"""

        # Execute parameterized query
        result = self.dune.run_query(
            query_id=query_id,
            parameters={
                'wallet_address': wallet_address
            }
        )

        return result.data

# Example Dune query (SQL)
"""
SELECT
    COUNT(DISTINCT tx_hash) as total_transactions,
    COUNT(DISTINCT to_address) as unique_interactions,
    SUM(amount_usd) as total_volume_usd,
    DATE_DIFF('day', MIN(block_time), MAX(block_time)) as account_age_days
FROM solana.transactions
WHERE from_address = {{wallet_address}}
AND block_time > NOW() - INTERVAL '90' DAY
"""
```

### Helius / QuickNode RPC

```python
# worker/helius_integration.py
import aiohttp

class HeliusIntegration:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = f"https://mainnet.helius-rpc.com/?api-key={api_key}"

    async def get_enhanced_transactions(
        self,
        wallet_address: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get parsed transactions with better data"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json={
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "getSignaturesForAddress",
                    "params": [wallet_address, {"limit": limit}]
                }
            ) as response:
                data = await response.json()
                return data['result']

    async def get_nft_metadata(self, mint_address: str) -> Dict:
        """Get NFT metadata including rarity"""
        # Helius provides enhanced NFT metadata
        pass
```

---

## 💰 Payment & Token Distribution

### Streamflow (Token Vesting)

```python
# worker/streamflow_integration.py
class StreamflowIntegration:
    """Distribute rewards via vested streams"""

    async def create_vesting_stream(
        self,
        recipient: str,
        amount: int,
        token_mint: str,
        release_schedule: Dict
    ):
        """Create vesting stream for reward"""

        # Example: Release 1000 tokens over 30 days
        stream = await streamflow.create({
            'recipient': recipient,
            'amount': amount,
            'token': token_mint,
            'start': datetime.now(),
            'cliff': timedelta(days=7),  # 7-day cliff
            'duration': timedelta(days=30),
            'cancelable': False
        })

        return stream.id

# Quest reward configuration
"""
quest:
  name: "Top Contributor"
  reward:
    payment_type: "vested"
    amount: 1000
    token: "YOUR_TOKEN_MINT"
    vesting:
      cliff_days: 7
      duration_days: 30
"""
```

### Squads (Multi-Sig Payments)

```python
# worker/squads_integration.py
class SquadsIntegration:
    """Pay rewards from community treasury via multi-sig"""

    async def create_payment_proposal(
        self,
        squad_address: str,
        recipients: List[Tuple[str, int]],  # (wallet, amount)
        description: str
    ):
        """Create multi-sig proposal for batch payments"""

        proposal = await squads.create_transaction({
            'squad': squad_address,
            'type': 'transfer',
            'recipients': recipients,
            'description': description,
            'auto_execute_threshold': 2  # Require 2/3 signatures
        })

        return proposal.id
```

---

## 🔧 Custom Integrations

### BPMN External Worker Template

Create your own integrations:

```python
# worker/custom_integration.py
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

def custom_worker_handler(task: ExternalTask) -> TaskResult:
    """Template for custom worker"""

    try:
        # 1. Get variables from BPMN process
        user_id = task.get_variable("user_id")
        action_data = task.get_variable("action_data")

        # 2. Perform your custom logic
        result = perform_custom_verification(user_id, action_data)

        # 3. Return success with output variables
        if result['success']:
            return task.complete({
                "verification_passed": True,
                "result_data": result['data']
            })
        else:
            return task.complete({
                "verification_passed": False,
                "reason": result['reason']
            })

    except Exception as e:
        # 4. Return failure for retry
        return task.failure(
            error_message=str(e),
            error_details="Custom verification failed",
            retries=3,
            retry_timeout=5000  # 5 seconds
        )

# Register worker
worker = ExternalTaskWorker(
    worker_id="custom_worker",
    base_url="http://engine:8080/engine-rest"
)
worker.subscribe("custom_verification_task", custom_worker_handler)
```

### REST API Integration Template

```python
# worker/rest_api_integration.py
import aiohttp

class CustomAPIIntegration:
    """Template for integrating any REST API"""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    async def verify_action(
        self,
        user_id: str,
        action_type: str,
        params: Dict
    ) -> Dict:
        """Generic API verification"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/verify",
                headers=self.headers,
                json={
                    'user_id': user_id,
                    'action': action_type,
                    'params': params
                }
            ) as response:
                return await response.json()

    async def get_user_data(self, user_id: str) -> Dict:
        """Fetch user data from external API"""

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/users/{user_id}",
                headers=self.headers
            ) as response:
                return await response.json()
```

---

## 🎓 Integration Examples

### Example 1: Multi-Protocol DeFi Quest

```yaml
quest:
  name: "DeFi Power User"
  description: "Use multiple DeFi protocols in one week"
  steps:
    - task: "Swap on Jupiter"
      verification: "jupiter_swap"
      min_amount: 50
      points: 100

    - task: "Provide liquidity on Raydium"
      verification: "raydium_add_liquidity"
      min_amount: 200
      points: 300

    - task: "Stake SOL"
      verification: "staking"
      min_amount: 1
      points: 200

  completion_bonus:
    points: 500
    badge: "DeFi Master"
```

### Example 2: Cross-Platform Social Campaign

```yaml
quest:
  name: "Social Amplification"
  description: "Spread the word across all platforms"
  steps:
    - task: "Tweet about us"
      platform: "twitter"
      requirements:
        mention: "@YourProject"
        hashtags: ["Solana", "DeFi"]
      points: 100

    - task: "Join Discord"
      platform: "discord"
      guild_id: "YOUR_GUILD_ID"
      points: 50

    - task: "Share in Telegram"
      platform: "telegram"
      channel: "@YourChannel"
      points: 50

  completion_bonus:
    points: 200
    badge: "Social Butterfly"
```

---

## 🔗 Next Steps

- **[API Reference →](API.md)** — Build custom integrations
- **[Architecture →](ARCHITECTURE.md)** — Understand the system
- **[Features →](FEATURES.md)** — See what's possible

---

[← Back to Main README](../README.md)
