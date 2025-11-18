# Luka Agent Pivot: BMAD-Style Sub-Agent Architecture

**Date:** November 18, 2025
**Status:** Architecture Design Document
**Purpose:** Transform luka_agent into a runtime engine that loads BMAD-compatible sub-agents

---

## Executive Summary

**Current State:**
- luka_agent is a generic LangGraph agent with tools
- System prompts are minimal and static
- No specialized agent personalities

**Proposed State:**
- luka_agent becomes a **runtime execution engine**
- Sub-agents define complete agent personalities (BMAD-compatible YAML + Markdown)
- Each deployment/app has a default sub-agent
- Users can explicitly switch sub-agents mid-conversation
- Dynamic agent switching with shared conversation history

**Key Decisions:**
- ✅ Dynamic agent switching (Q1.1 - Option D)
- ✅ BMAD-compatible with our extensions (Q2.1, Q2.2)
- ✅ Shared conversation history across agents (Q4.1)
- ✅ Agent state initialization, default per app (Q5.1)
- ✅ No tool-level prompt injection (Q8.1)
- ✅ Explicit user agent selection (Q7.1)
- ✅ Sub-agent validation on load (Q10.2)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│  ┌────────────────────┐          ┌─────────────────────┐        │
│  │  ag_ui_gateway     │          │  luka_bot (Telegram)│        │
│  │  config:           │          │  config:            │        │
│  │  DEFAULT_SUB_AGENT │          │  DEFAULT_SUB_AGENT  │        │
│  │  = "web_assistant" │          │  = "general_luka"   │        │
│  └─────────┬──────────┘          └──────────┬──────────┘        │
└────────────┼────────────────────────────────┼───────────────────┘
             │                                 │
             └────────────┬────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                   luka_agent (Execution Engine)                   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AgentState Initialization                                │   │
│  │  {                                                        │   │
│  │    user_id: 123,                                         │   │
│  │    thread_id: "user_123_thread_1",                       │   │
│  │    sub_agent_id: "general_luka",  ← FROM CONFIG          │   │
│  │    messages: [],                                         │   │
│  │    platform: "web",                                      │   │
│  │    language: "en",                                       │   │
│  │  }                                                        │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Sub-Agent Loader (graph.py or new loader node)          │   │
│  │  1. Load sub_agents/{sub_agent_id}/config.yaml           │   │
│  │  2. Validate YAML structure                              │   │
│  │  3. Load system_prompt.md (with language variants)       │   │
│  │  4. Hydrate state with:                                  │   │
│  │     - enabled_tools                                      │   │
│  │     - knowledge_bases (resolve templates)                │   │
│  │     - llm_config (provider, model, temp)                 │   │
│  │     - agent_metadata (name, icon, description)           │   │
│  │     - system_prompt_content                              │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LangGraph Execution (graph.py)                           │   │
│  │  START → agent_node → tools_node → suggestions → END     │   │
│  │                                                            │   │
│  │  agent_node:                                              │   │
│  │    - Uses state['system_prompt_content']                 │   │
│  │    - Creates tools from state['enabled_tools']           │   │
│  │    - Invokes LLM with state['llm_config']                │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│              Sub-Agent Definitions (BMAD-Compatible)              │
│                                                                    │
│  luka_agent/sub_agents/                                           │
│    ├─ general_luka/           ← Default sub-agent                │
│    │   ├─ config.yaml                                            │
│    │   ├─ system_prompt.md                                       │
│    │   └─ prompts/                                               │
│    │       ├─ en.md                                              │
│    │       └─ ru.md                                              │
│    │                                                              │
│    ├─ crypto_analyst/                                            │
│    │   ├─ config.yaml                                            │
│    │   ├─ system_prompt.md                                       │
│    │   └─ prompts/                                               │
│    │       ├─ en.md                                              │
│    │       └─ ru.md                                              │
│    │                                                              │
│    ├─ trip_planner/                                              │
│    │   ├─ config.yaml                                            │
│    │   └─ system_prompt.md                                       │
│    │                                                              │
│    └─ web_assistant/          ← Default for ag_ui_gateway       │
│        ├─ config.yaml                                            │
│        └─ system_prompt.md                                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Sub-Agent Definition Spec (BMAD-Compatible + Extensions)

### File Structure

```
luka_agent/sub_agents/{sub_agent_id}/
  ├─ config.yaml              # BMAD-compatible agent definition + our extensions
  ├─ system_prompt.md         # Default system prompt
  ├─ prompts/                 # Language-specific variants (optional)
  │   ├─ en.md
  │   ├─ ru.md
  │   └─ es.md
  └─ workflows/               # Sub-agent specific workflows (future)
      └─ onboarding.yaml
```

### config.yaml Format

```yaml
# BMAD-compatible agent definition with luka_agent extensions

# ============================================================================
# BMAD Core Section (Compatible with BMAD Method)
# ============================================================================

agent:
  metadata:
    id: "general_luka"                    # Unique identifier
    name: "Luka"                          # Display name
    title: "General AI Assistant"        # Full title
    icon: "🤖"                            # Icon/emoji
    version: "1.0.0"                      # Semver
    description: "General-purpose AI assistant for Telegram and web"

  persona:
    role: "Helpful AI Assistant + Task Manager"
    identity: |
      You are Luka, a versatile AI assistant that helps users with:
      - Conversation management through threads
      - Knowledge base search
      - Task organization (GTD methodology)
      - Workflow execution
    communication_style: "Friendly, concise, and professional"
    principles:
      - "Be concise and respectful of user's time"
      - "Ask clarifying questions when needed"
      - "Use emojis sparingly, only for clarity"
      - "Provide actionable answers"

  # BMAD menu - not used in luka_agent (we use explicit tool calls instead)
  # Kept for BMAD compatibility
  menu: []

# ============================================================================
# Luka Agent Extensions (Not in BMAD spec)
# ============================================================================

luka_extensions:
  # System prompt configuration
  system_prompt:
    base: "sub_agents/general_luka/system_prompt.md"
    language_variants:
      en: "sub_agents/general_luka/prompts/en.md"
      ru: "sub_agents/general_luka/prompts/ru.md"
    # Template variables available in prompt
    template_vars:
      agent_name: "{metadata.name}"
      user_name: "{user.name}"
      platform: "{state.platform}"
      language: "{state.language}"

  # Tools this sub-agent can use
  enabled_tools:
    - "knowledge_base"
    - "sub_agent"         # Discovery tools (get_available, get_details, start)
    - "youtube"
    - "support"

  # Knowledge base indices (supports template variables)
  knowledge_bases:
    - "user-kb-{user_id}"      # User's personal KB
    # Add more as needed:
    # - "crypto-tweets"
    # - "defi-protocols"

  # LLM configuration
  llm_config:
    provider: "ollama"         # "ollama", "openai", "anthropic"
    model: "llama3.2"          # Model name
    temperature: 0.7
    max_tokens: 2000
    streaming: true

  # Agent capability boundaries
  capabilities:
    # Data access scope (future: enforce via KB filters)
    data_access:
      allowed_kb_patterns:
        - "user-kb-*"
        - "public-*"
      forbidden_kb_patterns:
        - "admin-*"
        - "system-*"

    # Feature flags
    features:
      can_create_threads: true
      can_execute_workflows: true
      can_search_external: false
      can_modify_user_data: false

  # Intent triggers for auto-switching (future - not implemented in phase 1)
  intent_triggers: []
```

