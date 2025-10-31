# KB Search Final Fixes - HTML Links & Bot Message Filtering

**Date**: 2025-10-11  
**Status**: ✅ Implemented

## Problems Identified

### 1. HTML Links Not Rendering
**Issue**: The `<a href>` tags in KB search results were showing as plain text instead of clickable links.

**Example**:
```
🔗 <a href='https://t.me/c/1902150742/168342'>View in group</a>
```
Should render as a clickable link, but appeared as plain text.

**Root Cause**: The `escape_html()` function was escaping ALL HTML, including the properly formatted `<a href>` tags from the KB tool.

### 2. Bot's Own Responses in Results
**Issue**: Search results included the bot's own summary messages, creating confusing recursion.

**Example Results**:
- Message #1, #2, #3, #5 were all the bot's own responses saying "Сегодня в нашей группе уже обсуждали..."
- Only Message #4 was an actual user message

**Root Cause**: The bot's responses were being indexed in the KB, and then appearing in search results when users asked about the same topic.

### 3. Inconsistent Formatting
**Issue**: Some messages were bot summaries that themselves contained lists of other messages, creating nested/confusing structure.

## Solutions Implemented

### Fix 1: Preserve HTML in KB Snippets

**File**: `luka_bot/handlers/group_messages.py`

Added conditional HTML escaping - skip escaping when response contains KB snippets:

```python
# Send or update final response
if full_response:
    # Don't escape HTML if response contains KB snippets (they have proper HTML formatting)
    has_kb_snippets = '━━━━━━━━━━━━━━━━━━━━' in full_response
    if has_kb_snippets:
        # KB snippets already have proper HTML formatting with <a href> tags
        formatted_response = full_response
    else:
        # Regular response - escape HTML for safety
        formatted_response = escape_html(full_response)
    
    if bot_message:
        await message.bot.edit_message_text(
            text=formatted_response,
            chat_id=message.chat.id,
            message_id=bot_message.message_id,
            parse_mode="HTML"  # This enables HTML rendering
        )
```

**Result**: HTML links now render as clickable links in Telegram.

### Fix 2: Filter Bot Summary Messages

**File**: `luka_bot/agents/tools/knowledge_base_tools.py`

Added filtering logic to exclude bot's own summary messages:

```python
# Request more results to account for bot message filtering
results = await es_service.search_messages_text(
    index_name=kb_index,
    query_text=query,
    min_score=settings.DEFAULT_MIN_SCORE,
    max_results=actual_max_results * 3  # Get more, we'll filter
)

if results:
    # Filter out bot's own summary messages (they're not original content)
    filtered_results = []
    for result in results:
        doc = result.get('doc', {})
        role = doc.get('role', 'user')
        message_text = doc.get('text', '')
        
        # Skip bot messages that look like summaries (long + summary phrases)
        if role == 'assistant' or role == 'bot':
            if len(message_text) > 200 and any(phrase in message_text.lower() for phrase in [
                'обсуждали', 'в базе знаний', 'упоминается', 
                'обсуждалась', 'сообщениях нашей группы',
                'discussed', 'in the knowledge base', 'in our group'
            ]):
                logger.debug(f"Filtered bot summary: {message_text[:80]}...")
                continue
        
        filtered_results.append(result)
    
    all_results.extend(filtered_results)
    logger.info(f"Found {len(filtered_results)} relevant results (filtered {len(results) - len(filtered_results)} bot summaries)")
```

**Detection Criteria** for bot summaries:
- Role is `assistant` or `bot`
- Message length > 200 characters
- Contains summary phrases:
  - Russian: `обсуждали`, `в базе знаний`, `упоминается`, `обсуждалась`, `сообщениях нашей группы`
  - English: `discussed`, `in the knowledge base`, `in our group`

**Result**: Only original user messages and short bot responses are shown in search results.

### Fix 3: Simplified Header Format

**File**: `luka_bot/agents/tools/knowledge_base_tools.py`

Changed the header to be clearer:

```python
response_parts = [
    f"\n━━━━━━━━━━━━━━━━━━━━",
    f"📚 Found {len(all_results)} relevant message(s):\n" if user_lang == "en" 
    else f"📚 Найдено {len(all_results)} релевантных сообщения:\n"
]
```

