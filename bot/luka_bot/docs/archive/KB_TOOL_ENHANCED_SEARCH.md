# Knowledge Base Tool Enhancement - Deeplinks & Better Formatting

**Date**: 2025-10-11  
**Status**: ✅ Complete

## Overview

Enhanced the `search_knowledge_base` tool to provide a better user experience similar to the `/search` command, with AI summaries, detailed message information, and clickable deeplinks to group messages.

## Changes Made

### 1. **Enhanced Message Formatting**

#### Before:
```
1. 👤 [2025-10-11 21:16] Evgeny:
   Hey @GuruKeeperBot...
```

#### After:
```
1. 👤 👥 Group • Evgeny • 2025-10-11 21:16
   МОжешь найти в базе знаний О чем я спрашивал сегодня @GuruKeeperBot
   🔗 View in group
```

**Improvements**:
- ✅ Shows source type (👥 Group or 👤 DM)
- ✅ Better visual separation with bullets (•)
- ✅ Increased text preview from 80 to 150 characters
- ✅ Clickable deeplink to original message in group

### 2. **Telegram Deeplinks**

Added automatic deeplink generation for group messages:

**Format**: `https://t.me/c/{chat_id}/{message_id}`

**Implementation**:
- Extracts `group_id` from Elasticsearch document
- Parses `message_id` to get Telegram message ID
- Converts group ID format: `-1001234567890` → `1234567890` (removes `-100` prefix)
- Creates HTML link: `<a href='https://t.me/c/{chat_id}/{message_id}'>View in group</a>`

**Example**:
- Group ID: `-1001902150742`
- Message ID: `-1001902150742_168280`
- Deeplink: `https://t.me/c/1902150742/168280`

### 3. **Improved AI Summary**

#### Before:
- Max 280 characters (tweet-like)
- Basic factual response
- Temperature: 0.3

#### After:
- Max 400 characters (2-3 sentences)
- More conversational and helpful
- Better context extraction (200 chars per message vs 150)
- Improved prompt engineering

**New Summary Prompt**:
```
Provide a clear, informative summary (2-3 sentences, max 400 characters) that:
1. Directly answers what was found about "{query}"
2. Highlights the most important information from the conversations
3. Be specific and factual
```

### 4. **Increased Result Count**

- **Before**: Max 3 results shown
- **After**: Max 5 results shown

This provides more comprehensive search results while keeping the output manageable.

### 5. **Source Indicators**

Messages now clearly indicate their source:
- 👥 **Group**: Messages from group conversations
- 👤 **DM**: Messages from direct message conversations

## Technical Details

### Deeplink Construction

```python
# Extract telegram message ID from composite message_id
# Format: {group_id}_{telegram_message_id}
parts = message_id.split('_')
telegram_msg_id = parts[-1]

# Convert group_id for deeplink
group_id_str = str(group_id)
if group_id_str.startswith('-100'):
    chat_id_for_link = group_id_str[4:]  # Remove -100 prefix
    deeplink = f"<a href='https://t.me/c/{chat_id_for_link}/{telegram_msg_id}'>View in group</a>"
```

### HTML Parse Mode

The `handle_group_message` handler already uses `parse_mode="HTML"` (line 784), so HTML links in KB search results will render correctly as clickable links.

## User Experience

### Example KB Search Result

```
📊 Summary:
Based on your conversation history, you asked about what you discussed today. 
The knowledge base shows no previous questions recorded for today's date.

📚 References (showing 2 of 2 results):

1. 👤 👥 Group • Evgeny • 2025-10-11 21:16
   Hey @GuruKeeperBot
   🔗 View in group

2. 👤 👥 Group • Evgeny • 2025-10-11 21:16
   МОжешь найти в базе знаний О чем я спрашивал сегодня @GuruKeeperBot
   🔗 View in group

💡 Tip: Refine your search with more specific keywords for better results.
```

## Benefits

1. **Better Context**: Users can now see exactly where information came from (DM or specific group)
2. **Quick Access**: Deeplinks allow instant navigation to the original message
3. **Richer Summaries**: More detailed AI-generated summaries provide better understanding
4. **More Results**: 5 results instead of 3 provides more comprehensive search coverage
5. **Professional UX**: Matches the quality of the `/search` command interface

## Testing Checklist

✅ Test KB search in groups with mentions
✅ Verify deeplinks work and navigate to correct messages
✅ Test with both group and DM messages
✅ Verify HTML rendering (links are clickable)
✅ Test with Russian language (i18n)
✅ Test with different message ID formats
✅ Verify AI summary generation
✅ Test with 0, 1, 3, and 5+ results

## Limitations

1. **Private Groups**: Deeplinks only work if the user is a member of the group
2. **Old Messages**: Very old messages might not have deeplinks if indexed before this change
3. **DM Messages**: DM messages don't have deeplinks (not supported by Telegram)
4. **Message ID Format**: Assumes standard format `{group_id}_{telegram_msg_id}`

## Future Enhancements

🔮 Add group name/title to results (requires metadata enrichment)
🔮 Add message thread context (for topics in supergroups)
🔮 Add "jump to context" button that shows surrounding messages
🔮 Cache group metadata to avoid repeated lookups
🔮 Add visual indicators for different message types (text, media, replies)

---

**Files Modified**: `luka_bot/agents/tools/knowledge_base_tools.py`

**Compatibility**: ✅ Works with existing Elasticsearch indices, HTML is already enabled in group handlers

**Deployment**: ✅ Ready for production - no breaking changes

