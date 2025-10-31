# Contributing to SOL Atlas

Thank you for your interest in contributing to SOL Atlas! We're building the future of Telegram-native community platforms for Web3, and we'd love your help.

---

## 🌟 Ways to Contribute

There are many ways to contribute to SOL Atlas:

### 1. 🤖 Bot Templates
Create pre-built bot templates for specific use cases:
- DeFi trading communities
- NFT holder groups
- DAO governance bots
- Gaming guilds
- Educational communities

### 2. 🎯 Quest Patterns
Design reusable quest patterns:
- Social engagement quests
- On-chain verification quests
- Learning & education quests
- Referral & growth quests
- Cross-community quests

### 3. 🔌 Integrations
Build connectors for popular services:
- Solana protocols (DEXes, NFT marketplaces, etc.)
- Analytics platforms (Dune, Flipside, etc.)
- Social platforms (Twitter, Discord, Farcaster)
- Payment systems (Streamflow, Squads, etc.)

### 4. 📚 Documentation
Improve our docs:
- Write tutorials
- Create video guides
- Translate documentation
- Fix typos and clarify explanations

### 5. 🐛 Bug Reports
Help us improve quality:
- Report bugs
- Suggest improvements
- Test new features

### 6. 💻 Code Contributions
Submit pull requests:
- Fix bugs
- Add features
- Improve performance
- Enhance security

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.9+ (for workers)
- Node.js 18+ (for GUI)
- Git
- Basic knowledge of Telegram Bot API
- (Optional) Solana development experience

### Setup Development Environment