### system_prompt.md Format

```markdown
# System Prompt for {agent_name}

You are **{agent_name}**, {persona.role}.

## Identity

{persona.identity}

## Communication Style

{persona.communication_style}

## Core Principles

{persona.principles}

## Available Tools

### 🔍 search_knowledge_base
Search your personal knowledge base of indexed messages and documents.

**When to use:**
- User asks about past conversations
- User wants to find specific information from their history
- User asks "what did I say about X?"

**Usage:**
```
User: "Find my notes about blockchain"
→ search_knowledge_base(query="blockchain", date_from="30d")
```

**Critical:**
- Check conversation history FIRST for recent topics
- Use KB search for historical or stored information
- Always cite the source (date, original message)

### 🎥 get_youtube_transcript
Fetch transcript from a YouTube video.

**When to use:**
- User shares a YouTube link
- User asks to summarize a video
- User wants to extract information from a video

**Usage:**
```
User: "Summarize this video: https://youtube.com/watch?v=..."
→ get_youtube_transcript(video_url="...", language="en")
```

### 🛠️ Sub-Agent Tools (get_available_sub_agents, get_sub_agent_details, start_sub_agent)

These tools help discover and launch specialized sub-agents.

**When to use:**
- User asks about available capabilities beyond your scope
- User mentions topics that might have specialized agents (trips, crypto, etc.)
- You're unsure if a specialized agent exists for a topic

**Usage:**
```
User: "Can you help me plan a trip?"
→ get_available_sub_agents()  # Check if trip_planner exists
→ If found: "I found a specialized Trip Planner agent. Would you like me to switch to it?"
```

## Conversation Guidelines

1. **Thread Context:** Each thread has its own conversation history. Always consider the current thread's context.

2. **Language Preference:** The user prefers to communicate in **{language}**. Respond in {language} unless explicitly asked otherwise.

3. **Conciseness:** Be brief and to the point. Users are busy.

4. **Clarifying Questions:** If unclear, ask 1-2 specific questions rather than making assumptions.

5. **Tool Usage:** Use tools when they provide better answers than your knowledge. Don't try to answer from memory if a tool can give real-time or accurate data.

## Example Interactions

**User:** "What did I say about the meeting last week?"

**Good Response:**
```
Let me search your conversation history...

[Calls search_knowledge_base(query="meeting", date_from="7d")]

I found 3 mentions of meetings last week:

1. **Nov 12**: You mentioned rescheduling the standup to 10am
2. **Nov 14**: Discussed Q4 planning meeting agenda
3. **Nov 15**: Confirmed attendance for the all-hands

Which one were you referring to?
```

**User:** "Plan a trip to Paris"

**Good Response:**
```
I can help with general travel information, but I noticed we have a specialized Trip Planner agent that provides:
- Interactive route planning
- POI suggestions with ratings
- Day-by-day itineraries
- Location search

Would you like me to switch to the Trip Planner agent? (Just say "yes" or "switch to trip planner")
```

---

## Platform Context

- **Platform:** {platform} (web, telegram, etc.)
- **User:** {user_name}
- **Language:** {language}

Remember: You are a general assistant. For specialized needs, help users discover and switch to appropriate sub-agents.
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

#### 1.1 Update AgentState

```python
# luka_agent/state.py

