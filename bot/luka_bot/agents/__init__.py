"""
Agentic Architecture for Luka Bot - Phase 4.

This package implements the pydantic-ai powered conversational agent system,
migrated and adapted from bot_server/agents/ with Luka-specific enhancements.

Core Components:
- agent_factory: Create and configure agents with tools
- context: Type-safe conversation context models
- message_history: Pydantic-AI message history with Redis persistence
- tools/: LLM tool implementations (KB, YouTube, Support, Workflows)

Architecture:
- Multi-tier agent strategy (tools → static → simple)
- Automatic tool discovery and execution
- Streaming support with tool calls
- Thread-scoped configuration (provider, model, enabled tools)
- Conversation continuity across sessions

Usage:
    from luka_bot.agents import create_agent
    from luka_bot.agents.context import ConversationContext
    
    agent = await create_agent(user_id, thread, language="en")
    async with agent.run_stream(user_prompt, deps=ctx) as stream:
        async for chunk in stream.stream_text():
            yield chunk
"""

__version__ = "1.0.0"

# Import core components
from .context import ConversationContext, TaskContext
from .agent_factory import (
	create_static_agent_with_basic_tools,
	create_simple_agent_without_tools,
	create_agent_with_user_tasks,
)

# Re-export tools modules for convenience
from .tools import support_tools
from .tools import youtube_tools  # newly added

__all__ = [
	"ConversationContext",
	"TaskContext",
	"create_static_agent_with_basic_tools",
	"create_simple_agent_without_tools",
	"create_agent_with_user_tasks",
	"support_tools",
	"youtube_tools",
]

