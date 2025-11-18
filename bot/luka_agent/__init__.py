"""
Luka Agent - Unified LangGraph Agent Module

This module provides the core agent logic for both Telegram (luka_bot) and Web (ag_ui_gateway) platforms.

Architecture:
- Platform-agnostic agent implementation
- Shared tools (KB, workflow, trip planner, YouTube, etc.)
- Unified state schema with platform field
- Redis-based checkpointing for state persistence
- Integration helpers for Telegram and Web platforms

Usage:

    Option 1: Direct graph usage (advanced)
    ----------------------------------------
    from luka_agent.graph import get_unified_agent_graph
    from luka_agent.tools import create_tools_for_user

    # Create graph
    graph = await get_unified_agent_graph()

    # Create initial state
    state = {
        "messages": [HumanMessage(content="Hello")],
        "user_id": 123,
        "thread_id": "thread_456",
        "platform": "web",  # or "telegram"
        # ... other fields
    }

    # Execute
    result = await graph.ainvoke(state, config={"configurable": {"thread_id": "thread_456"}})


    Option 2: Integration helpers (recommended)
    -------------------------------------------
    from luka_agent.integration import stream_telegram_response, stream_web_response

    # Telegram
    async for event in stream_telegram_response(
        user_message="Hello",
        user_id=123,
        thread_id="thread_456",
        knowledge_bases=["tg-kb-user-123"],
        language="en"
    ):
        if event["type"] == "text_chunk":
            print(event["content"])
        elif event["type"] == "suggestions":
            print(event["keyboard"])

    # Web
    async for event in stream_web_response(
        user_message="Hello",
        user_id=123,
        thread_id="thread_456",
        knowledge_bases=["tg-kb-user-123"],
        language="en"
    ):
        if event["type"] == "textStreamDelta":
            print(event["delta"])
        elif event["type"] == "stateUpdate":
            print(event["suggestions"])
"""

from luka_agent.graph import get_unified_agent_graph
from luka_agent.tools import create_tools_for_user
from luka_agent.state import AgentState
from luka_agent.integration import stream_telegram_response, stream_web_response

__version__ = "1.0.0"

__all__ = [
    "get_unified_agent_graph",
    "create_tools_for_user",
    "AgentState",
    "stream_telegram_response",
    "stream_web_response",
]
