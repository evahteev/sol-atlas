"""
Tools for Luka Bot Agents - Phase 4.

Pydantic-AI powered tools with automatic discovery and execution.
Each tool module exports:
- Tool functions with Field annotations
- get_tools() function returning List[Tool]
- get_prompt_description() for dynamic system prompts

Available Tools:
- support: Help resources and escalation ✅ Phase 4
- knowledge_base: Text search in user's message history ✅ Phase 5
- youtube: Video transcript search and analysis ✅ Phase 4
- twitter: Twitter account info and content analysis ✅ Phase 1 (KB Gathering)
- workflow: Dialog workflow discovery and execution (Phase 4+)

Tools are:
- Thread-configurable (enabled_tools in Thread model)
- Context-aware (receive ConversationContext)
- Type-safe (Pydantic Field validation)
- Automatically executed by agent during streaming
"""

from . import support_tools
from . import knowledge_base_tools
from . import workflow_tools
from . import workflow_context_tools
from . import twitter_tools

__all__ = ['support_tools', 'knowledge_base_tools', 'workflow_tools', 'workflow_context_tools', 'twitter_tools']