from typing import TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for luka_agent graph with sub-agent support."""

    # Existing fields
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: int
    thread_id: str
    platform: str  # "web", "telegram"
    language: str  # "en", "ru", etc.

    # Sub-agent fields (NEW)
    sub_agent_id: str  # Current sub-agent identifier
    sub_agent_name: str  # Display name (e.g., "Luka", "Crypto Analyst")
    sub_agent_icon: str  # Icon/emoji for UI

    # Hydrated from sub-agent config
    enabled_tools: list[str]
    knowledge_bases: list[str]
    system_prompt_content: str  # Fully rendered system prompt

    # LLM config from sub-agent
    llm_provider: str  # "ollama", "openai"
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int
    llm_streaming: bool

    # Execution state
    next_action: Literal["tools", "suggestions", "end"] | None
    conversation_suggestions: list[str]

    # Workflow state (existing)
    active_workflow: str | None
    workflow_step: str | None
    workflow_suggestions: list[str]
    _workflow_suggestion_hints: list[str]
```

#### 1.2 Create Sub-Agent Loader

```python
# luka_agent/sub_agents/loader.py

import yaml
from pathlib import Path
from typing import Any
from loguru import logger


class SubAgentConfig:
    """Parsed sub-agent configuration."""

    def __init__(self, config_dict: dict):
        self.raw = config_dict
        self.agent = config_dict.get("agent", {})
        self.metadata = self.agent.get("metadata", {})
        self.persona = self.agent.get("persona", {})
        self.extensions = config_dict.get("luka_extensions", {})

    @property
    def id(self) -> str:
        return self.metadata.get("id", "unknown")

    @property
    def name(self) -> str:
        return self.metadata.get("name", "Agent")

    @property
    def icon(self) -> str:
        return self.metadata.get("icon", "🤖")

    @property
    def enabled_tools(self) -> list[str]:
        return self.extensions.get("enabled_tools", [])

    @property
    def knowledge_bases(self) -> list[str]:
        return self.extensions.get("knowledge_bases", [])

    @property
    def llm_config(self) -> dict:
        return self.extensions.get("llm_config", {})

    @property
    def system_prompt_config(self) -> dict:
        return self.extensions.get("system_prompt", {})

    @property
    def capabilities(self) -> dict:
        return self.extensions.get("capabilities", {})


class SubAgentLoader:
    """Loads and validates sub-agent configurations."""

    def __init__(self, base_path: Path = None):
        if base_path is None:
            # Default to luka_agent/sub_agents/
            base_path = Path(__file__).parent
        self.base_path = base_path
        logger.info(f"SubAgentLoader initialized with base_path: {self.base_path}")

    def load(self, sub_agent_id: str) -> SubAgentConfig:
        """Load sub-agent configuration by ID.

        Args:
            sub_agent_id: Sub-agent identifier (e.g., "general_luka")

        Returns:
            SubAgentConfig instance

        Raises:
            FileNotFoundError: If config.yaml not found
            ValueError: If validation fails
        """
        config_path = self.base_path / sub_agent_id / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(
                f"Sub-agent config not found: {config_path}\n"
                f"Available sub-agents: {self.list_available()}"
            )

        logger.info(f"Loading sub-agent config: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)

        # Validate structure
        self._validate_config(config_dict, sub_agent_id)

        config = SubAgentConfig(config_dict)
        logger.info(f"✅ Loaded sub-agent: {config.name} ({config.id})")

        return config

    def _validate_config(self, config: dict, sub_agent_id: str):
        """Validate sub-agent config structure.

        Raises:
            ValueError: If validation fails
        """
        # Check BMAD required fields
        if "agent" not in config:
            raise ValueError(f"Sub-agent {sub_agent_id}: Missing 'agent' section")

        agent = config["agent"]

        if "metadata" not in agent:
            raise ValueError(f"Sub-agent {sub_agent_id}: Missing 'agent.metadata'")

        metadata = agent["metadata"]
        required_metadata = ["id", "name"]
        for field in required_metadata:
            if field not in metadata:
                raise ValueError(
                    f"Sub-agent {sub_agent_id}: Missing required metadata field '{field}'"
                )

        if "persona" not in agent:
            raise ValueError(f"Sub-agent {sub_agent_id}: Missing 'agent.persona'")

        persona = agent["persona"]
        required_persona = ["role", "identity", "communication_style"]
        for field in required_persona:
            if field not in persona:
                raise ValueError(
                    f"Sub-agent {sub_agent_id}: Missing required persona field '{field}'"
                )

        # Check luka_extensions
        if "luka_extensions" not in config:
            raise ValueError(f"Sub-agent {sub_agent_id}: Missing 'luka_extensions' section")

        extensions = config["luka_extensions"]
        required_extensions = ["system_prompt", "enabled_tools", "knowledge_bases", "llm_config"]
        for field in required_extensions:
            if field not in extensions:
                raise ValueError(
                    f"Sub-agent {sub_agent_id}: Missing required extension field '{field}'"
                )

        logger.debug(f"✅ Validation passed for sub-agent: {sub_agent_id}")

    def load_system_prompt(
        self,
        config: SubAgentConfig,
        language: str = "en",
        template_vars: dict = None,
    ) -> str:
        """Load and render system prompt for sub-agent.

        Args:
            config: SubAgentConfig instance
            language: Preferred language code
            template_vars: Variables for prompt template (user_name, platform, etc.)

        Returns:
            Rendered system prompt content
        """
        prompt_config = config.system_prompt_config

        # Determine which prompt file to load
        prompt_path = None

        # Check for language-specific variant
        if "language_variants" in prompt_config and language in prompt_config["language_variants"]:
            prompt_path = self.base_path.parent / prompt_config["language_variants"][language]

        # Fall back to base prompt
        if prompt_path is None or not prompt_path.exists():
            if "base" in prompt_config:
                prompt_path = self.base_path.parent / prompt_config["base"]
            else:
                raise ValueError(f"No system prompt configured for {config.id}")

        if not prompt_path.exists():
            raise FileNotFoundError(f"System prompt not found: {prompt_path}")

        logger.info(f"Loading system prompt: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # Render template with variables
        if template_vars:
            prompt = self._render_template(prompt_template, config, template_vars)
        else:
            prompt = prompt_template

        return prompt

    def _render_template(self, template: str, config: SubAgentConfig, vars: dict) -> str:
        """Render prompt template with variables.

        Supports:
        - {agent_name} → config.name
        - {user_name} → vars['user_name']
        - {platform} → vars['platform']
        - {language} → vars['language']
        - {persona.role} → config.persona['role']
        - {persona.identity} → config.persona['identity']
        - etc.
        """
        # Build context with config fields
        context = {
            "agent_name": config.name,
            "metadata": config.metadata,
            "persona": config.persona,
        }

        # Add user-provided vars
        context.update(vars)

        # Simple template rendering (replace {key} with value)
        # For nested keys like {persona.role}, use dot notation
        result = template

        # Replace flat keys first
        for key, value in context.items():
            if isinstance(value, str):
                result = result.replace(f"{{{key}}}", value)

        # Replace nested keys (persona.role, metadata.name, etc.)
        import re
        nested_pattern = r'\{(\w+)\.(\w+)\}'

        def replace_nested(match):
            obj_name = match.group(1)
            field_name = match.group(2)
            if obj_name in context and isinstance(context[obj_name], dict):
                return str(context[obj_name].get(field_name, match.group(0)))
            return match.group(0)

        result = re.sub(nested_pattern, replace_nested, result)

        return result

    def list_available(self) -> list[str]:
        """List all available sub-agent IDs.

        Returns:
            List of sub-agent directory names with config.yaml
        """
        sub_agents = []
        for item in self.base_path.iterdir():
            if item.is_dir() and (item / "config.yaml").exists():
                sub_agents.append(item.name)
        return sorted(sub_agents)

    def resolve_knowledge_bases(
        self,
        kb_templates: list[str],
        user_id: int,
        group_id: int | None = None,
    ) -> list[str]:
        """Resolve KB template variables.

        Args:
            kb_templates: List of KB patterns like ["user-kb-{user_id}", "crypto-tweets"]
            user_id: User ID for substitution
            group_id: Group ID for substitution (optional)

        Returns:
            List of resolved KB indices
        """
        resolved = []
        for template in kb_templates:
            kb = template
            kb = kb.replace("{user_id}", str(user_id))
            if group_id:
                kb = kb.replace("{group_id}", str(abs(group_id)))
            resolved.append(kb)
        return resolved


# Global loader instance
_loader = None

def get_sub_agent_loader() -> SubAgentLoader:
    """Get global SubAgentLoader instance."""
    global _loader
    if _loader is None:
        _loader = SubAgentLoader()
    return _loader
```

#### 1.3 Update graph.py

```python
# luka_agent/graph.py

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from luka_agent.state import AgentState
from luka_agent.nodes import agent_node, tools_node, suggestions_node, should_continue
from luka_agent.sub_agents.loader import get_sub_agent_loader
from loguru import logger


def hydrate_state_with_sub_agent(state: AgentState) -> dict:
    """Hydrate state with sub-agent configuration.

    This function loads the sub-agent config and populates state fields.
    Called at the start of graph execution or when switching agents.

    Args:
        state: Current agent state with sub_agent_id

    Returns:
        State updates (dict) to merge into state
    """
    sub_agent_id = state.get("sub_agent_id", "general_luka")

    logger.info(f"🔄 Hydrating state with sub-agent: {sub_agent_id}")

    try:
        # Load sub-agent config
        loader = get_sub_agent_loader()
        config = loader.load(sub_agent_id)

        # Resolve knowledge bases
        knowledge_bases = loader.resolve_knowledge_bases(
            config.knowledge_bases,
            user_id=state["user_id"],
            group_id=None,  # TODO: Get from state if in group context
        )

        # Load system prompt
        template_vars = {
            "user_name": state.get("user_name", "User"),
            "platform": state.get("platform", "unknown"),
            "language": state.get("language", "en"),
        }

        system_prompt_content = loader.load_system_prompt(
            config,
            language=state.get("language", "en"),
            template_vars=template_vars,
        )

        # Get LLM config
        llm_config = config.llm_config

        # Build state updates
        updates = {
            "sub_agent_id": sub_agent_id,
            "sub_agent_name": config.name,
            "sub_agent_icon": config.icon,
            "enabled_tools": config.enabled_tools,
            "knowledge_bases": knowledge_bases,
            "system_prompt_content": system_prompt_content,
            "llm_provider": llm_config.get("provider", "ollama"),
            "llm_model": llm_config.get("model", "llama3.2"),
            "llm_temperature": llm_config.get("temperature", 0.7),
            "llm_max_tokens": llm_config.get("max_tokens", 2000),
            "llm_streaming": llm_config.get("streaming", True),
        }

        logger.info(f"✅ State hydrated with sub-agent: {config.name}")
        logger.debug(f"   Tools: {config.enabled_tools}")
        logger.debug(f"   KBs: {knowledge_bases}")
        logger.debug(f"   LLM: {updates['llm_provider']}/{updates['llm_model']}")

        return updates

    except Exception as e:
        logger.error(f"❌ Failed to hydrate state with sub-agent {sub_agent_id}: {e}")
        # Return minimal fallback state
        return {
            "sub_agent_name": "Luka (Fallback)",
            "sub_agent_icon": "🤖",
            "enabled_tools": ["knowledge_base"],
            "knowledge_bases": [f"user-kb-{state['user_id']}"],
            "system_prompt_content": "You are a helpful AI assistant.",
            "llm_provider": "ollama",
            "llm_model": "llama3.2",
            "llm_temperature": 0.7,
            "llm_max_tokens": 2000,
            "llm_streaming": True,
        }


def create_graph():
    """Create LangGraph agent graph with sub-agent support."""

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("suggestions", suggestions_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "suggestions": "suggestions",
        }
    )

    # Tools -> agent (loop back for additional tool calls or final response)
    workflow.add_edge("tools", "agent")

    # Suggestions -> END
    workflow.add_edge("suggestions", END)

    # Compile with checkpointer
    # Note: In production, use RedisSaver instead of MemorySaver
    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)

    return graph


# Export
__all__ = ["create_graph", "hydrate_state_with_sub_agent"]
```

#### 1.4 Update nodes.py (agent_node)

```python
# luka_agent/nodes.py (updated agent_node)

async def agent_node(state: AgentState) -> dict:
    """Main agent node with sub-agent system prompt support."""
    from langchain_ollama import ChatOllama
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage
    from luka_agent.tools import create_tools_for_user
    from luka_agent.graph import hydrate_state_with_sub_agent

    logger.info(f"🤖 Agent node processing for user {state['user_id']}")

    # Check if state needs hydration (first run or agent switch)
    if "system_prompt_content" not in state or not state.get("system_prompt_content"):
        logger.info("🔄 State not hydrated, loading sub-agent config")
        hydration_updates = hydrate_state_with_sub_agent(state)
        # Merge updates into state (simulate state update)
        state = {**state, **hydration_updates}

    # Create tools for this sub-agent
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
    temperature = state.get("llm_temperature", 0.7)

    if llm_provider == "ollama":
        from luka_bot.core.config import settings
        ollama_url = settings.OLLAMA_URL.rstrip("/v1").rstrip("/")
        llm = ChatOllama(
            model=llm_model,
            base_url=ollama_url,
            temperature=temperature,
        )
    elif llm_provider == "openai":
        llm = ChatOpenAI(
            model=llm_model,
            temperature=temperature,
        )
    else:
        logger.error(f"Unknown LLM provider: {llm_provider}, falling back to ollama")
        from luka_bot.core.config import settings
        ollama_url = settings.OLLAMA_URL.rstrip("/v1").rstrip("/")
        llm = ChatOllama(
            model="llama3.2",
            base_url=ollama_url,
            temperature=0.7,
        )

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Build system message from sub-agent prompt
    system_prompt = state.get("system_prompt_content", "You are a helpful AI assistant.")
    system_message = SystemMessage(content=system_prompt)

    # Invoke LLM with system prompt + conversation history
    messages = [system_message] + state["messages"]

    logger.info(f"🧠 Invoking LLM: {llm_provider}/{llm_model} with {len(tools)} tools")
    logger.debug(f"   System prompt length: {len(system_prompt)} chars")

    response = await llm_with_tools.ainvoke(messages)

    # Determine next action
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
```

### Phase 2: Default Sub-Agents (Week 1-2)

#### 2.1 Create general_luka Sub-Agent

```yaml
# luka_agent/sub_agents/general_luka/config.yaml

agent:
  metadata:
    id: "general_luka"
    name: "Luka"
    title: "General AI Assistant"
    icon: "🤖"
    version: "1.0.0"
    description: "General-purpose AI assistant for conversation, knowledge search, and task management"

  persona:
    role: "Helpful AI Assistant + Task Manager + Knowledge Navigator"
    identity: |
      You are Luka, a versatile AI assistant integrated into Telegram and web platforms.

      You help users with:
      - Natural conversation and answering questions
      - Searching their personal knowledge base (indexed messages and documents)
      - Finding and watching YouTube videos
      - Discovering and launching specialized sub-agents for specific tasks
      - General information and assistance

    communication_style: "Friendly, concise, and professional. Use emojis sparingly for clarity."

    principles:
      - "Be concise and respectful of user's time"
      - "Ask 1-2 clarifying questions when unclear, don't make assumptions"
      - "Use tools when they provide better answers than your knowledge"
      - "Help users discover specialized sub-agents for complex tasks"
      - "Always cite sources when using knowledge base search"

  menu: []  # Not used in luka_agent

luka_extensions:
  system_prompt:
    base: "sub_agents/general_luka/system_prompt.md"
    language_variants:
      en: "sub_agents/general_luka/prompts/en.md"
      ru: "sub_agents/general_luka/prompts/ru.md"
    template_vars:
      agent_name: "{metadata.name}"
      user_name: "{user.name}"
      platform: "{state.platform}"
      language: "{state.language}"

  enabled_tools:
    - "knowledge_base"
    - "sub_agent"      # Discovery: get_available, get_details, start
    - "youtube"
    - "support"

  knowledge_bases:
    - "user-kb-{user_id}"

  llm_config:
    provider: "ollama"
    model: "llama3.2"
    temperature: 0.7
    max_tokens: 2000
    streaming: true

  capabilities:
    data_access:
      allowed_kb_patterns:
        - "user-kb-*"
        - "public-*"
      forbidden_kb_patterns:
        - "admin-*"
        - "crypto-tweets"  # Use crypto_analyst for this

    features:
      can_create_threads: true
      can_execute_workflows: true
      can_search_external: false
      can_modify_user_data: false

  intent_triggers: []  # Default agent, no auto-switch
```

```markdown
<!-- luka_agent/sub_agents/general_luka/system_prompt.md -->

# System Prompt for {agent_name}

You are **{agent_name}**, a helpful AI assistant.

## Your Role

{persona.identity}

## Communication Style

{persona.communication_style}

## Core Principles

1. **Conciseness:** Be brief and to the point. Users are busy.
2. **Clarity:** Ask 1-2 specific clarifying questions when needed.
3. **Tool Usage:** Use tools when they provide better answers than your knowledge.
4. **Helpfulness:** Guide users to specialized sub-agents for complex tasks.
5. **Citations:** Always cite sources when using knowledge base search.

## Available Tools

### 🔍 search_knowledge_base

Search your personal knowledge base of indexed messages and documents.

**When to use:**
- User asks about past conversations: "What did I say about X?"
- User wants to find specific information from their history
- User asks for a summary of recent topics

**When NOT to use:**
- Questions about THIS conversation (use conversation history)
- General knowledge questions (use your training)

**Usage:**
```
User: "Find my notes about the blockchain meeting"
→ search_knowledge_base(query="blockchain meeting", date_from="30d")
```

**Critical Rules:**
- ALWAYS cite the source (date, original message snippet)
- Check conversation history FIRST for very recent topics
- Use KB search for historical or stored information

---

### 🎥 get_youtube_transcript

Fetch and analyze transcripts from YouTube videos.

**When to use:**
- User shares a YouTube link
- User asks to summarize a video
- User wants to extract specific information from a video

**Usage:**
```
User: "Summarize this video: https://youtube.com/watch?v=abc123"
→ get_youtube_transcript(video_url="https://youtube.com/watch?v=abc123", language="{language}")
```

**Tips:**
- Always confirm the video URL before calling
- Offer to find specific parts if the transcript is very long

---

### 🤖 Sub-Agent Discovery Tools

Tools for discovering and launching specialized sub-agents.

**Available Tools:**
- `get_available_sub_agents()` - List all specialized agents
- `get_sub_agent_details(domain)` - Get info about a specific agent
- `start_sub_agent(domain)` - Launch a specialized agent (switches the conversation)

**When to use:**
- User asks about capabilities you don't have
- User mentions topics that might have specialized agents:
  - Crypto/blockchain → crypto_analyst
  - Trip planning → trip_planner
  - DeFi education → defi_educator
- You're unsure if a specialized agent exists for a topic

**Usage Flow:**
```
User: "Can you help me plan a trip to Paris?"

Step 1: Check available sub-agents
→ get_available_sub_agents()

Step 2: If trip_planner found, inform user
"I found a specialized Trip Planner agent that can help with:
- Interactive route planning
- POI suggestions with ratings
- Day-by-day itineraries

Would you like me to switch to the Trip Planner? (Just say 'yes')"

Step 3: If user confirms, switch
→ start_sub_agent(domain="trip_planner")
```

**Critical:**
- ALWAYS ask user permission before switching agents
- Explain what the specialized agent can do
- Be transparent: "I'm switching you to [Agent Name]..."

---

### 🛠️ get_support_info

Get help and support resources.

**When to use:**
- User asks how to use features
- User reports issues or bugs
- User needs help with commands

**Usage:**
```
User: "How do I create a new thread?"
→ get_support_info(question="how to create thread")
```

---

## Example Interactions

### Example 1: Knowledge Base Search

**User:** "What did I say about the Q4 planning meeting?"

**Good Response:**
```
Let me search your conversation history...

[Calls: search_knowledge_base(query="Q4 planning meeting", date_from="30d")]

I found 2 mentions of the Q4 planning meeting:

1. **November 12** - You shared the agenda with 5 key topics
2. **November 14** - You mentioned rescheduling it to Nov 20

Which one were you referring to?
```

---

### Example 2: Discovering Sub-Agents

**User:** "I want to learn about DeFi protocols"

**Good Response:**
```
Let me check if we have a specialized agent for DeFi...

[Calls: get_available_sub_agents()]

Great! I found a **DeFi Educator** agent that provides:
- Interactive DeFi learning modules
- Protocol comparisons
- Risk assessments
- Step-by-step guides

Would you like me to switch to the DeFi Educator? It's better suited for in-depth DeFi education.

(Just say "yes" or "switch to defi educator")
```

**User:** "Yes"

**Good Response:**
```
Switching to DeFi Educator... 🎓

[Calls: start_sub_agent(domain="defi_educator")]

[DeFi Educator takes over the conversation]
```

---

### Example 3: YouTube Summary

**User:** "Summarize this: https://youtube.com/watch?v=xyz789"

**Good Response:**
```
I'll fetch the transcript and summarize it for you...

[Calls: get_youtube_transcript(video_url="https://youtube.com/watch?v=xyz789", language="{language}")]

**Video Summary:**

[Provide concise summary based on transcript]

Key Points:
- Point 1
- Point 2
- Point 3

Would you like me to elaborate on any specific part?
```

---

## Platform Context

- **Platform:** {platform}
- **User:** {user_name}
- **Language:** {language}

**Language Rule:** The user prefers {language}. Always respond in {language} unless explicitly asked otherwise.

---

## Final Reminders

1. **Thread Context:** Each thread has its own conversation history. Always consider the current thread.

2. **Conversation History vs KB:**
   - Recent topics (last few messages) → Use conversation history
   - Historical topics, stored notes → Use knowledge_base tool

3. **Specialized Agents:** When users need specialized help (crypto, trips, etc.), proactively suggest switching to the appropriate sub-agent.

4. **Transparency:** Always be clear about what you're doing:
   - "Let me search your knowledge base..."
   - "I'm fetching the video transcript..."
   - "I'm switching you to the Trip Planner agent..."

5. **Conciseness:** Keep responses short and actionable. Users can always ask for more details.

You are **{agent_name}**. Be helpful, clear, and efficient. 🤖
```

#### 2.2 Create crypto_analyst Sub-Agent (Example)

```yaml
# luka_agent/sub_agents/crypto_analyst/config.yaml

agent:
  metadata:
    id: "crypto_analyst"
    name: "Crypto Analyst"
    title: "Crypto Market Analyst + On-Chain Expert"
    icon: "📈"
    version: "1.0.0"
    description: "Specialized crypto market analyst with real-time data and crypto Twitter insights"

  persona:
    role: "Crypto Market Expert + On-Chain Analyst + DeFi Researcher"
    identity: |
      You are a crypto market analyst with 15+ years of experience in blockchain technology,
      DeFi protocols, and on-chain analysis. You help users understand crypto markets,
      analyze tokens, track sentiment, and make informed decisions.

    communication_style: "Data-driven, concise, always cite sources. Serious but approachable."

    principles:
      - "Always cite data sources (on-chain, exchange, social)"
      - "Explain volatility and risk context"
      - "Never give financial advice, only analysis"
      - "Update information is time-sensitive - always check timestamps"
      - "Warn about scams and high-risk tokens"

  menu: []

luka_extensions:
  system_prompt:
    base: "sub_agents/crypto_analyst/system_prompt.md"
    language_variants:
      en: "sub_agents/crypto_analyst/prompts/en.md"
      ru: "sub_agents/crypto_analyst/prompts/ru.md"

  enabled_tools:
    - "knowledge_base"    # Now searches crypto-tweets!
    - "token_info"
    - "get_dex_stats"
    - "chart_generator"
    # NOT: swap_executor (keep analysis separate from execution)

  knowledge_bases:
    - "crypto-tweets"     # Crypto Twitter index
    - "defi-protocols"    # DeFi docs
    - "user-kb-{user_id}" # User's crypto notes

  llm_config:
    provider: "openai"
    model: "gpt-4o"       # Use more capable model for analysis
    temperature: 0.7
    max_tokens: 2000
    streaming: true

  capabilities:
    data_access:
      allowed_kb_patterns:
        - "crypto-tweets"
        - "defi-protocols"
        - "user-kb-*"
      forbidden_kb_patterns:
        - "admin-*"

    features:
      can_create_threads: true
      can_execute_workflows: false
      can_search_external: true   # Crypto Twitter
      can_modify_user_data: false

  intent_triggers:
    - "crypto"
    - "token"
    - "blockchain"
    - "defi"
    - "what is [crypto project]"
    - "price of"
```

### Phase 3: Configuration Integration (Week 2)

#### 3.1 Update luka_bot/core/config.py

```python
# luka_bot/core/config.py

class LukaSettings(EnvBaseSettings):
    """Luka bot identity and personality settings."""

    # ... existing fields ...

    # Sub-Agent Configuration (NEW)
    # Default sub-agent for Telegram bot (can be different per deployment)
    DEFAULT_SUB_AGENT: str = "general_luka"

    # ... rest of existing config ...
```

#### 3.2 Update ag_ui_gateway/config/ (NEW)

```python
# ag_ui_gateway/config/__init__.py

from pydantic_settings import BaseSettings


class AGUIGatewaySettings(BaseSettings):
    """AG-UI Gateway specific settings."""

    # Sub-Agent Configuration
    # Default sub-agent for web users
    DEFAULT_SUB_AGENT: str = "web_assistant"  # Different from Telegram!

    # ... other AG-UI settings ...


agui_settings = AGUIGatewaySettings()
```

#### 3.3 Update State Initialization in Adapters

```python
# ag_ui_gateway/adapters/llm_adapter.py (excerpt)

from ag_ui_gateway.config import agui_settings

async def create_agent_session(user_id: int, session_id: str, ...):
    """Create new agent session with default sub-agent."""

    initial_state = {
        "user_id": user_id,
        "thread_id": f"web_{session_id}",
        "sub_agent_id": agui_settings.DEFAULT_SUB_AGENT,  # ← Use web default
        "platform": "web",
        "language": user_language,
        "messages": [],
        # ... rest will be hydrated by sub-agent loader
    }

    return initial_state
```

```python
# luka_bot/handlers/chat.py (excerpt)

from luka_bot.core.config import settings

async def handle_private_message(message: Message, ...):
    """Handle private message with default sub-agent."""

    initial_state = {
        "user_id": message.from_user.id,
        "thread_id": f"user_{message.from_user.id}",
        "sub_agent_id": settings.DEFAULT_SUB_AGENT,  # ← Use Telegram default
        "platform": "telegram",
        "language": user.language,
        "messages": [],
        # ... rest will be hydrated
    }

    # Invoke luka_agent graph
    result = await graph.ainvoke(initial_state, config={"configurable": {"thread_id": ...}})
```

### Phase 4: Agent Switching (Week 2-3)

#### 4.1 Create Agent Switch Tool

```python
# luka_agent/tools/agent_switch.py

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from loguru import logger


class SwitchSubAgentInput(BaseModel):
    """Input for switching sub-agent."""
    domain: str = Field(..., description="Sub-agent domain/ID to switch to (e.g., 'crypto_analyst')")


async def switch_sub_agent_impl(domain: str) -> str:
    """Switch to a different sub-agent.

    NOTE: This is a special tool that triggers state update.
    The actual switch happens in the graph via state update.

    Args:
        domain: Sub-agent ID to switch to

    Returns:
        Confirmation message
    """
    from luka_agent.sub_agents.loader import get_sub_agent_loader

    try:
        # Validate sub-agent exists
        loader = get_sub_agent_loader()
        config = loader.load(domain)

        # Return special marker that tells graph to hydrate with new agent
        return f"AGENT_SWITCH:{domain}:{config.name}"

    except Exception as e:
        logger.error(f"Failed to switch to sub-agent '{domain}': {e}")
        available = loader.list_available()
        return f"Error: Sub-agent '{domain}' not found. Available: {', '.join(available)}"


def create_switch_sub_agent_tool() -> StructuredTool:
    """Create sub-agent switching tool."""
    return StructuredTool.from_function(
        func=switch_sub_agent_impl,
        name="switch_sub_agent",
        description="Switch to a different specialized sub-agent (e.g., crypto_analyst, trip_planner)",
        args_schema=SwitchSubAgentInput,
    )
```

#### 4.2 Handle Agent Switch in Graph

```python
# luka_agent/nodes.py (update agent_node to handle switch)

async def agent_node(state: AgentState) -> dict:
    """Main agent node with sub-agent switching support."""

    # ... existing code ...

    response = await llm_with_tools.ainvoke(messages)

    # Check if response contains agent switch marker
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call.get("name") == "switch_sub_agent":
                # Extract new sub_agent_id from tool call
                new_agent_id = tool_call["args"]["domain"]

                logger.info(f"🔄 Agent switch requested: {state['sub_agent_id']} → {new_agent_id}")

                # Trigger state hydration with new agent
                from luka_agent.graph import hydrate_state_with_sub_agent

                # Create temporary state for hydration
                temp_state = {**state, "sub_agent_id": new_agent_id}
                hydration_updates = hydrate_state_with_sub_agent(temp_state)

                # Return state updates + switch confirmation message
                switch_message = AIMessage(
                    content=f"✅ Switched to {hydration_updates['sub_agent_name']} {hydration_updates['sub_agent_icon']}"
                )

                return {
                    **hydration_updates,  # New agent config
                    "messages": [switch_message],
                    "next_action": "end",  # End this turn, new agent takes over next turn
                }

    # ... existing next_action logic ...
```

### Phase 5: CLI Testing Tool (Week 3)

```python
# luka_agent/cli.py (NEW)

import asyncio
import sys
from pathlib import Path
from loguru import logger
from luka_agent.graph import create_graph, hydrate_state_with_sub_agent


async def test_sub_agent(sub_agent_id: str, message: str):
    """Test a sub-agent with a message.

    Usage:
        python -m luka_agent.cli test general_luka "Hello, who are you?"
    """
    print(f"\n🧪 Testing sub-agent: {sub_agent_id}")
    print(f"📝 Message: {message}\n")

    # Create initial state
    initial_state = {
        "user_id": 0,
        "thread_id": "cli_test",
        "sub_agent_id": sub_agent_id,
        "platform": "cli",
        "language": "en",
        "messages": [],
    }

    # Hydrate with sub-agent
    print("🔄 Loading sub-agent configuration...")
    updates = hydrate_state_with_sub_agent(initial_state)
    state = {**initial_state, **updates}

    print(f"✅ Loaded: {state['sub_agent_name']} {state['sub_agent_icon']}")
    print(f"🔧 Tools: {', '.join(state['enabled_tools'])}")
    print(f"📚 KBs: {', '.join(state['knowledge_bases'])}")
    print(f"🧠 LLM: {state['llm_provider']}/{state['llm_model']}\n")

    # Add user message
    from langchain_core.messages import HumanMessage
    state["messages"].append(HumanMessage(content=message))

    # Create and invoke graph
    print("🚀 Invoking agent graph...\n")
    graph = create_graph()

    result = await graph.ainvoke(state, config={"configurable": {"thread_id": "cli_test"}})

    # Print response
    print("\n💬 Agent Response:\n")
    last_message = result["messages"][-1]
    print(last_message.content)

    # Print tool calls if any
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print("\n🔧 Tool Calls:")
        for tool_call in last_message.tool_calls:
            print(f"  - {tool_call['name']}({tool_call['args']})")

    print("\n✅ Test complete\n")


async def validate_sub_agent(sub_agent_id: str):
    """Validate a sub-agent configuration.

    Usage:
        python -m luka_agent.cli validate general_luka
    """
    print(f"\n🔍 Validating sub-agent: {sub_agent_id}\n")

    from luka_agent.sub_agents.loader import get_sub_agent_loader

    try:
        loader = get_sub_agent_loader()
        config = loader.load(sub_agent_id)

        print(f"✅ Config loaded successfully")
        print(f"   ID: {config.id}")
        print(f"   Name: {config.name}")
        print(f"   Icon: {config.icon}")
        print(f"   Tools: {', '.join(config.enabled_tools)}")
        print(f"   KBs: {', '.join(config.knowledge_bases)}")
        print(f"   LLM: {config.llm_config.get('provider')}/{config.llm_config.get('model')}")

        # Try loading system prompt
        print(f"\n📄 Loading system prompt...")
        prompt = loader.load_system_prompt(
            config,
            language="en",
            template_vars={"user_name": "TestUser", "platform": "cli", "language": "en"}
        )
        print(f"✅ System prompt loaded ({len(prompt)} chars)")

        print(f"\n✅ Validation passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Validation failed: {e}\n")
        logger.exception("Validation error")
        return False


async def list_sub_agents():
    """List all available sub-agents.

    Usage:
        python -m luka_agent.cli list
    """
    print("\n📋 Available Sub-Agents:\n")

    from luka_agent.sub_agents.loader import get_sub_agent_loader

    loader = get_sub_agent_loader()
    sub_agents = loader.list_available()

    if not sub_agents:
        print("No sub-agents found.\n")
        return

    for sub_agent_id in sub_agents:
        try:
            config = loader.load(sub_agent_id)
            print(f"  {config.icon} {config.name}")
            print(f"     ID: {config.id}")
            print(f"     Description: {config.metadata.get('description', 'N/A')}")
            print(f"     Tools: {len(config.enabled_tools)}")
            print()
        except Exception as e:
            print(f"  ❌ {sub_agent_id} (failed to load: {e})\n")

    print(f"Total: {len(sub_agents)} sub-agents\n")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("""