1. **Fork and clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/sol-atlas.git
cd sol-atlas
```

2. **Copy environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start the development environment:**
```bash
docker-compose -f docker-compose.dev.yaml up -d
```

4. **Verify services are running:**
```bash
docker-compose ps
```

You should see:
- `sol-atlas-engine` (Camunda BPMN)
- `sol-atlas-bot` (Telegram bot)
- `sol-atlas-workers` (External workers)
- `sol-atlas-gui` (Web interface)
- `sol-atlas-db` (PostgreSQL)
- `sol-atlas-redis` (Cache)

---

## 📝 Development Workflow

### Branch Strategy

We use a simplified Git flow:

- `main` — Production-ready code
- `develop` — Integration branch for features
- `feature/*` — New features
- `fix/*` — Bug fixes
- `docs/*` — Documentation updates

### Making Changes

1. **Create a branch:**
```bash
git checkout -b feature/my-awesome-feature
```

2. **Make your changes**
   - Write clear, commented code
   - Follow existing code style
   - Add tests for new features

3. **Test your changes:**
```bash
# Run tests
docker-compose exec workers pytest

# Run linting
docker-compose exec workers flake8

# Test bot manually in Telegram
```

4. **Commit with clear messages:**
```bash
git add .
git commit -m "feat: add Jupiter swap verification worker

- Implement Jupiter program ID detection
- Add USD amount calculation
- Add tests for swap verification"
```

We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `style:` — Code style (formatting, etc.)
- `refactor:` — Code refactoring
- `test:` — Adding tests
- `chore:` — Maintenance tasks

5. **Push and create Pull Request:**
```bash
git push origin feature/my-awesome-feature
```

Then open a Pull Request on GitHub with:
- Clear title and description
- Reference any related issues
- Screenshots/videos if UI changes
- Test results

---

## 🧪 Testing

### Running Tests

```bash
# All tests
docker-compose exec workers pytest

# Specific test file
docker-compose exec workers pytest tests/test_quest_worker.py

# With coverage
docker-compose exec workers pytest --cov=worker tests/
```

### Writing Tests

```python
# tests/test_quest_worker.py
import pytest
from worker.quest_worker import award_points_worker

def test_award_points_success():
    """Test successful point award"""
    # Setup
    task = MockExternalTask({
        "user_id": 12345,
        "points": 100,
        "reason": "Test quest"
    })

    # Execute
    result = award_points_worker(task)

    # Assert
    assert result.is_success()
    assert result.get_variable("points_awarded") == 100

def test_award_points_invalid_user():
    """Test point award with invalid user"""
    task = MockExternalTask({
        "user_id": 99999,  # Non-existent user
        "points": 100,
        "reason": "Test quest"
    })

    result = award_points_worker(task)

    assert result.is_failure()
```

---

## 📐 Code Style

### Python

We follow [PEP 8](https://pep8.org/) with some modifications:

```python
# Good
async def verify_wallet_ownership(
    wallet_address: str,
    signed_message: str,
    signature: str
) -> bool:
    """Verify user owns the wallet.

    Args:
        wallet_address: Solana wallet public key
        signed_message: Message that was signed
        signature: Base64 encoded signature

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        is_valid = verify_signature(
            message=signed_message,
            signature=signature,
            public_key=wallet_address
        )
        return is_valid
    except Exception as e:
        logger.error(f"Wallet verification failed: {e}")
        return False
```

### JavaScript/TypeScript

We use Prettier and ESLint:

```typescript
// Good
async function getUserPoints(userId: number): Promise<number> {
  const cacheKey = `user:${userId}:points`;

  // Try cache first
  const cached = await redis.get(cacheKey);
  if (cached) {
    return parseInt(cached);
  }

  // Query database
  const result = await db.query(
    'SELECT total_points FROM users WHERE id = $1',
    [userId]
  );

  // Cache for 5 minutes
  await redis.setex(cacheKey, 300, result.rows[0].total_points);

  return result.rows[0].total_points;
}
```

### SQL

```sql
-- Good: Clear formatting, meaningful names
SELECT
    u.id,
    u.username,
    SUM(pl.points) as total_points,
    COUNT(DISTINCT qp.quest_id) as quests_completed,
    ROW_NUMBER() OVER (ORDER BY SUM(pl.points) DESC) as rank
FROM users u
LEFT JOIN points_log pl ON u.id = pl.user_id
    AND pl.timestamp > NOW() - INTERVAL '7 days'
LEFT JOIN quest_progress qp ON u.id = qp.user_id
    AND qp.completed_at > NOW() - INTERVAL '7 days'
GROUP BY u.id, u.username
ORDER BY total_points DESC
LIMIT 100;
```

---

## 🎨 Creating Bot Templates

Share your bot template with the community:

1. **Create template directory:**
```bash
mkdir -p templates/my-template
cd templates/my-template
```

2. **Add template files:**
```
my-template/
├── README.md           # Template description
├── config.yaml        # Bot configuration
├── quests/            # Quest definitions
│   ├── welcome.yaml
│   └── daily.yaml
├── workflows/         # BPMN workflows
│   └── onboarding.bpmn
└── assets/            # Images, badges, etc.
    └── badges/
```

3. **Document your template:**
```markdown
# My Template Name

## Description
Brief description of what this template does and who it's for.

## Features
- Feature 1
- Feature 2

## Configuration
Required environment variables:
- `VARIABLE_NAME` - Description

## Usage
Steps to deploy and customize this template.
```

4. **Submit Pull Request**

---

## 🔌 Creating Integrations

### Integration Structure

```
worker/integrations/
└── my_protocol/
    ├── __init__.py
    ├── client.py          # Protocol interaction
    ├── worker.py          # Camunda external worker
    ├── config.yaml        # Configuration schema
    ├── tests/
    │   └── test_worker.py
    └── README.md          # Integration docs
```

### Integration Template

```python
# worker/integrations/my_protocol/client.py
from typing import Dict, Optional
import aiohttp

class MyProtocolClient:
    """Client for interacting with MyProtocol"""

    def __init__(self, api_key: str, rpc_url: str):
        self.api_key = api_key
        self.rpc_url = rpc_url

    async def verify_action(
        self,
        wallet_address: str,
        action_type: str,
        min_amount: float = 0
    ) -> Optional[Dict]:
        """Verify user completed specific action"""
        # Implementation here
        pass

# worker/integrations/my_protocol/worker.py
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from .client import MyProtocolClient

def my_protocol_worker(task: ExternalTask) -> TaskResult:
    """External worker for MyProtocol verification"""

    user_id = task.get_variable("user_id")
    wallet_address = task.get_variable("wallet_address")
    action_type = task.get_variable("action_type")

    client = MyProtocolClient(
        api_key=os.getenv("MY_PROTOCOL_API_KEY"),
        rpc_url=os.getenv("SOLANA_RPC_URL")
    )

    try:
        result = await client.verify_action(
            wallet_address=wallet_address,
            action_type=action_type
        )

        if result:
            return task.complete({
                "verification_passed": True,
                "transaction_signature": result['signature'],
                "amount": result['amount']
            })
        else:
            return task.complete({
                "verification_passed": False,
                "reason": "Action not found"
            })

    except Exception as e:
        return task.failure(
            error_message=str(e),
            error_details="MyProtocol verification failed"
        )

# Register worker
worker = ExternalTaskWorker(
    worker_id="my_protocol_worker",
    base_url=os.getenv("CAMUNDA_URL")
)
worker.subscribe("my_protocol_verification", my_protocol_worker)
```

---

## 📚 Documentation Guidelines

### Writing Good Docs

- **Be clear and concise**
- **Use examples** — Show, don't just tell
- **Include code snippets** — Copy-pasteable examples
- **Add screenshots** — For UI features
- **Test your instructions** — Follow them yourself

### Documentation Structure

```markdown
# Feature Name

## Overview
What is this feature and why does it exist?

## Quick Start
Minimal example to get started quickly.

## Configuration
Detailed configuration options.

## Examples
Real-world use cases and examples.

## API Reference
(If applicable) Detailed API documentation.

## Troubleshooting
Common issues and solutions.
```

---

## 🤝 Community

### Join the Atlas Network

- **Telegram:** [@SolanaAtlas](https://t.me/SolanaAtlas)
- **Discord:** Coming soon
- **Twitter:** [@GuruNetwork](https://twitter.com/GuruNetwork)

### Getting Help

- Browse existing [GitHub Issues](https://github.com/dex-guru/sol-atlas/issues)
- Ask in our Telegram community
- Check the [documentation](docs/)

### Code of Conduct

We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/0/code_of_conduct/).

**Summary:**
- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community

---

## 🏆 Recognition

Contributors are recognized in multiple ways:

### 1. Contributors Page
Your GitHub profile will appear on our website's contributors page.

### 2. Special Badge
Active contributors get a special "Atlas Builder" badge in the SOL Atlas community.

### 3. Early Access
Contributors get early access to new features and beta programs.

### 4. Revenue Share (for major contributions)
Significant contributions may qualify for revenue share from enterprise deployments.

---

## 📋 Pull Request Checklist

Before submitting, ensure:

- [ ] Code follows style guidelines
- [ ] Tests are added for new features
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] PR description is clear and complete
- [ ] Related issues are referenced

---

## ❓ Questions?

If you have questions about contributing, feel free to:

- Open a [GitHub Discussion](https://github.com/dex-guru/sol-atlas/discussions)
- Ask in our [Telegram community](https://t.me/SolanaAtlas)
- Email us at: [email protected]

---

**Thank you for helping build the future of Web3 communities! 🚀**

Your contributions help projects turn followers into believers, and that's what matters most.

---

[← Back to Main README](../README.md)
