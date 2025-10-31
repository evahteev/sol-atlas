# Group Reply Handler Feature

**Date**: 2025-10-11  
**Status**: ✅ Complete

## Overview

Added intelligent reply detection in groups so users can naturally continue conversations with the bot by replying to its messages, without needing to @mention it every time.

## Feature Description

When a user replies to a bot's message in a group, the bot now:
1. ✅ Automatically detects the reply (treated like a mention)
2. ✅ Includes the original bot message in the LLM context
3. ✅ Generates a contextually-aware response
4. ✅ Maintains conversation continuity

## Implementation Details

### 1. Reply Detection

```python
# Check if this is a reply to bot's message
if message.reply_to_message:
    replied_message = message.reply_to_message
    # Check if the replied message is from the bot
    if replied_message.from_user and replied_message.from_user.id == bot_info.id:
        is_reply_to_bot = True
        bot_original_message = replied_message.text or replied_message.caption or ""
        logger.info(f"✅ Reply to bot detected from user {user_id} in group {group_id}")
```

**Detection Logic**:
- Checks if `message.reply_to_message` exists
- Verifies the replied message is from the bot (compares user IDs)
- Extracts text or caption from the original bot message
- Logs the reply detection for monitoring

### 2. Context Building

When a reply is detected, the LLM receives enhanced context:

```python
if is_reply_to_bot and bot_original_message:
    context_parts = [
        f"[GROUP REPLY from {sender_name}]",
        f"[In topic/thread ID: {thread_id}]",  # If in a topic
        f"[User is replying to your previous message: \"{truncated_original}\"]",
        f"User's reply: {message_text}"
    ]
```

**Context Format**:
```
[GROUP REPLY from John Doe]
[In topic/thread ID: 123]
[User is replying to your previous message: "Based on your conversation history..."]
User's reply: Thanks! Can you tell me more about the first result?
```

### 3. Original Message Truncation

To avoid overwhelming the context window:
- Original bot messages are truncated to 200 characters
- Ellipsis (`...`) added if truncated
- Full message content is still available in conversation history

### 4. Interaction Types

The bot now distinguishes between:
- **Mentions**: Direct @bot mentions → `"Bot mention in group"`
- **Replies**: Replies to bot messages → `"Bot reply in group"`

Both are handled with appropriate context and logging.

## User Experience

### Before (Mentions Only):
```
User: @GuruKeeperBot what did we discuss today?
Bot: Based on your conversation history...

User: @GuruKeeperBot can you tell me more about the first result?
Bot: [Processes without knowing which "first result"]
```

### After (With Reply Handler):
```
User: @GuruKeeperBot what did we discuss today?
Bot: Based on your conversation history...

User: [Replies to bot's message] Can you tell me more about the first result?
Bot: [Understands context from original message and responds appropriately]
```

## Benefits

1. **Natural Conversation Flow**: Users can reply like in normal chats
2. **Better Context**: LLM knows exactly what it said previously
3. **Reduced Typing**: No need to @mention for follow-ups
4. **Improved UX**: More intuitive conversation threading
5. **Topic Support**: Works seamlessly with supergroup topics

## Technical Considerations

### Message ID Handling

The bot tracks:
- `message.message_id`: Current user message
- `message.reply_to_message.message_id`: Original bot message
- `message.reply_to_message.from_user.id`: Verify it's from bot

### Edge Cases Handled

✅ **No replied message**: Falls back to normal mention detection  
✅ **Reply to non-bot message**: Ignored, only mentions trigger response  
✅ **Reply to bot with mention**: Works, treated as reply (takes precedence)  
✅ **Empty bot message**: Gracefully handles with fallback  
✅ **Media messages**: Extracts caption if text is unavailable  
✅ **Topics/threads**: Thread ID preserved in context  

### Logging

Enhanced logging shows interaction type:
```
INFO - 🔔 Bot reply in group -1001902150742 by user 922705
INFO - 🔔 Bot mention in group -1001902150742 by user 922705
```

This helps distinguish reply-based interactions from direct mentions in logs.

## Moderation Integration

Reply-based interactions are treated identically to mentions:
- ✅ Reputation updates apply
- ✅ Background moderation runs
- ✅ Reply tracking for retroactive deletion
- ✅ KB indexing includes reply context

## Testing Scenarios

### Test 1: Simple Reply
```
1. User mentions bot: "@GuruKeeperBot Hello!"
2. Bot responds: "Hello! How can I help?"
3. User replies to bot's message: "Tell me about your features"
4. Bot should respond with context
```

### Test 2: Reply in Topic
```
1. In a supergroup topic
2. User mentions bot
3. Bot responds
4. User replies to bot's message
5. Bot should maintain topic context + reply context
```

### Test 3: Reply to Old Message
```
1. Bot sent a message 1 hour ago
2. User replies to that old message now
3. Bot should still respond with original message context
```

### Test 4: Multiple Users Replying
```
1. Bot responds to User A
2. User B replies to bot's message to User A
3. Bot should respond to User B with context
```

## Configuration

No additional configuration required:
- ✅ Enabled by default for all groups
- ✅ Works with existing group settings
- ✅ Compatible with language preferences
- ✅ Works with moderation settings

## Future Enhancements

🔮 **Thread Visualization**: Show conversation threads in UI  
🔮 **Multi-turn Context**: Track entire reply chains  
🔮 **Reply Suggestions**: Suggest common follow-up questions  
🔮 **Reply Analytics**: Track reply-based vs mention-based interactions  
🔮 **Smart Reply Detection**: Detect implicit replies without formal reply feature  

## Performance Impact

- **Minimal**: Only checks `reply_to_message` attribute
- **No additional API calls**: Uses existing message object
- **Memory efficient**: Only stores 200 chars of original message
- **Logging overhead**: One additional log line per reply

## Compatibility

✅ **Telegram API**: Uses standard `reply_to_message` feature  
✅ **Aiogram**: Works with aiogram 3.x Message object  
✅ **Existing features**: Compatible with mentions, KB indexing, moderation  
✅ **Topics**: Works in supergroup topics with thread IDs  
✅ **Multi-language**: Respects group language settings  

---

**Files Modified**: `luka_bot/handlers/group_messages.py`

**Lines Added**: ~20 lines of logic + comments

**Testing Status**: ✅ Ready for testing in production groups

**Deployment**: ✅ No migration required, works with existing data