Usage:
  python -m luka_agent.cli list
  python -m luka_agent.cli validate <sub_agent_id>
  python -m luka_agent.cli test <sub_agent_id> <message>

Examples:
  python -m luka_agent.cli list
  python -m luka_agent.cli validate general_luka
  python -m luka_agent.cli test general_luka "Hello, who are you?"
  python -m luka_agent.cli test crypto_analyst "What's the price of SOL?"
        """)
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        asyncio.run(list_sub_agents())
    elif command == "validate":
        if len(sys.argv) < 3:
            print("Error: Missing sub_agent_id")
            sys.exit(1)
        sub_agent_id = sys.argv[2]
        asyncio.run(validate_sub_agent(sub_agent_id))
    elif command == "test":
        if len(sys.argv) < 4:
            print("Error: Missing sub_agent_id or message")
            sys.exit(1)
        sub_agent_id = sys.argv[2]
        message = " ".join(sys.argv[3:])
        asyncio.run(test_sub_agent(sub_agent_id, message))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Migration Path

### Week 1: Foundation
- ✅ Create `SubAgentLoader` class
- ✅ Update `AgentState` with sub-agent fields
- ✅ Add `hydrate_state_with_sub_agent()` to graph.py
- ✅ Update `agent_node()` to use sub-agent system prompts
- ✅ Create `general_luka` sub-agent (BMAD-compatible)
- ✅ Test with CLI tool

### Week 2: Configuration & Integration
- ✅ Add `DEFAULT_SUB_AGENT` to luka_bot config
- ✅ Add `DEFAULT_SUB_AGENT` to ag_ui_gateway config
- ✅ Update state initialization in Telegram handlers
- ✅ Update state initialization in AG-UI adapters
- ✅ Create `crypto_analyst` sub-agent (example)
- ✅ Create `web_assistant` sub-agent for AG-UI

### Week 3: Agent Switching
- ✅ Create `switch_sub_agent` tool
- ✅ Update `agent_node()` to handle agent switches
- ✅ Update sub-agent tools to include `start_sub_agent`
- ✅ Test multi-agent conversations

### Week 4: Testing & Documentation
- ✅ Write unit tests for `SubAgentLoader`
- ✅ Write integration tests for agent switching
- ✅ Document sub-agent creation guide
- ✅ Create 2-3 more example sub-agents (trip_planner, defi_educator)

---

## Testing Strategy

### Unit Tests

```python
# tests/test_sub_agent_loader.py

from luka_agent.sub_agents.loader import SubAgentLoader, SubAgentConfig
import pytest


def test_load_general_luka():
    """Test loading general_luka sub-agent."""
    loader = SubAgentLoader()
    config = loader.load("general_luka")

    assert config.id == "general_luka"
    assert config.name == "Luka"
    assert config.icon == "🤖"
    assert "knowledge_base" in config.enabled_tools
    assert "user-kb-{user_id}" in config.knowledge_bases


def test_load_system_prompt():
    """Test loading and rendering system prompt."""
    loader = SubAgentLoader()
    config = loader.load("general_luka")

    prompt = loader.load_system_prompt(
        config,
        language="en",
        template_vars={"user_name": "Alice", "platform": "web", "language": "en"}
    )

    assert "Luka" in prompt
    assert "Alice" in prompt
    assert "web" in prompt


def test_resolve_knowledge_bases():
    """Test KB template resolution."""
    loader = SubAgentLoader()

    templates = ["user-kb-{user_id}", "crypto-tweets"]
    resolved = loader.resolve_knowledge_bases(templates, user_id=123)

    assert resolved == ["user-kb-123", "crypto-tweets"]


def test_validation_missing_fields():
    """Test validation catches missing fields."""
    loader = SubAgentLoader()

    with pytest.raises(ValueError, match="Missing 'agent' section"):
        loader._validate_config({}, "test_agent")
```

### Integration Tests

```python
# tests/test_agent_switching.py

from luka_agent.graph import create_graph, hydrate_state_with_sub_agent
from langchain_core.messages import HumanMessage
import pytest


@pytest.mark.asyncio
async def test_agent_switch_flow():
    """Test switching from general_luka to crypto_analyst."""

    # Start with general_luka
    initial_state = {
        "user_id": 1,
        "thread_id": "test_123",
        "sub_agent_id": "general_luka",
        "platform": "test",
        "language": "en",
        "messages": [HumanMessage(content="What's the price of SOL?")],
    }

    # Hydrate state
    updates = hydrate_state_with_sub_agent(initial_state)
    state = {**initial_state, **updates}

    assert state["sub_agent_name"] == "Luka"
    assert "knowledge_base" in state["enabled_tools"]

    # Simulate agent suggesting switch
    # (In real flow, agent would call get_available_sub_agents, then suggest)

    # User confirms switch
    state["messages"].append(HumanMessage(content="Switch to crypto analyst"))

    # Agent calls switch_sub_agent tool (simulated)
    new_state = {**state, "sub_agent_id": "crypto_analyst"}
    updates = hydrate_state_with_sub_agent(new_state)
    state = {**new_state, **updates}

    assert state["sub_agent_name"] == "Crypto Analyst"
    assert state["sub_agent_icon"] == "📈"
    assert "crypto-tweets" in state["knowledge_bases"]
```

### E2E CLI Tests

```bash
# Test sub-agent validation
python -m luka_agent.cli validate general_luka
python -m luka_agent.cli validate crypto_analyst

# Test sub-agent invocation
python -m luka_agent.cli test general_luka "Hello, who are you?"
python -m luka_agent.cli test crypto_analyst "What's the price of SOL?"

# List all sub-agents
python -m luka_agent.cli list
```

---

## Benefits of This Architecture

### Immediate Benefits
✅ **BMAD Compatibility:** Can run BMAD workflows as sub-agents with minimal modification
✅ **Separation of Concerns:** Agent personalities separate from execution engine
✅ **Flexibility:** Different defaults for Telegram vs Web
✅ **Maintainability:** Each agent is self-contained (config + prompts)
✅ **Testability:** Easy to test individual sub-agents in isolation

### Long-term Benefits
✅ **Extensibility:** Add new sub-agents without touching core code
✅ **Customization:** Different deployments can have different agent sets
✅ **Localization:** Language-specific prompts per sub-agent
✅ **Specialization:** Deep expertise per domain (crypto, trips, etc.)
✅ **User Choice:** Explicit agent switching empowers users

---

## Future Enhancements

### Phase 5 (Future): Hot Reload
- Watch sub_agents/ directory for changes
- Reload configs without restart
- Version management for A/B testing

### Phase 6 (Future): Agent Marketplace
- User-created sub-agents
- Community sharing
- Sub-agent templates

### Phase 7 (Future): Multi-Agent Collaboration
- BMAD-style "Party Mode"
- Multiple agents discuss a problem
- Agent handoffs with context transfer

---

## Appendix: File Tree

```
luka_agent/
├─ __init__.py
├─ cli.py                      # NEW: CLI testing tool
├─ graph.py                    # UPDATED: hydrate_state_with_sub_agent
├─ nodes.py                    # UPDATED: agent_node uses sub-agent prompts
├─ state.py                    # UPDATED: Added sub-agent fields
├─ tools/
│   ├─ __init__.py
│   ├─ knowledge_base.py
│   ├─ sub_agent.py           # UPDATED: Includes switch_sub_agent
│   └─ youtube.py
└─ sub_agents/                 # NEW: Sub-agent definitions
    ├─ __init__.py
    ├─ loader.py               # NEW: SubAgentLoader class
    │
    ├─ general_luka/           # NEW: Default sub-agent
    │   ├─ config.yaml
    │   ├─ system_prompt.md
    │   └─ prompts/
    │       ├─ en.md
    │       └─ ru.md
    │
    ├─ crypto_analyst/         # NEW: Example specialized agent
    │   ├─ config.yaml
    │   ├─ system_prompt.md
    │   └─ prompts/
    │       ├─ en.md
    │       └─ ru.md
    │
    ├─ trip_planner/           # NEW: Example specialized agent
    │   ├─ config.yaml
    │   └─ system_prompt.md
    │
    └─ web_assistant/          # NEW: Default for AG-UI
        ├─ config.yaml
        └─ system_prompt.md
```

---

## Conclusion

This architecture transforms `luka_agent` from a generic agent into a **runtime execution engine** that loads specialized BMAD-compatible sub-agents. Each sub-agent is fully self-contained with:

- ✅ BMAD-compatible YAML config
- ✅ Markdown system prompts with language variants
- ✅ Tool and KB configuration
- ✅ LLM provider settings
- ✅ Capability boundaries

**Key Design Decisions:**
- Dynamic agent switching with shared conversation history
- Default sub-agent per deployment (Telegram vs Web)
- Explicit user agent selection
- BMAD compatibility with Luka extensions
- No tool-level prompt injection (agents own full prompts)
- Validation on load, hot reload in future

**Result:** A flexible, maintainable, and extensible agent system that can support BMAD workflows while maintaining our existing LangGraph infrastructure.

---

**Document Status:** Final Architecture Design
**Author:** Claude Code + Evgeny
**Date:** November 18, 2025
**Next Steps:** Begin Phase 1 implementation
