# Provider Cache Startup Clear

## Problem

When the bot restarts, it was **keeping the cached preferred provider** from the previous session. This caused:

- If **Ollama failed** previously → OpenAI was cached for 30 minutes
- Even after Ollama is fixed/restarted, the bot **keeps using OpenAI** until cache expires
- User expects bot to always try **primary provider first** on startup

## Example from Logs

```
Cached openai as preferred provider (TTL: 1800s)
✅ [user_922705] Created OPENAI model
🔄 Streaming mode: cumulative (OpenAI) [actual_provider=openai, ctx_provider=None]
```

Even though Ollama is the primary provider, OpenAI was being used because it was cached from a previous session.

## Solution

Added cache clearing in `on_startup()` to **reset provider preference** on every bot restart:

```python
async def on_startup() -> None:
    """Bot startup initialization."""
    logger.info("🚀 luka_bot starting...")
    
    # Clear cached LLM provider preference to always start fresh with primary provider
    try:
        from luka_bot.services.llm_provider_fallback import get_llm_provider_fallback
        fallback = get_llm_provider_fallback()
        await fallback.redis.delete(fallback.PREFERRED_PROVIDER_KEY)
        logger.info("🗑️  Cleared cached LLM provider preference - will use primary provider")
    except Exception as e:
        logger.warning(f"⚠️  Failed to clear provider cache: {e}")
```

## Benefits

1. ✅ **Fresh start**: Every bot restart tries primary provider first
2. ✅ **Predictable behavior**: Users know which provider will be used
3. ✅ **Quick recovery**: If Ollama is fixed, restart bot to use it immediately
4. ✅ **Runtime fallback preserved**: During runtime, failover still works and caches for 30 minutes

## Behavior

### On Startup
```
🚀 luka_bot starting...
🗑️  Cleared cached LLM provider preference - will use primary provider
```

### First Request After Startup
- Tries **Ollama** (primary) first
- If Ollama fails → falls back to **OpenAI** and caches for 30 minutes
- If Ollama works → uses **Ollama** and caches for 30 minutes

### Subsequent Requests (Same Session)
- Uses **cached preferred provider** (either Ollama or OpenAI)
- No repeated health checks unless cache expires

### Next Restart
- Cache cleared again → starts fresh with primary provider

## When to Use This

**Good use cases:**
- Development: Frequently switching between Ollama and OpenAI
- Production: Ensuring predictable startup behavior
- Recovery: After fixing Ollama, restart bot to use it immediately

**Not needed if:**
- You always want to use OpenAI → set `DEFAULT_LLM_PROVIDER="openai"` in config
- You're fine with cache persisting across restarts

## Related Settings

- **Primary provider order**: **Determined by `AVAILABLE_PROVIDERS` dict order** in `config.py`
  - **First key** = Primary provider (tried first)
  - **Second key** = Fallback provider (used if primary fails)
  - Example:
    ```python
    AVAILABLE_PROVIDERS: dict = {
        "ollama": ["gpt-oss", "llama3.2"],  # Primary
        "openai": ["gpt-5", "gpt-4-turbo"], # Fallback
    }
    ```
  - **To change priority**: Simply reorder the dict keys (Python 3.7+ preserves dict insertion order)
- **Cache TTL**: 30 minutes (`PREFERRED_PROVIDER_TTL_SECONDS = 1800`)
- **Redis key**: `llm:preferred_provider`

## Important: Provider Order Configuration

The provider order is **dynamically loaded** from the `AVAILABLE_PROVIDERS` dictionary in `config.py`. The order of keys in this dictionary determines the priority:

**Example 1: Ollama Primary**
```python
AVAILABLE_PROVIDERS: dict = {
    "ollama": ["gpt-oss", "llama3.2"],  # 1st = Primary
    "openai": ["gpt-5", "gpt-4-turbo"], # 2nd = Fallback
}
```

**Example 2: OpenAI Primary**
```python
AVAILABLE_PROVIDERS: dict = {
    "openai": ["gpt-5", "gpt-4-turbo"], # 1st = Primary
    "ollama": ["gpt-oss", "llama3.2"],  # 2nd = Fallback
}
```

On bot startup, you'll see:
```
✅ LLMProviderFallback initialized
🔧 Provider order: openai → ollama
🔧 Primary: openai, Fallback: ollama
```

This makes it easy to switch providers without changing code - just reorder the dict and restart the bot!

## Testing

After restart, you should see:
```
🚀 luka_bot starting...
🗑️  Cleared cached LLM provider preference - will use primary provider
```

Then on first LLM request:
```
🔄 Streaming mode: delta (Ollama) [actual_provider=ollama, ctx_provider=None]
```
(Assuming Ollama is primary and working)

Or if Ollama is down:
```
❌ Health check: Ollama not reachable: ConnectError
⚠️ Primary provider failed, using fallback: openai
🔄 Streaming mode: cumulative (OpenAI) [actual_provider=openai, ctx_provider=None]
```

## Files Modified

- `/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/__main__.py` (lines 32-39)

