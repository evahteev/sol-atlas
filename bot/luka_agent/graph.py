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


def hydrate_state_with_sub_agent(state: AgentState) -> dict:
    """
    Hydrate state with sub-agent configuration.

    This function loads the sub-agent config and populates state fields.
    Called at the start of graph execution or when switching agents.

    Args:
        state: Current agent state with sub_agent_id

    Returns:
        State updates (dict) to merge into state

    Example:
        >>> state = {"sub_agent_id": "general_luka", "user_id": 123, ...}
        >>> updates = hydrate_state_with_sub_agent(state)
        >>> state.update(updates)
    """
    from luka_agent.sub_agents.loader import get_sub_agent_loader

    sub_agent_id = state.get("sub_agent_id", "general_luka")

    logger.info(f"🔄 Hydrating state with sub-agent: {sub_agent_id}")

    try:
        # Load sub-agent config
        loader = get_sub_agent_loader()
        config = loader.load(sub_agent_id)

        # Resolve knowledge bases with template substitution
        knowledge_bases = []
        for kb_pattern in config.knowledge_bases:
            # Substitute template variables
            kb = kb_pattern.replace("{user_id}", str(state["user_id"]))
            knowledge_bases.append(kb)

        # Load system prompt with template variables
        template_vars = {
            "user_name": state.get("user_name", f"User{state['user_id']}"),
            "platform": state.get("platform", "unknown"),
            "language": state.get("language", "en"),
        }

        system_prompt_content = loader.load_system_prompt(
            config,
            language=state.get("language", "en"),
            template_vars=template_vars,
        )

        # Load LLM config from environment variables (not from sub-agent config)
        import os
        llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "ollama")
        llm_model = os.getenv("DEFAULT_LLM_MODEL", "llama3.2")
        llm_temperature = float(os.getenv("DEFAULT_LLM_TEMPERATURE", "0.7"))
        llm_max_tokens = int(os.getenv("DEFAULT_LLM_MAX_TOKENS", "2000"))
        llm_streaming = os.getenv("DEFAULT_LLM_STREAMING", "true").lower() == "true"

        # Build state updates
        updates = {
            "sub_agent_id": sub_agent_id,
            "sub_agent_metadata": {
                "id": config.id,
                "name": config.name,
                "icon": config.icon,
                "description": config.description,
                "version": config.version,
            },
            "sub_agent_persona": {
                "role": config.role,
                "identity": config.identity,
                "communication_style": config.communication_style,
                "principles": config.principles,
            },
            "enabled_tools": config.enabled_tools,
            "knowledge_bases": knowledge_bases,
            "system_prompt_content": system_prompt_content,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "llm_temperature": llm_temperature,
            "llm_max_tokens": llm_max_tokens,
            "llm_streaming": llm_streaming,
        }

        logger.info(f"✅ State hydrated with sub-agent: {config.name}")
        logger.debug(f"   Tools: {config.enabled_tools}")
        logger.debug(f"   KBs: {knowledge_bases}")
        logger.debug(f"   LLM: {updates['llm_provider']}/{updates['llm_model']}")

        return updates

    except Exception as e:
        logger.error(f"❌ Failed to hydrate state with sub-agent {sub_agent_id}: {e}")
        # Return minimal fallback state
        return {
            "sub_agent_metadata": {
                "id": sub_agent_id,
                "name": "Luka (Fallback)",
                "icon": "🤖",
                "description": "Fallback agent",
                "version": "1.0.0",
            },
            "sub_agent_persona": {
                "role": "AI Assistant",
                "identity": "You are a helpful AI assistant.",
                "communication_style": "Friendly and helpful",
                "principles": [],
            },
            "enabled_tools": ["knowledge_base"],
            "knowledge_bases": [f"user-kb-{state['user_id']}"],
            "system_prompt_content": "You are a helpful AI assistant.",
            "llm_provider": "ollama",
            "llm_model": "llama3.2",
            "llm_temperature": 0.7,
            "llm_max_tokens": 2000,
            "llm_streaming": True,
        }


async def get_unified_agent_graph(use_memory: bool | None = None):
    """Get or create the singleton agent graph instance.

    This function creates the LangGraph workflow with nodes and edges:

    Flow:
        START → agent → [tools?] → suggestions → END

    The graph uses checkpointing for automatic state persistence.
    By default, uses in-memory checkpointing. Set use_memory=False or
    LUKA_USE_MEMORY_CHECKPOINTER=false env var to use Redis.

    Args:
        use_memory: Optional override for checkpointer type.
                   If True, use MemorySaver. If False, use RedisSaver.
                   If None, use settings (defaults to True/MemorySaver).

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

    # Get checkpointer (pass use_memory parameter)
    checkpointer = await get_checkpointer(use_memory=use_memory)

    # Compile graph with checkpointer
    _graph_instance = workflow.compile(checkpointer=checkpointer)

    logger.info("✅ Unified agent graph built successfully")

    return _graph_instance


__all__ = ["get_unified_agent_graph", "hydrate_state_with_sub_agent"]
