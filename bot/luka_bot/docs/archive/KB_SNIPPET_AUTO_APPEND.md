# Knowledge Base Snippet Auto-Append Fix

**Date**: 2025-10-11  
**Status**: ✅ Implemented

## Problem

When users mention the bot in groups and ask about previous discussions, the KB search tool is called but the formatted message snippets with deeplinks are not displayed. Instead, the LLM consumes the formatted output and rephrases it in its own words, losing the structure and clickable links.

### User Report
```
User: "@GuruKeeperBot Че там про шахедов сегодня писали?"

Bot Response (BEFORE FIX):
"Сегодня в нашей группе уже обсуждались 'шахеды'. В базе данных 
упоминается, что шахеды — это мученики, погибшие на службе своей страны..."
[No links, no structured snippets - just LLM narrative]
```

### Expected Behavior
```
Bot Response (AFTER FIX):
"Сегодня в нашей группе уже обсуждались 'шахеды'. Вот что я нашёл:

━━━━━━━━━━━━━━━━━━━━
📚 Найдено 5 сообщений:

1. 👤 Evgeny • 👥 Group • 2025-10-11 20:39
   🔗 View in group
   💬 "Discussing shakheds..."

2. 🤖 GURU Keeper • 👥 Group • 2025-10-11 21:09
   🔗 View in group
   💬 "Shakheds are martyrs..."

━━━━━━━━━━━━━━━━━━━━
```

## Root Cause

The knowledge base tool (`search_knowledge_base`) returns formatted snippets, but they're passed to the LLM as part of the tool result. The LLM then:
1. Reads the formatted snippets
2. Generates its own narrative summary based on them
3. Returns ONLY its narrative, discarding the original formatted snippets

The user never sees the clickable deeplinks or structured message cards.

## Solution

Implemented a **post-processing check** in `llm_service.py` that:

1. **Checks if formatted snippets are already in the response**
   - Uses the separator pattern `━━━━━━━━━━━━━━━━━━━━` as the indicator
   
2. **If snippets are missing:**
   - Scans all tool return messages
   - Extracts any results containing the separator (formatted snippets)
   - Appends them to the LLM's response
   
3. **If snippets are present:**
   - Does nothing (LLM already included them)

### Implementation

```python
# In llm_service.py, stream_response()

# After streaming completes...
has_formatted_snippets = '━━━━━━━━━━━━━━━━━━━━' in full_response

if not has_formatted_snippets:
    # Extract formatted snippets from tool returns
    all_msgs = stream.all_messages()
    kb_tool_results = []
    
    for msg in all_msgs:
        if msg.kind == 'request':
            for part in msg.parts:
                if part.__class__.__name__ == 'ToolReturnPart':
                    result = str(part.content) or str(part.tool_return)
                    if result and '━━━━━━━━━━━━━━━━━━━━' in result:
                        kb_tool_results.append(result)
    
    # Append to response
    if kb_tool_results:
        for kb_result in kb_tool_results:
            yield '\n\n'
            yield kb_result
            full_response += '\n\n' + kb_result
```

## Key Advantages

1. **Simple & Robust**: Doesn't rely on tool name detection or complex logic
2. **Non-Intrusive**: Only activates when KB snippets are actually present in tool results
3. **Preserves LLM Narrative**: LLM's summary is shown first, then snippets
4. **Universal**: Works in both DMs and groups
5. **Fail-Safe**: If LLM already included snippets, nothing changes

## User Experience

Users now always see:

1. **LLM's Narrative**: Contextual summary in conversational language
2. **Formatted Snippets**: Structured message cards with:
   - Sender name and emoji (👤 User / 🤖 Bot)
   - Source indicator (👥 Group / 👤 DM)
   - Timestamp
   - Message preview
   - **Clickable deeplink** to original message

## Testing

To test:

1. In a group chat, send several messages on a topic
2. Mention the bot with a search query:
   ```
   @BotName что мы обсуждали про [тема]?
   ```
3. Verify the response includes:
   - LLM summary at the top
   - Separator line
   - Formatted message cards with working deeplinks below

## Logging

Added informative logs:
- `🔍 KB snippets not in response, scanning N messages for tool results...`
- `📚 Found KB snippets in tool result: N chars`
- `✅ Appending N KB snippet section(s) that LLM didn't include`
- `✅ KB snippets already present in LLM response`
- `📚 No KB snippets found in tool results`

## Files Modified

- `/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/services/llm_service.py`
  - Enhanced `stream_response()` with post-processing snippet detection
  - Simplified from complex two-pass tool detection to pattern matching
  - Added informative logging for debugging

## Related Documentation

- `KB_TOOL_RENDERING_FIX.md` - Initial attempt (superseded by this approach)
- `KB_TOOL_ENHANCED_SEARCH.md` - KB tool format specification
- `KB_SEARCH_FORMATTING_UPDATE.md` - Original formatting requirements

---

**Result**: KB search now works consistently in groups and DMs, always showing formatted message snippets with clickable deeplinks, regardless of how the LLM chooses to format its response.

