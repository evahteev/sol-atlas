# luka_agent Integration Helpers

**Purpose:** Simplify integration of luka_agent with Telegram (aiogram) and Web (FastAPI/CopilotKit) platforms.

---

## Overview

The integration helpers provide ready-to-use functions that:
- Stream responses from luka_agent graph
- Format events for platform-specific consumption
- Handle tool notifications
- Render suggestions (keyboards for Telegram, quick prompts for Web)

These helpers sit between your platform handlers (Telegram bot, FastAPI endpoints) and the core luka_agent graph.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Platform Handlers                                          │
│  (luka_bot/handlers/streaming_dm.py, ag_ui_gateway/api/)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Integration Helpers (THIS MODULE)                          │
│  - stream_telegram_response()                               │
│  - stream_web_response()                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  luka_agent Core                                            │
│  - Graph (agent → tools → suggestions)                      │
│  - Tools (KB, workflows, YouTube)                           │
│  - Platform Adapters (formatting)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Telegram Integration

### Stream Telegram Response

**Function:** `stream_telegram_response()`

**Purpose:** Stream agent responses formatted for Telegram (aiogram)

**Usage:**

```python
from luka_agent.integration import stream_telegram_response
from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

async def handle_message(message: Message, bot: Bot):
    user_id = message.from_user.id
    text = message.text

    # Collect response
    full_response = ""
    keyboard = None

    async for event in stream_telegram_response(
        user_message=text,
        user_id=user_id,
        thread_id=f"telegram_{user_id}",
        knowledge_bases=[f"tg-kb-user-{user_id}"],
        language="en",
    ):
        if event["type"] == "text_chunk":
            full_response += event["content"]

        elif event["type"] == "tool_notification":
            # Optional: Send tool notification as separate message
            await bot.send_message(
                chat_id=message.chat.id,
                text=event["content"]
            )

        elif event["type"] == "suggestions":
            # Convert keyboard dict to aiogram ReplyKeyboardMarkup
            keyboard_dict = event["keyboard"]
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=btn["text"]) for btn in row]
                    for row in keyboard_dict["keyboard"]
                ],
                resize_keyboard=keyboard_dict["resize_keyboard"],
                one_time_keyboard=keyboard_dict["one_time_keyboard"],
            )

    # Send final response with keyboard
    await message.answer(full_response, reply_markup=keyboard)
```

### Event Types

**Text Chunk:**
```python
{
    "type": "text_chunk",
    "content": "Some text..."
}
```

**Tool Notification:**
```python
{
    "type": "tool_notification",
    "content": "🔍 Searching knowledge base..."
}
```

**Suggestions (Keyboard):**
```python
{
    "type": "suggestions",
    "keyboard": {
        "keyboard": [
            [{"text": "Option 1"}, {"text": "Option 2"}],
            [{"text": "Option 3"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
        "input_field_placeholder": "Choose an option or type your own..."
    }
}
```

---

## Web Integration

### Stream Web Response

**Function:** `stream_web_response()`

**Purpose:** Stream agent responses formatted for Web (AG-UI protocol)

**Usage:**

```python
from luka_agent.integration import stream_web_response
from fastapi import WebSocket

async def handle_web_message(websocket: WebSocket, user_id: int, message: str):
    async for event in stream_web_response(
        user_message=message,
        user_id=user_id,
        thread_id=f"web_{user_id}",
        knowledge_bases=[f"tg-kb-user-{user_id}"],
        language="en",
        is_guest=False,
    ):
        # Send AG-UI protocol events to client
        await websocket.send_json(event)
```

### Event Types

**Text Stream Delta (AG-UI):**
```python
{
    "type": "textStreamDelta",
    "delta": "Some text..."
}
```

**Tool Invocation:**
```python
{
    "type": "toolInvocation",
    "tool": "knowledge_base",
    "status": "started",
    "message": "🔍 Searching knowledge base..."
}
```

**Tool Result:**
```python
{
    "type": "toolResult",
    "tool": "knowledge_base",
    "result": "Search results...",
    "message": "✅ Knowledge base search complete"
}
```

**State Update (Suggestions):**
```python
{
    "type": "stateUpdate",
    "suggestions": [
        {"title": "Option 1", "message": "Option 1"},
        {"title": "Option 2", "message": "Option 2"}
    ]
}
```

---

## Non-Streaming Invocation

For cases where streaming is not needed (e.g., testing, batch processing):

### Telegram

```python
from luka_agent.integration.telegram import invoke_telegram_response

result = await invoke_telegram_response(
    user_message="What is DeFi?",
    user_id=123,
    thread_id="thread_123",
    knowledge_bases=["tg-kb-user-123"],
    language="en",
)

print(result["message"])  # Full response text
print(result["suggestions"])  # List of suggestion strings
print(result["keyboard"])  # Keyboard dict
```

### Web

