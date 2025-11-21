# Platform Adapters

**Transform platform-agnostic luka_agent output into platform-specific formats.**

---

<objective>
Provide platform adapters that handle rendering differences between Telegram and Web while keeping luka_agent core platform-agnostic.
</objective>

<context>
## What Are Platform Adapters?

Platform adapters are the bridge between luka_agent's unified output and platform-specific rendering requirements.

### Problem They Solve

**luka_agent produces**:
- Plain text messages
- List of suggestion strings
- Standard markdown

**Platforms require**:
- **Telegram**: ReplyKeyboardMarkup, MarkdownV2 escaping, 4096 char limit
- **Web**: Quick prompts (AG-UI), standard markdown, no length limits

**Adapters transform** luka_agent output → Platform-specific format

### Architecture

```
luka_agent graph
    ↓
AgentState (platform-agnostic)
    ↓
Platform Adapter
    ↓
    ┌─────────────────────────────────┐
    │ Telegram Adapter                │
    │ - ReplyKeyboardMarkup           │
    │ - MarkdownV2 escaping           │
    │ - Message chunking (4096 limit) │
    └─────────────────────────────────┘
    OR
    ┌─────────────────────────────────┐
    │ Web Adapter                     │
    │ - AG-UI quick prompts           │
    │ - Standard markdown             │
    │ - No length limits              │
    └─────────────────────────────────┘
    ↓
Platform-specific rendering
    ↓
User sees response
```
</context>

---

<requirements>
## Adapter Requirements

### All Adapters Must

- [ ] **Extend BasePlatformAdapter**: Inherit from base class
- [ ] **Implement all abstract methods**: render_suggestions, format_message, chunk_long_message, escape_markdown
- [ ] **Be stateless**: No instance state, pure transformation
- [ ] **Handle edge cases**: Empty suggestions, very long messages, special characters
- [ ] **Document constraints**: Platform-specific limits and quirks

### Telegram Adapter Must

- [ ] **Keyboard rendering**: Convert suggestions to ReplyKeyboardMarkup
- [ ] **MarkdownV2 escaping**: Escape special characters properly
- [ ] **Message chunking**: Split messages >4096 characters
- [ ] **Button limits**: Recommend 3-4 buttons per row for mobile UX
- [ ] **Link parsing**: Handle "Text - URL" suggestion format

### Web Adapter Must

- [ ] **Quick prompts**: Convert suggestions to AG-UI format
- [ ] **Standard markdown**: No special escaping needed
- [ ] **Streaming support**: Format streaming chunks
- [ ] **Tool notifications**: Format tool execution status
- [ ] **AG-UI protocol**: Follow CopilotKit/AG-UI conventions
</requirements>

---

<implementation>
## Using Platform Adapters

### Basic Usage

```python
from luka_agent.adapters import TelegramAdapter, WebAdapter

# Create adapter
telegram_adapter = TelegramAdapter()
web_adapter = WebAdapter()

# Render suggestions
suggestions = ["Option 1", "Option 2", "Option 3"]

telegram_keyboard = telegram_adapter.render_suggestions(suggestions)
# Returns: Dict compatible with aiogram ReplyKeyboardMarkup

web_prompts = web_adapter.render_suggestions(suggestions)
# Returns: List of AG-UI quick prompt dicts

# Format message
long_message = "..." * 2000  # Very long message

telegram_formatted = telegram_adapter.format_message(long_message)
# Returns: Truncated message with indicator

web_formatted = web_adapter.format_message(long_message)
# Returns: Full message (web handles length)
```

### Integration Example (Telegram)

