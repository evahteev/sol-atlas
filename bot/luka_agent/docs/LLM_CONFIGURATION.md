# LLM Configuration Guide

## Architecture Overview

LLM configuration in luka_agent uses a **3-tier priority system** that separates infrastructure defaults from user-specific settings:

```
Runtime Parameters > Environment Variables > Hardcoded Defaults
     (user)               (deployment)            (system)
```

This design enables:
- **CLI/Worker**: Simple env-based configuration
- **Web/Telegram**: Per-user LLM preferences
- **All platforms**: Consistent fallback behavior

## Priority System

### 1. Runtime Parameters (Highest Priority)
User-specific settings passed when creating state. Allows individual users to choose their LLM.

**Use case:** User A wants GPT-4o, User B wants Claude Sonnet.

### 2. Environment Variables (Middle Priority)
Deployment defaults set in `.env`. Used when no runtime override provided.

**Use case:** Dev environment uses local Ollama, production uses OpenAI.

### 3. Hardcoded Defaults (Lowest Priority)
System fallbacks when neither runtime nor env vars provided.

**Use case:** Fresh install with no `.env` file.

## Configuration Options

### Available Environment Variables

```bash
# .env file
DEFAULT_LLM_PROVIDER=ollama          # ollama, openai, anthropic
DEFAULT_LLM_MODEL=llama3.2           # Model name
DEFAULT_LLM_TEMPERATURE=0.7          # 0.0-1.0
DEFAULT_LLM_MAX_TOKENS=2000          # Max response length
DEFAULT_LLM_STREAMING=true           # Stream responses
```

### Supported Providers

#### Ollama (Local)
```bash
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=llama3.2
OLLAMA_URL=http://localhost:11434
```

#### OpenAI (Cloud)
```bash
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

#### Anthropic (Cloud)
```bash
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_LLM_MODEL=claude-sonnet-4
ANTHROPIC_API_KEY=sk-ant-...
```

## Usage Examples

### CLI / Worker Platform

**Scenario:** Background jobs, CLI commands
**Behavior:** Always uses environment variables

```bash
# Set in .env
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=gpt-oss

# CLI automatically uses these
./luka-agent.sh run general_luka "Hello"
# → Uses ollama/gpt-oss from .env
```

### Web Platform

**Scenario:** User-specific model selection in web UI
**Behavior:** Users can override defaults

```python
# In copilotkit_adapter.py or ag_ui_gateway

from luka_agent import create_initial_state

# User chose GPT-4o in settings
user_preferences = get_user_preferences(user_id)

state = create_initial_state(
    user_message=message,
    user_id=user_id,
    thread_id=thread_id,
    platform="web",
    # Runtime overrides (user-specific)
    llm_provider=user_preferences.llm_provider,  # "openai"
    llm_model=user_preferences.llm_model,        # "gpt-4o"
    llm_temperature=user_preferences.temperature, # 0.4
)
# → Uses openai/gpt-4o, ignoring .env defaults
```

### Telegram Platform

**Scenario:** Premium users get better models
**Behavior:** Different models per user tier

```python
# In telegram_adapter.py or luka_bot message handler

from luka_agent import create_initial_state

