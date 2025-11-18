"""
Unified AgentState schema for Luka agent.

This state is used by both web (ag_ui_gateway) and Telegram (luka_bot) platforms.
Platform-specific behavior is controlled via the 'platform' field.
"""

from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

try:
    from copilotkit.langgraph import CopilotKitProperties
except ImportError:
    # CopilotKit not installed - define placeholder type
    CopilotKitProperties = Dict[str, Any]  # type: ignore


class AgentState(TypedDict):
    """
    Unified state for conversational agent (web + Telegram).

    This state is automatically persisted by LangGraph's Redis checkpointer,
    eliminating the need for manual conversation history management.

    The same state schema is used for both platforms, with platform-specific
    fields marked as optional or populated conditionally.
    """

    # =========================================================================
    # CORE FIELDS (Required for both platforms)
    # =========================================================================

    #: Message history (automatic reducer via add_messages)
    #: LangGraph automatically handles message deduplication and ordering
    messages: Annotated[List[BaseMessage], add_messages]

    #: User ID (Telegram user ID or web user ID)
    user_id: int

    #: Thread ID for conversation context
    #: - Web: Generated thread ID
    #: - Telegram: User ID or group chat ID
    thread_id: str

    #: User's preferred language (e.g., "en", "ru")
    language: str

    #: Platform identifier
    #: - "web": ag_ui_gateway (CopilotKit)
    #: - "telegram": luka_bot (aiogram)
    platform: Literal["web", "telegram"]

    # =========================================================================
    # KNOWLEDGE BASE & TOOLS
    # =========================================================================

    #: List of knowledge base indices the user can access
    #: - Web guest: [PUBLIC_KB] or []
    #: - Web auth: [f"tg-kb-user-{user_id}"]
    #: - Telegram: [f"tg-kb-user-{user_id}"]
    knowledge_bases: List[str]

    #: List of enabled tool names
    #: Common: ["knowledge_base", "workflow", "youtube"]
    #: Web-specific: ["trip_planner"]
    #: All platforms: ["support", "menu", "twitter"]
    enabled_tools: List[str]

    # =========================================================================
    # SUB-AGENT STATE (BMAD-Compatible)
    # =========================================================================
    # Sub-agents are complete AI personalities with their own prompts, tools, and configs
    # Based on BMAD Method - each sub-agent is a specialized persona
    # Examples: general_luka, crypto_analyst, trip_planner

    #: Current active sub-agent ID (e.g., "general_luka", "crypto_analyst")
    #: This determines which system prompt, tools, and KB are loaded
    sub_agent_id: str

    #: Sub-agent metadata (loaded from config.yaml)
    #: Contains: name, icon, description, version
    sub_agent_metadata: Dict[str, Any]

    #: Sub-agent persona (loaded from config.yaml)
    #: Contains: role, identity, communication_style, principles
    sub_agent_persona: Dict[str, Any]

    # =========================================================================
    # LEGACY WORKFLOW FIELDS (Deprecated, kept for backward compatibility)
    # =========================================================================
    # These fields are from the old workflow system and will be removed in Phase 2
    # Use sub_agent_id instead

    #: DEPRECATED: Use sub_agent_id instead
    active_workflow: Optional[str]

    #: DEPRECATED: Workflows don't have steps in BMAD model
    workflow_step: Optional[str]

    #: DEPRECATED: Progress tracking moved to workflow-specific sub-agents
    workflow_progress: float

    # =========================================================================
    # SUGGESTIONS (LLM-generated, contextual)
    # =========================================================================

    #: User-facing suggestions (displayed in UI/keyboard)
    #: These are LLM-generated, contextually aware suggestions
    #: - Web: Shown as quickPrompts in CopilotKit
    #: - Telegram: Shown in reply keyboard buttons
    conversation_suggestions: List[str]

    #: Internal sub-agent hints (used in LLM prompt, NOT shown directly to users)
    #: These come from sub-agent step definitions (config.yaml) and guide the LLM
    #: when generating conversation_suggestions
    #: Private field (prefixed with _) to indicate internal use
    _workflow_suggestion_hints: List[str]

    # =========================================================================
    # PLATFORM-SPECIFIC FIELDS (Optional)
    # =========================================================================

    #: Guest mode flag (Web only)
    #: - Web: True if unauthenticated user
    #: - Telegram: Always False (users must authenticate with Telegram)
    is_guest: bool

    #: CopilotKit integration state (Web only)
    #: - Web: {"actions": [...], "context": [...]}
    #: - Telegram: None
    #: This field enables CopilotKit's frontend state synchronization
    copilotkit: Optional[CopilotKitProperties]

    # =========================================================================
    # INTERNAL STATE
    # =========================================================================

    #: Tool execution results (keyed by tool call ID)
    tool_results: Dict[str, Any]

    #: Routing decision from agent node
    #: - "tools": Execute tools
    #: - "end": Generate suggestions and finish
    #: - None: Not yet determined
    next_action: Optional[Literal["tools", "end"]]

    #: UI context signals (platform-agnostic)
    #: Used to signal UI updates (e.g., keyboard refresh needed)
    #: Example: {"keyboard_update_needed": True}
    ui_context: Dict[str, Any]

    #: Additional metadata (extensible)
    metadata: Dict[str, Any]


