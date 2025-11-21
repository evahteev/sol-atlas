"""
LangGraph nodes for luka_agent.

This module defines the core nodes used in the agent graph:
- agent: Main LLM node that processes user input and decides next action
- tools: Tool execution node
- suggestions: Suggestion generation node
"""

from typing import cast
from langchain_core.messages import AIMessage, ToolMessage
from loguru import logger

from luka_agent.state import AgentState


async def agent_node(state: AgentState) -> dict:
    """Main agent node that processes user input.

    This node:
    1. Takes the current state (with messages)
    2. Hydrates state with sub-agent config if needed
    3. Calls the LLM with tools and sub-agent system prompt
    4. Returns the LLM's response (text or tool calls)

    The LLM decides whether to:
    - Answer directly (text response)
    - Call tools (tool invocations)

    Args:
        state: Current agent state with message history

    Returns:
        State update with new message
    """
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import SystemMessage
    from luka_agent.tools import create_tools_for_user
    from luka_agent.graph import hydrate_state_with_sub_agent

    # Try to import settings, gracefully handle if not available (CLI mode)
    try:
        from luka_agent.core.config import settings
    except Exception:
        settings = None

    logger.info(f"🤖 Agent node processing for user {state['user_id']}")

    # Check if state needs hydration (first run or agent switch)
    if not state.get("system_prompt_content"):
        logger.info("🔄 State not hydrated, loading sub-agent config")
        hydration_updates = hydrate_state_with_sub_agent(state)
        # Merge updates into state (simulate state update for this turn)
        state = {**state, **hydration_updates}

    # Create tools for this user (using sub-agent's enabled_tools)
    tools = create_tools_for_user(
        user_id=state["user_id"],
        thread_id=state["thread_id"],
        knowledge_bases=state["knowledge_bases"],
        enabled_tools=state["enabled_tools"],
        platform=state["platform"],
        language=state["language"],
    )

    # Select LLM provider based on sub-agent config
    llm_provider = state.get("llm_provider", "ollama")
    llm_model = state.get("llm_model", "llama3.2")
    llm_temperature = state.get("llm_temperature", 0.7)

    logger.info(f"🧠 Invoking LLM: {llm_provider}/{llm_model} (temp={llm_temperature})")

    if llm_provider == "ollama":
        # Get Ollama URL from settings or environment/default
        if settings:
            ollama_url = settings.OLLAMA_URL.rstrip("/")
        else:
            import os
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")

        # Use OpenAI-compatible API for Ollama (requires /v1 endpoint)
        # This allows using models like gpt-oss that are hosted via Ollama
        llm = ChatOpenAI(
            model=llm_model,
            base_url=f"{ollama_url}/v1",
            api_key="ollama",  # Ollama doesn't require a real API key
            temperature=llm_temperature,
        )
    elif llm_provider == "openai":
        llm = ChatOpenAI(
            model=llm_model,
            temperature=llm_temperature,
        )
    elif llm_provider == "anthropic":
        llm = ChatAnthropic(
            model=llm_model,
            temperature=llm_temperature,
        )
    else:
        logger.error(f"Unknown LLM provider: {llm_provider}, falling back to ollama")
        import os
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        # Use OpenAI-compatible API for Ollama fallback
        llm = ChatOpenAI(
            model="llama3.2",
            base_url=f"{ollama_url}/v1",
            api_key="ollama",  # Ollama doesn't require a real API key
            temperature=0.7,
        )

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Use sub-agent's system prompt
    system_prompt_content = state.get(
        "system_prompt_content",
        "You are a helpful AI assistant."
    )

    logger.debug(f"📝 System prompt length: {len(system_prompt_content)} chars")
    logger.debug(f"🔧 Tools available: {len(tools)}")

    # Build messages with system prompt
    system_message = SystemMessage(content=system_prompt_content)
    messages = [system_message] + state["messages"]

    # Invoke LLM with current message history
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
    from langchain_core.messages import ToolMessage
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

    # Create a tool lookup dict
    tools_by_name = {tool.name: tool for tool in tools}

    # Get tool calls from the last message
    last_message = state["messages"][-1]
    tool_calls = last_message.tool_calls if hasattr(last_message, "tool_calls") else []

    # Execute each tool call
    tool_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id", "")

        # Find the tool
        tool = tools_by_name.get(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found"
            logger.error(error_msg)
            tool_messages.append(
                ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_id,
                    name=tool_name,
                )
            )
            continue

        # Execute the tool
        try:
            logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
            result = await tool.ainvoke(tool_args)
            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_id,
                    name=tool_name,
                )
            )
            logger.debug(f"Tool {tool_name} executed successfully")
        except Exception as e:
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            tool_messages.append(
                ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_id,
                    name=tool_name,
                )
            )

    logger.info(f"✅ Tools node completed, executed {len(tool_messages)} tools")

    return {"messages": tool_messages}


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
    from langchain_openai import ChatOpenAI
    import json
    import random
    import os

    # Try to import settings, gracefully handle if not available
    try:
        from luka_agent.core.config import settings
    except Exception:
        settings = None

    logger.info(f"💡 Suggestions node generating for user {state['user_id']}")

    # Check if suggestions are enabled
    if not state.get("generate_suggestions", True):
        logger.info("Suggestions generation disabled, skipping")
        return {"conversation_suggestions": []}

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
            # Select LLM provider (use state config if available, else fallback)
            llm_provider = state.get("llm_provider", "ollama")
            llm_model = state.get("llm_model", "llama3.2")

            if llm_provider == "ollama":
                if settings:
                    ollama_url = settings.OLLAMA_URL.rstrip("/")
                else:
                    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")

                # Use OpenAI-compatible API for Ollama
                llm = ChatOpenAI(
                    model=llm_model,
                    base_url=f"{ollama_url}/v1",
                    api_key="ollama",  # Ollama doesn't require a real API key
                    temperature=0.7,
                )
            else:
                llm = ChatOpenAI(
                    model=llm_model,
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