async def handle_message(message, user):
    # Determine model based on subscription tier
    if user.is_premium:
        llm_provider = "openai"
        llm_model = "gpt-4o"
    elif user.is_subscribed:
        llm_provider = "openai"
        llm_model = "gpt-4o-mini"
    else:
        # Free tier uses env defaults (e.g., local Ollama)
        llm_provider = None
        llm_model = None

    state = create_initial_state(
        user_message=message.text,
        user_id=user.id,
        thread_id=f"tg_{user.id}",
        platform="telegram",
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
    # Premium → gpt-4o
    # Subscribed → gpt-4o-mini
    # Free → env default (ollama/llama3.2)
```

## Real-World Scenarios

### Scenario 1: Multi-Tenant SaaS

**Setup:**
- Shared infrastructure with different customer tiers
- Each customer can choose their preferred model
- Deployment default is cost-effective local model

```python
# .env (deployment default)
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=llama3.2

# Customer A (Enterprise tier)
state_a = create_initial_state(
    ...,
    llm_provider="anthropic",
    llm_model="claude-sonnet-4",
)

# Customer B (Standard tier)
state_b = create_initial_state(
    ...,
    llm_provider="openai",
    llm_model="gpt-4o-mini",
)

# Customer C (Free tier)
state_c = create_initial_state(
    ...,
    # No overrides - uses env default
)
```

### Scenario 2: A/B Testing

**Setup:**
- Test GPT-4o vs Claude Sonnet for quality
- 50% of users get each model
- Easy rollback to env default if needed

```python
import random

def get_llm_for_ab_test(user_id):
    if user_id % 2 == 0:
        return "openai", "gpt-4o"
    else:
        return "anthropic", "claude-sonnet-4"

provider, model = get_llm_for_ab_test(user_id)

state = create_initial_state(
    ...,
    llm_provider=provider,
    llm_model=model,
)
```

### Scenario 3: Cost Optimization

**Setup:**
- Simple queries use cheap local model
- Complex analysis uses expensive cloud model
- Smart routing based on query complexity

```python
def get_optimal_llm(query: str):
    # Simple heuristic (in production, use actual complexity analysis)
    if len(query) < 50 and "?" not in query:
        # Simple chat - use local
        return None, None  # Use env defaults
    else:
        # Complex query - use cloud
        return "openai", "gpt-4o"

provider, model = get_optimal_llm(user_message)

state = create_initial_state(
    user_message=user_message,
    ...,
    llm_provider=provider,
    llm_model=model,
)
```

## Migration from Sub-Agent Config

**Before (WRONG):**
```yaml
# sub_agents/crypto_analyst/config.yaml
luka_extensions:
  llm_config:
    provider: "openai"  # ❌ Don't do this anymore
    model: "gpt-4o"
```

**After (CORRECT):**
```bash
# .env (deployment default)
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=llama3.2
```

```python
# Web/Telegram adapter (user-specific)
state = create_initial_state(
    ...,
    llm_provider=user.preferred_provider,
    llm_model=user.preferred_model,
)
```

## Best Practices

1. **Use env vars for deployment defaults**
   - Set sensible defaults in `.env`
   - Different values per environment (dev/staging/prod)

2. **Use runtime params for user preferences**
   - Store user LLM choice in database
   - Pass to `create_initial_state()` at runtime

3. **Don't put LLM config in sub-agent YAML**
   - Sub-agents define **personality**, not **infrastructure**
   - Keeps agents portable across deployments

4. **Partial overrides are OK**
   - Override only `llm_model`, keep env `llm_provider`
   - Mix and match as needed

5. **Test with different providers**
   - Verify behavior with local and cloud models
   - Ensure quality doesn't degrade with cheaper models

## Troubleshooting

### Issue: CLI not using my .env values

**Check:**
```bash
# Verify .env is loaded
./luka-agent.sh info general_luka | grep "LLM Configuration"
```

**Solution:** Ensure `.env` exists in project root and contains correct vars.

### Issue: Web users not seeing their model choice

**Check:** Verify runtime parameters are passed:
```python
state = create_initial_state(
    ...,
    llm_provider=user.llm_provider,  # ✅ Pass user preference
    llm_model=user.llm_model,
)
```

**Solution:** Don't forget to pass runtime overrides!

### Issue: All users using same model despite different settings

**Debug:**
```python
# Add logging
logger.info(f"User {user_id} using {llm_provider}/{llm_model}")

# Verify state
logger.info(f"State LLM: {state['llm_provider']}/{state['llm_model']}")
```

**Solution:** Check priority order - env vars might be overriding runtime params by mistake.

## Summary

| Platform | LLM Source | Use Case |
|----------|-----------|----------|
| **Worker/CLI** | Environment variables | Background jobs, testing, dev |
| **Web** | Runtime parameters | Per-user model selection |
| **Telegram** | Runtime parameters | Subscription tiers, premium features |

The priority system ensures:
- ✅ Infrastructure flexibility (change defaults via .env)
- ✅ User personalization (per-user model choice)
- ✅ Cost optimization (smart routing)
- ✅ Easy testing (override in specific scenarios)
