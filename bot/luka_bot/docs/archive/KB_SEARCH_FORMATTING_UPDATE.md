# Knowledge Base Search - Structured Message Snippets

**Date**: 2025-10-11  
**Status**: ✅ Complete

## Overview

Updated the knowledge base search tool to display results as clean, structured message snippets with clickable deeplinks, separate from the LLM's narrative summary. This provides a better user experience similar to search engines that show results as cards.

## Problem

Previously, when users asked questions that triggered KB search:
1. The tool returned formatted results with links
2. The LLM would then reformat these results in its own words
3. Links were sometimes lost or poorly formatted
4. The output was verbose and mixed narrative with data

**Example of old behavior**:
```
User: В каких сообщениях это упоминалось?

Bot: Обсуждение о "шахедах" происходило в следующих сообщениях нашей группы:

1. [Сообщение от Evgeny, 2025-10-11 20:39](https://t.me/c/...) - Здесь обсуждалась тема...
2. [Сообщение от меня (GURU Keeper), 2025-10-11 21:09](https://t.me/c/...) - Я упомянул...
```

The LLM was manually reformatting the links and adding its own descriptions.

## Solution

**New behavior**:
1. **LLM provides brief summary** (2-3 sentences)
2. **Tool automatically appends structured message cards** below the summary
3. **Clean separation** between narrative and data

### Updated System Prompt

Added instructions to the agent:
```
**IMPORTANT**: When using search_knowledge_base:
  1. Provide a brief summary of what was found (2-3 sentences)
  2. The tool will automatically display formatted message snippets with clickable links
  3. Do NOT manually reformat or list the search results - they will be shown automatically
  4. Just summarize the findings and let the tool display the actual messages
```

### Updated Tool Output Format

The tool now returns:

```
━━━━━━━━━━━━━━━━━━━━
📚 References (showing 5 of 5 results):

1. 👤 Evgeny • 👥 Group • 2025-10-11 20:39
   🔗 View in group
   💬 <i>МОжешь найти в базе знаний О чем я спрашивал сегодня...</i>

2. 🤖 GURU Keeper • 👥 Group • 2025-10-11 21:09
   🔗 View in group
   💬 <i>Сегодня в нашей группе уже обсуждали "шахедов"...</i>

3. 👤 Evgeny • 👥 Group • 2025-10-11 20:57
   🔗 View in group
   💬 <i>что сегодня писали про шахедов...</i>

━━━━━━━━━━━━━━━━━━━━
```

## New User Experience

### Example 1: KB Search in Group

```
User: В каких сообщениях это упоминалось?

Bot: Сегодня в нашей группе обсуждали "шахедов" в нескольких сообщениях. 
В базе знаний найдено 5 упоминаний этой темы. Смотрите сообщения ниже:

━━━━━━━━━━━━━━━━━━━━
📚 References (showing 5 of 5 results):

1. 👤 Evgeny • 👥 Group • 2025-10-11 20:39
   🔗 View in group
   💬 что такое шахеды?

2. 🤖 GURU Keeper • 👥 Group • 2025-10-11 20:39
   🔗 View in group
   💬 Шахеды — это мученики, погибшие на службе своей страны...

[... more results ...]

━━━━━━━━━━━━━━━━━━━━
```

### Example 2: Follow-up Question

```
User: [replies to bot] Can you tell me more about the first result?

Bot: В первом сообщении Evgeny спросил "что такое шахеды?", 
что и запустило это обсуждение в группе.
```

## Technical Changes

### 1. Message Card Format

Each message is now displayed as a card with:
- **Bold sender name**: `<b>Evgeny</b>`
- **Source indicator**: 👥 Group or 👤 DM
- **Timestamp**: `2025-10-11 20:39`
- **Clickable link**: `🔗 View in group` (HTML link)
- **Italicized message preview**: `<i>message text...</i>`

### 2. HTML Formatting

```python
message_card = f"\n{i}. {role_emoji} <b>{sender}</b> • {source_info} • {date_str}"
if deeplink:
    message_card += deeplink
message_card += f"\n   💬 <i>{text}</i>\n"
```

### 3. Visual Separators

```
━━━━━━━━━━━━━━━━━━━━
📚 References (showing 5 of 5 results):
[... results ...]
━━━━━━━━━━━━━━━━━━━━
```

These separators clearly distinguish the structured data from the LLM's narrative.

### 4. Deeplinks

