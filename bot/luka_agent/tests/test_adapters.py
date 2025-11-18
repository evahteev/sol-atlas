"""
Tests for platform adapters.
"""

import pytest

from luka_agent.adapters import TelegramAdapter, WebAdapter
from luka_agent.adapters.base import BasePlatformAdapter


# =============================================================================
# Base Adapter Tests
# =============================================================================


def test_base_adapter_is_abstract():
    """Test that BasePlatformAdapter cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BasePlatformAdapter()


# =============================================================================
# Telegram Adapter Tests
# =============================================================================


def test_telegram_adapter_instantiation():
    """Test Telegram adapter can be instantiated."""
    adapter = TelegramAdapter()
    assert adapter is not None
    assert adapter.get_platform_name() == "telegram"


def test_telegram_render_suggestions_basic():
    """Test basic suggestion rendering for Telegram."""
    adapter = TelegramAdapter()
    suggestions = ["Option 1", "Option 2", "Option 3"]

    keyboard = adapter.render_suggestions(suggestions)

    assert keyboard is not None
    assert "keyboard" in keyboard
    assert len(keyboard["keyboard"]) == 1  # 1 row with 3 buttons
    assert len(keyboard["keyboard"][0]) == 3  # 3 buttons in row
    assert keyboard["resize_keyboard"] is True
    assert keyboard["one_time_keyboard"] is True


def test_telegram_render_suggestions_multiple_rows():
    """Test suggestion rendering with multiple rows."""
    adapter = TelegramAdapter()
    suggestions = ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"]

    keyboard = adapter.render_suggestions(suggestions)

    assert len(keyboard["keyboard"]) == 2  # 2 rows (3 + 2)
    assert len(keyboard["keyboard"][0]) == 3  # First row: 3 buttons
    assert len(keyboard["keyboard"][1]) == 2  # Second row: 2 buttons


def test_telegram_render_suggestions_limit():
    """Test suggestion limiting (max 12)."""
    adapter = TelegramAdapter()
    suggestions = [f"Option {i}" for i in range(20)]  # 20 suggestions

    keyboard = adapter.render_suggestions(suggestions)

    # Should limit to 12 (4 rows × 3 buttons)
    total_buttons = sum(len(row) for row in keyboard["keyboard"])
    assert total_buttons == 12


def test_telegram_render_suggestions_empty():
    """Test empty suggestions."""
    adapter = TelegramAdapter()
    suggestions = []

    keyboard = adapter.render_suggestions(suggestions)

    assert keyboard is None


def test_telegram_format_message_short():
    """Test formatting short message (under limit)."""
    adapter = TelegramAdapter()
    short_message = "This is a short message."

    formatted = adapter.format_message(short_message)

    assert formatted == short_message  # No changes


def test_telegram_format_message_long():
    """Test formatting long message (over 4096 limit)."""
    adapter = TelegramAdapter()
    long_message = "A" * 5000  # Exceeds 4096 limit

    formatted = adapter.format_message(long_message)

    assert len(formatted) <= adapter.MAX_MESSAGE_LENGTH
    assert "truncated" in formatted.lower()


def test_telegram_chunk_long_message():
    """Test chunking very long message."""
    adapter = TelegramAdapter()
    very_long_message = "Paragraph. " * 1000  # ~11000 chars

    chunks = adapter.chunk_long_message(very_long_message)

    # Should be split into multiple chunks
    assert len(chunks) > 1
    # Each chunk should be within limit
    for chunk in chunks:
        assert len(chunk) <= adapter.MAX_MESSAGE_LENGTH
    # Continuation indicators should be present
    assert any("continued" in chunk.lower() for chunk in chunks)


def test_telegram_chunk_short_message():
    """Test chunking short message (no chunking needed)."""
    adapter = TelegramAdapter()
    short_message = "Short message."

    chunks = adapter.chunk_long_message(short_message)

    assert len(chunks) == 1
    assert chunks[0] == short_message


def test_telegram_escape_markdown():
    """Test MarkdownV2 escaping."""
    adapter = TelegramAdapter()
    text_with_special_chars = "Hello_world *test* [link] #tag . ! -"

    escaped = adapter.escape_markdown(text_with_special_chars)

    # Should have escape characters
    assert "\\" in escaped
    # Original special chars should be escaped
    # (exact escaping depends on implementation)


def test_telegram_escape_markdown_preserves_code():
    """Test that code blocks are not escaped."""
    adapter = TelegramAdapter()
    text_with_code = "Regular text `code_with_underscore` more text"

    escaped = adapter.escape_markdown(text_with_code)

    # Code content should not be escaped
    assert "`code_with_underscore`" in escaped


def test_telegram_format_link():
    """Test link formatting."""
    adapter = TelegramAdapter()
    text = "Click here"
    url = "https://example.com"

    link = adapter.format_link(text, url)

    assert "[" in link
    assert "](" in link
    assert url in link


def test_telegram_remove_keyboard():
    """Test keyboard removal."""
    adapter = TelegramAdapter()

    remove = adapter.remove_keyboard()

    assert "remove_keyboard" in remove
    assert remove["remove_keyboard"] is True


def test_telegram_parse_suggestion_with_link():
    """Test parsing suggestion with link."""
    adapter = TelegramAdapter()

    # With link
    text, url = adapter.parse_suggestion_with_link("🚀 Launch - https://example.com")
    assert text == "🚀 Launch"
    assert url == "https://example.com"

    # Without link
    text, url = adapter.parse_suggestion_with_link("Simple option")
    assert text == "Simple option"
    assert url is None


# =============================================================================
# Web Adapter Tests
# =============================================================================


def test_web_adapter_instantiation():
    """Test Web adapter can be instantiated."""
    adapter = WebAdapter()
    assert adapter is not None
    assert adapter.get_platform_name() == "web"


def test_web_render_suggestions_basic():
    """Test basic suggestion rendering for Web."""
    adapter = WebAdapter()
    suggestions = ["Option 1", "Option 2", "Option 3"]

    prompts = adapter.render_suggestions(suggestions)

    assert isinstance(prompts, list)
    assert len(prompts) == 3
    for prompt in prompts:
        assert "title" in prompt
        assert "message" in prompt


def test_web_render_suggestions_limit():
    """Test suggestion limiting (recommended 5)."""
    adapter = WebAdapter()
    suggestions = [f"Option {i}" for i in range(10)]

    prompts = adapter.render_suggestions(suggestions)

    assert len(prompts) == adapter.RECOMMENDED_SUGGESTIONS  # 5


def test_web_render_suggestions_empty():
    """Test empty suggestions."""
    adapter = WebAdapter()
    suggestions = []

    prompts = adapter.render_suggestions(suggestions)

    assert prompts == []


def test_web_render_suggestions_with_link():
    """Test suggestion rendering with link."""
    adapter = WebAdapter()
    suggestions = ["🚀 Launch - https://example.com"]

    prompts = adapter.render_suggestions(suggestions)

    assert len(prompts) == 1
    assert prompts[0]["title"] == "🚀 Launch"
    assert "metadata" in prompts[0]
    assert prompts[0]["metadata"]["url"] == "https://example.com"


def test_web_format_message():
    """Test message formatting for Web (no changes)."""
    adapter = WebAdapter()
    message = "This is a message."

    formatted = adapter.format_message(message)

    assert formatted == message  # No formatting needed for web


def test_web_format_message_long():
    """Test long message formatting (web handles it)."""
    adapter = WebAdapter()
    long_message = "A" * 10000  # Very long

    formatted = adapter.format_message(long_message)

    # Web doesn't truncate
    assert formatted == long_message


def test_web_chunk_long_message():
    """Test chunking (web doesn't chunk)."""
    adapter = WebAdapter()
    long_message = "A" * 10000

    chunks = adapter.chunk_long_message(long_message)

    # Web returns single chunk
    assert len(chunks) == 1
    assert chunks[0] == long_message


def test_web_escape_markdown():
    """Test markdown escaping (minimal for web)."""
    adapter = WebAdapter()
    text_with_markdown = "**bold** *italic* `code`"

    escaped = adapter.escape_markdown(text_with_markdown)

    # Web uses standard markdown, no escaping needed
    assert escaped == text_with_markdown


def test_web_format_code_block():
    """Test code block formatting."""
    adapter = WebAdapter()
    code = "print('hello')"

    # Without language
    formatted = adapter.format_code_block(code)
    assert "```" in formatted
    assert code in formatted

    # With language
    formatted = adapter.format_code_block(code, "python")
    assert "```python" in formatted
    assert code in formatted


def test_web_format_link():
    """Test link formatting."""
    adapter = WebAdapter()
    text = "Click here"
    url = "https://example.com"

    link = adapter.format_link(text, url)

    assert link == f"[{text}]({url})"


def test_web_parse_suggestion_with_link():
    """Test parsing suggestion with link."""
    adapter = WebAdapter()

    # With link
    text, url = adapter.parse_suggestion_with_link("🚀 Launch - https://example.com")
    assert text == "🚀 Launch"
    assert url == "https://example.com"

    # Without link
    text, url = adapter.parse_suggestion_with_link("Simple option")
    assert text == "Simple option"
    assert url is None


def test_web_format_ag_ui_response_basic():
    """Test AG-UI response formatting."""
    adapter = WebAdapter()
    message = "Hello, how can I help?"

    response = adapter.format_ag_ui_response(message)

    assert "message" in response
    assert response["message"] == message


def test_web_format_ag_ui_response_with_suggestions():
    """Test AG-UI response with suggestions."""
    adapter = WebAdapter()
    message = "Choose an option:"
    suggestions = ["Option 1", "Option 2"]

    response = adapter.format_ag_ui_response(message, suggestions)

    assert "message" in response
    assert "suggestions" in response
    assert len(response["suggestions"]) == 2


def test_web_format_ag_ui_response_with_metadata():
    """Test AG-UI response with metadata."""
    adapter = WebAdapter()
    message = "Processing..."
    metadata = {"workflow": "onboarding", "step": 1}

    response = adapter.format_ag_ui_response(message, metadata=metadata)

    assert "message" in response
    assert "metadata" in response
    assert response["metadata"] == metadata


def test_web_format_tool_notification():
    """Test tool notification formatting."""
    adapter = WebAdapter()

    # Started
    notification = adapter.format_tool_notification("knowledge_base", "started")
    assert "🔍" in notification or "knowledge" in notification.lower()
    assert "..." in notification or "using" in notification.lower()

    # Completed
    notification = adapter.format_tool_notification("youtube", "completed")
    assert "✅" in notification or "complete" in notification.lower()

    # Failed
    notification = adapter.format_tool_notification("search", "failed")
    assert "❌" in notification or "failed" in notification.lower()


def test_web_format_streaming_chunk():
    """Test streaming chunk formatting."""
    adapter = WebAdapter()
    chunk = "Hello"

    formatted = adapter.format_streaming_chunk(chunk)

    assert "type" in formatted
    assert formatted["type"] == "textStreamDelta"
    assert "delta" in formatted
    assert formatted["delta"] == chunk


# =============================================================================
# Comparison Tests
# =============================================================================


def test_adapters_handle_same_input_differently():
    """Test that adapters transform same input appropriately for each platform."""
    suggestions = ["Option 1", "Option 2", "Option 3"]

    telegram_adapter = TelegramAdapter()
    web_adapter = WebAdapter()

    telegram_result = telegram_adapter.render_suggestions(suggestions)
    web_result = web_adapter.render_suggestions(suggestions)

    # Different formats
    assert isinstance(telegram_result, dict)  # Keyboard dict
    assert isinstance(web_result, list)  # Quick prompts list

    # Both valid
    assert telegram_result is not None
    assert len(web_result) == 3