# =============================================================================
# State Utility Functions
# =============================================================================


def create_initial_state(
    user_message: str,
    user_id: int,
    thread_id: str,
    platform: Literal["web", "telegram"],
    language: str = "en",
    knowledge_bases: Optional[List[str]] = None,
    enabled_tools: Optional[List[str]] = None,
    is_guest: bool = False,
    active_workflow: Optional[str] = None,  # DEPRECATED: Use sub_agent_id instead
    sub_agent_id: Optional[str] = None,
) -> AgentState:
    """
    Create initial AgentState for a new conversation turn.

    This is a helper function to create properly formatted initial state.
    Platform adapters (copilotkit_adapter.py, telegram_adapter.py) may
    provide more specialized versions.

    Args:
        user_message: User's message text
        user_id: User ID
        thread_id: Thread ID
        platform: "web" or "telegram"
        language: User language (default: "en")
        knowledge_bases: KB indices (default: user's KB or loaded from sub-agent)
        enabled_tools: Tool names (default: loaded from sub-agent config)
        is_guest: Guest mode flag (default: False)
        active_workflow: DEPRECATED - Use sub_agent_id instead
        sub_agent_id: Sub-agent to load (default: platform default)

    Returns:
        Initial AgentState ready for graph execution
    """
    from langchain_core.messages import HumanMessage

    # Determine sub-agent ID (platform defaults)
    if sub_agent_id is None:
        # Load from platform config
        from luka_bot.core.config import settings
        if platform == "telegram":
            sub_agent_id = getattr(settings, "DEFAULT_SUB_AGENT_TELEGRAM", "general_luka")
        else:  # web
            sub_agent_id = getattr(settings, "DEFAULT_SUB_AGENT_WEB", "general_luka")

    # Load sub-agent configuration
    from luka_agent.sub_agents.loader import get_sub_agent_loader
    loader = get_sub_agent_loader()
    try:
        sub_agent_config = loader.load(sub_agent_id)
    except Exception as e:
        # Fall back to general_luka if specified agent fails to load
        from loguru import logger
        logger.warning(f"Failed to load sub-agent '{sub_agent_id}', falling back to general_luka: {e}")
        sub_agent_config = loader.load("general_luka")
        sub_agent_id = "general_luka"

    # Load knowledge bases from sub-agent config (with template substitution)
    if knowledge_bases is None:
        knowledge_bases = []
        for kb_pattern in sub_agent_config.knowledge_bases:
            # Substitute template variables
            kb = kb_pattern.replace("{user_id}", str(user_id))
            knowledge_bases.append(kb)

    # Load enabled tools from sub-agent config
    if enabled_tools is None:
        enabled_tools = sub_agent_config.enabled_tools

    # Platform-specific copilotkit field
    copilotkit_value = (
        {"actions": [], "context": []} if platform == "web" else None
    )

    return {
        "messages": [HumanMessage(content=user_message)],
        "user_id": user_id,
        "thread_id": thread_id,
        "language": language,
        "platform": platform,
        "knowledge_bases": knowledge_bases,
        "enabled_tools": enabled_tools,
        # New sub-agent fields
        "sub_agent_id": sub_agent_id,
        "sub_agent_metadata": {
            "id": sub_agent_config.id,
            "name": sub_agent_config.name,
            "icon": sub_agent_config.icon,
            "description": sub_agent_config.description,
            "version": sub_agent_config.version,
        },
        "sub_agent_persona": {
            "role": sub_agent_config.role,
            "identity": sub_agent_config.identity,
            "communication_style": sub_agent_config.communication_style,
            "principles": sub_agent_config.principles,
        },
        # Legacy workflow fields (deprecated)
        "active_workflow": active_workflow,
        "workflow_step": None,
        "workflow_progress": 0.0,
        # Rest of state
        "conversation_suggestions": [],
        "_workflow_suggestion_hints": [],
        "is_guest": is_guest,
        "copilotkit": copilotkit_value,
        "tool_results": {},
        "next_action": None,
        "ui_context": {},
        "metadata": {},
    }


__all__ = ["AgentState", "create_initial_state"]