Telegram deeplinks remain the same:
- Format: `https://t.me/c/{chat_id}/{message_id}`
- Rendered as: `🔗 <a href='...'>View in group</a>`
- Clickable in Telegram clients

## Benefits

### 1. **Clear Separation**
- LLM provides context and summary
- Structured data shows actual messages
- No mixing of narrative and references

### 2. **Consistent Formatting**
- All KB results have the same visual style
- Bold names, italicized messages
- Clean card-like appearance

### 3. **Clickable Links**
- Deep links are always in the same place
- Easy to spot the 🔗 icon
- One click to jump to original message

### 4. **Better Readability**
- Visual separators guide the eye
- Message previews are concise (150 chars)
- Emojis indicate role and source

### 5. **Less Verbose**
- LLM doesn't need to describe each message
- Just provides a brief summary
- Tool handles the detailed presentation

## Comparison

### Before:
```
Обсуждение о "шахедах" происходило в следующих сообщениях нашей группы:

1. [Сообщение от Evgeny, 2025-10-11 20:39](https://t.me/c/1902150742/168310) 
   - Здесь обсуждалась тема шахедов в контексте общего разговора.
2. [Сообщение от меня (GURU Keeper), 2025-10-11 21:09](https://t.me/c/1902150742/168326) 
   - Я упомянул о шахедах, как о мучениках, погибших на службе своей страны.
...
```
**Issues**: Mixed narrative, inconsistent format, verbose descriptions

### After:
```
Сегодня обсуждали "шахедов" в нескольких сообщениях. 
Найдено 5 упоминаний. Смотрите ниже:

━━━━━━━━━━━━━━━━━━━━
📚 References (showing 5 of 5 results):

1. 👤 Evgeny • 👥 Group • 2025-10-11 20:39
   🔗 View in group
   💬 что такое шахеды?
...
━━━━━━━━━━━━━━━━━━━━
```
**Benefits**: Clean separation, consistent format, concise presentation

## Implementation Details

### Files Modified
1. `luka_bot/agents/tools/knowledge_base_tools.py`
   - Updated output format
   - Added HTML formatting for names and messages
   - Added visual separators
   - Updated system prompt instructions

### Key Changes

**Line 200-203**: Removed AI summary from tool output, only show references
```python
response_parts = [
    f"\n━━━━━━━━━━━━━━━━━━━━",
    f"📚 {references_header}\n"
]
```

**Line 265-270**: Enhanced message card formatting
```python
message_card = f"\n{i}. {role_emoji} <b>{sender}</b> • {source_info} • {date_str}"
if deeplink:
    message_card += deeplink
message_card += f"\n   💬 <i>{text}</i>\n"
```

**Line 305-309**: Updated system prompt
```python
**IMPORTANT**: When using search_knowledge_base:
  1. Provide a brief summary of what was found (2-3 sentences)
  2. The tool will automatically display formatted message snippets
  3. Do NOT manually reformat or list the search results
  4. Just summarize the findings and let the tool display the messages
```

## Testing

### Test Scenarios

1. **Basic KB Search**
   - User asks: "What did we discuss today?"
   - Verify: LLM summary + structured results
   
2. **Multiple Results**
   - User asks question with 5+ results
   - Verify: All results shown in cards, links work

3. **Mixed DM and Group Messages**
   - Results from both sources
   - Verify: Source indicators correct (👥/👤)

4. **HTML Rendering**
   - Bold names, italic messages
   - Verify: HTML renders correctly in Telegram

5. **Deeplinks**
   - Click on "View in group" links
   - Verify: Navigate to correct message

## Future Enhancements

🔮 **Inline Buttons**: Add "View Context" button for surrounding messages  
🔮 **Message Threads**: Show reply chains visually  
🔮 **Media Previews**: Show thumbnails for photos/videos  
🔮 **Search Filters**: Filter by date, sender, type  
🔮 **Relevance Indicators**: Visual score/relevance badges  

## Compatibility

✅ **HTML Rendering**: Group handlers use `parse_mode="HTML"`  
✅ **Deeplinks**: Standard Telegram format  
✅ **Multi-language**: Respects user language for headers  
✅ **Topics**: Works in supergroup topics  
✅ **Existing Data**: No migration needed  

---

**Deployment**: ✅ Ready for production  
**Breaking Changes**: None  
**User Impact**: Improved UX, clearer results presentation  

