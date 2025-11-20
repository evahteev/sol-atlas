"""
Tests for sub-agent tools.

Tests the sub-agent tool creation, loading, and execution.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from luka_agent.tools.sub_agent import create_sub_agent_tools


class TestSubAgentToolsCreation:
    """Test sub-agent tools are created correctly."""

    def test_create_sub_agent_tools_returns_list(self):
        """Test that create_sub_agent_tools returns a list of tools."""
        tools = create_sub_agent_tools(
            user_id=123,
            thread_id="test_thread",
            language="en"
        )

        assert isinstance(tools, list)
        assert len(tools) == 5

    def test_all_sub_agent_tools_present(self):
        """Test that all 5 sub-agent tools are created."""
        tools = create_sub_agent_tools(
            user_id=123,
            thread_id="test_thread",
            language="en"
        )

        tool_names = {tool.name for tool in tools}

        expected_names = {
            "get_available_sub_agents",
            "get_sub_agent_details",
            "suggest_sub_agent",
            "get_sub_agent_step_guidance",
            "execute_sub_agent",
        }

        assert tool_names == expected_names

    def test_tools_have_descriptions(self):
        """Test that all tools have non-empty descriptions."""
        tools = create_sub_agent_tools(
            user_id=123,
            thread_id="test_thread",
            language="en"
        )

        for tool in tools:
            assert hasattr(tool, "description")
            assert tool.description
            assert len(tool.description) > 20  # Meaningful description


class TestSubAgentToolExecution:
    """Test sub-agent tool execution logic."""

    @pytest.mark.asyncio
    @patch('luka_agent.services.workflow_context_service.get_workflow_context_service')
    async def test_get_available_sub_agents(self, mock_service_getter):
        """Test get_available_sub_agents returns sub-agent list."""
        # Mock the service
        mock_service = Mock()
        mock_service.get_all_workflows_summary = AsyncMock(
            return_value="Available sub-agents:\n- sol_atlas_onboarding\n- trip_planner_onboarding"
        )
        mock_service_getter.return_value = mock_service

        # Create tools
        tools = create_sub_agent_tools(
            user_id=123,
            thread_id="test_thread",
            language="en"
        )

        # Find get_available_sub_agents tool
        tool = next(t for t in tools if t.name == "get_available_sub_agents")

        # Execute tool
        result = await tool.ainvoke({})

        assert "Available sub-agents" in result
        assert "sol_atlas_onboarding" in result
        mock_service.get_all_workflows_summary.assert_called_once()

    @pytest.mark.asyncio
    @patch('luka_agent.services.workflow_context_service.get_workflow_context_service')
    async def test_get_sub_agent_details(self, mock_service_getter):
        """Test get_sub_agent_details returns documentation."""
        # Mock the service
        mock_service = Mock()
        mock_service.get_workflow_context = AsyncMock(
            return_value="SOL Atlas Onboarding\n\nThis sub-agent helps users..."
        )
        mock_service_getter.return_value = mock_service

        # Create tools
        tools = create_sub_agent_tools(
            user_id=123,
            thread_id="test_thread",
            language="en"
        )

        # Find get_sub_agent_details tool
        tool = next(t for t in tools if t.name == "get_sub_agent_details")

        # Execute tool
        result = await tool.ainvoke({
            "domain": "sol_atlas_onboarding",
            "include_full_documentation": True
        })

        assert "SOL Atlas Onboarding" in result
        mock_service.get_workflow_context.assert_called_once_with(
            "sol_atlas_onboarding", True
        )

    @pytest.mark.asyncio
    @patch('luka_agent.services.workflow_context_service.get_workflow_context_service')
    async def test_suggest_sub_agent(self, mock_service_getter):
        """Test suggest_sub_agent recommends appropriate sub-agent."""
        # Mock the service
        mock_service = Mock()
        mock_service.get_workflow_for_user_intent = AsyncMock(
            return_value="trip_planner_onboarding - Plan trips with AI"
        )
        mock_service_getter.return_value = mock_service

        # Create tools
        tools = create_sub_agent_tools(
            user_id=123,
            thread_id="test_thread",
            language="en"
        )

        # Find suggest_sub_agent tool
        tool = next(t for t in tools if t.name == "suggest_sub_agent")

        # Execute tool
        result = await tool.ainvoke({
            "user_query": "I want to plan a trip from Berlin to Paris"
        })

        assert "trip_planner_onboarding" in result
        mock_service.get_workflow_for_user_intent.assert_called_once()

    @pytest.mark.asyncio
    @patch('luka_agent.services.get_workflow_service')
    @patch('luka_agent.services.get_workflow_discovery_service')
    async def test_execute_sub_agent_starts_new(self, mock_discovery_getter, mock_service_getter):
        """Test execute_sub_agent starts a new sub-agent instance."""
        # Mock discovery service
        mock_discovery = Mock()
        mock_discovery.initialize = AsyncMock()
        mock_workflow_def = Mock()
        mock_workflow_def.name = "SOL Atlas Onboarding"
        mock_workflow_def.tool_chain = {
            "steps": [
                {
                    "id": "step_1",
                    "instruction": "Welcome! What brings you here?"
                }
            ]
        }
        mock_discovery.get_workflow = Mock(return_value=mock_workflow_def)
        mock_discovery_getter.return_value = mock_discovery

        # Mock workflow service
        mock_service = Mock()
        mock_service._initialized = True
        mock_service.get_active_workflow_for_user = AsyncMock(return_value=None)
        mock_service.start_workflow = AsyncMock(return_value="wf_123")
        mock_service_getter.return_value = mock_service

        # Create tools
        tools = create_sub_agent_tools(
            user_id=123,
            thread_id="test_thread",
            language="en"
        )

        # Find execute_sub_agent tool
        tool = next(t for t in tools if t.name == "execute_sub_agent")

        # Execute tool
        result = await tool.ainvoke({
            "domain": "sol_atlas_onboarding"
        })

        assert "SOL Atlas Onboarding" in result
        assert "Welcome" in result
        mock_service.start_workflow.assert_called_once()


class TestSubAgentToolIntegration:
    """Integration tests for sub-agent tools with tool factory."""

    def test_sub_agent_tools_in_factory(self):
        """Test that sub_agent tools are created via factory."""
        from luka_agent.tools import create_tools_for_user

        tools = create_tools_for_user(
            user_id=123,
            thread_id="test_thread",
            knowledge_bases=["tg-kb-user-123"],
            enabled_tools=["sub_agent"],
            platform="telegram",
            language="en"
        )

        # Should create 5 sub-agent tools
        assert len(tools) == 5

        tool_names = {tool.name for tool in tools}
        assert "get_available_sub_agents" in tool_names
        assert "execute_sub_agent" in tool_names

    def test_sub_agent_tools_with_other_tools(self):
        """Test that sub_agent tools work alongside other tools."""
        from luka_agent.tools import create_tools_for_user

        tools = create_tools_for_user(
            user_id=123,
            thread_id="test_thread",
            knowledge_bases=["tg-kb-user-123"],
            enabled_tools=["knowledge_base", "sub_agent", "youtube"],
            platform="telegram",
            language="en"
        )

        # Should create: 1 KB + 5 sub-agent + 1 YouTube = 7 tools
        assert len(tools) == 7

        tool_names = {tool.name for tool in tools}
        assert "search_knowledge_base" in tool_names
        assert "get_available_sub_agents" in tool_names
        assert "execute_sub_agent" in tool_names
        assert "get_youtube_transcript" in tool_names


class TestSubAgentDiscovery:
    """Test that sub-agents can be discovered from luka_agent/sub_agents/."""

    @pytest.mark.asyncio
    @patch('luka_agent.services.workflow_context_service.get_workflow_context_service')
    async def test_sub_agents_directory_discovered(self, mock_service_getter):
        """Test that sub-agents in luka_agent/sub_agents/ are discovered."""
        # Mock service to return our sub-agents
        mock_service = Mock()
        mock_service.get_all_workflows_summary = AsyncMock(
            return_value="""Available sub-agents:

1. sol_atlas_onboarding - Onboard to SOL Atlas community
2. trip_planner_onboarding - Plan trips with AI
3. defi_onboarding - Learn DeFi concepts
"""
        )
        mock_service_getter.return_value = mock_service

        # Create tools
        tools = create_sub_agent_tools(
            user_id=123,
            thread_id="test_thread",
            language="en"
        )

        # Get available sub-agents
        tool = next(t for t in tools if t.name == "get_available_sub_agents")
        result = await tool.ainvoke({})

        # Should include our migrated sub-agents
        assert "sol_atlas_onboarding" in result
        assert "trip_planner_onboarding" in result
        assert "defi_onboarding" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
