# LLM Provider Debugging & Timeout Fixes

**Date**: 2025-10-11  
**Status**: ✅ Implemented

## Overview

Enhanced debugging and timeout handling for LLM provider fallback system. The bot now provides detailed logs showing exactly which provider (Ollama/OpenAI) is handling each request and automatically invalidates the cache when timeouts occur.

## Changes Implemented

### 1. ⏱️ Reduced Timeouts for Faster Failover

**File**: `luka_bot/core/config.py`

- **OLLAMA_TIMEOUT**: Reduced from 60s → **15s**
- **OPENAI_TIMEOUT**: Reduced from 60s → **30s**

This enables much faster failover when a provider is unresponsive.

### 2. 🔍 Enhanced Provider Debugging Logs

#### In `llm_model_factory.py`:

**Before model creation**:
```
🏗️  [user_922705] Creating LLM model using provider: OLLAMA
```

**After successful creation**:
```
✅ [user_922705] Created OLLAMA model successfully
   └─ Model: gpt-oss
   └─ Endpoint: http://nginx-gpu-proxy.dexguru.biz/11434/v1
   └─ Timeout: 15s
```

#### In `llm_service.py`:

**Before making LLM request**:
```
🌐 [REQUEST] Starting LLM call via model: OpenAIModel()
🌐 [REQUEST] Provider: OllamaProvider, Endpoint: http://nginx-gpu-proxy.dexguru.biz/11434/v1
🌐 [REQUEST] Model: gpt-oss
⏱️  [REQUEST] Timeout: 15s
```

**After successful response**:
```
✅ Agent response complete: 234 chars
✅ [SUCCESS] Provider OllamaProvider handled request successfully
```

**On timeout/error**:
```
⏱️  [TIMEOUT] Provider OllamaProvider timed out after 15s
🗑️  Cleared provider cache - next request will try fallback
```

Or for general errors:
```
❌ [ERROR] Provider OllamaProvider failed: Request timed out.
⏱️  LLM timeout detected on OllamaProvider, invalidating cache...
🗑️  Cleared preferred provider cache
```

### 3. ⚡ Fail-Fast Health Checks

**File**: `luka_bot/services/llm_provider_fallback.py`

Added quick 3-second health checks before using any provider:

**For Ollama**:
- Performs GET request to `/api/tags` endpoint
- 3-second timeout (much faster than 15s request timeout)
- Tests actual connectivity before committing to provider

**For OpenAI**:
- Checks if API key is configured
- Cloud-based, assumed healthy if key exists

**Logs**:
```
🏥 Health check: Testing Ollama at http://localhost:11434
✅ Health check: Ollama is responsive
```

Or on failure:
```
❌ Health check: Ollama not reachable: ConnectError
⚡ Fail-fast: ollama failed health check, trying fallback...
```

### 4. 🗑️ Automatic Cache Invalidation

**File**: `luka_bot/services/llm_service.py`

Enhanced error handling to automatically clear the cached preferred provider when:
- `asyncio.TimeoutError` occurs
- `openai.APITimeoutError` occurs
- Any timeout-like error is detected

This ensures the next request will re-evaluate provider health and try the fallback (OpenAI) instead of using the cached failing provider.

### 5. 🧹 Redis Cache Cleared

Manually cleared the existing Redis cache key `llm:preferred_provider` to ensure immediate fallback testing.

## Expected Behavior

### Normal Flow (Ollama Working):
1. **Health check** tests Ollama (3s timeout)
2. Logs show: `✅ Health check: Ollama is responsive`
3. Bot creates Ollama model
4. Logs show: `Created OLLAMA model successfully`
5. Makes request via OllamaProvider
6. Response completes within 15s
7. Logs show: `[SUCCESS] Provider OllamaProvider handled request successfully`

### Fail-Fast Flow (Ollama Down) - NEW! ⚡:
1. **Health check** tests Ollama (3s timeout)
2. Logs show: `❌ Health check: Ollama not reachable`
3. Logs show: `⚡ Fail-fast: ollama failed health check, trying fallback...`
4. **Immediately** tries OpenAI (total time: ~3 seconds instead of 15!)
5. Bot creates OpenAI model
6. Logs show: `Created OPENAI model successfully`
7. Request completes via OpenAIProvider
8. OpenAI is cached as preferred for 30 minutes

### Slow Timeout Flow (Ollama Slow but Responsive):
1. Health check passes (Ollama responds within 3s)
2. Bot creates Ollama model
3. Makes request via OllamaProvider
4. Request times out after 15s (model generating is slow)
5. Logs show: `[TIMEOUT] Provider OllamaProvider timed out after 15s`
6. Cache is cleared: `Cleared provider cache - next request will try fallback`
7. **Next request** runs health check, fails, uses OpenAI immediately

## Testing

To test the failover:

1. **Stop Ollama** (or break the connection):
   ```bash
   # On the Ollama server
   systemctl stop ollama
   ```

2. **Send a message to the bot** in Telegram

3. **Check logs** - should see:
   - Ollama creation attempt
   - Timeout after 15s
   - Cache cleared
   - Next message uses OpenAI automatically

4. **Restart Ollama**:
   ```bash
   systemctl start ollama
   ```

5. **Wait 30 minutes** (or manually clear cache):
   ```python
   python3 -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.delete('llm:preferred_provider')"
   ```

6. **Send another message** - should revert to Ollama

## Benefits

✅ **⚡ Fail-fast health checks**: 3s detection instead of 15s timeout (5x faster!)  
✅ **Faster failover**: 15s timeout instead of 60s (4x faster for slow responses)  
✅ **Transparent debugging**: See exactly which provider handles each request  
✅ **Automatic recovery**: Cache invalidation ensures fallback happens  
✅ **Production-ready**: Detailed logs for troubleshooting without code changes  
✅ **Two-tier protection**: Quick connectivity check (3s) + full timeout protection (15s)  

## Files Modified

1. `luka_bot/core/config.py` - Reduced timeouts (60s → 15s for Ollama, 60s → 30s for OpenAI)
2. `luka_bot/services/llm_model_factory.py` - Enhanced logging with provider details
3. `luka_bot/services/llm_service.py` - Enhanced logging + cache invalidation on errors
4. `luka_bot/services/llm_provider_fallback.py` - **NEW: Fail-fast health checks** (3s timeout)

## Key Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Timeout (primary) | 60s | 15s | **4x faster** |
| Timeout (fallback) | 60s | 30s | **2x faster** |
| Connectivity check | None | 3s | **5x faster than timeout** |
| Total failover time (Ollama down) | 60s | **3s** | **20x faster!** 🚀 |

## Next Steps

- Monitor logs in production to verify fail-fast works as expected
- Consider adding a `/llm_status` admin command to show current provider and health
- Add Prometheus metrics for provider failover events and health check results
- Consider making health check timeout configurable (currently hardcoded 3s)

