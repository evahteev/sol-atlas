# Streaming Mode Fix: Provider-Specific Handling

## Problem

The bot was not correctly handling streaming responses when switching between OpenAI and Ollama providers. This caused:
- **Ollama**: Only last chunk visible (response appeared incomplete)
- **OpenAI**: Duplicated text (102,519 chars instead of 1,291)

## Root Cause

OpenAI and Ollama use **different streaming modes**:

### OpenAI: Cumulative Streaming
Each chunk contains the **full text so far**:
```
Chunk 1: "Hello"
Chunk 2: "Hello world"
Chunk 3: "Hello world, how"
```
→ Need to extract only the **delta** (new part)

### Ollama: Delta Streaming
Each chunk contains only **new text**:
```
Chunk 1: "Hello"
Chunk 2: " world"
Chunk 3: ", how"
```
→ Need to **accumulate** chunks

## Solution

### 1. Explicit Provider Detection
Added logic to determine the actual provider being used:
```python
# Check cached preferred provider (from fallback system)
cached_provider = await fallback.redis.get(fallback.PREFERRED_PROVIDER_KEY)
actual_provider = cached_provider.decode() if cached_provider else (ctx.llm_provider or settings.DEFAULT_LLM_PROVIDER)

is_cumulative_streaming = (actual_provider == "openai")
```

### 2. Provider-Specific Handling
```python
if isinstance(chunk, str):
    if chunk:
        if is_cumulative_streaming:
            # OpenAI mode: extract delta
            if chunk.startswith(full_response):
                delta = chunk[len(full_response):]
                if delta:
                    full_response = chunk
                    yield delta
        else:
            # Ollama mode: accumulate
            full_response += chunk
            yield chunk
```

### 3. Enhanced Logging
```
🔄 Streaming mode: cumulative (OpenAI) [actual_provider=openai, ctx_provider=None]
🔄 Streaming mode: delta (Ollama) [actual_provider=ollama, ctx_provider=None]
```

## Benefits

1. ✅ **Correct Ollama responses**: Full text visible, properly accumulated
2. ✅ **Correct OpenAI responses**: No duplication, only deltas shown
3. ✅ **Automatic fallback support**: Uses the actual provider after failover
4. ✅ **Debug visibility**: Logs show which mode and provider are active

## Testing

After restart, test both providers:

### Ollama Test
```
User: "What are we discussing?"
Expected: Full response visible, all chunks accumulated
```

### OpenAI Test
```
User: "Tell me about Belgrade"
Expected: Smooth streaming, no duplication, correct char count
```

Check logs for:
```
🔄 Streaming mode: delta (Ollama) [actual_provider=ollama, ctx_provider=None]
✅ Response complete: N chars
```

## Related Files

- `/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/services/llm_service.py` (lines 307-342)
- `/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/services/llm_provider_fallback.py`
- `/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/core/config.py` (`DEFAULT_LLM_PROVIDER`)

