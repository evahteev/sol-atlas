"""
Unified tool factory for luka_agent.

This module provides a single entry point for creating tools for both
Telegram and Web platforms. All tools are LangChain StructuredTools.
"""

from typing import List
from langchain_core.tools import BaseTool
from loguru import logger

from luka_agent.tools.knowledge_base import create_knowledge_base_tool
from luka_agent.tools.sub_agent import create_sub_agent_tools
from luka_agent.tools.youtube import create_youtube_tool
from luka_agent.tools.image_description import create_image_description_tool


def create_tools_for_user(
    user_id: int,
    thread_id: str,
    knowledge_bases: List[str],
    enabled_tools: List[str],
    platform: str = "telegram",
    language: str = "en",
) -> List[BaseTool]:
    """Create all enabled tools for a user.

    This is the main entry point for creating tools. It returns a list of
    LangChain tools based on the user's configuration.

    Args:
        user_id: User ID for context
        thread_id: Thread ID for workflows and context
        knowledge_bases: List of KB indices user can access
        enabled_tools: List of tool names to enable (e.g., ["knowledge_base", "workflow"])
        platform: Platform identifier ("web" or "telegram")
        language: User's preferred language (default: "en")

    Returns:
        List of LangChain BaseTool instances

    Example:
        >>> tools = create_tools_for_user(
        ...     user_id=123,
        ...     thread_id="user_123",
        ...     knowledge_bases=["tg-kb-user-123"],
        ...     enabled_tools=["knowledge_base", "workflow", "youtube"],
        ...     platform="telegram",
        ...     language="en"
        ... )
        >>> # Use in LangGraph agent
        >>> llm_with_tools = llm.bind_tools(tools)
    """
    tools = []

    # Map of tool names to factory functions
    tool_factories = {
        "knowledge_base": lambda: create_knowledge_base_tool(
            user_id, thread_id, language, knowledge_bases
        ),
        "sub_agent": lambda: create_sub_agent_tools(user_id, thread_id, language),  # Returns list of 5 tools
        "youtube": lambda: create_youtube_tool(user_id, thread_id, language),
        "image_description": lambda: create_image_description_tool(user_id, thread_id, language),
        # Additional tools will be added as they are migrated
    }

    # Create tools based on enabled list
    for tool_name in enabled_tools:
        if tool_name in tool_factories:
            try:
                result = tool_factories[tool_name]()
                # workflow_context returns a list of tools, others return single tool
                if isinstance(result, list):
                    tools.extend(result)
                    logger.debug(f"Created {len(result)} tools for: {tool_name}")
                else:
                    tools.append(result)
                    logger.debug(f"Created tool: {tool_name} for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to create tool {tool_name}: {e}")
        else:
            logger.warning(f"Unknown tool name: {tool_name} (not yet migrated to luka_agent)")

    logger.info(f"Created {len(tools)} tools for user {user_id} on {platform}: {enabled_tools}")
    return tools


__all__ = ["create_tools_for_user"]
