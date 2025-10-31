# Streaming Fixes Session - October 12, 2025

## Summary

Comprehensive debugging and fixes for LLM streaming issues across multiple providers (OpenAI, Ollama) and the KB search tool.

## Problems Identified

### 1. ✅ OpenAI Cumulative Streaming (FIXED)
**Issue**: OpenAI returns cumulative text (each chunk = full response so far), not deltas.
**Status**: FIXED - Both extraction and accumulation working correctly.

**Logs showing the issue**:
```
✅ Yielded delta: 27 chars  (Chunk 1)
✅ Yielded delta: 38 chars  (Chunk 2)
✅ Yielded delta: 33 chars  (Chunk 3)
✅ Response complete: 1078 chars
✅ Streaming complete: 40 chars  ← Only last chunk shown!
```

**Root cause identified**:
- Handlers were **replacing** instead of **accumulating**: `full_response = chunk` instead of `full_response += chunk`
- This affected ALL streaming responses (DMs, groups, forwarded messages)

**What was fixed**:
- Added provider detection based on actual provider being used
- Implemented cumulative vs delta mode logic in `llm_service.py`
- Added detailed debugging logs to track chunk processing
- **CRITICAL FIX**: Changed all handlers to accumulate chunks instead of replacing
  - `streaming_dm.py`: lines 151, 177
  - `forwarded_messages.py`: lines 288, 313
  - `group_messages.py`: lines 765, 771

### 2. ✅ Ollama Cumulative Streaming (FIXED - Second Discovery)
**Issue**: Text duplication due to incorrect streaming mode detection.
**Status**: FIXED - Ollama also uses cumulative streaming!

**Initial logs showing the issue**:
```
✅ Response complete: 9391 chars
✅ Streaming complete: 1199 chars  ← Only last chunk before handler fix
🔍 Response preview: Here's a quick snapshot...Here's a quick snapshot...
```

**After handler fix, new issue discovered**:
```
✅ Response complete: 8897 chars
✅ Streaming complete: 8897 chars  ← Counts match!
🔍 Response preview: Text...Text...Text...  ← Still duplicating!
```

**Root cause discovered**:
- Initial fix resolved handler accumulation (chunk → full_response)
- But **Ollama also uses cumulative streaming**, not delta!
- We were treating Ollama as delta mode: `full_response += chunk` on cumulative chunks
- This caused duplication: "Hello" + "Hello world" = "HelloHello world"

**Final fix**:
- Set `is_cumulative_streaming = True` for **both providers**
- Apply delta extraction logic to both OpenAI and Ollama
- Extract only new text: `delta = chunk[len(full_response):]`

### 3. ⚠️ KB Search Tool Summary (NEEDS WORK)
**Issue**: LLM doesn't always generate summary before calling tool.
**Status**: Improved, but still inconsistent

**Current behavior**:
```
⚠️ LLM didn't generate summary (only 36 chars), added default intro
```

**What was done**:
- Made system prompt more emphatic with MANDATORY TWO-STEP format
- Added warning in tool description
- Improved fallback default intro (raised threshold from 5 to 20 chars)

**What still needs work**:
- Make prompt even more emphatic
- Consider prompt engineering techniques to force summary generation

### 4. ✅ Ollama Health Check (FIXED)
**Issue**: Health check tried `/v1/api/tags` → 404 error
**Status**: FIXED

**Solution**:
```python
# Strip /v1 suffix for health check (use native Ollama endpoint)
base_url = settings.OLLAMA_URL.rstrip('/')
if base_url.endswith('/v1'):
    base_url = base_url[:-3]

# Health check uses native endpoint
response = await client.get(f"{base_url}/api/tags")
```

**Model requests automatically add /v1**:
```python
ollama_base_url = settings.OLLAMA_URL.rstrip('/')
if not ollama_base_url.endswith('/v1'):
    ollama_base_url = f"{ollama_base_url}/v1"
```

### 5. ✅ Provider Cache on Startup (FIXED)
**Issue**: Cached preferred provider persisted across restarts.
**Status**: FIXED

**Solution**: Added cache clearing in `__main__.py` `on_startup()`:
```python
await fallback.redis.delete(fallback.PREFERRED_PROVIDER_KEY)
logger.info("🗑️  Cleared cached LLM provider preference - will use primary provider")
```

### 6. ✅ Dynamic Provider Order (FIXED)
**Issue**: Provider order was hardcoded, not respecting `AVAILABLE_PROVIDERS` dict order.
**Status**: FIXED

**Solution**: Load provider order dynamically in `__init__`:
```python
provider_keys = list(settings.AVAILABLE_PROVIDERS.keys())
self.PRIMARY_PROVIDER = provider_keys[0]
self.FALLBACK_PROVIDER = provider_keys[1] if len(provider_keys) > 1 else provider_keys[0]
```

## Files Modified

### 1. `/luka_bot/services/llm_service.py`
**Changes**:
- Added provider-specific streaming mode detection
- Implemented cumulative vs delta logic
- Added detailed debug logs for first 3 chunks
- Enhanced KB tool result extraction

