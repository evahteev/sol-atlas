# Forwarded Messages Handler

This handler processes messages that are forwarded to the bot, extracting comprehensive information about the original source and providing rich context to the LLM for analysis.

## Features

### 1. **Automatic Detection**
The handler automatically detects when a message has been forwarded using aiogram's `F.forward_origin` filter.

### 2. **Source Information Extraction**
Extracts detailed information about the forwarded message source:

- **From Users:**
  - User ID
  - Full name
  - Username (if available)
  - Handles both public users and users with privacy settings enabled

- **From Groups/Chats:**
  - Chat ID
  - Group name
  - Username (if public group)
  - Thread/Topic ID (for supergroup topics)

- **From Channels:**
  - Channel ID
  - Channel name
  - Username (if public channel)
  - Original message ID

- **Additional Context:**
  - Original message date/time
  - Message ID (for linking back to original)

### 3. **User-Friendly Display**
The bot displays formatted information to the user before processing:

```
📨 Forwarded Message

👥 From Group: Crypto Trading Group (@cryptotrade)
🆔 Chat ID: -1001234567890
📝 Original Message ID: 12345
📅 Original Date: 2025-10-10 13:45:30
```

### 4. **LLM Context Enhancement**
The forwarding information is formatted as structured context for the LLM:

```
[FORWARDED MESSAGE CONTEXT]
Source: Group/Chat 'Crypto Trading Group'
Username: @cryptotrade
Chat ID: -1001234567890
Original Message ID: 12345
Thread/Topic ID: 67890
Original Date: 2025-10-10 13:45:30

[FORWARDED MESSAGE CONTENT]
<original message text>

[END FORWARDED MESSAGE]

Please analyze this forwarded message, taking into account its source and context.
```

This allows the LLM to:
- Understand the message came from an external source
- Consider the source's context in its analysis
- Provide more accurate and context-aware responses

## Important Privacy Limitation

**Group/Channel Information Visibility:**

When a user forwards a message to the bot from a group or channel where **the bot is NOT a member**, Telegram protects privacy by NOT revealing the group/channel information. In this case, you will only see:

```
📨 Forwarded Message

👤 From User: John Doe (@johndoe)
🆔 User ID: 123456789
📅 Original Date: 2025-10-10 13:45:30
```

**To see full group/thread information**, the bot must be:
1. Added as a member to that group/channel
2. Given appropriate permissions

Only then will you see details like:
- Group/Channel ID
- Group/Channel name
- Thread/Topic ID (for supergroups)
- Original message ID

This is a Telegram privacy feature to prevent bots from harvesting information about private groups they're not part of.

## Supported Forward Types

### User Forwards
```python
# From a user with public account
info["origin_type"] = "user"
info["origin_id"] = 123456789
info["origin_name"] = "John Doe"
info["origin_username"] = "johndoe"
```

### Hidden User Forwards
```python
# From a user with privacy settings enabled
info["origin_type"] = "hidden_user"
info["origin_name"] = "John"  # Only first name available
```

### Group/Chat Forwards
```python
# From a group or supergroup
info["origin_type"] = "chat"
info["origin_id"] = -1001234567890
info["origin_name"] = "My Group"
info["origin_username"] = "mygroup"  # If public
info["thread_id"] = "12345"  # If from topic
```

### Channel Forwards
```python
# From a channel
info["origin_type"] = "channel"
info["origin_id"] = -1001234567890
info["origin_name"] = "My Channel"
info["origin_username"] = "mychannel"  # If public
info["message_id"] = 67890
```

## Usage Examples

### Example 1: Analyzing a Forwarded Group Message

**User forwards a message from a crypto group:**

Bot response:
```
📨 Forwarded Message

👥 From Group: Crypto Trading Group (@cryptotrade)
🆔 Chat ID: -1001234567890
📝 Original Message ID: 12345
📅 Original Date: 2025-10-10 13:45:30

🤔 [analyzing...]
```

LLM receives:
```
[FORWARDED MESSAGE CONTEXT]
Source: Group/Chat 'Crypto Trading Group'
Username: @cryptotrade
Chat ID: -1001234567890
Original Message ID: 12345
Original Date: 2025-10-10 13:45:30

[FORWARDED MESSAGE CONTENT]
Bitcoin just broke $50k! 🚀

[END FORWARDED MESSAGE]

Please analyze this forwarded message, taking into account its source and context.
```

### Example 2: Forwarded Channel Post

**User forwards a news article from a channel:**

```
📨 Forwarded Message

📢 From Channel: Tech News Daily (@technewsdaily)
🆔 Channel ID: -1001234567890
📝 Original Message ID: 456
📅 Original Date: 2025-10-10 12:00:00
```

### Example 3: Private User Message

**User forwards a message from another user:**

```
📨 Forwarded Message

👤 From User: Alice (@alice)
🆔 User ID: 987654321
📅 Original Date: 2025-10-10 11:30:00
```

## Implementation Details

### Handler Priority
The forwarded messages handler is registered **before** the general streaming handler to ensure forwarded messages are caught and processed with their special context.

```python
router.include_router(forwarded_router)  # Specific - catches forwarded messages
router.include_router(streaming_router)  # General - catches all other messages
```

### Filter
Uses aiogram's `F.forward_origin` filter to detect forwarded messages:

```python
@router.message(F.chat.type == ChatType.PRIVATE, F.forward_origin)
async def handle_forwarded_message(message: Message, state: FSMContext) -> None:
```

### Thread Integration
Forwarded messages are processed within the user's active thread, maintaining conversation context:

```python
thread = await thread_service.get_or_create_active_thread(user_id)
thread_id = thread.thread_id
```

### Streaming Support
The handler uses the same streaming mechanism as regular messages, providing real-time responses and tool usage indicators.

## Error Handling

### Non-Text Messages
If a forwarded message doesn't contain text (e.g., photos, videos without captions):

```
📨 I received a forwarded message, but it doesn't contain text to analyze. 
Please forward messages with text content.
```

### Processing Errors
If an error occurs during analysis:

```
❌ Sorry, I encountered an error while analyzing the forwarded message. 
Please try again.
```

## Logging

The handler provides detailed logging for debugging:

```python
logger.info(f"📨 Forwarded message from user {user_id}: {text[:50]}...")
logger.info(
    f"📨 Forward details: type={forward_info['origin_type']}, "
    f"name={forward_info['origin_name']}, "
    f"id={forward_info['origin_id']}, "
    f"thread_id={forward_info['thread_id']}"
)
logger.info(f"🤖 Sending forwarded message to LLM with context: {len(llm_input)} chars")
logger.info(f"✅ Forwarded message analysis complete: {len(full_response)} chars")
```

## Future Enhancements

Potential improvements for future versions:

1. **Media Support** - Process forwarded media (images, videos) with captions
2. **Batch Processing** - Handle multiple forwarded messages at once
3. **Source Verification** - Verify authenticity of forwarded content
4. **Link Preservation** - Maintain links back to original messages when possible
5. **Thread Mapping** - Automatically link to relevant conversation threads based on source
6. **Analytics** - Track forwarding patterns and popular sources

## See Also

- `luka_bot/handlers/streaming_dm.py` - Regular message handling
- `luka_bot/services/llm_service.py` - LLM integration
- `luka_bot/services/thread_service.py` - Thread management
- [Aiogram Forward Origin Documentation](https://docs.aiogram.dev/en/latest/api/types/forward_origin.html)

