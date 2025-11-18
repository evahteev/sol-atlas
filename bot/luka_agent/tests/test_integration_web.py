"""
Tests for luka_agent Web/AG-UI integration helpers.

Tests validate that integration helpers in luka_agent/integration/web.py
correctly stream responses from the unified agent graph and format them
for Web/CopilotKit consumption using the AG-UI protocol.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from langchain_core.messages import HumanMessage, AIMessage

from luka_agent.integration.web import (
    stream_web_response,
    invoke_web_response,
)


class TestStreamWebResponse:
    """Test stream_web_response function."""

    @pytest.mark.asyncio
    async def test_streams_text_deltas(self):
        """Test that text chunks are streamed as AG-UI deltas."""
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

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_web_response(
                    user_message="Test message",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Should have textStreamDelta events
        text_deltas = [e for e in events if e.get("type") == "textStreamDelta"]
        assert len(text_deltas) == 2
        assert text_deltas[0]["delta"] == "Hello "
        assert text_deltas[1]["delta"] == "world!"

    @pytest.mark.asyncio
    async def test_emits_tool_invocation_events(self):
        """Test that tool executions emit AG-UI toolInvocation events."""
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

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_web_response(
                    user_message="Search knowledge base",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Should have toolInvocation and toolResult events
        tool_invocations = [e for e in events if e.get("type") == "toolInvocation"]
        tool_results = [e for e in events if e.get("type") == "toolResult"]

        assert len(tool_invocations) == 1
        assert tool_invocations[0]["tool"] == "knowledge_base"
        assert tool_invocations[0]["status"] == "started"

        assert len(tool_results) == 1
        assert tool_results[0]["tool"] == "knowledge_base"

    @pytest.mark.asyncio
    async def test_yields_suggestions_as_state_update(self):
        """Test that suggestions are yielded as AG-UI stateUpdate."""
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

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_web_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Should have stateUpdate event with suggestions
        state_updates = [e for e in events if e.get("type") == "stateUpdate"]
        assert len(state_updates) == 1
        assert "suggestions" in state_updates[0]

        # Suggestions should be AG-UI quick prompts
        suggestions = state_updates[0]["suggestions"]
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    @pytest.mark.asyncio
    async def test_handles_guest_users(self):
        """Test that guest users are handled correctly."""
        mock_graph = AsyncMock()
        mock_graph.astream_events = AsyncMock(return_value=iter([]))
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user') as mock_create_tools:
                mock_create_tools.return_value = []

                async for _ in stream_web_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["luka-public-kb"],  # Public KB
                    language="en",
                    is_guest=True
                ):
                    pass

                # Verify create_tools_for_user was called with is_guest context
                call_args = mock_graph.astream_events.call_args
                initial_state = call_args[0][0]
                assert initial_state.get("is_guest") is True

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

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_web_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Should only have non-empty text deltas
        text_deltas = [e for e in events if e.get("type") == "textStreamDelta"]
        assert len(text_deltas) == 1
        assert text_deltas[0]["delta"] == "Hello"

    @pytest.mark.asyncio
    async def test_uses_enabled_tools(self):
        """Test that enabled_tools parameter is respected."""
        mock_graph = AsyncMock()
        mock_graph.astream_events = AsyncMock(return_value=iter([]))
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user') as mock_create_tools:
                mock_create_tools.return_value = []

                async for _ in stream_web_response(
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
        """Test that tool errors emit proper AG-UI events."""
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

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_web_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Should have tool invocation and error result
        tool_invocations = [e for e in events if e.get("type") == "toolInvocation"]
        tool_results = [e for e in events if e.get("type") == "toolResult"]

        assert len(tool_invocations) == 1
        assert len(tool_results) == 1
        assert "error" in tool_results[0]


class TestInvokeWebResponse:
    """Test invoke_web_response function."""

    @pytest.mark.asyncio
    async def test_returns_complete_response(self):
        """Test that complete AG-UI response is returned."""
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
        mock_graph.aget_state = AsyncMock(
            return_value=Mock(values={"conversation_suggestions": ["Opt 1", "Opt 2"]})
        )

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                result = await invoke_web_response(
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

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                result = await invoke_web_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                )

        assert result["suggestions"] is None or len(result["suggestions"]) == 0

    @pytest.mark.asyncio
    async def test_accumulates_all_text_chunks(self):
        """Test that all text chunks are accumulated."""
        mock_graph = AsyncMock()

        async def mock_stream_events(*args, **kwargs):
            for word in ["One ", "Two ", "Three"]:
                yield {
                    "event": "on_chat_model_stream",
                    "data": {"chunk": Mock(content=word)}
                }

        mock_graph.astream_events = mock_stream_events
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                result = await invoke_web_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                )

        assert result["message"] == "One Two Three"


class TestWebIntegrationAGUIProtocol:
    """Test AG-UI protocol compatibility."""

    @pytest.mark.asyncio
    async def test_text_deltas_have_required_fields(self):
        """Test that textStreamDelta events have required AG-UI fields."""
        mock_graph = AsyncMock()

        async def mock_stream_events(*args, **kwargs):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": Mock(content="Test")}
            }

        mock_graph.astream_events = mock_stream_events

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_web_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        text_delta = events[0]
        assert text_delta["type"] == "textStreamDelta"
        assert "delta" in text_delta
        assert isinstance(text_delta["delta"], str)

    @pytest.mark.asyncio
    async def test_tool_events_have_required_fields(self):
        """Test that tool events have required AG-UI fields."""
        mock_graph = AsyncMock()

        async def mock_stream_events(*args, **kwargs):
            yield {
                "event": "on_tool_start",
                "name": "knowledge_base"
            }
            yield {
                "event": "on_tool_end",
                "name": "knowledge_base",
                "data": {"output": "Results"}
            }

        mock_graph.astream_events = mock_stream_events
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                events = []
                async for event in stream_web_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    events.append(event)

        # Tool invocation event
        tool_inv = [e for e in events if e.get("type") == "toolInvocation"][0]
        assert "tool" in tool_inv
        assert "status" in tool_inv

        # Tool result event
        tool_res = [e for e in events if e.get("type") == "toolResult"][0]
        assert "tool" in tool_res
        assert "result" in tool_res or "error" in tool_res


class TestWebIntegrationParameters:
    """Test parameter validation and handling."""

    @pytest.mark.asyncio
    async def test_defaults_enabled_tools(self):
        """Test that enabled_tools defaults correctly."""
        mock_graph = AsyncMock()
        mock_graph.astream_events = AsyncMock(return_value=iter([]))
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user') as mock_create_tools:
                mock_create_tools.return_value = []

                async for _ in stream_web_response(
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

    @pytest.mark.asyncio
    async def test_passes_platform_as_web(self):
        """Test that platform is set to 'web'."""
        mock_graph = AsyncMock()
        mock_graph.astream_events = AsyncMock(return_value=iter([]))
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                async for _ in stream_web_response(
                    user_message="Test",
                    user_id=123,
                    thread_id="test_thread",
                    knowledge_bases=["kb-123"],
                    language="en"
                ):
                    pass

                # Check initial state passed to graph
                call_args = mock_graph.astream_events.call_args
                initial_state = call_args[0][0]
                assert initial_state["platform"] == "web"

    @pytest.mark.asyncio
    async def test_passes_language_to_graph(self):
        """Test that language is passed to graph state."""
        mock_graph = AsyncMock()
        mock_graph.astream_events = AsyncMock(return_value=iter([]))
        mock_graph.aget_state = AsyncMock(return_value=Mock(values={"conversation_suggestions": []}))

        with patch('luka_agent.integration.web.get_unified_agent_graph', return_value=mock_graph):
            with patch('luka_agent.integration.web.create_tools_for_user', return_value=[]):
                async for _ in stream_web_response(
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
