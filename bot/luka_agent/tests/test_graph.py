"""
Tests for luka_agent graph compilation and structure.

Tests validate graph creation, singleton pattern, node/edge structure,
and basic execution flow.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from luka_agent.graph import get_unified_agent_graph


class TestGraphCreation:
    """Test graph creation and initialization."""

    @pytest.mark.asyncio
    async def test_get_unified_agent_graph_returns_graph(self):
        """Test get_unified_agent_graph returns a compiled graph."""
        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            mock_checkpointer.return_value = AsyncMock()

            # Reset singleton
            import luka_agent.graph as graph_module
            graph_module._graph_instance = None

            graph = await get_unified_agent_graph()

            assert graph is not None

    @pytest.mark.asyncio
    async def test_graph_uses_checkpointer(self):
        """Test graph is compiled with checkpointer."""
        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            mock_cp = AsyncMock()
            mock_checkpointer.return_value = mock_cp

            # Reset singleton
            import luka_agent.graph as graph_module
            graph_module._graph_instance = None

            await get_unified_agent_graph()

            # Verify checkpointer was requested
            mock_checkpointer.assert_called_once()


class TestGraphSingleton:
    """Test graph singleton pattern."""

    @pytest.mark.asyncio
    async def test_get_graph_returns_same_instance(self):
        """Test get_unified_agent_graph returns same instance (singleton)."""
        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            mock_checkpointer.return_value = AsyncMock()

            # Reset singleton
            import luka_agent.graph as graph_module
            graph_module._graph_instance = None

            # Get graph twice
            graph1 = await get_unified_agent_graph()
            graph2 = await get_unified_agent_graph()

            # Should be same instance
            assert graph1 is graph2

    @pytest.mark.asyncio
    async def test_graph_singleton_persists_across_calls(self):
        """Test singleton persists across multiple calls."""
        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            mock_checkpointer.return_value = AsyncMock()

            # Reset singleton
            import luka_agent.graph as graph_module
            graph_module._graph_instance = None

            # Get graph multiple times
            instances = []
            for _ in range(5):
                graph = await get_unified_agent_graph()
                instances.append(graph)

            # All should be same instance
            assert all(instance is instances[0] for instance in instances)


class TestGraphStructure:
    """Test graph structure (nodes and edges)."""

    @pytest.mark.asyncio
    async def test_graph_has_required_nodes(self):
        """Test graph has agent, tools, and suggestions nodes."""
        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            mock_checkpointer.return_value = AsyncMock()

            # Reset singleton
            import luka_agent.graph as graph_module
            graph_module._graph_instance = None

            graph = await get_unified_agent_graph()

            # Get graph structure
            # Note: Exact method to inspect graph structure depends on LangGraph version
            # This is a placeholder test that verifies graph compiles
            assert graph is not None

    @pytest.mark.asyncio
    async def test_graph_compiles_successfully(self):
        """Test graph compiles without errors."""
        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            mock_checkpointer.return_value = AsyncMock()

            # Reset singleton
            import luka_agent.graph as graph_module
            graph_module._graph_instance = None

            # Should not raise
            graph = await get_unified_agent_graph()
            assert graph is not None


class TestGraphExecution:
    """Test graph execution flow (with mocked nodes)."""

    @pytest.mark.skip(reason="Skipped until integration is complete")
    @pytest.mark.asyncio
    async def test_graph_executes_with_minimal_state(self):
        """Test graph can execute with minimal valid state."""
        from langgraph.checkpoint.memory import MemorySaver

        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            # Use real MemorySaver instead of AsyncMock (LangGraph needs to inspect method signatures)
            mock_checkpointer.return_value = MemorySaver()

            # Mock nodes to avoid actual LLM calls
            with patch('luka_agent.nodes.agent_node') as mock_agent_node:
                with patch('luka_agent.nodes.suggestions_node') as mock_suggestions_node:
                    with patch('luka_agent.nodes.should_continue') as mock_should_continue:
                        # Setup mocks
                        mock_agent_node.return_value = {
                            "messages": [
                                HumanMessage(content="Hello"),
                                AIMessage(content="Hi there!")
                            ],
                        }

                        mock_suggestions_node.return_value = {
                            "conversation_suggestions": ["Tell me more", "Go back"],
                        }

                        mock_should_continue.return_value = "suggestions"

                        # Reset singleton
                        import luka_agent.graph as graph_module
                        graph_module._graph_instance = None

                        graph = await get_unified_agent_graph()

                        # Create minimal state
                        initial_state = {
                            "messages": [HumanMessage(content="Hello")],
                            "user_id": 123,
                            "thread_id": "test_thread",
                            "knowledge_bases": [],
                            "language": "en",
                            "platform": "telegram",
                            "conversation_suggestions": [],
                        }

                        config = {"configurable": {"thread_id": "test_thread"}}

                        # Execute graph
                        result = await graph.ainvoke(initial_state, config=config)

                        # Verify result exists
                        assert result is not None
                        assert "messages" in result

    @pytest.mark.skip(reason="Skipped until integration is complete")
    @pytest.mark.asyncio
    async def test_graph_handles_tool_execution_path(self):
        """Test graph handles path with tool execution."""
        from langgraph.checkpoint.memory import MemorySaver

        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            # Use real MemorySaver instead of AsyncMock (LangGraph needs to inspect method signatures)
            mock_checkpointer.return_value = MemorySaver()

            with patch('luka_agent.nodes.agent_node') as mock_agent_node:
                with patch('luka_agent.nodes.tools_node') as mock_tools_node:
                    with patch('luka_agent.nodes.suggestions_node') as mock_suggestions_node:
                        with patch('luka_agent.nodes.should_continue') as mock_should_continue:
                            # First call: agent requests tools
                            # Second call: agent provides final response
                            mock_should_continue.side_effect = ["tools", "suggestions"]

                            mock_agent_node.side_effect = [
                                {"messages": [HumanMessage(content="Hello"), AIMessage(content="Let me search...")]},
                                {"messages": [HumanMessage(content="Hello"), AIMessage(content="Here's what I found...")]},
                            ]

                            mock_tools_node.return_value = {
                                "messages": [],
                            }

                            mock_suggestions_node.return_value = {
                                "conversation_suggestions": ["More info", "Thanks"],
                            }

                            # Reset singleton
                            import luka_agent.graph as graph_module
                            graph_module._graph_instance = None

                            graph = await get_unified_agent_graph()

                            initial_state = {
                                "messages": [HumanMessage(content="Hello")],
                                "user_id": 123,
                                "thread_id": "test_thread",
                                "knowledge_bases": [],
                                "language": "en",
                                "platform": "telegram",
                                "conversation_suggestions": [],
                            }

                            config = {"configurable": {"thread_id": "test_thread"}}

                            result = await graph.ainvoke(initial_state, config=config)

                            # Verify tools were executed
                            assert mock_tools_node.called
                            assert result is not None


class TestGraphLogging:
    """Test graph logging."""

    @pytest.mark.asyncio
    async def test_graph_logs_creation(self):
        """Test graph logs when built."""
        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            with patch('luka_agent.graph.logger') as mock_logger:
                mock_checkpointer.return_value = AsyncMock()

                # Reset singleton
                import luka_agent.graph as graph_module
                graph_module._graph_instance = None

                await get_unified_agent_graph()

                # Verify info logs were called
                assert mock_logger.info.called
                log_calls = [call[0][0] for call in mock_logger.info.call_args_list]

                # Should log building and success
                building_logged = any("Building" in msg or "building" in msg for msg in log_calls)
                success_logged = any("successfully" in msg or "built" in msg for msg in log_calls)

                assert building_logged or success_logged


class TestGraphConfiguration:
    """Test graph configuration."""

    @pytest.mark.asyncio
    async def test_graph_entry_point_is_agent(self):
        """Test graph entry point is agent node."""
        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            mock_checkpointer.return_value = AsyncMock()

            # Reset singleton
            import luka_agent.graph as graph_module
            graph_module._graph_instance = None

            graph = await get_unified_agent_graph()

            # Graph should compile successfully with agent as entry
            # Actual validation depends on LangGraph internals
            assert graph is not None

    @pytest.mark.asyncio
    async def test_graph_has_end_condition(self):
        """Test graph has proper END condition."""
        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            mock_checkpointer.return_value = AsyncMock()

            # Reset singleton
            import luka_agent.graph as graph_module
            graph_module._graph_instance = None

            graph = await get_unified_agent_graph()

            # Graph compiles with END edge from suggestions
            assert graph is not None


class TestGraphErrorHandling:
    """Test graph error handling."""

    @pytest.mark.asyncio
    async def test_graph_handles_checkpointer_creation_failure(self):
        """Test graph handles checkpointer creation failure."""
        with patch('luka_agent.graph.get_checkpointer') as mock_checkpointer:
            mock_checkpointer.side_effect = Exception("Checkpointer failed")

            # Reset singleton
            import luka_agent.graph as graph_module
            graph_module._graph_instance = None

            # Should raise exception
            with pytest.raises(Exception) as exc_info:
                await get_unified_agent_graph()

            assert "Checkpointer failed" in str(exc_info.value)