```python
from aiogram import Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from luka_agent import get_unified_agent_graph, create_tools_for_user
from luka_agent.adapters import TelegramAdapter
from langchain_core.messages import HumanMessage

async def handle_telegram_message(bot: Bot, user_id: int, chat_id: int, text: str):
    # Create adapter
    adapter = TelegramAdapter()

    # Get graph and invoke
    graph = await get_unified_agent_graph()
    config = {"configurable": {"thread_id": f"telegram_{user_id}"}}

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=text)]},
        config=config
    )

    # Extract response
    agent_message = result["messages"][-1].content
    suggestions = result.get("suggestions", [])

    # Format for Telegram
    formatted_message = adapter.format_message(agent_message)

    # Render keyboard
    keyboard_dict = adapter.render_suggestions(suggestions)
    keyboard = None
    if keyboard_dict:
        # Convert dict to aiogram ReplyKeyboardMarkup
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn["text"]) for btn in row] for row in keyboard_dict["keyboard"]],
            resize_keyboard=keyboard_dict["resize_keyboard"],
            one_time_keyboard=keyboard_dict["one_time_keyboard"],
        )

    # Send to Telegram
    await bot.send_message(
        chat_id=chat_id,
        text=formatted_message,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
```

### Integration Example (Web / AG-UI)

```python
from fastapi import WebSocket
from luka_agent import get_unified_agent_graph
from luka_agent.adapters import WebAdapter
from langchain_core.messages import HumanMessage

async def handle_web_message(websocket: WebSocket, user_id: int, text: str):
    # Create adapter
    adapter = WebAdapter()

    # Get graph and invoke
    graph = await get_unified_agent_graph()
    config = {"configurable": {"thread_id": f"web_{user_id}"}}

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=text)]},
        config=config
    )

    # Extract response
    agent_message = result["messages"][-1].content
    suggestions = result.get("suggestions", [])

    # Format for AG-UI
    response = adapter.format_ag_ui_response(
        message=agent_message,
        suggestions=suggestions
    )

    # Send to client via WebSocket
    await websocket.send_json(response)
```

### Streaming Example (Web)

```python
from luka_agent import get_unified_agent_graph
from luka_agent.adapters import WebAdapter

async def handle_web_streaming(websocket: WebSocket, user_id: int, text: str):
    adapter = WebAdapter()
    graph = await get_unified_agent_graph()
    config = {"configurable": {"thread_id": f"web_{user_id}"}}

    # Stream events
    async for event in graph.astream_events(
        {"messages": [HumanMessage(content=text)]},
        config=config,
        version="v2"
    ):
        if event["event"] == "on_chat_model_stream":
            # Stream text chunks
            chunk = event["data"]["chunk"].content
            formatted_chunk = adapter.format_streaming_chunk(chunk)
            await websocket.send_json(formatted_chunk)

        elif event["event"] == "on_tool_start":
            # Tool started notification
            tool_name = event["name"]
            notification = adapter.format_tool_notification(tool_name, "started")
            await websocket.send_json({"type": "notification", "message": notification})

        elif event["event"] == "on_tool_end":
            # Tool completed notification
            tool_name = event["name"]
            notification = adapter.format_tool_notification(tool_name, "completed")
            await websocket.send_json({"type": "notification", "message": notification})
```
</implementation>

---

<output>
## API Reference

### BasePlatformAdapter

**Abstract Methods**:
```python
def render_suggestions(suggestions: list[str]) -> Any:
    """Convert suggestions to platform-specific UI."""

def format_message(text: str) -> str:
    """Format message for platform constraints."""

def chunk_long_message(text: str) -> list[str]:
    """Split long messages into platform-appropriate chunks."""

def escape_markdown(text: str) -> str:
    """Escape markdown for platform-specific rendering."""
```

### TelegramAdapter

**Platform**: Telegram Bot API (aiogram 3.x)

**Constraints**:
- Max message length: 4096 characters
- Recommended buttons per row: 3
- Markdown: MarkdownV2 with special escaping

