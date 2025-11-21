"""
Telegram Integration Helper for luka_agent.

This module provides helper functions for integrating luka_agent with
Telegram bots using aiogram. It handles streaming responses, tool notifications,
and keyboard rendering.
"""

from typing import AsyncIterator, Dict, Any, List, Optional
from langchain_core.messages import HumanMessage
from loguru import logger

from luka_agent import get_unified_agent_graph
from luka_agent.adapters import TelegramAdapter
from luka_agent.tools import create_tools_for_user


async def stream_telegram_response(
    user_message: str,
    user_id: int,
    thread_id: str,
    knowledge_bases: List[str],
    language: str = "en",
    enabled_tools: Optional[List[str]] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """
    Stream LangGraph agent response formatted for Telegram.

    This function streams events from the luka_agent graph and formats them
    for consumption by Telegram bot handlers. It yields dictionaries with
    different event types that the handler can process.

    Args:
        user_message: User's text message
        user_id: Telegram user ID
        thread_id: Conversation thread ID
        knowledge_bases: List of KB indices to search
        language: User's language code (en, ru, etc.)
        enabled_tools: List of tool names to enable (None = all tools)

    Yields:
        Event dictionaries with the following types:

        Text chunk:
            {"type": "text_chunk", "content": "..."}

        Tool notification (started):
            {"type": "tool_notification", "content": "🔍 Searching knowledge base..."}

        Tool notification (completed):
            {"type": "tool_notification", "content": "✅ Knowledge base search complete"}

        Suggestions (final):
            {"type": "suggestions", "keyboard": {...}}
            The keyboard dict is compatible with aiogram's ReplyKeyboardMarkup

    Example:
        >>> async for event in stream_telegram_response(
        ...     user_message="What is DeFi?",
        ...     user_id=123,
        ...     thread_id="thread_123",
        ...     knowledge_bases=["tg-kb-user-123"],
        ...     language="en"
        ... ):
        ...     if event["type"] == "text_chunk":
        ...         print(event["content"], end="", flush=True)
        ...     elif event["type"] == "tool_notification":
        ...         print(f"\\n{event['content']}")
        ...     elif event["type"] == "suggestions":
        ...         print(f"\\nKeyboard: {event['keyboard']}")

    Integration with aiogram:
        >>> from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        >>>
        >>> # In your message handler:
        >>> full_response = ""
        >>> keyboard = None
        >>>
        >>> async for event in stream_telegram_response(...):
        ...     if event["type"] == "text_chunk":
        ...         full_response += event["content"]
        ...     elif event["type"] == "suggestions":
        ...         keyboard_dict = event["keyboard"]
        ...         keyboard = ReplyKeyboardMarkup(
        ...             keyboard=[[KeyboardButton(text=btn["text"]) for btn in row]
        ...                      for row in keyboard_dict["keyboard"]],
        ...             resize_keyboard=keyboard_dict["resize_keyboard"],
        ...             one_time_keyboard=keyboard_dict["one_time_keyboard"],
        ...         )
        >>>
        >>> await message.answer(full_response, reply_markup=keyboard)
    """
    # Get graph and adapter
    graph = await get_unified_agent_graph()
    adapter = TelegramAdapter()

    # Create tools for user
    if enabled_tools is None:
        enabled_tools = ["knowledge_base", "sub_agent", "youtube"]

    tools = create_tools_for_user(
        user_id=user_id,
        thread_id=thread_id,
        knowledge_bases=knowledge_bases,
        enabled_tools=enabled_tools,
        platform="telegram",
        language=language,
    )

    # Create initial state
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "user_id": user_id,
        "thread_id": thread_id,
        "knowledge_bases": knowledge_bases,
        "language": language,
        "platform": "telegram",
        "conversation_suggestions": [],
    }

    config = {"configurable": {"thread_id": thread_id}}

    logger.debug(
        f"🎬 Starting Telegram stream for user {user_id}, thread {thread_id}, "
        f"enabled_tools={enabled_tools}"
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
                        yield {"type": "text_chunk", "content": content}

            # Tool started
            elif event_type == "on_tool_start":
                tool_name = event.get("name", "")
                if tool_name:
                    notification = adapter.format_tool_notification(tool_name, "started")
                    yield {"type": "tool_notification", "content": notification}
                    logger.debug(f"🔧 Tool started: {tool_name}")

            # Tool completed
            elif event_type == "on_tool_end":
                tool_name = event.get("name", "")
                if tool_name:
                    notification = adapter.format_tool_notification(tool_name, "completed")
                    yield {"type": "tool_notification", "content": notification}
                    logger.debug(f"✅ Tool completed: {tool_name}")

            # Tool failed
            elif event_type == "on_tool_error":
                tool_name = event.get("name", "")
                if tool_name:
                    notification = adapter.format_tool_notification(tool_name, "error")
                    yield {"type": "tool_notification", "content": notification}
                    logger.warning(f"❌ Tool failed: {tool_name}")

    except Exception as e:
        logger.error(f"❌ Error streaming Telegram response: {e}", exc_info=True)
        raise

    # Get final state for suggestions
    try:
        final_state = await graph.aget_state(config)
        suggestions = final_state.values.get("conversation_suggestions", [])

        if suggestions:
            logger.debug(f"💡 Generated {len(suggestions)} suggestions")
            # Render as Telegram keyboard
            keyboard = adapter.render_suggestions(suggestions)
            if keyboard:
                yield {"type": "suggestions", "keyboard": keyboard}
        else:
            logger.debug("💡 No suggestions generated")

    except Exception as e:
        logger.warning(f"⚠️ Could not get final state for suggestions: {e}")
        # Don't fail - just skip suggestions


async def invoke_telegram_response(
    user_message: str,
    user_id: int,
    thread_id: str,
    knowledge_bases: List[str],
    language: str = "en",
    enabled_tools: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Invoke agent and get complete response (non-streaming).

    This is a convenience function for non-streaming responses. Use
    `stream_telegram_response` for better UX with typing indicators.

    Args:
        user_message: User's text message
        user_id: Telegram user ID
        thread_id: Conversation thread ID
        knowledge_bases: List of KB indices to search
        language: User's language code (en, ru, etc.)
        enabled_tools: List of tool names to enable (None = all tools)

    Returns:
        {
            "message": "Full AI response text",
            "suggestions": ["Suggestion 1", "Suggestion 2", ...],
            "keyboard": {...}  # aiogram-compatible keyboard dict
        }

    Example:
        >>> result = await invoke_telegram_response(
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
    keyboard = None

    async for event in stream_telegram_response(
        user_message=user_message,
        user_id=user_id,
        thread_id=thread_id,
        knowledge_bases=knowledge_bases,
        language=language,
        enabled_tools=enabled_tools,
    ):
        if event["type"] == "text_chunk":
            full_response += event["content"]
        elif event["type"] == "suggestions":
            keyboard = event["keyboard"]

    # Extract suggestions from keyboard
    suggestions = []
    if keyboard and "keyboard" in keyboard:
        for row in keyboard["keyboard"]:
            for button in row:
                suggestions.append(button["text"])

    return {
        "message": full_response,
        "suggestions": suggestions,
        "keyboard": keyboard,
    }


def create_telegram_keyboard_from_suggestions(
    suggestions: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Create Telegram keyboard dict from suggestion strings.

    This is a convenience function for creating keyboards outside
    of the streaming context.

    Args:
        suggestions: List of suggestion strings

    Returns:
        Keyboard dict compatible with aiogram's ReplyKeyboardMarkup,
        or None if suggestions is empty

    Example:
        >>> suggestions = ["Option 1", "Option 2", "Option 3"]
        >>> keyboard_dict = create_telegram_keyboard_from_suggestions(suggestions)
        >>>
        >>> from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        >>> keyboard = ReplyKeyboardMarkup(
        ...     keyboard=[[KeyboardButton(text=btn["text"]) for btn in row]
        ...              for row in keyboard_dict["keyboard"]],
        ...     resize_keyboard=keyboard_dict["resize_keyboard"],
        ...     one_time_keyboard=keyboard_dict["one_time_keyboard"],
        ... )
    """
    if not suggestions:
        return None

    adapter = TelegramAdapter()
    return adapter.render_suggestions(suggestions)


__all__ = [
    "stream_telegram_response",
    "invoke_telegram_response",
    "create_telegram_keyboard_from_suggestions",
]
