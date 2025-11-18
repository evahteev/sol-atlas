"""
LangGraph nodes for luka_agent.

This module defines the core nodes used in the agent graph:
- agent: Main LLM node that processes user input and decides next action
- tools: Tool execution node
- suggestions: Suggestion generation node
"""

from typing import cast
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from loguru import logger

from luka_agent.state import AgentState


async def agent_node(state: AgentState) -> dict:
    """Main agent node that processes user input.

    This node:
    1. Takes the current state (with messages)
    2. Calls the LLM with tools
    3. Returns the LLM's response (text or tool calls)

    The LLM decides whether to:
    - Answer directly (text response)
    - Call tools (tool invocations)

    Args:
        state: Current agent state with message history

    Returns:
        State update with new message
    """
    from langchain_ollama import ChatOllama
    from langchain_openai import ChatOpenAI
    from luka_bot.core.config import settings
    from luka_agent.tools import create_tools_for_user

    logger.info(f"🤖 Agent node processing for user {state['user_id']}")

    # Create tools for this user
    tools = create_tools_for_user(
        user_id=state["user_id"],
        thread_id=state["thread_id"],
        knowledge_bases=state["knowledge_bases"],
        enabled_tools=state["enabled_tools"],
        platform=state["platform"],
        language=state["language"],
    )

    # Select LLM provider based on configuration
    if settings.DEFAULT_LLM_PROVIDER == "ollama":
        ollama_url = settings.OLLAMA_URL.rstrip("/v1").rstrip("/")
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL_NAME,
            base_url=ollama_url,
            temperature=0.7,
        )
    else:
        llm = ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL or "gpt-4o-mini",
            temperature=0.7,
        )

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Build system prompt
    system_prompt = f"""You are Luka, a helpful AI assistant.

Platform: {state['platform']}
Language: {state['language']}

You have access to tools to help users. Use them when appropriate.
"""

    # Invoke LLM with current message history
    messages = state["messages"]
    response = await llm_with_tools.ainvoke(messages)

    logger.info(f"✅ Agent node completed, response type: {type(response).__name__}")

    # Determine next action based on response
    next_action = None
    if hasattr(response, "tool_calls") and response.tool_calls:
        next_action = "tools"
        logger.info(f"🔧 Agent wants to call {len(response.tool_calls)} tools")
    else:
        next_action = "end"
        logger.info(f"💬 Agent provided text response")

    return {
        "messages": [response],
        "next_action": next_action,
    }


async def tools_node(state: AgentState) -> dict:
    """Tool execution node.

    This node:
    1. Extracts tool calls from the last AI message
    2. Executes each tool
    3. Returns tool results as ToolMessages

    Args:
        state: Current agent state

    Returns:
        State update with tool results
    """
    from luka_agent.tools import create_tools_for_user

    logger.info(f"🔧 Tools node executing for user {state['user_id']}")

    # Create tools for this user
    tools = create_tools_for_user(
        user_id=state["user_id"],
        thread_id=state["thread_id"],
        knowledge_bases=state["knowledge_bases"],
        enabled_tools=state["enabled_tools"],
        platform=state["platform"],
        language=state["language"],
    )

    # Use LangGraph's built-in ToolNode for execution
    tool_node = ToolNode(tools)

    # Execute tools
    result = await tool_node.ainvoke(state)

    logger.info(f"✅ Tools node completed")

    return result


async def suggestions_node(state: AgentState) -> dict:
    """Suggestion generation node.

    This node:
    1. Analyzes the conversation history
    2. Generates contextual suggestions for the user
    3. Returns suggestions in the state

    Suggestions are generated based on:
    - Conversation context (last few messages)
    - Active workflow (if any)
    - Platform (web vs Telegram)

    Args:
        state: Current agent state

    Returns:
        State update with suggestions
    """
    from langchain_ollama import ChatOllama
    from langchain_openai import ChatOpenAI
    from luka_bot.core.config import settings
    import json
    import random

    logger.info(f"💡 Suggestions node generating for user {state['user_id']}")

    # Check if we have an active workflow
    active_workflow = state.get("active_workflow")
    workflow_hints = state.get("_workflow_suggestion_hints", [])

    suggestions = []

    if active_workflow and workflow_hints:
        # Generate workflow-specific suggestions using hints
        logger.info(f"📋 Generating workflow suggestions (workflow: {active_workflow})")
        # For now, use workflow hints directly
        # TODO: Enhance with LLM generation based on hints
        suggestions = workflow_hints[:3]
    else:
        # Generate conversational suggestions based on history
        logger.info(f"💬 Generating conversational suggestions")

        # Extract last few messages for context
        messages = state["messages"]
        recent_messages = messages[-5:] if len(messages) >= 5 else messages

        # Build context string
        context_parts = []
        for msg in recent_messages:
            if hasattr(msg, "content") and msg.content:
                role = "User" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                context_parts.append(f"{role}: {str(msg.content)[:100]}")

        context = "\n".join(context_parts)

        # Generate suggestions with LLM
        try:
            # Select LLM provider
            if settings.DEFAULT_LLM_PROVIDER == "ollama":
                ollama_url = settings.OLLAMA_URL.rstrip("/v1").rstrip("/")
                llm = ChatOllama(
                    model=settings.OLLAMA_MODEL_NAME,
                    base_url=ollama_url,
                    temperature=0.7,
                )
            else:
                llm = ChatOpenAI(
                    model=settings.DEFAULT_LLM_MODEL or "gpt-4o-mini",
                    temperature=0.7,
                )

            prompt = f"""Based on this conversation, suggest 3 short things the user might say next:

{context}

Generate 3 natural, short suggestions (max 50 chars each) in {state['language']} language.
Return only the suggestions, one per line. No numbering."""

            response = await llm.ainvoke(prompt)
            suggestions_text = response.content.strip()

            # Parse suggestions
            raw_suggestions = [s.strip() for s in suggestions_text.split("\n") if s.strip()]
            suggestions = [s.lstrip("1234567890.-•* ").strip() for s in raw_suggestions if s][:3]

            logger.info(f"✅ Generated {len(suggestions)} suggestions: {suggestions}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to generate suggestions: {e}")
            # Fallback to static suggestions
            suggestions = [
                "Tell me more",
                "What else can you do?",
                "Thanks!"
            ]

    return {
        "conversation_suggestions": suggestions,
    }


def should_continue(state: AgentState) -> str:
    """Router function to determine next node.

    Args:
        state: Current agent state

    Returns:
        Next node name: "tools", "suggestions", or "end"
    """
    next_action = state.get("next_action")

    if next_action == "tools":
        logger.info(f"🔀 Routing to tools")
        return "tools"
    else:
        logger.info(f"🔀 Routing to suggestions")
        return "suggestions"


__all__ = [
    "agent_node",
    "tools_node",
    "suggestions_node",
    "should_continue",
]
