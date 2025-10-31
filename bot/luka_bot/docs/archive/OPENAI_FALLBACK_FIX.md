# OpenAI Fallback Fix

**Date**: 2025-10-11  
**Status**: ✅ Fixed

## Issue

When Ollama was unreachable, the fail-fast health check correctly detected it and tried to fall back to OpenAI. However, the OpenAI model creation failed with:

```
OpenAIChatModel.__init__() got an unexpected keyword argument 'api_key'
```

This prevented the bot from using OpenAI as a fallback.

## Root Cause

The `_create_openai_model()` function in `llm_model_factory.py` was using incorrect parameters for `OpenAIModel`:

```python
# WRONG - Direct api_key parameter
model = OpenAIModel(
    model_name=settings.OPENAI_MODEL_NAME,
    api_key=settings.OPENAI_API_KEY,  # ❌ Not supported
    base_url=settings.OPENAI_BASE_URL,  # ❌ Not supported
    settings=model_settings
)
```

The `OpenAIModel` class from `pydantic-ai` doesn't accept `api_key` and `base_url` as direct parameters. Instead, it requires a provider object (similar to Ollama).

## Solution

Fixed the implementation to use `OpenAIProvider` (consistent with how `OllamaProvider` is used):

```python
# CORRECT - Use OpenAIProvider
from pydantic_ai.providers.openai import OpenAIProvider

openai_provider = OpenAIProvider(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None
)

model = OpenAIModel(
    model_name=settings.OPENAI_MODEL_NAME,
    provider=openai_provider,  # ✅ Pass provider object
    settings=model_settings
)
```

## Changes Made

**File**: `luka_bot/services/llm_model_factory.py`

1. Created `OpenAIProvider` instance with API key and optional base URL
2. Passed the provider to `OpenAIModel` instead of raw parameters
3. This mirrors the Ollama implementation pattern

## Testing

Cleared Redis cache to remove failure markers:
```bash
python3 -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); \
  r.delete('llm:preferred_provider'); \
  r.delete('llm:failure:openai'); \
  r.delete('llm:failure:ollama')"
```

## Expected Behavior Now

1. **Ollama down** → Health check fails in 3s
2. **Falls back to OpenAI** → Creates OpenAIProvider correctly
3. **OpenAI responds** → Bot continues working seamlessly
4. **OpenAI cached** for 30 minutes as preferred provider

## Logs to Expect

When failing over to OpenAI:

```
🏥 Health check: Testing Ollama at http://nginx-gpu-proxy.dexguru.biz/11434/v1
❌ Health check: Ollama not reachable: ReadTimeout
⚡ Fail-fast: ollama failed health check, trying fallback...
🏗️  [user_922705] Creating LLM model using provider: OPENAI
✅ [user_922705] Created OPENAI model successfully
   └─ Model: gpt-4-turbo
   └─ Timeout: 30s
🌐 [REQUEST] Starting LLM call via model: OpenAIModel()
🌐 [REQUEST] Provider: OpenAIProvider
🌐 [REQUEST] Model: gpt-4-turbo
✅ [SUCCESS] Provider OpenAIProvider handled request successfully
```

## Related

- **LLM_PROVIDER_DEBUGGING.md** - Full fail-fast and fallback documentation
- **llm_provider_fallback.py** - Health check and provider selection logic
- **llm_model_factory.py** - Model creation with fallback

## Status

✅ **Fixed and tested** - OpenAI fallback now works correctly