**Methods**:
```python
render_suggestions(suggestions: list[str]) -> dict:
    """Returns dict compatible with aiogram ReplyKeyboardMarkup."""

format_message(text: str) -> str:
    """Truncates to 4096 chars with indicator if needed."""

chunk_long_message(text: str) -> list[str]:
    """Splits at paragraph/sentence/word boundaries."""

escape_markdown(text: str) -> str:
    """Escapes MarkdownV2 special characters."""

format_link(text: str, url: str) -> str:
    """Returns Telegram markdown link."""

remove_keyboard() -> dict:
    """Returns dict for ReplyKeyboardRemove."""

parse_suggestion_with_link(suggestion: str) -> tuple[str, Optional[str]]:
    """Parses 'Text - URL' format suggestions."""
```

### WebAdapter

**Platform**: Web (AG-UI protocol / CopilotKit)

**Constraints**:
- No practical message length limit
- Recommended suggestions: 5
- Markdown: Standard markdown

**Methods**:
```python
render_suggestions(suggestions: list[str]) -> list[dict[str, str]]:
    """Returns list of AG-UI quick prompt dicts."""

format_message(text: str) -> str:
    """Returns text as-is (web handles long content)."""

chunk_long_message(text: str) -> list[str]:
    """Returns single chunk (rarely needed for web)."""

escape_markdown(text: str) -> str:
    """Returns text as-is (standard markdown)."""

format_link(text: str, url: str) -> str:
    """Returns standard markdown link."""

format_code_block(code: str, language: str = "") -> str:
    """Returns formatted code block with syntax highlighting."""

format_ag_ui_response(message: str, suggestions: list[str] = None, metadata: dict = None) -> dict:
    """Returns complete AG-UI protocol response."""

format_tool_notification(tool_name: str, status: str = "started") -> str:
    """Returns formatted tool execution notification."""

format_streaming_chunk(chunk: str) -> dict:
    """Returns AG-UI streaming chunk."""
```
</output>

---

<validation>
## Testing Adapters

### Unit Tests

```python
import pytest
from luka_agent.adapters import TelegramAdapter, WebAdapter


def test_telegram_render_suggestions():
    """Test Telegram keyboard rendering."""
    adapter = TelegramAdapter()
    suggestions = ["Option 1", "Option 2", "Option 3", "Option 4"]

    keyboard = adapter.render_suggestions(suggestions)

    assert keyboard is not None
    assert "keyboard" in keyboard
    assert len(keyboard["keyboard"]) == 2  # 2 rows (3 + 1)
    assert len(keyboard["keyboard"][0]) == 3  # First row has 3 buttons
    assert keyboard["resize_keyboard"] is True


def test_telegram_message_truncation():
    """Test Telegram message truncation."""
    adapter = TelegramAdapter()
    long_message = "A" * 5000  # Exceeds 4096 limit

    formatted = adapter.format_message(long_message)

    assert len(formatted) <= adapter.MAX_MESSAGE_LENGTH
    assert "truncated" in formatted.lower()


def test_telegram_markdown_escaping():
    """Test MarkdownV2 escaping."""
    adapter = TelegramAdapter()
    text_with_special_chars = "Hello_world *test* [link](url) #tag"

    escaped = adapter.escape_markdown(text_with_special_chars)

    # Special chars should be escaped (outside code blocks)
    assert "\\_" in escaped or "_" not in escaped  # _ escaped or removed
    assert "\\*" in escaped or "*" in "```" or "`"  # * escaped or in code


def test_web_render_suggestions():
    """Test Web quick prompts rendering."""
    adapter = WebAdapter()
    suggestions = ["Option 1", "Option 2", "Option 3"]

    prompts = adapter.render_suggestions(suggestions)

    assert isinstance(prompts, list)
    assert len(prompts) == 3
    assert all("title" in p and "message" in p for p in prompts)


def test_web_ag_ui_response():
    """Test AG-UI response formatting."""
    adapter = WebAdapter()
    message = "Hello, how can I help?"
    suggestions = ["Option 1", "Option 2"]

    response = adapter.format_ag_ui_response(message, suggestions)

    assert "message" in response
    assert "suggestions" in response
    assert response["message"] == message
    assert len(response["suggestions"]) == 2


def test_web_tool_notification():
    """Test tool notification formatting."""
    adapter = WebAdapter()

    started = adapter.format_tool_notification("knowledge_base", "started")
    assert "🔍" in started or "knowledge" in started.lower()

    completed = adapter.format_tool_notification("youtube", "completed")
    assert "✅" in completed or "complete" in completed.lower()
```