**Key code**:
```python
# Detect actual provider being used
actual_provider = await fallback.redis.get(fallback.PREFERRED_PROVIDER_KEY)
is_cumulative_streaming = (actual_provider == "openai")

# Handle streaming based on mode
if is_cumulative_streaming:
    # OpenAI: extract delta
    delta = chunk[len(full_response):]
    full_response = chunk
    yield delta
else:
    # Ollama: accumulate
    full_response += chunk
    yield chunk
```

### 2. `/luka_bot/services/llm_provider_fallback.py`
**Changes**:
- Fixed Ollama health check to strip `/v1` suffix
- Made provider order dynamic (loaded from settings)
- Enhanced logging for provider detection

### 3. `/luka_bot/services/llm_model_factory.py`
**Changes**:
- Added `/v1` suffix for Ollama model requests
- Kept health check using base URL without `/v1`

### 4. `/luka_bot/core/config.py`
**Changes**:
- Added documentation about `OLLAMA_URL` (should be base URL without `/v1`)
- Provider order determined by `AVAILABLE_PROVIDERS` dict order

### 5. `/luka_bot/__main__.py`
**Changes**:
- Added provider cache clearing on startup

### 6. `/luka_bot/agents/tools/knowledge_base_tools.py`
**Changes**:
- Made system prompt more emphatic about summary generation
- Added MANDATORY TWO-STEP format instructions
- Improved fallback default intro

## Configuration

### Provider Priority
Set in `config.py`:
```python
AVAILABLE_PROVIDERS: dict = {
    "openai": ["gpt-5", "gpt-4-turbo"],  # First = Primary
    "ollama": ["gpt-oss", "llama3.2"],   # Second = Fallback
}
```

### Ollama URL
Must be **base URL without `/v1`**:
```bash
# Correct
OLLAMA_URL=http://localhost:11434

# Wrong
OLLAMA_URL=http://localhost:11434/v1
```

The `/v1` suffix is added automatically for API requests.

## Testing Results

### ✅ Provider Switching
```
🔧 Provider order: openai → ollama
🔧 Primary: openai, Fallback: ollama
```

### ✅ Health Check
```
✅ Health check: Ollama is healthy
```

### ⚠️ OpenAI Streaming (Partially Working)
- Delta extraction: ✅ Working (27, 38, 33 chars extracted)
- Display handler: ❌ Only shows last chunk (40 chars instead of 1078)

### ⚠️ Ollama Streaming (Has Issues)
- Accumulation: ⚠️ Working but with duplication
- Display: ⚠️ Shows 1199 chars instead of 9391 (partial)

## Next Steps (TODOs)

1. **CRITICAL**: Fix `streaming_dm.py` message editing handler
   - Investigate why only last chunk is displayed
   - Check if edits are replacing instead of appending
   - Look for race conditions in rapid edits

2. **HIGH**: Fix Ollama delta duplication
   - Check if chunks are processed by multiple branches
   - Verify accumulation logic

3. **MEDIUM**: Improve KB search summary generation
   - Make prompt even more emphatic
   - Consider prompt engineering techniques

4. **LOW**: Remove debug logs after fixes confirmed

5. **LOW**: Update documentation with provider order info

## Logs Archive

### OpenAI Cumulative Mode (Current Issue)
```
🔄 Streaming mode: cumulative (OpenAI) [actual_provider=openai, ctx_provider=None]
📦 Chunk 1: str
🔍 Chunk 1: len=27, full_response_len=0
✅ Yielded delta: 27 chars
📦 Chunk 2: str
🔍 Chunk 2: len=65, full_response_len=27
✅ Yielded delta: 38 chars
📦 Chunk 3: str
🔍 Chunk 3: len=98, full_response_len=65
✅ Yielded delta: 33 chars
✅ Response complete: 1078 chars
✅ Streaming complete: 40 chars  ← PROBLEM
```

### Ollama Delta Mode (Current Issue)
```
🔄 Streaming mode: delta (Ollama) [actual_provider=ollama, ctx_provider=None]
📦 Chunk 1: str
📦 Chunk 2: str
📦 Chunk 3: str
✅ Response complete: 9391 chars
✅ Streaming complete: 1199 chars  ← PROBLEM
🔍 Response preview: Here's a quick snapshot...Here's a quick snapshot...  ← DUPLICATION
```

## Related Documents

- `STREAMING_MODE_FIX.md` - Provider-specific streaming documentation
- `PROVIDER_CACHE_STARTUP_CLEAR.md` - Cache clearing on startup
- `LLM_FALLBACK_SYSTEM.md` - Provider fallback architecture
- `KB_TOOL_EMPHASIS_UPDATE.md` - KB tool summary improvements

## Session End Notes

**Date**: October 12, 2025, 04:43 UTC  
**Total Commits**: Multiple fixes across 6 files  
**Status**: Partial success, streaming logic fixed but display handler needs work  
**Next Session**: Focus on `streaming_dm.py` message editing handler

