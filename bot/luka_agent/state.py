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
    #: - "worker": CLI, background jobs, API workers
    platform: Literal["web", "telegram", "worker"]

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

    #: Rendered system prompt content (loaded from sub-agent's system_prompt.md)
    #: This is the full prompt text with template variables substituted
    #: Used by agent_node to set SystemMessage
    system_prompt_content: str

    # =========================================================================
    # LLM CONFIGURATION (from sub-agent config)
    # =========================================================================
    # These fields are loaded from sub-agent's luka_extensions.llm_config section
    # They allow each sub-agent to use different LLM providers and settings

    #: LLM provider (e.g., "ollama", "openai", "anthropic")
    llm_provider: str

    #: LLM model name (e.g., "llama3.2", "gpt-4o", "claude-sonnet-4")
    llm_model: str

    #: LLM temperature setting (0.0 to 2.0)
    llm_temperature: float

    #: Maximum tokens for LLM response
    llm_max_tokens: int

    #: Whether to stream LLM responses
    llm_streaming: bool

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
    platform: Literal["web", "telegram", "worker"],
    language: str = "en",
    knowledge_bases: Optional[List[str]] = None,
    enabled_tools: Optional[List[str]] = None,
    is_guest: bool = False,
    active_workflow: Optional[str] = None,  # DEPRECATED: Use sub_agent_id instead
    sub_agent_id: Optional[str] = None,
    # LLM runtime overrides (optional, for user-specific settings)
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
    llm_temperature: Optional[float] = None,
    llm_max_tokens: Optional[int] = None,
    llm_streaming: Optional[bool] = None,
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
        platform: "web", "telegram", or "worker"
        language: User language (default: "en")
        knowledge_bases: KB indices (default: user's KB or loaded from sub-agent)
        enabled_tools: Tool names (default: loaded from sub-agent config)
        is_guest: Guest mode flag (default: False)
        active_workflow: DEPRECATED - Use sub_agent_id instead
        sub_agent_id: Sub-agent to load (default: platform default)
        llm_provider: Override LLM provider (optional, for user-specific settings)
        llm_model: Override LLM model (optional, for user-specific settings)
        llm_temperature: Override temperature (optional, for user-specific settings)
        llm_max_tokens: Override max tokens (optional, for user-specific settings)
        llm_streaming: Override streaming (optional, for user-specific settings)

    Returns:
        Initial AgentState ready for graph execution

    LLM Configuration Priority:
        1. Runtime parameters (user-specific, passed to this function)
        2. Environment variables (deployment defaults from .env)
        3. Hardcoded fallbacks (system defaults)

    Example - Web platform with user's preferred model:
        >>> state = create_initial_state(
        ...     user_message="Hello",
        ...     user_id=123,
        ...     thread_id="user_123",
        ...     platform="web",
        ...     llm_provider="openai",     # User chose GPT-4o
        ...     llm_model="gpt-4o",
        ... )
    """
    from langchain_core.messages import HumanMessage

    # Determine sub-agent ID (platform defaults)
    if sub_agent_id is None:
        # Try to load from platform config, fallback to general_luka
        try:
            from luka_bot.core.config import settings
            if platform == "telegram":
                sub_agent_id = getattr(settings, "DEFAULT_SUB_AGENT_TELEGRAM", "general_luka")
            else:  # web
                sub_agent_id = getattr(settings, "DEFAULT_SUB_AGENT_WEB", "general_luka")
        except Exception:
            # Fallback if luka_bot config not available (CLI mode)
            sub_agent_id = "general_luka"

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

    # Load system prompt with template variables
    template_vars = {
        "user_name": f"User{user_id}",  # TODO: Get real user name from database
        "platform": platform,
        "language": language,
    }
    try:
        system_prompt_content = loader.load_system_prompt(
            sub_agent_config,
            language=language,
            template_vars=template_vars,
        )
    except Exception as e:
        from loguru import logger
        logger.warning(f"Failed to load system prompt for '{sub_agent_id}', using fallback: {e}")
        system_prompt_content = f"You are {sub_agent_config.name}, a helpful AI assistant."

    # Load LLM configuration with priority: runtime > env > defaults
    # This allows user-specific settings on web/telegram while using env defaults for CLI
    import os

    # Priority 1: Runtime parameter (user-specific)
    # Priority 2: Environment variable (deployment default)
    # Priority 3: Hardcoded fallback (system default)
    final_llm_provider = (
        llm_provider if llm_provider is not None
        else os.getenv("DEFAULT_LLM_PROVIDER", "ollama")
    )
    final_llm_model = (
        llm_model if llm_model is not None
        else os.getenv("DEFAULT_LLM_MODEL", "llama3.2")
    )
    final_llm_temperature = (
        llm_temperature if llm_temperature is not None
        else float(os.getenv("DEFAULT_LLM_TEMPERATURE", "0.7"))
    )
    final_llm_max_tokens = (
        llm_max_tokens if llm_max_tokens is not None
        else int(os.getenv("DEFAULT_LLM_MAX_TOKENS", "2000"))
    )
    final_llm_streaming = (
        llm_streaming if llm_streaming is not None
        else os.getenv("DEFAULT_LLM_STREAMING", "true").lower() == "true"
    )

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
        "system_prompt_content": system_prompt_content,
        # LLM configuration (with runtime > env > default priority)
        "llm_provider": final_llm_provider,
        "llm_model": final_llm_model,
        "llm_temperature": final_llm_temperature,
        "llm_max_tokens": final_llm_max_tokens,
        "llm_streaming": final_llm_streaming,
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
