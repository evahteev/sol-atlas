# Streaming Fix Test Plan - October 12, 2025

## Critical Bug Fixed ✅

**Issue**: All streaming handlers were **replacing** chunks instead of accumulating them.
**Result**: Only the last chunk was displayed, truncating all responses.

**Fix Applied**: Changed `full_response = chunk` to `full_response += chunk` in 3 handlers:
- `streaming_dm.py`
- `forwarded_messages.py`  
- `group_messages.py`

## Test Scenarios

### 1. OpenAI Streaming (Cumulative Mode)

**Setup**:
```python
# In luka_bot/core/config.py
AVAILABLE_PROVIDERS: dict = {
    "openai": ["gpt-5", "gpt-4-turbo"],  # First = Primary
    "ollama": ["gpt-oss", "llama3.2"],
}
```

**Test Steps**:
1. Restart the bot
2. Send a long question in DM (e.g., "How to get to Belgrade?")
3. Watch the logs for:
   ```
   ✅ Response complete: XXXX chars
   ✅ Streaming complete: XXXX chars  ← Should match!
   ```

**Expected Before Fix**:
```
✅ Response complete: 1078 chars
✅ Streaming complete: 40 chars  ← Last chunk only!
```

**Expected After Fix**:
```
✅ Response complete: 1078 chars
✅ Streaming complete: 1078 chars  ← Full response! ✅
```

**User Should See**: Complete answer, not just the last sentence.

### 2. Ollama Streaming (Delta Mode)

**Setup**:
```python
# In luka_bot/core/config.py
AVAILABLE_PROVIDERS: dict = {
    "ollama": ["gpt-oss", "llama3.2"],   # First = Primary
    "openai": ["gpt-5", "gpt-4-turbo"],
}
```

**Test Steps**:
1. Restart the bot
2. Send a long question in DM (e.g., "Explain quantum computing")
3. Watch the logs for:
   ```
   ✅ Response complete: XXXX chars
   ✅ Streaming complete: XXXX chars  ← Should match!
   🔍 Response preview: ...  ← Should NOT have duplicates!
   ```

**Expected Before Fix**:
```
✅ Response complete: 9391 chars
✅ Streaming complete: 1199 chars  ← Last chunk only!
🔍 Response preview: Here's a quick...Here's a quick...  ← Duplication!
```

**Expected After Fix**:
```
✅ Response complete: 9391 chars
✅ Streaming complete: 9391 chars  ← Full response! ✅
🔍 Response preview: Here's a quick...  ← No duplication! ✅
```

**User Should See**: Complete answer with no duplicate text.

### 3. Group Mentions

**Test Steps**:
1. Mention bot in a group: `@GuruKeeperBot How does Bitcoin work?`
2. Verify full response is displayed
3. Check logs for matching char counts

**Expected**: Full LLM response, not truncated to last chunk.

### 4. Group Replies

**Test Steps**:
1. Reply to one of bot's messages in a group
2. Bot should respond with full answer
3. Check logs for matching char counts

**Expected**: Full LLM response, not truncated.

### 5. Forwarded Messages

**Test Steps**:
1. Forward any message to bot in DM
2. Bot should analyze it and provide full response
3. Check logs for matching char counts

**Expected**: Full analysis, not truncated to last chunk.

### 6. KB Search Tool (If applicable)

**Test Steps**:
1. Ask bot to search message history: `"What did we discuss about X?"`
2. Verify LLM summary is shown
3. Verify message snippets are shown below summary
4. Check that all snippets have deeplinks

**Expected**:
```
[LLM Summary: 1-3 sentences]

━━━━━━━━━━━━━━━━━━━━
📚 Found 5 relevant message(s):

1. 👤 User • 👤 DM • Mar 15, 2024
   💬 <message text>
   🔗 View in group

...
━━━━━━━━━━━━━━━━━━━━
```

## Log Patterns to Watch

### ✅ Success Indicators
```
🔧 Provider order: openai → ollama (or ollama → openai)
🔧 Primary: openai, Fallback: ollama
✅ Created OPENAI model (or OLLAMA model)
🔄 Streaming mode: cumulative (OpenAI) [or delta (Ollama)]
✅ Response complete: XXXX chars
✅ Streaming complete: XXXX chars  ← MUST MATCH!
```

### ❌ Failure Indicators
```
✅ Response complete: 1078 chars
✅ Streaming complete: 40 chars  ← Mismatch = Bug still present!
```

```
🔍 Response preview: Same text...Same text...  ← Duplication = Bug present!
```

## Debug Logs (Temporary)

The following debug logs were added for diagnosis and should be removed after testing:

**In `llm_service.py` (lines ~340-350)**:
```python
if chunk_count <= 3:
    logger.info(f"🔍 Chunk {chunk_count}: len={len(chunk)}, full_response_len={len(full_response)}")
    logger.info(f"🔍 Chunk preview: {chunk[:100]}...")
    logger.info(f"🔍 Starts with full_response: {chunk.startswith(full_response)}")
```

These can be removed once both providers are confirmed working.

## Checklist

- [ ] Test OpenAI cumulative streaming
  - [ ] Char counts match in logs
  - [ ] Full response displayed to user
  - [ ] No truncation

- [ ] Test Ollama delta streaming
  - [ ] Char counts match in logs
  - [ ] Full response displayed to user
  - [ ] No text duplication
  - [ ] No truncation

- [ ] Test group mentions
  - [ ] Full responses displayed
  - [ ] No truncation

- [ ] Test group replies
  - [ ] Full responses displayed
  - [ ] No truncation

- [ ] Test forwarded messages
  - [ ] Full analysis displayed
  - [ ] No truncation

- [ ] Test KB search tool (if applicable)
  - [ ] LLM summary shown
  - [ ] Message snippets shown
  - [ ] Deeplinks working

- [ ] Remove debug logs from `llm_service.py`

- [ ] Update documentation with provider order info

## Notes

- The same fix was applied to all 3 streaming handlers, so if it works in DMs it should work everywhere
- Both OpenAI (cumulative) and Ollama (delta) modes use the same accumulation logic now
- The bug was present since streaming was first implemented
- This fix should also resolve any KB search issues where snippets weren't showing

## Success Criteria

**Test passes if**:
1. Char counts match in logs: `Response complete` == `Streaming complete`
2. Full response is displayed to user (not just last sentence)
3. No text duplication
4. KB search results show summary + snippets (if tested)

**Test fails if**:
1. Char counts mismatch (only last chunk displayed)
2. Truncated responses
3. Text duplication
4. Missing KB snippets

