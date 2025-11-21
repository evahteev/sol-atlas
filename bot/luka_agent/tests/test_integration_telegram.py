"""
Tests for luka_agent Telegram integration helpers.

Tests validate that integration helpers in luka_agent/integration/telegram.py
correctly stream responses from the unified agent graph and format them
for Telegram bot consumption.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from luka_agent.integration.telegram import (
    stream_telegram_response,
    invoke_telegram_response,
    create_telegram_keyboard_from_suggestions,
)


class TestStreamTelegramResponse:
    """Test stream_telegram_response function."""

    @pytest.mark.asyncio
    async def test_streams_text_chunks(self):
        """Test that text chunks are streamed correctly."""
        # Mock the graph to emit text streaming events
        mock_graph = AsyncMock()

        async def mock_stream_events(*args, **kwargs):
            # Simulate LLM streaming events
            yield {
                "event": "on_chat_model_stream",
                "data": {
                    "chunk": Mock(content="Hello ")
                }
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {
                    "chunk": Mock(content="world!")
                }
            }

        mock_graph.astream_events = mock_stream_events

        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        async def mock_get_graph():
            return mock_graph

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', side_effect=mock_get_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_telegram_response(
                    user_message="Test message",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Should have text_chunk events
        text_chunks = [e for e in events if e.get("type") == "text_chunk"]
        assert len(text_chunks) == 2
        assert text_chunks[0]["content"] == "Hello "
        assert text_chunks[1]["content"] == "world!"

    @pytest.mark.asyncio
    async def test_streams_tool_notifications(self):
        """Test that tool notifications are emitted."""
        mock_graph = AsyncMock()

        async def mock_stream_events(*args, **kwargs):
            # Simulate tool execution events
            yield {
                "event": "on_tool_start",
                "name": "knowledge_base"
            }
            yield {
                "event": "on_tool_end",
                "name": "knowledge_base",
                "data": {"output": "Search results"}
            }

        mock_graph.astream_events = mock_stream_events
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        # Make get_unified_agent_graph async
        async def mock_get_graph():
            return mock_graph

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', side_effect=mock_get_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_telegram_response(
                    user_message="Search knowledge base",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Should have tool notification events
        tool_events = [e for e in events if e.get("type") == "tool_notification"]
        assert len(tool_events) == 2  # Start and end
        assert "🔍" in tool_events[0]["content"]  # Search emoji
        assert "✅" in tool_events[1]["content"]  # Complete emoji

    @pytest.mark.asyncio
    async def test_yields_suggestions_keyboard(self):
        """Test that suggestions are yielded as keyboard."""
        mock_graph = AsyncMock()

        async def mock_stream_events(*args, **kwargs):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": Mock(content="Response")}
            }

        mock_graph.astream_events = mock_stream_events

        # Mock final state with suggestions
        mock_final_state = Mock(
            values={"conversation_suggestions": ["Option 1", "Option 2", "Option 3"]}
        )
        mock_graph.aget_state = AsyncMock(return_value=mock_final_state)

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_telegram_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Should have suggestions event
        suggestions = [e for e in events if e.get("type") == "suggestions"]
        assert len(suggestions) == 1
        assert "keyboard" in suggestions[0]

        # Keyboard should be aiogram-compatible
        keyboard = suggestions[0]["keyboard"]
        assert isinstance(keyboard, dict)
        assert "keyboard" in keyboard
        assert "resize_keyboard" in keyboard

    @pytest.mark.asyncio
    async def test_handles_empty_chunks(self):
        """Test that empty chunks are handled gracefully."""
        mock_graph = AsyncMock()

        async def mock_stream_events(*args, **kwargs):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": Mock(content="")}  # Empty chunk
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": Mock(content="Hello")}
            }

        mock_graph.astream_events = mock_stream_events
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_telegram_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Should only have non-empty text chunks
        text_chunks = [e for e in events if e.get("type") == "text_chunk"]
        assert len(text_chunks) == 1
        assert text_chunks[0]["content"] == "Hello"

    @pytest.mark.skip(reason="Skipped until integration is complete")
    @pytest.mark.asyncio
    async def test_uses_enabled_tools(self):
        """Test that enabled_tools parameter is respected."""
        mock_graph = AsyncMock()
        mock_graph.astream_events = AsyncMock(return_value=iter([]))
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user') as mock_create_tools:
                mock_create_tools.return_value = []

                async for _ in stream_telegram_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en",
                    enabled_tools=["knowledge_base", "youtube"]
                ):
                    pass

                # Verify create_tools_for_user was called with correct enabled_tools
                mock_create_tools.assert_called_once()
                call_kwargs = mock_create_tools.call_args[1]
                assert call_kwargs["enabled_tools"] == ["knowledge_base", "youtube"]

    @pytest.mark.asyncio
    async def test_handles_tool_errors(self):
        """Test that tool errors are handled gracefully."""
        mock_graph = AsyncMock()

        async def mock_stream_events(*args, **kwargs):
            yield {
                "event": "on_tool_start",
                "name": "knowledge_base"
            }
            yield {
                "event": "on_tool_error",
                "name": "knowledge_base",
                "data": {"error": "Search failed"}
            }

        mock_graph.astream_events = mock_stream_events
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_telegram_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Should have tool notification for failure
        tool_events = [e for e in events if e.get("type") == "tool_notification"]
        assert len(tool_events) == 2  # Start and error
        assert "❌" in tool_events[1]["content"]  # Failure emoji


class TestInvokeTelegramResponse:
    """Test invoke_telegram_response function."""

    @pytest.mark.asyncio
    async def test_returns_complete_response(self):
        """Test that complete response is returned."""
        mock_graph = AsyncMock()

        async def mock_stream_events(*args, **kwargs):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": Mock(content="Hello ")}
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": Mock(content="world!")}
            }

        mock_graph.astream_events = mock_stream_events
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": ["Opt 1", "Opt 2"]}))

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user', return_value=[]):
                result = await invoke_telegram_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                )

        # Should have complete message
        assert "message" in result
        assert result["message"] == "Hello world!"

        # Should have suggestions
        assert "suggestions" in result
        assert len(result["suggestions"]) == 2

        # Should have keyboard
        assert "keyboard" in result
        assert result["keyboard"] is not None

    @pytest.mark.asyncio
    async def test_handles_no_suggestions(self):
        """Test response when no suggestions are generated."""
        mock_graph = AsyncMock()

        async def mock_stream_events(*args, **kwargs):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": Mock(content="Response")}
            }

        mock_graph.astream_events = mock_stream_events
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user', return_value=[]):
                result = await invoke_telegram_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                )

        assert result["suggestions"] == []
        assert result["keyboard"] is None


class TestCreateTelegramKeyboard:
    """Test create_telegram_keyboard_from_suggestions function."""

    def test_creates_keyboard_from_suggestions(self):
        """Test keyboard creation from suggestion strings."""
        suggestions = ["Option 1", "Option 2", "Option 3"]
        keyboard = create_telegram_keyboard_from_suggestions(suggestions)

        assert keyboard is not None
        assert "keyboard" in keyboard
        assert "resize_keyboard" in keyboard
        assert "one_time_keyboard" in keyboard

        # Should have buttons for all suggestions
        buttons = [btn for row in keyboard["keyboard"] for btn in row]
        assert len(buttons) == 3
        assert buttons[0]["text"] == "Option 1"

    def test_handles_empty_suggestions(self):
        """Test that empty suggestions return None."""
        keyboard = create_telegram_keyboard_from_suggestions([])
        assert keyboard is None

    def test_keyboard_aiogram_compatible(self):
        """Test that keyboard format is aiogram-compatible."""
        suggestions = ["Test"]
        keyboard = create_telegram_keyboard_from_suggestions(suggestions)

        # Should have all required fields for aiogram ReplyKeyboardMarkup
        assert isinstance(keyboard["keyboard"], list)
        assert isinstance(keyboard["resize_keyboard"], bool)
        assert isinstance(keyboard["one_time_keyboard"], bool)

        # Buttons should have text field
        button = keyboard["keyboard"][0][0]
        assert "text" in button


class TestTelegramIntegrationParameters:
    """Test parameter validation and handling."""

    @pytest.mark.skip(reason="Skipped until integration is complete")
    @pytest.mark.asyncio
    async def test_requires_user_message(self):
        """Test that user_message is required."""
        mock_graph = AsyncMock()
        mock_graph.astream_events = AsyncMock(return_value=iter([]))
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user', return_value=[]):
                # Should work with empty message (graph will handle validation)
                events = []
                async for event in stream_telegram_response(
                    user_message="",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

    @pytest.mark.skip(reason="Skipped until integration is complete")
    @pytest.mark.asyncio
    async def test_defaults_enabled_tools(self):
        """Test that enabled_tools defaults correctly."""
        mock_graph = AsyncMock()
        mock_graph.astream_events = AsyncMock(return_value=iter([]))
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user') as mock_create_tools:
                mock_create_tools.return_value = []

                async for _ in stream_telegram_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                    # enabled_tools not specified
                ):
                    pass

                # Should default to ["knowledge_base", "sub_agent", "youtube"]
                call_kwargs = mock_create_tools.call_args[1]
                assert "knowledge_base" in call_kwargs["enabled_tools"]
                assert "sub_agent" in call_kwargs["enabled_tools"]
                assert "youtube" in call_kwargs["enabled_tools"]

    @pytest.mark.skip(reason="Skipped until integration is complete")
    @pytest.mark.asyncio
    async def test_passes_language_to_graph(self):
        """Test that language is passed to graph state."""
        mock_graph = AsyncMock()
        mock_graph.astream_events = AsyncMock(return_value=iter([]))
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.telegram.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.telegram.create_tools_for_user', return_value=[]):
                async for _ in stream_telegram_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="ru"  # Russian
                ):
                    pass

                # Check initial state passed to graph
                call_args = mock_graph.astream_events.call_args
                initial_state = call_args[0][0]
                assert initial_state["language"] == "ru"