### Integration Tests

Test adapters with actual luka_agent graph:

```python
@pytest.mark.asyncio
async def test_telegram_adapter_integration():
    """Test Telegram adapter with real graph output."""
    from luka_agent import get_unified_agent_graph
    from luka_agent.adapters import TelegramAdapter
    from langchain_core.messages import HumanMessage

    adapter = TelegramAdapter()
    graph = await get_unified_agent_graph()
    config = {"configurable": {"thread_id": "test_telegram"}}

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="Hello")]},
        config=config
    )

    # Format output
    message = result["messages"][-1].content
    suggestions = result.get("suggestions", [])

    formatted_message = adapter.format_message(message)
    keyboard = adapter.render_suggestions(suggestions)

    # Verify formatting
    assert isinstance(formatted_message, str)
    assert len(formatted_message) <= adapter.MAX_MESSAGE_LENGTH
    if keyboard:
        assert "keyboard" in keyboard
```
</validation>

---

<constraints>
## Design Constraints with WHY

### Adapter Constraints

**ALWAYS keep adapters stateless**
- WHY: Adapters should be pure transformation functions
- DO: Create new instance per request (lightweight)
- DON'T: Store state in adapter instance

**ALWAYS handle None/empty inputs gracefully**
- WHY: Suggestions may be None or empty list
- DO: Return appropriate "no suggestions" format
- DON'T: Raise exceptions on empty input

**NEVER include business logic in adapters**
- WHY: Business logic belongs in luka_agent tools/graph
- DO: Transform data only
- DON'T: Make decisions about what to show

**ALWAYS preserve semantic meaning**
- WHY: Platform differences shouldn't change meaning
- DO: Format differently but keep intent
- DON'T: Add/remove content based on platform

### Telegram Constraints

**ALWAYS respect 4096 character limit**
- WHY: Telegram API rejects longer messages
- DO: Truncate or chunk appropriately
- DON'T: Send messages exceeding limit

**ALWAYS escape MarkdownV2 special characters**
- WHY: Unescaped chars cause parsing errors
- DO: Escape outside code blocks
- DON'T: Escape inside ``` code blocks or ` inline code `

**ALWAYS limit keyboard buttons for mobile UX**
- WHY: Too many buttons overwhelm mobile users
- DO: Recommend 3-4 buttons per row, max ~12 total
- DON'T: Create keyboards with 20+ buttons

### Web Constraints

**ALWAYS follow AG-UI protocol conventions**
- WHY: Compatibility with CopilotKit and AG-UI clients
- DO: Use standard field names (title, message, etc.)
- DON'T: Invent custom protocol fields

**ALWAYS provide streaming support**
- WHY: Web users expect real-time responses
- DO: Format chunks for progressive rendering
- DON'T: Only support batch responses
</constraints>

---

## Resources

- **Base Adapter**: `luka_agent/adapters/base.py`
- **Telegram Adapter**: `luka_agent/adapters/telegram.py`
- **Web Adapter**: `luka_agent/adapters/web.py`
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **AG-UI Protocol**: https://github.com/CopilotKit/CopilotKit
- **aiogram Docs**: https://docs.aiogram.dev/

---

## Questions?

For issues or questions:
1. **Check adapter source code**: `luka_agent/adapters/*.py`
2. **Review integration examples**: See `<implementation>` section above
3. **Test with actual platform**: Verify rendering on Telegram/Web
4. **Create GitHub issue** with:
   - Platform (Telegram/Web)
   - Input data
   - Expected vs actual output
   - Error logs (if any)

---

**Platform adapters enable unified luka_agent to serve multiple platforms seamlessly! 🚀**
