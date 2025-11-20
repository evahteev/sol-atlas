"""
Web/CopilotKit Integration Helper for luka_agent.

This module provides helper functions for integrating luka_agent with
web platforms using FastAPI and CopilotKit's AG-UI protocol.

NOTE: This is a placeholder for future CopilotKit integration.
The actual implementation requires careful handling of CopilotKit's
state synchronization and AG-UI protocol expectations.

See: docs/INTEGRATION_ANALYSIS.md for detailed integration approach.
"""

from typing import AsyncIterator, Dict, Any, List, Optional
from langchain_core.messages import HumanMessage
from loguru import logger

from luka_agent import get_unified_agent_graph
from luka_agent.adapters import WebAdapter
from luka_agent.tools import create_tools_for_user


async def stream_web_response(
    user_message: str,
    user_id: int,
    thread_id: str,
    knowledge_bases: List[str],
    language: str = "en",
    enabled_tools: Optional[List[str]] = None,
    is_guest: bool = False,
) -> AsyncIterator[Dict[str, Any]]:
    """
    Stream LangGraph agent response formatted for Web (AG-UI protocol).

    This function streams events from the luka_agent graph and formats them
    according to the AG-UI protocol for consumption by CopilotKit clients.

    Args:
        user_message: User's text message
        user_id: User ID
        thread_id: Conversation thread ID
        knowledge_bases: List of KB indices to search
        language: User's language code (en, ru, etc.)
        enabled_tools: List of tool names to enable (None = all tools)
        is_guest: Whether user is a guest (unauthenticated)

    Yields:
        AG-UI protocol events:

        Text stream delta:
            {"type": "textStreamDelta", "delta": "..."}

        Tool invocation (started):
            {"type": "toolInvocation", "tool": "knowledge_base", "status": "started"}

        Tool result (completed):
            {"type": "toolResult", "tool": "knowledge_base", "result": "..."}

        State update (suggestions):
            {"type": "stateUpdate", "suggestions": [...]}

    Example:
        >>> async for event in stream_web_response(
        ...     user_message="What is DeFi?",
        ...     user_id=123,
        ...     thread_id="thread_123",
        ...     knowledge_bases=["tg-kb-user-123"],
        ...     language="en"
        ... ):
        ...     if event["type"] == "textStreamDelta":
        ...         print(event["delta"], end="", flush=True)
        ...     elif event["type"] == "stateUpdate":
        ...         print(f"\\nSuggestions: {event['suggestions']}")

    NOTE: This is a basic implementation. For full CopilotKit compatibility,
    you may need to use CopilotKit's native LangGraph integration instead.
    See: ag_ui_gateway/adapters/ for CopilotKit-specific adapters.
    """
    # Get graph and adapter
    graph = await get_unified_agent_graph()
    adapter = WebAdapter()

    # Create tools for user
    if enabled_tools is None:
        enabled_tools = ["knowledge_base", "sub_agent", "youtube"]

    tools = create_tools_for_user(
        user_id=user_id,
        thread_id=thread_id,
        knowledge_bases=knowledge_bases,
        enabled_tools=enabled_tools,
        platform="web",
        language=language,
    )

    # Create initial state
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "user_id": user_id,
        "thread_id": thread_id,
        "knowledge_bases": knowledge_bases,
        "language": language,
        "platform": "web",
        "is_guest": is_guest,
        "conversation_suggestions": [],
    }

    config = {"configurable": {"thread_id": thread_id}}

    logger.debug(
        f"🎬 Starting Web stream for user {user_id}, thread {thread_id}, "
        f"enabled_tools={enabled_tools}, is_guest={is_guest}"
    )

    # Stream events from graph
    try:
        async for event in graph.astream_events(initial_state, config=config, version="v2"):
            event_type = event.get("event")

            # LLM streaming chunks
            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content"):
                    content = chunk.content
                    if content:
                        # Format as AG-UI streaming chunk
                        formatted = adapter.format_streaming_chunk(content)
                        yield formatted

            # Tool started
            elif event_type == "on_tool_start":
                tool_name = event.get("name", "")
                if tool_name:
                    yield {
                        "type": "toolInvocation",
                        "tool": tool_name,
                        "status": "started",
                        "message": adapter.format_tool_notification(tool_name, "started"),
                    }
                    logger.debug(f"🔧 Tool started: {tool_name}")

            # Tool completed
            elif event_type == "on_tool_end":
                tool_name = event.get("name", "")
                if tool_name:
                    result = event.get("data", {}).get("output", "")
                    yield {
                        "type": "toolResult",
                        "tool": tool_name,
                        "result": str(result),
                        "message": adapter.format_tool_notification(tool_name, "completed"),
                    }
                    logger.debug(f"✅ Tool completed: {tool_name}")

            # Tool failed
            elif event_type == "on_tool_error":
                tool_name = event.get("name", "")
                error = event.get("data", {}).get("error", "Unknown error")
                if tool_name:
                    yield {
                        "type": "toolResult",
                        "tool": tool_name,
                        "error": str(error),
                        "message": adapter.format_tool_notification(tool_name, "error"),
                    }
                    logger.warning(f"❌ Tool failed: {tool_name}")

    except Exception as e:
        logger.error(f"❌ Error streaming Web response: {e}", exc_info=True)
        raise

    # Get final state for suggestions
    try:
        final_state = await graph.aget_state(config)
        suggestions = final_state.values.get("conversation_suggestions", [])

        if suggestions:
            logger.debug(f"💡 Generated {len(suggestions)} suggestions")
            # Render as AG-UI quick prompts
            quick_prompts = adapter.render_suggestions(suggestions)
            if quick_prompts:
                yield {
                    "type": "stateUpdate",
                    "suggestions": quick_prompts,
                }
        else:
            logger.debug("💡 No suggestions generated")

    except Exception as e:
        logger.warning(f"⚠️ Could not get final state for suggestions: {e}")
        # Don't fail - just skip suggestions


