"""
Unified LangGraph graph builder for luka_agent.

This module provides the graph construction logic that is shared
between Telegram and Web platforms.
"""

from typing import Optional
from langgraph.graph import StateGraph, END
from loguru import logger

from luka_agent.state import AgentState
from luka_agent.nodes import agent_node, tools_node, suggestions_node, should_continue
from luka_agent.checkpointer import get_checkpointer

# Global graph instance (singleton)
_graph_instance: Optional[object] = None


async def get_unified_agent_graph():
    """Get or create the singleton agent graph instance.

    This function creates the LangGraph workflow with nodes and edges:

    Flow:
        START → agent → [tools?] → suggestions → END

    The graph uses Redis checkpointing for automatic state persistence.

    Returns:
        Compiled LangGraph graph ready for execution

    Example:
        >>> graph = await get_unified_agent_graph()
        >>> config = {"configurable": {"thread_id": "user_123"}}
        >>> result = await graph.ainvoke(initial_state, config=config)
    """
    global _graph_instance

    if _graph_instance is not None:
        return _graph_instance

    logger.info("🔨 Building unified agent graph...")

    # Create state graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("suggestions", suggestions_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional routing from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "suggestions": "suggestions",
        },
    )

    # After tools, go back to agent for final response
    workflow.add_edge("tools", "agent")

    # After suggestions, end
    workflow.add_edge("suggestions", END)

    # Get checkpointer
    checkpointer = await get_checkpointer()

    # Compile graph with checkpointer
    _graph_instance = workflow.compile(checkpointer=checkpointer)

    logger.info("✅ Unified agent graph built successfully")

    return _graph_instance


__all__ = ["get_unified_agent_graph"]