```python
from luka_agent.integration.web import invoke_web_response

result = await invoke_web_response(
    user_message="What is DeFi?",
    user_id=123,
    thread_id="thread_123",
    knowledge_bases=["tg-kb-user-123"],
    language="en",
)

print(result["message"])  # Full response text
print(result["suggestions"])  # AG-UI quick prompts
```

---

## Advanced Usage

### Custom Tool Selection

Enable specific tools only:

```python
async for event in stream_telegram_response(
    user_message="What is DeFi?",
    user_id=123,
    thread_id="thread_123",
    knowledge_bases=["tg-kb-user-123"],
    language="en",
    enabled_tools=["knowledge_base", "youtube"],  # ← Only KB and YouTube
):
    # Process events...
```

### Guest Users (Web)

For unauthenticated web users:

```python
async for event in stream_web_response(
    user_message="What is DeFi?",
    user_id=0,  # Guest user ID
    thread_id="guest_session_abc123",
    knowledge_bases=["luka-public-kb"],  # Public KB
    language="en",
    is_guest=True,  # ← Mark as guest
    enabled_tools=["knowledge_base", "youtube", "support"],  # Limited tools
):
    # Process events...
```

### Multi-Language Support

Specify user's language:

```python
async for event in stream_telegram_response(
    user_message="Что такое DeFi?",
    user_id=123,
    thread_id="thread_123",
    knowledge_bases=["tg-kb-user-123"],
    language="ru",  # ← Russian language
):
    # Process events...
```

---

## Error Handling

Both streaming functions handle errors gracefully:

```python
try:
    async for event in stream_telegram_response(...):
        # Process events
        pass
except Exception as e:
    logger.error(f"Error streaming response: {e}")
    # Send error message to user
    await message.answer("Sorry, an error occurred. Please try again.")
```

---

## Integration Checklist

### Telegram Integration

- [ ] Import `stream_telegram_response` from `luka_agent.integration`
- [ ] Set up streaming loop in message handler
- [ ] Handle `text_chunk` events (accumulate response)
- [ ] Handle `tool_notification` events (optional: show to user)
- [ ] Handle `suggestions` events (convert to `ReplyKeyboardMarkup`)
- [ ] Send final response with keyboard
- [ ] Add error handling

### Web Integration

- [ ] Import `stream_web_response` from `luka_agent.integration`
- [ ] Set up WebSocket or SSE streaming
- [ ] Forward AG-UI events to client (`textStreamDelta`, `toolInvocation`, etc.)
- [ ] Handle `stateUpdate` for suggestions
- [ ] Add error handling

---

## Comparison with Direct Graph Usage

### Without Integration Helpers

```python
# Direct graph usage (more complex)
from luka_agent import get_unified_agent_graph
from luka_agent.adapters import TelegramAdapter
from langchain_core.messages import HumanMessage

graph = await get_unified_agent_graph()
adapter = TelegramAdapter()

initial_state = {
    "messages": [HumanMessage(content=text)],
    "user_id": user_id,
    # ... 10 more fields to set up ...
}

config = {"configurable": {"thread_id": thread_id}}

async for event in graph.astream_events(initial_state, config=config, version="v2"):
    event_type = event.get("event")

    if event_type == "on_chat_model_stream":
        chunk = event.get("data", {}).get("chunk")
        if chunk and hasattr(chunk, "content"):
            content = chunk.content
            # Process chunk...

    elif event_type == "on_tool_start":
        # Extract tool name, format notification...
        pass

    # ... many more event types to handle ...

# Get final state for suggestions
final_state = await graph.aget_state(config)
suggestions = final_state.values.get("conversation_suggestions", [])
keyboard = adapter.render_suggestions(suggestions)
```

### With Integration Helpers

```python
# Using integration helper (simple)
from luka_agent.integration import stream_telegram_response

async for event in stream_telegram_response(
    user_message=text,
    user_id=user_id,
    thread_id=thread_id,
    knowledge_bases=[f"tg-kb-user-{user_id}"],
    language="en",
):
    if event["type"] == "text_chunk":
        # Process chunk
        pass
    elif event["type"] == "suggestions":
        # Get keyboard
        keyboard = event["keyboard"]
```

**Benefits:**
- ✅ Less boilerplate code
- ✅ Consistent event handling
- ✅ Platform-specific formatting handled automatically
- ✅ Tool selection simplified
- ✅ Error handling built-in

---

## See Also

- **Platform Adapters:** `/luka_agent/adapters/README.md`
- **Graph Architecture:** `/luka_agent/README.md`
- **Integration Analysis:** `/docs/INTEGRATION_ANALYSIS.md`
- **Telegram Bot Example:** `/luka_bot/handlers/streaming_dm.py`
- **Web API Example:** `/ag_ui_gateway/api/copilotkit.py`

---

## Questions?

For issues or questions:
1. Check integration examples above
2. Review `/docs/INTEGRATION_ANALYSIS.md`
3. Test with `/luka_agent/tests/test_integration.py` (if available)
4. Create GitHub issue with:
   - Platform (Telegram/Web)
   - Code snippet
   - Expected vs actual behavior
   - Error logs (if any)