### Fix 4: Enhanced System Prompt

Updated instructions to LLM about how to use the tool:

```
**How to use it:**
1. Call search_knowledge_base(query="user's question")
2. Provide a BRIEF 1-2 sentence summary (e.g., "Found several discussions about X:")
3. The tool automatically displays formatted message cards with clickable deeplinks
4. Do NOT try to list, quote, or reformat the search results yourself
5. Your summary should be SHORT - the actual messages will be shown below it
```

## Expected User Experience

### Before (Wrong):
```
User: "@GuruKeeperBot Че там про шахедов писали?"

Bot:
━━━━━━━━━━━━━━━━━━━━
📚 📋 References (5 of 5 matches):

1. 🤖 GURU Keeper • 2025-10-11 21:30
   🔗 <a href='https://t.me/c/.../168342'>View in group</a>  ❌ PLAIN TEXT
   💬 Обсуждение о "шахедах" происходило в следующих сообщениях...  ❌ BOT SUMMARY

2. 🤖 GURU Keeper • 2025-10-11 21:09
   🔗 <a href='https://t.me/c/.../168326'>View in group</a>  ❌ PLAIN TEXT
   💬 Сегодня в нашей группе уже обсуждали...  ❌ BOT SUMMARY
```

### After (Correct):
```
User: "@GuruKeeperBot Че там про шахедов писали?"

Bot: Found several relevant discussions:

━━━━━━━━━━━━━━━━━━━━
📚 Найдено 3 релевантных сообщения:

1. 👤 evgenijj • 👥 Group • 2025-10-11 20:39
   🔗 View in group  ✅ CLICKABLE LINK
   💬 Че там шахеды жужжат или че там как там...  ✅ ORIGINAL MESSAGE

2. 👤 Alex • 👥 Group • 2025-10-11 19:15
   🔗 View in group  ✅ CLICKABLE LINK
   💬 Про шахедов вот интересная статья...  ✅ ORIGINAL MESSAGE

3. 👤 Marina • 👥 Group • 2025-10-11 18:45
   🔗 View in group  ✅ CLICKABLE LINK
   💬 Слышала что шахеды это...  ✅ ORIGINAL MESSAGE

━━━━━━━━━━━━━━━━━━━━
```

## Key Improvements

1. ✅ **Clickable Links**: HTML `<a href>` tags now render properly
2. ✅ **Original Content Only**: Bot summaries are filtered out
3. ✅ **Clear Structure**: LLM brief summary → separator → message snippets
4. ✅ **Consistent Format**: All messages follow the same card format
5. ✅ **No Recursion**: No more nested bot summaries

## Testing

To verify fixes work:

1. **Restart the bot** to load changes
2. **Ask about past discussions**:
   ```
   @GuruKeeperBot Че там про [тема] писали?
   ```
3. **Verify response has**:
   - Brief LLM summary (1-2 sentences)
   - Separator line
   - Message cards with **clickable links** (not plain text)
   - **Only user messages** or short bot responses (no summaries)

4. **Check logs**:
   ```
   🔧 ✅ TOOL CALLED: search_knowledge_base
   Found N relevant results (filtered M bot summaries)
   ```

## Files Modified

1. `/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/handlers/group_messages.py`
   - Added conditional HTML escaping for KB snippets

2. `/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/agents/tools/knowledge_base_tools.py`
   - Added bot message filtering logic
   - Simplified header format
   - Enhanced system prompt instructions

## Impact

- ✅ Users can now click deeplinks to view original messages
- ✅ Search results show only relevant original content
- ✅ No more confusing nested bot summaries
- ✅ Consistent, clean formatting
- ✅ Better UX overall

## Related Documentation

- `KB_TOOL_EMPHASIS_UPDATE.md` - Tool usage emphasis
- `KB_SNIPPET_AUTO_APPEND.md` - Auto-append mechanism
- `KB_TOOL_ENHANCED_SEARCH.md` - Original formatting spec

---

**Result**: KB search now provides clean, clickable message snippets showing only original content, with proper HTML link rendering.

