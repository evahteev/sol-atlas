# Luka Agent - Unified LangGraph Architecture

**Agent-friendly instructions for understanding, using, and extending the unified platform-agnostic agent system.**

---

<objective>
Provide a unified, platform-agnostic LangGraph-based agent architecture that:
- Serves both Telegram (luka_bot) and Web (ag_ui_gateway) platforms identically
- Eliminates code duplication through single source of truth
- Enables systematic tool and sub-agent development
- Maintains state persistence via Redis checkpointing
- Follows factory pattern for user-scoped tool creation
</objective>

<context>
## What is luka_agent?

luka_agent is a standalone Python module that provides a unified conversational AI system using LangGraph.

### Problem It Solves

**Before luka_agent** (duplicated implementations):
- `luka_bot/langgraph/` - Telegram-specific graph with its own tools and state
- `ag_ui_gateway/agents/` - Web-specific graph with different tools and state
- **Issues**:
  - Feature parity problems (one platform gets feature, other doesn't)
  - Duplicate code maintenance (fix bug twice)
  - Testing overhead (test everything twice)
  - Inconsistent behavior across platforms

**After luka_agent** (unified architecture):
- `luka_agent/` - Single graph, single state, single tool set
- Platform adapters handle only rendering differences (keyboards vs buttons)
- **Benefits**:
  - Feature parity guaranteed (both platforms get all features)
  - Single source of truth (fix bug once)
  - Unified testing (test once, works everywhere)
  - Consistent user experience

### Architecture Overview

```
User Message
    ↓
Platform Adapter (Telegram/Web)
    ↓
luka_agent/graph.py (Unified StateGraph)
    ↓
    ┌─────────────────────────────────────┐
    │ Agent Node (LLM with tools)         │
    │   ↓                                 │
    │ Tool Node (Execute selected tools)  │
    │   ↓                                 │
    │ Suggestions Node (Generate prompts) │
    └─────────────────────────────────────┘
    ↓
Redis (State persistence via checkpointer)
    ↓
Platform Adapter (Render response)
    ↓
User receives response
```

### When to Use luka_agent

**Use luka_agent for**:
- Building conversational AI features for both Telegram and Web
- Creating tools that work across platforms
- Developing guided experiences (sub-agents) with multiple steps
- Managing conversation state with Redis persistence
- Systematic agent development with templates and patterns

**Don't use luka_agent for**:
- Platform-specific features (Telegram payments, Web-only UI)
- Non-conversational background tasks
- Simple REST API endpoints without conversation context
</context>

---

<requirements>
## Integration Requirements

### For Platforms Using luka_agent

**Essential**:
- [ ] **Python 3.11+**: Required for type hints and async support
- [ ] **Redis**: For state persistence via checkpointer
- [ ] **LangGraph**: Core graph execution engine
- [ ] **LangChain**: For StructuredTools
- [ ] **Service layer**: Provides external service access (Elasticsearch, APIs, etc.)

**Optional**:
- [ ] **Pydantic-AI**: If using Pydantic-AI agents (luka_bot does)
- [ ] **OpenAI/Anthropic SDKs**: For LLM providers
- [ ] **Elasticsearch**: If using knowledge base tool
- [ ] **YouTube Transcript API**: If using YouTube tool

### For Tools

- [ ] **LangChain StructuredTool**: All tools must be StructuredTools
- [ ] **Pydantic Input Schema**: Type-safe parameter validation
- [ ] **Async Implementation**: Tools must be async functions
- [ ] **Platform Agnostic**: No Telegram/Web-specific code
- [ ] **Runtime Dependency Injection**: Import services inside implementation

### For Sub-Agents

- [ ] **config.yaml**: YAML configuration with metadata, persona, steps
- [ ] **YAML Format**: Valid YAML syntax
- [ ] **Sequential Steps**: At least 1 conversational step
- [ ] **Platform Agnostic**: No platform-specific references in instructions
- [ ] **README.md**: Documentation (recommended)

### For State Management

- [ ] **AgentState TypedDict**: Use unified state schema
- [ ] **Platform Field**: Specify "telegram" or "web"
- [ ] **Thread ID**: Unique conversation identifier
- [ ] **User ID**: User identifier for context
</requirements>

---

<constraints>
## Design Constraints with WHY Explanations

### Platform Constraints

**DON'T use platform-specific code in luka_agent**
- WHY: Must work identically on Telegram and Web
- DO: Use platform field in state to detect platform
- DON'T: Import aiogram or FastAPI in luka_agent code

**DON'T handle rendering in luka_agent**
- WHY: Platform adapters handle display differences
- DO: Return structured data (tools, suggestions, messages)
- DON'T: Format markdown for specific platform

### Tool Constraints

**ALWAYS use LangChain StructuredTool**
- WHY: LangGraph native support, Pydantic validation, consistent interface
- DO: Create tools with `StructuredTool.from_function()`
- DON'T: Use plain functions or Pydantic-AI tools directly

**ALWAYS import services at runtime (inside implementation)**
- WHY: Avoids circular imports, enables testing, allows service substitution
- DO: `from luka_bot.services.x import get_x_service` inside function
- DON'T: Import services at module level

**ALWAYS use factory pattern for user context**
- WHY: Tools need user_id, thread_id but shouldn't expose in LLM interface
- DO: `create_my_tool(user_id, thread_id, language)` returns bound tool
- DON'T: Include user_id, thread_id in tool's input schema

**ALWAYS handle service unavailability gracefully**
- WHY: Services can be down, disabled, or misconfigured
- DO: Return user-friendly error messages with fix instructions
- DON'T: Raise exceptions or return technical error messages

### State Constraints

**ALWAYS use TypedDict (not Pydantic BaseModel)**
- WHY: LangGraph requires TypedDict for state
- DO: Define fields with type annotations
- DON'T: Use Pydantic BaseModel for AgentState

**ALWAYS include platform field**
- WHY: Platform adapters need to know how to render
- DO: Set platform = "telegram" or "web"
- DON'T: Assume one platform or omit field

**ALWAYS use add_messages reducer for messages**
- WHY: LangGraph's standard pattern for message accumulation
- DO: `messages: Annotated[Sequence[BaseMessage], add_messages]`
- DON'T: Manually append to messages list

### Graph Constraints

**ALWAYS use Redis checkpointer for production**
- WHY: State persistence across bot restarts, handles concurrent users
- DO: Initialize checkpointer in graph.py with Redis connection
- DON'T: Use MemorySaver in production (only for testing)

**ALWAYS use thread_id in config**
- WHY: Isolates conversation state per user/thread
- DO: `config = {"configurable": {"thread_id": "thread_123"}}`
- DON'T: Share thread_id across users

### Dependency Constraints

**DON'T depend on luka_bot at module level**
- WHY: luka_agent should be standalone and reusable
- DO: Import luka_bot services at runtime inside tool implementations
- DON'T: Import luka_bot in __init__.py or at module level

**DON'T create circular dependencies**
- WHY: Makes testing difficult, breaks imports
- DO: Use runtime imports and dependency injection
- DON'T: Import luka_agent from luka_bot services
</constraints>

---

<implementation>
## Directory Structure

```
luka_agent/
├── __init__.py              # Public API exports
├── README.md                # This file (architecture guide)
├── CONFIG.md                # Configuration strategy
├── DEPENDENCY_CHECKING.md   # Error handling patterns
│
├── state.py                 # AgentState TypedDict
├── checkpointer.py          # Redis checkpointer singleton
├── nodes.py                 # Graph nodes (agent, tools, suggestions)
├── graph.py                 # Graph builder with Redis persistence
│
├── tools/                   # LangChain StructuredTools
│   ├── __init__.py          # Tool factory (create_tools_for_user)
│   ├── README.md            # Tools development guide
│   ├── TEMPLATE.md          # Tool template with all patterns
│   ├── meta-prompting/      # Meta-prompting system for tools
│   │   ├── README.md
│   │   ├── create-tool-prompt.md
│   │   └── run-tool-prompt.md
│   ├── knowledge_base.py    # KB search tool
│   ├── sub_agent.py         # 5 sub-agent tools
│   ├── youtube.py           # YouTube transcript tool
│   └── [TODO] support.py, menu.py, twitter.py, tripplanner/
│
├── sub_agents/              # Sub-agent configurations (YAML)
│   ├── README.md            # Sub-agents development guide
│   ├── README_TEMPLATE.md   # Template for sub-agent READMEs
│   ├── TEMPLATE/            # Complete sub-agent template
│   │   ├── config.yaml
│   │   └── README.md
│   ├── sol_atlas_onboarding/
│   │   ├── config.yaml
│   │   └── README.md
│   ├── trip_planner/
│   │   ├── config.yaml
│   │   └── README.md
│   └── defi_onboarding/
│       ├── config.yaml
│       └── README.md
│
└── tests/                   # Test suite
    ├── __init__.py
    └── test_sub_agent_tools.py
```

## Using luka_agent

### Step 1: Create Tools for User

```python
from luka_agent import create_tools_for_user

# Create user-scoped tools
tools = create_tools_for_user(
    user_id=123,
    thread_id="thread_123",
    knowledge_bases=["tg-kb-user-123"],  # User's KB indexes
    enabled_tools=["knowledge_base", "sub_agent", "youtube"],
    platform="telegram",  # or "web"
    language="en"
)

# Result: List of LangChain StructuredTools bound to this user
# Tools automatically have user_id, thread_id, language in closure
```

### Step 2: Get Unified Graph

```python
from luka_agent import get_unified_agent_graph

# Get compiled graph (singleton, cached)
graph = await get_unified_agent_graph()

# Graph uses Redis checkpointer for state persistence
# Automatically loads/saves state based on thread_id
```

### Step 3: Create Initial State

```python
from luka_agent import create_initial_state

# Create state for new conversation
initial_state = create_initial_state(
    user_id=123,
    thread_id="thread_123",
    language="en",
    platform="telegram",  # or "web"
    knowledge_bases=["tg-kb-user-123"],
    enabled_tools=["knowledge_base", "sub_agent"],
)

# State includes:
# - messages: []
# - platform: "telegram"
# - user_id: 123
# - thread_id: "thread_123"
# - language: "en"
# - knowledge_bases: ["tg-kb-user-123"]
# - enabled_tools: ["knowledge_base", "sub_agent"]
```

### Step 4: Invoke Graph

```python
# Configure with thread_id for state isolation
config = {"configurable": {"thread_id": "thread_123"}}

# Invoke graph with user message
result = await graph.ainvoke(
    {"messages": [HumanMessage(content="Hello!")]},
    config=config
)

# Result contains:
# - messages: All conversation messages (history + new)
# - suggestions: Optional quick prompts for user
# - Other state fields
```

### Step 5: Stream Responses (Optional)

```python
# Stream for real-time updates
async for event in graph.astream_events(
    {"messages": [HumanMessage(content="Search my notes")]},
    config=config,
    version="v2"
):
    # Handle streaming events
    if event["event"] == "on_chat_model_stream":
        # LLM token
        print(event["data"]["chunk"].content, end="", flush=True)
    elif event["event"] == "on_tool_start":
        # Tool started
        print(f"\n🔧 Using tool: {event['name']}")
    elif event["event"] == "on_tool_end":
        # Tool completed
        print(f"✅ Tool result: {event['data']['output']}")
```

## Creating a New Tool

**See `luka_agent/tools/README.md` for complete guide and `luka_agent/tools/TEMPLATE.md` for template.**

### Quick Example

```python
# luka_agent/tools/my_tool.py

from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field


# =============================================================================
# Input Schema
# =============================================================================

class MyToolInput(BaseModel):
    """Input schema for my_tool."""

    query: str = Field(
        ...,
        description="What to search for (be specific)"
    )


# =============================================================================
# Implementation
# =============================================================================

async def my_tool_impl(
    query: str,
    user_id: int,
    thread_id: str,
    language: str,
) -> str:
    """Implementation of my_tool.

    Args:
        query: Search query
        user_id: User ID for context
        thread_id: Thread ID for context
        language: User's preferred language

    Returns:
        Result message or user-friendly error message
    """
    # Level 1: Check configuration (if needed)
    try:
        from luka_bot.core.config import settings
    except ImportError:
        logger.error("Unable to import settings")
        return "This feature is not configured. Please contact support."

    # Level 2: Import service at runtime
    try:
        from luka_bot.services.my_service import get_my_service
    except ImportError as e:
        logger.error(f"Unable to import service: {e}")
        return "Service is not available. Please contact support."

    # Level 3: Execute with error handling
    try:
        service = get_my_service()
        result = await service.do_something(query)

        logger.debug(f"Tool 'my_tool' executed for user {user_id}")
        return result

    except Exception as e:
        logger.error(f"Error in 'my_tool' for user {user_id}: {e}")
        return "An error occurred. Please try again."


# =============================================================================
# Factory
# =============================================================================

def create_my_tool(
    user_id: int,
    thread_id: str,
    language: str,
) -> StructuredTool:
    """Create my_tool with user context bound.

    Args:
        user_id: User ID
        thread_id: Thread ID
        language: User's preferred language

    Returns:
        LangChain StructuredTool instance
    """
    return StructuredTool.from_function(
        name="my_tool",
        description="Does something useful. Use when user asks to...",
        func=lambda query: my_tool_impl(query, user_id, thread_id, language),
        coroutine=lambda query: my_tool_impl(query, user_id, thread_id, language),
        args_schema=MyToolInput,
    )


__all__ = ["create_my_tool"]
```

### Register Tool

```python
# luka_agent/tools/__init__.py

from luka_agent.tools.my_tool import create_my_tool

# Add to tool_factories dict
tool_factories = {
    # ... existing tools ...
    "my_tool": lambda: create_my_tool(user_id, thread_id, language),
}
```

## Creating a New Sub-Agent

**See `luka_agent/sub_agents/README.md` for complete guide and `luka_agent/sub_agents/TEMPLATE/` for template.**

### Quick Steps

```bash
# 1. Copy template
cp -r luka_agent/sub_agents/TEMPLATE luka_agent/sub_agents/my_sub_agent

# 2. Edit config.yaml
cd luka_agent/sub_agents/my_sub_agent
# Replace all [PLACEHOLDERS]

# 3. Customize README.md
# Use README_TEMPLATE.md as guide

# 4. Test discovery
python -m luka_bot
# Check: tail -f logs/luka_bot.log | grep workflow

# 5. Test execution
# Use execute_sub_agent tool with domain="my_sub_agent"
```

### Minimal config.yaml

```yaml
workflow:
  metadata:
    domain: "my_sub_agent"
    name: "My Sub-Agent"
    version: "1.0.0"
    description: "Helps users accomplish X"

  persona:
    role: "Expert in X"
    style: "Warm and consultative"
    expertise_areas:
      - "Domain knowledge 1"
    behavior_rules:
      - "ALWAYS do X to achieve Y"
      - "NEVER do Z because it causes W"

  tool_chain:
    steps:
      - id: "step_1"
        name: "First Step"
        type: "conversational"
        instruction: |
          Ask user: "What brings you here?"

          If they say X: Do Y
          If they say Z: Do W

          Capture answer in 'user_goal' output.

        outputs:
          - name: "user_goal"
            type: "string"
            description: "What user wants"

        suggestions:
          - "Option 1"
          - "Option 2"
```
</implementation>

---

<output>
## Public API

### Exports from luka_agent/__init__.py

```python
from luka_agent import (
    # Graph
    get_unified_agent_graph,  # Get compiled StateGraph

    # State
    AgentState,               # TypedDict for state schema
    create_initial_state,     # Create initial state dict

    # Tools
    create_tools_for_user,    # Create user-scoped tools

    # Checkpointer
    get_redis_checkpointer,   # Get Redis checkpointer singleton
)
```

### AgentState Schema

```python
from typing import TypedDict, Sequence, Literal, Annotated, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict, total=False):
    """Unified state for agent graph."""

    # REQUIRED fields
    messages: Annotated[Sequence[BaseMessage], add_messages]
    platform: Literal["web", "telegram"]
    user_id: int
    thread_id: str
    language: str

    # Tool configuration
    knowledge_bases: list[str]
    enabled_tools: list[str]

    # Optional UI
    suggestions: Optional[list[str]]

    # Optional sub-agent hints
    workflow_hint: Optional[str]

    # Platform-specific (Web only)
    is_guest: Optional[bool]
    ui_context: Optional[dict]

    # CopilotKit integration (Web only)
    copilotkit: Optional[dict]
```

### Tool Factory Signature

```python
def create_tools_for_user(
    user_id: int,
    thread_id: str,
    knowledge_bases: list[str],
    enabled_tools: list[str],
    platform: Literal["web", "telegram"],
    language: str = "en",
) -> list[StructuredTool]:
    """Create user-scoped tools.

    Args:
        user_id: User identifier
        thread_id: Conversation thread identifier
        knowledge_bases: List of Elasticsearch indexes to search
        enabled_tools: List of tool names to enable
        platform: Platform context ("web" or "telegram")
        language: User's preferred language (ISO code)

    Returns:
        List of LangChain StructuredTools with user context bound
    """
```

### Graph Builder Signature

```python
async def get_unified_agent_graph() -> CompiledStateGraph:
    """Get compiled unified agent graph.

    Returns:
        Compiled LangGraph StateGraph with Redis checkpointer

    Note:
        - Singleton pattern (cached after first call)
        - Uses Redis for state persistence
        - Includes agent, tools, suggestions nodes
    """
```
</output>

---

<validation>
## Testing

### Run Tests

```bash
# All luka_agent tests
pytest luka_agent/tests/ -v

# Specific test file
pytest luka_agent/tests/test_sub_agent_tools.py -v

# With coverage
pytest luka_agent/tests/ --cov=luka_agent --cov-report=html

# Specific test function
pytest luka_agent/tests/test_sub_agent_tools.py::test_sub_agent_discovery -v
```

### Test Checklist for New Tools

- [ ] Tool appears in `create_tools_for_user` result
- [ ] Tool has correct name, description, args_schema
- [ ] Tool implementation handles user_id, thread_id, language
- [ ] Tool handles service unavailability gracefully
- [ ] Tool returns user-friendly error messages
- [ ] Tool works on both Telegram and Web platforms
- [ ] Tool follows factory pattern (no exposed user context)
- [ ] Tool uses runtime imports for services

### Test Checklist for New Sub-Agents

- [ ] Sub-agent appears in `get_available_sub_agents` list
- [ ] `get_sub_agent_details` returns complete config
- [ ] `execute_sub_agent` starts first step correctly
- [ ] All steps execute in sequence
- [ ] Inputs/outputs flow correctly between steps
- [ ] Suggestions render on both platforms
- [ ] Edge cases handled (typos, "idk", unexpected input)
- [ ] Platform-agnostic (no Telegram/Web-specific references)

### Integration Testing

**Test on Telegram**:
```bash
# Start bot
python -m luka_bot

# Test in Telegram client
# - Send message
# - Use tool
# - Execute sub-agent
```

**Test on Web**:
```bash
# Start gateway
cd bot
uvicorn ag_ui_gateway.main:app --reload

# Test in web interface
# - Send message via WebSocket
# - Use tool
# - Execute sub-agent
```
</validation>

---

<success_criteria>
## Production Readiness Criteria

A luka_agent feature (tool or sub-agent) is production-ready when:

### Technical Criteria
1. **Works on both platforms**: Identical behavior on Telegram and Web
2. **State persistence**: Conversation state survives bot restarts
3. **Error handling**: Graceful degradation with user-friendly messages
4. **Testing**: All tests pass, coverage >80%
5. **Type safety**: Proper type hints, Pydantic validation

### Quality Criteria
6. **Documentation**: README.md with XML markup, examples, WHY explanations
7. **Platform agnostic**: No platform-specific code in luka_agent
8. **Service isolation**: Runtime imports, no circular dependencies
9. **User experience**: Clear tool descriptions, helpful error messages
10. **Logging**: Debug logging with user context (user_id, tool_name)

### Integration Criteria
11. **Tool registration**: Added to `tool_factories` dict
12. **Sub-agent discovery**: Appears in `get_available_sub_agents`
13. **Platform adapters**: Rendering works on Telegram and Web
14. **Redis checkpointing**: State persists correctly
15. **Service layer**: External dependencies accessed via services
</success_criteria>

---

<research>
## Configuration Strategy

**Problem**: Tools need external service configs (Elasticsearch URL, API keys) but luka_agent shouldn't depend on luka_bot.

**Solution**: Runtime dependency injection via service layer.

### Pattern

```python
# Tool imports service at runtime (inside implementation)
async def search_kb_impl(...):
    # Runtime import (not at module level)
    from luka_bot.services.elasticsearch_service import get_elasticsearch_service

    # Service has access to config
    service = get_elasticsearch_service()

    # Service handles external resource
    return await service.search(...)
```

### Flow

```
.env file
    ↓
luka_bot/core/config.py (Pydantic settings)
    ↓
luka_bot/services/*.py (Singleton services with config access)
    ↓
luka_agent/tools/*.py (Runtime import inside implementation)
```

### Benefits

- **No circular dependencies**: luka_agent doesn't import luka_bot at module level
- **Easy testing**: Mock services without affecting luka_agent
- **Service substitution**: Replace luka_bot services with your own
- **Standalone module**: luka_agent can be used in other projects

**See `luka_agent/CONFIG.md` for complete details.**

## Internal Architecture

### State Flow

```
1. User sends message
    ↓
2. Platform adapter creates state dict
    ↓
3. Graph loads previous state from Redis (by thread_id)
    ↓
4. Agent node: LLM decides which tools to use
    ↓
5. Tool node: Execute selected tools
    ↓
6. Suggestions node: Generate quick prompts (optional)
    ↓
7. Graph saves state to Redis
    ↓
8. Platform adapter renders response
    ↓
9. User receives response
```

### Graph Structure

```python
# luka_agent/graph.py

graph_builder = StateGraph(AgentState)

# Add nodes
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("suggestions", suggestions_node)

# Add edges
graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {"continue": "tools", "end": "suggestions"}
)
graph_builder.add_edge("tools", "agent")
graph_builder.add_edge("suggestions", END)

# Compile with checkpointer
graph = graph_builder.compile(checkpointer=get_redis_checkpointer())
```

### Tool Discovery

```python
# luka_agent/tools/__init__.py

# Tool factories with lazy initialization
tool_factories = {
    "knowledge_base": lambda: create_knowledge_base_tool(user_id, thread_id, language),
    "youtube": lambda: create_youtube_tool(user_id, thread_id, language),
    "sub_agent": lambda: create_sub_agent_tools(user_id, thread_id, language),
}

def create_tools_for_user(...):
    tools = []
    for tool_name in enabled_tools:
        if tool_name in tool_factories:
            result = tool_factories[tool_name]()
            # Handle multi-tool factories (like sub_agent returns 5 tools)
            if isinstance(result, list):
                tools.extend(result)
            else:
                tools.append(result)
    return tools
```

### Sub-Agent Discovery

```python
# luka_bot/services/workflow_discovery_service.py (outside luka_agent)

def discover_sub_agents():
    """Scan luka_agent/sub_agents/ for config.yaml files."""
    sub_agents_dir = Path("luka_agent/sub_agents")

    for sub_dir in sub_agents_dir.iterdir():
        config_path = sub_dir / "config.yaml"
        if config_path.exists():
            # Parse YAML
            config = yaml.safe_load(config_path.read_text())
            # Register sub-agent
            register_sub_agent(config)
```

## Codebase References

### Core Files
- **Graph**: `luka_agent/graph.py` - Graph builder and node definitions
- **State**: `luka_agent/state.py` - AgentState TypedDict
- **Checkpointer**: `luka_agent/checkpointer.py` - Redis persistence
- **Tool Factory**: `luka_agent/tools/__init__.py` - Tool creation logic

### Example Implementations
- **Simple Tool**: `luka_agent/tools/knowledge_base.py` - Single tool example
- **Multi-Tool Factory**: `luka_agent/tools/sub_agent.py` - 5 tools from one factory
- **Sub-Agent**: `luka_agent/sub_agents/sol_atlas_onboarding/` - Complete example

### Platform Adapters (Outside luka_agent)
- **Telegram**: `luka_bot/handlers/chat.py` - Uses luka_agent graph
- **Web**: `ag_ui_gateway/websocket/chat.py` - Uses luka_agent graph

### Service Layer (Outside luka_agent)
- **Config**: `luka_bot/core/config.py` - Pydantic settings
- **Services**: `luka_bot/services/` - Elasticsearch, workflow, etc.
</research>

---

<examples>
## Usage Examples

### Example 1: Simple Tool Integration

```python
from luka_agent import get_unified_agent_graph, create_tools_for_user
from langchain_core.messages import HumanMessage

# Create tools
tools = create_tools_for_user(
    user_id=123,
    thread_id="thread_123",
    knowledge_bases=["tg-kb-user-123"],
    enabled_tools=["knowledge_base"],
    platform="telegram",
    language="en"
)

# Get graph
graph = await get_unified_agent_graph()

# Invoke
config = {"configurable": {"thread_id": "thread_123"}}
result = await graph.ainvoke(
    {"messages": [HumanMessage(content="Search my notes about Python")]},
    config=config
)

# Result contains full conversation history + tool results
print(result["messages"][-1].content)
```

### Example 2: Sub-Agent Execution

```python
from luka_agent import get_unified_agent_graph, create_tools_for_user
from langchain_core.messages import HumanMessage

# Create tools with sub_agent enabled
tools = create_tools_for_user(
    user_id=123,
    thread_id="thread_456",
    knowledge_bases=[],
    enabled_tools=["sub_agent"],
    platform="web",
    language="en"
)

# Get graph
graph = await get_unified_agent_graph()

# User triggers sub-agent
config = {"configurable": {"thread_id": "thread_456"}}
result = await graph.ainvoke(
    {"messages": [HumanMessage(content="Help me plan a trip")]},
    config=config
)

# LLM decides to use execute_sub_agent tool
# Sub-agent (trip_planner) guides user through planning steps
```

### Example 3: Streaming Response

```python
from luka_agent import get_unified_agent_graph
from langchain_core.messages import HumanMessage

graph = await get_unified_agent_graph()
config = {"configurable": {"thread_id": "thread_789"}}

# Stream events
async for event in graph.astream_events(
    {"messages": [HumanMessage(content="What's in my knowledge base?")]},
    config=config,
    version="v2"
):
    kind = event["event"]

    if kind == "on_chat_model_stream":
        # LLM token
        token = event["data"]["chunk"].content
        print(token, end="", flush=True)

    elif kind == "on_tool_start":
        # Tool execution started
        tool_name = event["name"]
        print(f"\n🔧 Using: {tool_name}")

    elif kind == "on_tool_end":
        # Tool execution completed
        output = event["data"]["output"]
        print(f"✅ Result: {output[:100]}...")
```

### Example 4: Custom Platform Integration

```python
# Your custom platform adapter
from luka_agent import get_unified_agent_graph, create_tools_for_user
from langchain_core.messages import HumanMessage

class MyPlatformAdapter:
    async def handle_message(self, user_id: int, text: str):
        # Create tools
        tools = create_tools_for_user(
            user_id=user_id,
            thread_id=f"my_platform_{user_id}",
            knowledge_bases=[f"my-kb-{user_id}"],
            enabled_tools=["knowledge_base", "sub_agent"],
            platform="web",  # Closest match
            language="en"
        )

        # Get graph
        graph = await get_unified_agent_graph()

        # Invoke
        config = {"configurable": {"thread_id": f"my_platform_{user_id}"}}
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=text)]},
            config=config
        )

        # Render for your platform
        response = result["messages"][-1].content
        suggestions = result.get("suggestions", [])

        return {
            "text": response,
            "quick_replies": suggestions
        }
```
</examples>

---

<troubleshooting>
## Troubleshooting

### Graph Not Compiling

**Symptom**: Error when calling `get_unified_agent_graph()`

**Solutions**:
1. **Check Redis connection**:
   ```bash
   redis-cli ping  # Should return PONG
   ```
2. **Verify REDIS_HOST and REDIS_PORT in .env**
3. **Check imports**: All nodes defined in `nodes.py`
4. **Check state schema**: AgentState must be TypedDict

### Tool Not Appearing

**Symptom**: Tool not in `create_tools_for_user` result

**Solutions**:
1. **Check tool registration**:
   ```python
   # luka_agent/tools/__init__.py
   tool_factories = {
       "my_tool": lambda: create_my_tool(user_id, thread_id, language),
   }
   ```
2. **Check enabled_tools list**: Must include "my_tool"
3. **Check factory return**: Must return StructuredTool or list of StructuredTools
4. **Check imports**: Tool factory imported in `__init__.py`

### Sub-Agent Not Discovered

**Symptom**: Sub-agent not in `get_available_sub_agents` result

**Solutions**:
1. **Check file location**: `luka_agent/sub_agents/[domain]/config.yaml`
2. **Validate YAML syntax**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('luka_agent/sub_agents/my_sub_agent/config.yaml'))"
   ```
3. **Check required fields**: metadata.domain, metadata.name, persona, tool_chain
4. **Restart bot**: Discovery happens at startup
5. **Check logs**: `tail -f logs/luka_bot.log | grep workflow`

### State Not Persisting

**Symptom**: Conversation state lost after bot restart

**Solutions**:
1. **Check Redis checkpointer**: Graph must use `get_redis_checkpointer()`
2. **Check thread_id**: Must be consistent across invocations
3. **Check Redis data**:
   ```bash
   redis-cli KEYS "*thread_123*"
   ```
4. **Verify config parameter**: `config = {"configurable": {"thread_id": "thread_123"}}`

### Circular Import Errors

**Symptom**: ImportError about circular dependencies

**Solutions**:
1. **Check module-level imports**: Don't import luka_bot at top of luka_agent files
2. **Use runtime imports**: Import services inside tool implementation functions
3. **Check import order**: luka_agent should not import from luka_bot/__init__.py

### Platform-Specific Bugs

**Symptom**: Works on Telegram but not Web (or vice versa)

**Solutions**:
1. **Check platform field**: Verify state has correct platform value
2. **Remove platform-specific code**: No aiogram or FastAPI in luka_agent
3. **Test adapters**: Platform adapters may have bugs
4. **Check suggestions rendering**: Different platforms render differently

### Service Unavailable Errors

**Symptom**: Tool returns "Service not available" message

**Solutions**:
1. **Check service is running**: Elasticsearch, etc.
2. **Check config**: Verify .env has correct URLs and API keys
3. **Check imports**: Service import path correct
4. **Check service initialization**: `get_*_service()` pattern works
5. **Add logging**:
   ```python
   logger.debug(f"Attempting to import service: {service_name}")
   ```
</troubleshooting>

---

## Migration Status

### ✅ Completed
- [x] Unified state schema (`state.py`)
- [x] Redis checkpointer (`checkpointer.py`)
- [x] Graph nodes and builder (`nodes.py`, `graph.py`)
- [x] Tool factory pattern (`tools/__init__.py`)
- [x] Core tools: `knowledge_base`, `sub_agent` (5 tools), `youtube`
- [x] Sub-agent scenarios: `sol_atlas_onboarding`, `trip_planner`, `defi_onboarding`
- [x] Comprehensive documentation with XML markup
- [x] Test suite (test_sub_agent_tools.py - 10/10 passing)
- [x] Configuration strategy (`CONFIG.md`)
- [x] Dependency checking patterns (`DEPENDENCY_CHECKING.md`)
- [x] Tool development templates and meta-prompting system
- [x] Sub-agent development templates

### 🔲 Pending
- [ ] Migrate additional tools: `support`, `menu`, `twitter`, `tripplanner` (9 tools)
- [ ] Create platform adapters (Telegram keyboard, Web quickPrompts)
- [ ] Update `ag_ui_gateway` to use luka_agent
- [ ] Update `luka_bot` to use luka_agent
- [ ] End-to-end testing on both platforms
- [ ] Feature flag for gradual rollout (`LUKA_USE_UNIFIED_AGENT`)
- [ ] Performance benchmarking (response time, memory usage)
- [ ] Load testing (concurrent users, Redis limits)

---

## Resources

### Documentation
- **Tools Guide**: `luka_agent/tools/README.md`
- **Sub-Agents Guide**: `luka_agent/sub_agents/README.md`
- **Configuration Strategy**: `luka_agent/CONFIG.md`
- **Dependency Checking**: `luka_agent/DEPENDENCY_CHECKING.md`
- **Project Conventions**: `CLAUDE.md` (repo root)

### Templates
- **Tool Template**: `luka_agent/tools/TEMPLATE.md`
- **Sub-Agent Template**: `luka_agent/sub_agents/TEMPLATE/`
- **README Template**: `luka_agent/sub_agents/README_TEMPLATE.md`

### Examples
- **Simple Tool**: `luka_agent/tools/knowledge_base.py`
- **Multi-Tool Factory**: `luka_agent/tools/sub_agent.py`
- **Sub-Agent**: `luka_agent/sub_agents/sol_atlas_onboarding/`

### External Resources
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **LangChain Tools**: https://python.langchain.com/docs/modules/agents/tools/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **Redis Docs**: https://redis.io/docs/

---

## FAQ

**Q: Why LangChain StructuredTools instead of Pydantic-AI tools?**

A: LangGraph natively supports LangChain tools. Pydantic-AI tools would require wrappers. StructuredTools provide the same Pydantic validation with better LangGraph integration.

**Q: Why separate luka_agent from luka_bot?**

A: To enable reuse across platforms (Telegram, Web, future platforms) and maintain single source of truth. luka_agent is standalone and platform-agnostic.

**Q: How do tools access config (Elasticsearch URL, API keys)?**

A: Runtime dependency injection via service layer. Tools import services inside implementation functions. Services access luka_bot config. See `CONFIG.md`.

**Q: Can I use luka_agent without luka_bot?**

A: Yes, but you'll need to provide services. The tool→service→config pattern allows replacing services with your own implementations.

**Q: Why "sub-agent" instead of "workflow"?**

A: "Sub-agent" better reflects their autonomous, LLM-powered nature. They're specialized agents with their own persona, tools, and step-by-step guidance — not just BPMN workflows.

**Q: What's the difference between tools and sub-agents?**

A: Tools are single-purpose functions (search KB, get transcript). Sub-agents are multi-step guided experiences (onboarding, trip planning) with their own persona and sequential steps.

**Q: How do I test platform compatibility?**

A: Test on both Telegram (`python -m luka_bot`) and Web (`uvicorn ag_ui_gateway.main:app`). Verify identical behavior. Use platform adapters for rendering only.

**Q: Why TypedDict instead of Pydantic BaseModel for state?**

A: LangGraph requires TypedDict for state. Pydantic BaseModel doesn't work with LangGraph's state management.

**Q: How do I handle breaking changes in luka_agent?**

A: Version luka_agent as a package. Use feature flags for gradual rollout. Test thoroughly before deploying to production.

---

## Questions?

For issues or questions:
1. **Check relevant README**: This file, `tools/README.md`, `sub_agents/README.md`
2. **Review examples**: Existing tools (`knowledge_base.py`) and sub-agents (`sol_atlas_onboarding/`)
3. **Check test suite**: `tests/test_sub_agent_tools.py` shows usage patterns
4. **Create GitHub issue** with:
   - Component (tool/sub-agent/graph/state)
   - Error logs
   - Steps to reproduce
   - Expected vs actual behavior
   - Platform (Telegram/Web)

---

**Happy building with luka_agent! 🚀**