async def invoke_web_response(
    user_message: str,
    user_id: int,
    thread_id: str,
    knowledge_bases: List[str],
    language: str = "en",
    enabled_tools: Optional[List[str]] = None,
    is_guest: bool = False,
) -> Dict[str, Any]:
    """
    Invoke agent and get complete response (non-streaming).

    Args:
        user_message: User's text message
        user_id: User ID
        thread_id: Conversation thread ID
        knowledge_bases: List of KB indices to search
        language: User's language code (en, ru, etc.)
        enabled_tools: List of tool names to enable (None = all tools)
        is_guest: Whether user is a guest (unauthenticated)

    Returns:
        {
            "message": "Full AI response text",
            "suggestions": [
                {"title": "...", "message": "..."},
                ...
            ],
            "metadata": {...}
        }

    Example:
        >>> result = await invoke_web_response(
        ...     user_message="What is DeFi?",
        ...     user_id=123,
        ...     thread_id="thread_123",
        ...     knowledge_bases=["tg-kb-user-123"],
        ...     language="en"
        ... )
        >>> print(result["message"])
        >>> print(result["suggestions"])
    """
    # Collect all chunks
    full_response = ""
    suggestions = []
    metadata = {}

    async for event in stream_web_response(
        user_message=user_message,
        user_id=user_id,
        thread_id=thread_id,
        knowledge_bases=knowledge_bases,
        language=language,
        enabled_tools=enabled_tools,
        is_guest=is_guest,
    ):
        if event.get("type") == "textStreamDelta":
            full_response += event["delta"]
        elif event.get("type") == "stateUpdate":
            suggestions = event.get("suggestions", [])

    adapter = WebAdapter()
    return adapter.format_ag_ui_response(
        message=full_response,
        suggestions=None if not suggestions else [s["title"] for s in suggestions],
        metadata=metadata,
    )


__all__ = [
    "stream_web_response",
    "invoke_web_response",
]
