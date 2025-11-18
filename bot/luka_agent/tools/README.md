# Luka Agent Tools - Development Guide

**Expert system for creating platform-agnostic LangChain tools that serve both Telegram and Web platforms.**

---

<objective>
Create production-ready LangChain StructuredTools that:
- Work identically on Telegram and Web platforms
- Follow consistent patterns for input validation, error handling, and logging
- Integrate seamlessly with external services via runtime dependency injection
- Provide user-friendly error messages with graceful degradation
</objective>

<context>
## Architecture Overview

luka_agent provides a unified tool layer that serves both platforms:

```
┌─────────────────────────────────────────────────┐
│           luka_agent (Unified Layer)            │
│  ┌────────────────────────────────────────┐    │
│  │         Unified LangGraph              │    │
│  │  ┌──────────────────────────────┐      │    │
│  │  │  Tools (Platform-Agnostic)   │      │    │
│  │  │  - knowledge_base.py         │      │    │
│  │  │  - sub_agent.py (5 tools)    │      │    │
│  │  │  - youtube.py                │      │    │
│  │  │  - [your new tools here]     │      │    │
│  │  └──────────────────────────────┘      │    │
│  └────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
┌──────────────┐        ┌──────────────┐
│   Telegram   │        │     Web      │
│   (luka_bot) │        │ (ag_ui_gate) │
└──────────────┘        └──────────────┘
```

**Key Benefits:**
- ✅ Single implementation serves both platforms
- ✅ Feature parity guaranteed
- ✅ Consistent behavior and error handling
- ✅ Easier testing and maintenance
- ✅ No code duplication

**Directory Structure:**
```
luka_agent/tools/
├── __init__.py              # Tool factory (create_tools_for_user)
├── README.md                # This file (development guide)
├── TEMPLATE.md              # Template for new tools
├── knowledge_base.py        # KB search tool
├── sub_agent.py             # 5 sub-agent tools
├── youtube.py               # YouTube transcript tool
└── [future tools]
    ├── support.py           # Support tools
    ├── menu.py              # Menu tools
    ├── twitter.py           # Twitter tools
    └── tripplanner/         # Trip planner tools (9 tools)
```
</context>

---

## Table of Contents

- [Quick Start](#quick-start)
- [Tool Structure](#tool-structure)
- [Creating a New Tool](#creating-a-new-tool)
- [Dependency Checking](#dependency-checking)
- [Configuration & Services](#configuration--services)
- [Input Schema Design](#input-schema-design)
- [Error Handling](#error-handling)
- [Testing Strategy](#testing-strategy)
- [Best Practices](#best-practices)
- [Existing Tools Reference](#existing-tools-reference)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

<requirements>
### Prerequisites

Before creating a tool, ensure you understand:

1. **LangChain StructuredTools**: Tools use `StructuredTool.from_function()` pattern
2. **Pydantic Validation**: Input schemas are Pydantic BaseModels with Field descriptions
3. **Async Functions**: All implementations must be async
4. **Factory Pattern**: Tools bind user context (user_id, thread_id, language) at creation
5. **Service Layer**: Tools import services at runtime (inside functions, not module-level)
6. **Dependency Checking**: Tools verify external resources are available before execution

### Tool Requirements Checklist

- [ ] **Platform-agnostic**: Works identically on Telegram and Web
- [ ] **LangChain StructuredTool**: Uses `StructuredTool.from_function()`
- [ ] **Pydantic input schema**: `*Input` class with Field descriptions for LLM
- [ ] **Async implementation**: `async def {tool}_impl()` returns `str`
- [ ] **Dependency checking**: Verifies configs, services, resources before execution
- [ ] **User-friendly errors**: Returns actionable messages, not technical errors
- [ ] **Runtime imports**: Imports services inside implementation function
- [ ] **Logging**: Uses loguru with context (user_id, tool name)
- [ ] **Type hints**: Full type annotations
- [ ] **Factory function**: Binds user context via closures
- [ ] **Registration**: Added to `__init__.py` tool factory
- [ ] **Tests**: Unit, integration, and E2E tests
</requirements>

---

## Tool Structure

<output>
### Standard Tool Pattern

Every tool follows this three-part structure:

**1. Input Schema** - Pydantic model for validation and LLM documentation
**2. Implementation** - Async function with dependency checking and error handling
**3. Factory** - Function that binds user context and returns StructuredTool

```python
"""
{Tool Name} tool for luka_agent.

{Brief description of what the tool does.}
"""

from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field


# =============================================================================
# Input Schema
# =============================================================================


class {ToolName}Input(BaseModel):
    """Input schema for {tool name} tool."""

    param1: str = Field(
        ...,  # Required field
        description="Clear description for LLM (what this parameter does)"
    )
    param2: int | None = Field(
        None,  # Optional field
        description="Optional parameter description"
    )
    param3: int = Field(
        10,  # Default value
        description="Parameter with default",
        ge=1,  # Validation: greater than or equal to 1
        le=100  # Validation: less than or equal to 100
    )


# =============================================================================
# Implementation
# =============================================================================


async def {tool_name}_impl(
    param1: str,
    param2: int | None,
    param3: int,
    user_id: int,
    thread_id: str,
    language: str,
) -> str:
    """Implementation of {tool name} tool.

    Args:
        param1: Description
        param2: Description
        param3: Description
        user_id: User ID for context
        thread_id: Thread ID for context
        language: User's preferred language

    Returns:
        Result message or error message
    """
    # Step 1: Check configuration (if feature requires external service)
    try:
        from luka_bot.core.config import settings
    except ImportError:
        logger.error("Unable to import settings - luka_bot config not available")
        return (
            "This feature is not configured. "
            "Please ensure luka_bot is properly installed."
        )

    # Check if feature is enabled (if applicable)
    if hasattr(settings, "MY_FEATURE_ENABLED") and not settings.MY_FEATURE_ENABLED:
        logger.warning("MY_FEATURE is disabled in settings")
        return (
            "This feature is currently disabled. "
            "To enable it, set MY_FEATURE_ENABLED=true in your .env file."
        )

    # Step 2: Import service at runtime (not at module level)
    try:
        from luka_bot.services.some_service import get_some_service
    except ImportError as import_err:
        logger.error(f"Unable to import service: {import_err}")
        return (
            "Service is not available. "
            "Please ensure luka_bot services are installed correctly."
        )

    # Step 3: Execute tool logic with error handling
    try:
        service = get_some_service()

        # Check service availability (if applicable)
        if not service.is_available():
            return (
                "Service is currently unavailable. "
                "Please try again later."
            )

        result = await service.do_something(param1, param2, param3)

        logger.debug(
            f"Tool '{tool_name}' executed successfully for user {user_id}"
        )
        return result

    except Exception as exc:
        logger.error(f"Error in '{tool_name}' for user {user_id}: {exc}")
        return (
            "Unable to complete operation. "
            "Please try again or contact support if the issue persists."
        )


# =============================================================================
# Factory
# =============================================================================


def create_{domain}_tool(
    user_id: int,
    thread_id: str,
    language: str,
    # Additional context params as needed
) -> StructuredTool:
    """Create {tool name} tool with user context bound.

    Args:
        user_id: User ID
        thread_id: Thread ID
        language: User's preferred language

    Returns:
        LangChain StructuredTool instance
    """
    return StructuredTool.from_function(
        name="{tool_name}",
        description=(
            "Clear, concise description of what this tool does. "
            "This is shown to the LLM to help it decide when to use the tool. "
            "Be specific about when to use it and what inputs are needed."
        ),
        func=lambda param1, param2=None, param3=10: {tool_name}_impl(
            param1, param2, param3, user_id, thread_id, language
        ),
        coroutine=lambda param1, param2=None, param3=10: {tool_name}_impl(
            param1, param2, param3, user_id, thread_id, language
        ),
        args_schema={ToolName}Input,
    )


__all__ = ["create_{domain}_tool"]
```

### Why This Pattern?

<constraints>
**Design Rationale:**

1. **Input Schema (Pydantic)**
   - WHY: LLM reads Field descriptions to understand parameters
   - WHY: Automatic validation prevents invalid inputs
   - WHY: Clear schema documentation improves LLM decision-making

2. **Dependency Checking**
   - WHY: Prevents crashes when external services are unavailable
   - WHY: User-friendly messages help users fix configuration issues
   - WHY: Graceful degradation maintains conversation flow

3. **Runtime Imports**
   - WHY: Avoids circular import dependencies
   - WHY: Keeps tools testable (can mock services)
   - WHY: Maintains luka_agent as standalone module

4. **Factory Pattern**
   - WHY: Binds user context automatically via closures
   - WHY: Tools don't need to pass user_id everywhere
   - WHY: Consistent interface across all tools

5. **User-Friendly Errors**
   - WHY: Technical errors confuse LLM and break conversation
   - WHY: Actionable messages help users fix issues
   - WHY: Logs capture technical details for debugging
</constraints>
</output>

---

## Creating a New Tool

<implementation>
### Step-by-Step Process

#### Step 1: Create Tool File

```bash
cd /path/to/bot/luka_agent/tools
touch my_new_tool.py
```

Or use the template:
```bash
cp TEMPLATE.md my_new_tool.py
# Edit my_new_tool.py with your implementation
```

#### Step 2: Define Input Schema

```python
# my_new_tool.py

from pydantic import BaseModel, Field

class MyNewToolInput(BaseModel):
    """Input schema for my new tool."""

    query: str = Field(
        ...,
        description="The search query or action to perform. Use specific keywords for best results."
    )
    max_results: int = Field(
        5,
        description="Maximum number of results to return (1-20). Use higher values for comprehensive searches.",
        ge=1,
        le=20
    )
```

<validation>
**Input Schema Best Practices:**

✅ **DO:**
- Write descriptions as if explaining to the LLM: "Use this when user asks for X"
- Provide defaults for optional parameters
- Add validation constraints (ge, le, regex, min_length)
- Use union types for flexibility (`str | None`)
- Document edge cases: "Use '*' for all messages"

❌ **DON'T:**
- Leave descriptions empty (LLM won't know when to use)
- Use vague descriptions ("The query")
- Skip validation (leads to runtime errors)
- Use complex nested objects (flatten when possible)

**Example - Good vs Bad:**

```python
# ✅ GOOD
class SearchInput(BaseModel):
    query: str = Field(
        ...,
        description="Search query. Use '*' for all messages, or keywords like 'postgres issues'. Be specific for better results."
    )
    max_results: int = Field(
        5,
        description="Maximum results (1-100). Use 20+ for comprehensive digests or summaries.",
        ge=1,
        le=100
    )

# ❌ BAD
class SearchInput(BaseModel):
    query: str  # No description
    max: int = 5  # Vague name, no validation, no description
```
</validation>

#### Step 3: Implement Tool Logic with Dependency Checking

See [Dependency Checking](#dependency-checking) section for the complete pattern.

**Key Points:**
1. Check configuration first (if feature requires it)
2. Import services at runtime (inside function)
3. Verify service availability
4. Execute with specific error handling
5. Return user-friendly messages
6. Log technical details for debugging

#### Step 4: Create Factory Function

```python
def create_my_new_tool(
    user_id: int,
    thread_id: str,
    language: str,
) -> StructuredTool:
    """Create my new tool with user context bound.

    Args:
        user_id: User ID
        thread_id: Thread ID
        language: User's preferred language

    Returns:
        LangChain StructuredTool instance
    """
    return StructuredTool.from_function(
        name="my_new_tool",
        description=(
            "Search for relevant information based on user query. "
            "Use this when user asks for specific data or wants to find something. "
            "Provide clear, specific queries for best results."
        ),
        func=lambda query, max_results=5: my_new_tool_impl(
            query, max_results, user_id, thread_id, language
        ),
        coroutine=lambda query, max_results=5: my_new_tool_impl(
            query, max_results, user_id, thread_id, language
        ),
        args_schema=MyNewToolInput,
    )
```

<constraints>
**Factory Function Rules:**

- **name**: snake_case, matches file/function name
- **description**: Clear, explains when to use (LLM reads this)
- **func & coroutine**: Both must have same signature
- **Lambda closure**: Binds user context (user_id, thread_id, language)
- **args_schema**: Links to input class for validation

WHY these rules:
- Consistent naming makes tools discoverable
- Good descriptions improve LLM decision-making
- Both func/coroutine needed for sync/async compatibility
- Closures eliminate need to pass context explicitly
</constraints>

#### Step 5: Register in Tool Factory

```python
# luka_agent/tools/__init__.py

from luka_agent.tools.my_new_tool import create_my_new_tool

def create_tools_for_user(
    user_id: int,
    thread_id: str,
    knowledge_bases: List[str],
    enabled_tools: List[str],
    platform: str = "telegram",
    language: str = "en",
) -> List[BaseTool]:
    """Create tools with user context bound."""

    tools = []

    tool_factories = {
        "knowledge_base": lambda: create_knowledge_base_tool(...),
        "sub_agent": lambda: create_sub_agent_tools(...),
        "youtube": lambda: create_youtube_tool(...),
        "my_new_tool": lambda: create_my_new_tool(user_id, thread_id, language),  # ADD THIS
    }

    for tool_name in enabled_tools:
        if tool_name in tool_factories:
            try:
                result = tool_factories[tool_name]()
                # Handle both single tool and list of tools
                if isinstance(result, list):
                    tools.extend(result)
                else:
                    tools.append(result)
                logger.info(f"✅ Created tool: {tool_name}")
            except Exception as exc:
                logger.error(f"❌ Failed to create tool '{tool_name}': {exc}")
        else:
            logger.warning(f"⚠️ Tool '{tool_name}' not found in factory")

    return tools
```

#### Step 6: Write Tests

```python
# luka_agent/tests/test_my_new_tool.py

import pytest
from luka_agent.tools.my_new_tool import create_my_new_tool, my_new_tool_impl

@pytest.mark.asyncio
async def test_my_new_tool_impl_success():
    """Test my_new_tool implementation with successful execution."""
    result = await my_new_tool_impl(
        query="test query",
        max_results=5,
        user_id=123,
        thread_id="test_thread",
        language="en"
    )

    assert isinstance(result, str)
    assert len(result) > 0
    # Add more specific assertions based on expected behavior

@pytest.mark.asyncio
async def test_my_new_tool_impl_service_unavailable(mocker):
    """Test error handling when service is unavailable."""
    # Mock service to be unavailable
    mock_service = mocker.Mock()
    mock_service.is_available.return_value = False
    mocker.patch(
        "luka_bot.services.my_service.get_my_service",
        return_value=mock_service
    )

    result = await my_new_tool_impl(
        query="test",
        max_results=5,
        user_id=123,
        thread_id="test",
        language="en"
    )

    assert "unavailable" in result.lower()

def test_create_my_new_tool():
    """Test tool factory creates valid StructuredTool."""
    tool = create_my_new_tool(
        user_id=123,
        thread_id="test_thread",
        language="en"
    )

    assert tool.name == "my_new_tool"
    assert tool.description != ""
    assert tool.args_schema is not None
    assert tool.coroutine is not None

@pytest.mark.asyncio
async def test_my_new_tool_in_factory():
    """Test tool appears in create_tools_for_user."""
    from luka_agent.tools import create_tools_for_user

    tools = create_tools_for_user(
        user_id=123,
        thread_id="test_thread",
        knowledge_bases=["test-kb"],
        enabled_tools=["my_new_tool"],
        platform="telegram",
        language="en"
    )

    assert len(tools) == 1
    assert tools[0].name == "my_new_tool"
```

<success_criteria>
**Test Coverage Requirements:**

- [ ] Unit test: Implementation function directly (fast, mocked services)
- [ ] Unit test: Error handling (service unavailable, ImportError, etc.)
- [ ] Integration test: Factory returns correct tool
- [ ] E2E test: Tool appears in create_tools_for_user
- [ ] E2E test: Tool works on both Telegram and Web platforms

WHY: Layered testing catches issues at different levels - unit tests find logic bugs, integration tests find interface issues, E2E tests find registration/platform problems.
</success_criteria>
</implementation>

---

## Dependency Checking

<requirements>
### Standard Dependency Checking Pattern

All tools that use external services MUST implement dependency checking to provide user-friendly error messages.

See **`luka_agent/DEPENDENCY_CHECKING.md`** for complete documentation.

**Quick Reference - 5 Levels:**

```python
async def my_tool_impl(...) -> str:
    """Implementation with complete dependency checking."""

    # Level 1: Check configuration
    try:
        from luka_bot.core.config import settings
    except ImportError:
        return "Feature not configured. Please ensure luka_bot is installed."

    if hasattr(settings, "MY_FEATURE_ENABLED") and not settings.MY_FEATURE_ENABLED:
        return (
            "Feature is currently disabled. "
            "Set MY_FEATURE_ENABLED=true in .env to enable."
        )

    # Level 2: Check credentials (if applicable)
    if hasattr(settings, "MY_API_KEY") and not settings.MY_API_KEY:
        return (
            "API key required. "
            "Set MY_API_KEY in your .env file."
        )

    # Level 3: Import service
    try:
        from luka_bot.services.my_service import get_my_service
    except ImportError:
        return "Service not available. Check installation."

    # Level 4: Check service health
    try:
        service = get_my_service()
        if not service.is_available():
            return "Service is temporarily unavailable. Try again later."
    except Exception as e:
        logger.error(f"Service initialization error: {e}")
        return "Unable to initialize service. Check configuration."

    # Level 5: Execute with specific error handling
    try:
        result = await service.do_something(...)
        return result
    except SpecificException as e:
        # Handle specific known errors with helpful messages
        return "Specific issue occurred. Here's how to fix it: ..."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "An error occurred. Please try again."
```

### Current Tool Status

| Tool | Config Check | Service Check | User-Friendly Errors |
|------|--------------|---------------|---------------------|
| knowledge_base.py | ✅ | ⚠️ Partial | ✅ |
| youtube.py | ✅ | ✅ | ✅ |
| sub_agent.py | ✅ | ✅ | ✅ |

<validation>
**Error Message Quality Guidelines:**

✅ **GOOD** - Clear, actionable, guides user to solution:
```python
return (
    "Knowledge base is currently disabled. "
    "To enable it, set ELASTICSEARCH_ENABLED=true in your .env file "
    "and restart the bot."
)
```

❌ **BAD** - Technical, no context, doesn't help user:
```python
return f"Error: {str(e)}"  # ConnectionRefusedError: [Errno 61]...
```

WHY: LLM passes these messages to users. Technical errors confuse users and break conversation flow. Actionable messages help users fix issues themselves.
</validation>
</requirements>

---

## Configuration & Services

<context>
### Runtime Dependency Injection Pattern

**Problem**: Tools need external service configs (Elasticsearch URL, API keys) but luka_agent shouldn't depend on luka_bot.

**Solution**: Runtime dependency injection via service layer.

See **`luka_agent/CONFIG.md`** for complete configuration strategy.

**Quick Summary:**

```
Flow: .env → luka_bot/core/config.py → luka_bot/services/*.py → luka_agent/tools/*.py
                (Pydantic Settings)      (Singleton Services)     (Runtime Import)
```

**Pattern:**

```python
# Tool imports service at runtime (inside implementation)
async def search_kb_impl(...):
    # Import INSIDE function (runtime dependency injection)
    from luka_bot.services.elasticsearch_service import get_elasticsearch_service

    # Service has access to settings.ELASTICSEARCH_URL, credentials, etc.
    service = get_elasticsearch_service()

    # Tool doesn't need to know about config details
    return await service.search(...)
```

<constraints>
**Service Integration Rules:**

✅ **DO:**
- Import services inside implementation function
- Use `get_*_service()` singleton pattern
- Handle ImportError gracefully
- Check service availability before use
- Log errors with context

❌ **DON'T:**
- Import services at module level (circular imports)
- Instantiate services directly (breaks singleton)
- Assume service is always available
- Access settings directly in tools
- Skip error handling

WHY: This pattern keeps luka_agent standalone and reusable, avoids circular dependencies, makes testing easy (mock services), and enables graceful degradation when services are unavailable.
</constraints>
</context>

---

## Input Schema Design

<validation>
### Field Description Best Practices

**LLM reads Field descriptions to decide when and how to use tools. Write for the LLM, not humans.**

✅ **GOOD Examples:**

```python
query: str = Field(
    ...,
    description=(
        "Search query for knowledge base. "
        "Use '*' to retrieve all messages, or provide specific keywords. "
        "Examples: 'postgres connection', 'deployment issues', 'API documentation'"
    )
)

date_from: str | None = Field(
    None,
    description=(
        "Start date for search filter. "
        "Formats: '7d' (last 7 days), '1w' (last week), '1m' (last month), "
        "or 'YYYY-MM-DD' for specific date. "
        "Leave empty to search all time."
    )
)

max_results: int = Field(
    10,
    description=(
        "Maximum number of results to return (1-100). "
        "Use 10-20 for specific queries, 50+ for comprehensive summaries or digests."
    ),
    ge=1,
    le=100
)
```

❌ **BAD Examples:**

```python
query: str  # No description - LLM doesn't know what to put here

date: str = Field(..., description="The date")  # Vague, no format info

limit: int = 10  # No description, no validation, unclear purpose
```

### Validation Constraints

```python
from pydantic import Field, field_validator

class ToolInput(BaseModel):
    # Numeric constraints
    count: int = Field(..., ge=1, le=100)  # Greater/less than or equal

    # String constraints
    query: str = Field(..., min_length=1, max_length=500)

    # Regex patterns
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

    # Custom validation
    @field_validator('query')
    def validate_query(cls, v):
        if v == '' or v.isspace():
            raise ValueError('Query cannot be empty or whitespace')
        return v.strip()
```

<constraints>
WHY validation matters:
- Prevents invalid inputs from reaching service layer
- Provides clear error messages to LLM
- Reduces unnecessary service calls
- Catches common mistakes early (empty strings, out-of-range numbers)
</constraints>
</validation>

---

## Error Handling

<requirements>
### Error Handling Strategy

**Goal**: Never crash. Always return a user-friendly string message.

**Principle**: Tools are the LLM's interface to external systems. Technical errors confuse the LLM and break conversation flow.

### Three-Layer Error Handling

```python
async def my_tool_impl(...) -> str:
    """Implementation with layered error handling."""

    # Layer 1: Configuration/Availability Errors
    try:
        from luka_bot.services.my_service import get_my_service
    except ImportError:
        logger.error("Service not available")
        return "Service is not configured. Please contact administrator."

    # Layer 2: Service-Level Errors
    try:
        service = get_my_service()
        if not service.is_available():
            logger.warning("Service unavailable")
            return "Service is temporarily unavailable. Please try again later."
    except Exception as e:
        logger.error(f"Service initialization error: {e}")
        return "Unable to initialize service. Please check configuration."

    # Layer 3: Execution Errors (specific → general)
    try:
        result = await service.execute(...)
        return result

    # Catch specific exceptions first
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found: {e}")
        return f"The requested resource was not found. Please check your input and try again."

    except PermissionError as e:
        logger.warning(f"Permission denied: {e}")
        return "You don't have permission to access this resource. Please contact support."

    except TimeoutError as e:
        logger.warning(f"Operation timed out: {e}")
        return "The operation took too long. Please try again with a simpler request."

    # Catch all other exceptions
    except Exception as e:
        logger.error(f"Unexpected error in {tool_name}: {e}", exc_info=True)
        return (
            "An unexpected error occurred. "
            "Please try again or contact support if the issue persists."
        )
```

### Error Message Templates

<output>
**Configuration Errors:**
```python
"Feature is not configured. Please ensure [service] is installed."
"Feature is currently disabled. Set [CONFIG_VAR]=true to enable."
"API key is required. Set [API_KEY] in your .env file."
```

**Availability Errors:**
```python
"Service is temporarily unavailable. Please try again later."
"Unable to connect to [service]. Please check your configuration."
"[Resource] is not accessible right now. Please try again."
```

**User Input Errors:**
```python
"Invalid input: [specific issue]. Please [corrective action]."
"The requested [resource] was not found. Please check [what to check]."
"Format not supported. Please use [correct format]."
```

**Generic Errors:**
```python
"An error occurred. Please try again."
"Unable to complete operation. Please contact support if this persists."
```
</output>

<constraints>
**Error Message Rules:**

✅ **DO:**
- Be specific about what went wrong
- Provide corrective action when possible
- Use plain language, not technical jargon
- Log full exception details for debugging
- Maintain conversational tone

❌ **DON'T:**
- Expose internal error messages
- Include stack traces or exception types
- Use technical terms (ImportError, ConnectionRefused, etc.)
- Say "Something went wrong" without context
- Skip logging (need debug info)

WHY: Users and LLMs need guidance, not technical details. Developers need full error context in logs.
</constraints>
</requirements>

---

## Testing Strategy

<success_criteria>
### Three-Level Testing Approach

#### Level 1: Unit Tests (Implementation Function)

**Purpose**: Test tool logic in isolation
**Speed**: Fast (mocked services)
**Coverage**: Business logic, error handling, edge cases

```python
@pytest.mark.asyncio
async def test_search_impl_success(mocker):
    """Test successful search execution."""
    # Mock the service
    mock_service = mocker.Mock()
    mock_service.search = AsyncMock(return_value=["result1", "result2"])
    mocker.patch("luka_bot.services.my_service.get_my_service", return_value=mock_service)

    # Test implementation directly
    result = await search_impl(
        query="test",
        user_id=123,
        thread_id="thread",
        language="en"
    )

    assert "result1" in result
    assert "result2" in result
    mock_service.search.assert_called_once()

@pytest.mark.asyncio
async def test_search_impl_service_unavailable(mocker):
    """Test error handling when service is down."""
    mock_service = mocker.Mock()
    mock_service.is_available.return_value = False
    mocker.patch("luka_bot.services.my_service.get_my_service", return_value=mock_service)

    result = await search_impl(query="test", user_id=123, thread_id="thread", language="en")

    assert "unavailable" in result.lower()
    assert "try again" in result.lower()

@pytest.mark.asyncio
async def test_search_impl_import_error(mocker):
    """Test graceful handling of missing service."""
    mocker.patch(
        "luka_bot.services.my_service.get_my_service",
        side_effect=ImportError("Module not found")
    )

    result = await search_impl(query="test", user_id=123, thread_id="thread", language="en")

    assert "not configured" in result.lower() or "not available" in result.lower()
```

#### Level 2: Integration Tests (Factory Function)

**Purpose**: Test tool creation and interface
**Speed**: Fast (no external services)
**Coverage**: StructuredTool interface, user context binding

```python
def test_create_search_tool():
    """Test factory creates valid StructuredTool."""
    tool = create_search_tool(user_id=123, thread_id="thread", language="en")

    assert tool.name == "search_tool"
    assert len(tool.description) > 0
    assert tool.args_schema is not None
    assert tool.func is not None
    assert tool.coroutine is not None

def test_tool_schema_validation():
    """Test input schema validation."""
    tool = create_search_tool(user_id=123, thread_id="thread", language="en")

    # Valid input should pass
    valid_input = {"query": "test", "max_results": 10}
    tool.args_schema(**valid_input)  # Should not raise

    # Invalid input should raise
    with pytest.raises(ValidationError):
        tool.args_schema(**{"query": "", "max_results": -1})
```

#### Level 3: E2E Tests (Full Tool Factory)

**Purpose**: Test tool registration and platform integration
**Speed**: Medium (some real services)
**Coverage**: Tool discovery, platform compatibility

```python
@pytest.mark.asyncio
async def test_tool_in_factory():
    """Test tool appears in create_tools_for_user."""
    from luka_agent.tools import create_tools_for_user

    tools = create_tools_for_user(
        user_id=123,
        thread_id="thread",
        knowledge_bases=["kb"],
        enabled_tools=["my_new_tool"],
        platform="telegram",
        language="en"
    )

    assert len(tools) >= 1
    assert any(t.name == "my_new_tool" for t in tools)

@pytest.mark.asyncio
async def test_tool_execution_end_to_end(mocker):
    """Test full execution flow through factory."""
    # Mock service
    mock_service = mocker.Mock()
    mock_service.search = AsyncMock(return_value="success")
    mocker.patch("luka_bot.services.my_service.get_my_service", return_value=mock_service)

    # Create tools
    tools = create_tools_for_user(
        user_id=123,
        thread_id="thread",
        knowledge_bases=["kb"],
        enabled_tools=["my_new_tool"],
        platform="telegram",
        language="en"
    )

    # Find and execute tool
    tool = next(t for t in tools if t.name == "my_new_tool")
    result = await tool.ainvoke({"query": "test"})

    assert isinstance(result, str)
    assert len(result) > 0
```

### Test Organization

```
luka_agent/tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_knowledge_base.py   # KB tool tests
├── test_youtube.py          # YouTube tool tests
├── test_sub_agent_tools.py  # Sub-agent tools tests
└── test_my_new_tool.py      # Your tool tests
```

<validation>
**Test Coverage Requirements:**

Before submitting, ensure:
- [ ] All implementation functions have unit tests
- [ ] Error paths are tested (ImportError, service unavailable, etc.)
- [ ] Factory function creates valid StructuredTool
- [ ] Tool appears in create_tools_for_user
- [ ] Input validation works correctly
- [ ] User-friendly error messages are returned
- [ ] Tests run successfully: `pytest luka_agent/tests/test_my_new_tool.py -v`

WHY: Layered testing catches different types of bugs - unit tests find logic errors, integration tests find interface issues, E2E tests find registration/platform problems.
</validation>
</success_criteria>

---

## Best Practices

<constraints>
### Naming Conventions

**Tool Files**: `{domain}.py`
- Examples: `knowledge_base.py`, `youtube.py`, `support.py`
- Use lowercase with underscores
- One word for simple tools, two words for complex domains

**Input Classes**: `{ToolName}Input`
- Examples: `SearchKnowledgeBaseInput`, `GetYouTubeTranscriptInput`
- PascalCase, descriptive

**Implementation Functions**: `{tool_name}_impl`
- Examples: `search_knowledge_base_impl`, `get_youtube_transcript_impl`
- snake_case, ends with `_impl`

**Factory Functions**: `create_{domain}_tool` or `create_{domain}_tools`
- Examples: `create_knowledge_base_tool`, `create_sub_agent_tools`
- Returns single tool or list of tools

WHY: Consistent naming makes code discoverable and maintainable.

### Code Organization

```python
"""
Module docstring - brief description.
"""

# Imports (grouped and sorted)
from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field

# Section markers for clarity
# =============================================================================
# Input Schema
# =============================================================================

class ToolInput(BaseModel):
    """Docstring."""
    ...

# =============================================================================
# Implementation
# =============================================================================

async def tool_impl(...) -> str:
    """Docstring."""
    ...

# =============================================================================
# Factory
# =============================================================================

def create_tool(...) -> StructuredTool:
    """Docstring."""
    ...

# Exports
__all__ = ["create_tool"]
```

WHY: Clear organization makes code easier to navigate and understand.

### Logging

```python
from loguru import logger

# ✅ GOOD - Context-rich logging
logger.debug(f"Executing {tool_name} for user {user_id}: query='{query[:50]}'")
logger.info(f"User {user_id} completed {action}")
logger.warning(f"Service unavailable for user {user_id}: {service_name}")
logger.error(f"Error in {tool_name} for user {user_id}: {exc}", exc_info=True)

# ❌ BAD - Missing context or sensitive data
print("Searching...")  # Don't use print
logger.info(f"Query: {query}")  # Missing user context
logger.debug(f"Password: {password}")  # Logging sensitive data
logger.error(f"Error: {exc}")  # Missing context (which tool? which user?)
```

<validation>
**Logging Rules:**

✅ **DO:**
- Include user_id and tool_name in logs
- Use appropriate levels (debug/info/warning/error)
- Truncate long strings in debug logs (query[:50])
- Use exc_info=True for exceptions
- Log configuration checks

❌ **DON'T:**
- Log sensitive data (passwords, tokens, API keys)
- Log entire responses (can be huge)
- Use print() instead of logger
- Skip user context
- Over-log (every line) or under-log (silent failures)

WHY: Logs are for debugging in production. Need enough context to diagnose issues without exposing sensitive data.
</validation>

### Platform Compatibility

<requirements>
**Platform-Agnostic Requirements:**

✅ **DO:**
- Return plain text strings (markdown supported)
- Work with user context only (user_id, thread_id, language)
- Keep output format simple and clear
- Test on both Telegram and Web

❌ **DON'T:**
- Include platform-specific formatting (Telegram keyboard markup)
- Assume platform features (inline buttons, media)
- Reference platform in tool logic
- Use platform-specific APIs

WHY: Tools must work identically on all platforms. Platform adapters handle rendering differences.

**Example - Platform-Agnostic Output:**

```python
# ✅ GOOD - Works everywhere
return (
    "Found 3 results:\n\n"
    "1. Result one\n"
    "2. Result two\n"
    "3. Result three\n\n"
    "Use the search tool again to refine."
)

# ❌ BAD - Platform-specific
from aiogram.types import InlineKeyboardMarkup
return InlineKeyboardMarkup(...)  # Only works on Telegram
```
</requirements>
</constraints>

---

## Existing Tools Reference

<context>
### 1. knowledge_base.py - Personal KB Search

**Purpose**: Search user's personal knowledge base (indexed messages)

**When to use**: User asks to find information from past conversations

**Input Schema**:
```python
class SearchKnowledgeBaseInput(BaseModel):
    query: str  # Search query or '*' for all messages
    from_user: str | None  # Filter by sender
    date_from: str | None  # Start date (7d, 1w, 1m, YYYY-MM-DD)
    date_to: str | None  # End date (YYYY-MM-DD)
    max_results: int  # 1-100 results (default: 10)
```

**Factory**: `create_knowledge_base_tool(user_id, thread_id, language, knowledge_bases)`

**Example Usage**:
```python
# LLM decides to search KB
search_knowledge_base(
    query="postgres connection issues",
    date_from="7d",
    max_results=10
)
```

**File**: `luka_agent/tools/knowledge_base.py`

---

### 2. sub_agent.py - Sub-Agent Management (5 tools)

**Purpose**: Discover, suggest, execute, and manage sub-agents (specialized guided experiences)

**Tools Provided**:
1. `get_available_sub_agents` - List all sub-agents
2. `get_sub_agent_details` - Get details for specific sub-agent
3. `suggest_sub_agent` - AI-powered recommendation based on user query
4. `get_sub_agent_step_guidance` - Get help for specific step
5. `execute_sub_agent` - Start/manage sub-agent execution

**Factory**: `create_sub_agent_tools(user_id, thread_id, language)` → Returns list of 5 tools

**Example Usage**:
```python
# LLM discovers available sub-agents
get_available_sub_agents()

# LLM gets details about trip planner
get_sub_agent_details(domain="trip_planner")

# LLM starts trip planner
execute_sub_agent(domain="trip_planner")
```

**File**: `luka_agent/tools/sub_agent.py`

---

### 3. youtube.py - YouTube Transcript Fetcher

**Purpose**: Fetch YouTube video transcripts for analysis

**When to use**: User shares YouTube link or asks about video content

**Input Schema**:
```python
class GetYouTubeTranscriptInput(BaseModel):
    video_url: str  # YouTube URL or video ID
    language: str  # Preferred language (en, ru, etc.) - default: "en"
```

**Factory**: `create_youtube_tool(user_id, thread_id, language)`

**Example Usage**:
```python
# User asks "summarize this video: https://youtube.com/watch?v=..."
get_youtube_transcript(
    video_url="https://youtube.com/watch?v=abc123",
    language="en"
)
```

**File**: `luka_agent/tools/youtube.py`

</context>

---

## Troubleshooting

<validation>
### Common Issues & Solutions

#### Tool Not Appearing in Enabled Tools

**Symptoms**: Tool doesn't show up when using create_tools_for_user

**Diagnose**:
1. Check registration in `luka_agent/tools/__init__.py`
   ```bash
   grep "my_new_tool" luka_agent/tools/__init__.py
   ```

2. Verify factory key matches enabled_tools list
   ```python
   # Must match exactly
   enabled_tools = ["my_new_tool"]
   tool_factories = {"my_new_tool": lambda: ...}
   ```

3. Check for import errors
   ```bash
   python -c "from luka_agent.tools import create_tools_for_user; print('OK')"
   ```

4. Check logs
   ```bash
   grep "Created tool" logs/luka_bot.log
   grep "Failed to create" logs/luka_bot.log
   ```

**Solution**: Ensure tool is registered in tool_factories dict with correct key

---

#### Circular Import Errors

**Symptoms**: `ImportError: cannot import name 'X' from partially initialized module`

**Cause**: Importing luka_bot services at module level

**Solution**: Move service imports inside implementation function

```python
# ❌ BAD - Module-level import
from luka_bot.services.my_service import get_my_service

async def my_tool_impl(...):
    service = get_my_service()
    ...

# ✅ GOOD - Runtime import
async def my_tool_impl(...):
    from luka_bot.services.my_service import get_my_service
    service = get_my_service()
    ...
```

---

#### Tool Returns None Instead of String

**Symptoms**: Tool execution completes but LLM gets None

**Diagnose**:
1. Check all code paths return string
2. Verify async function is awaited
3. Check error handling returns messages

**Solution**: Ensure every code path returns a string

```python
# ❌ BAD - Implicit None return
async def my_tool_impl(...):
    if condition:
        return "success"
    # Missing else - returns None

# ✅ GOOD - All paths return string
async def my_tool_impl(...):
    if condition:
        return "success"
    else:
        return "no results found"
```

---

#### Input Validation Fails

**Symptoms**: Tool raises ValidationError when invoked

**Diagnose**:
1. Check Field types match actual usage
2. Verify validation constraints (ge, le, etc.)
3. Test with edge cases

**Solution**: Review input schema validation

```python
# ❌ BAD - Too restrictive or wrong type
max_results: int = Field(..., ge=10)  # Forces min 10

# ✅ GOOD - Reasonable validation
max_results: int = Field(10, ge=1, le=100)  # Default 10, allow 1-100
```

---

#### Service Not Found Errors

**Symptoms**: ImportError or AttributeError when getting service

**Diagnose**:
1. Service exists in luka_bot/services/
2. Service has get_*_service() function
3. Import path is correct

**Solution**: Check service availability and handle gracefully

```python
try:
    from luka_bot.services.my_service import get_my_service
    service = get_my_service()
except ImportError:
    return "Service not available. Please check installation."
```

---

#### Tests Failing

**Symptoms**: pytest failures, import errors, or assertion errors

**Diagnose**:
1. Run specific test file: `pytest luka_agent/tests/test_my_tool.py -v`
2. Check test has all required fixtures
3. Verify mocks are set up correctly
4. Check async tests use @pytest.mark.asyncio

**Common Test Issues**:

```python
# ❌ BAD - Forgot async decorator
async def test_my_tool():
    result = await my_tool_impl(...)

# ✅ GOOD - Has async decorator
@pytest.mark.asyncio
async def test_my_tool():
    result = await my_tool_impl(...)

# ❌ BAD - Not mocking service
async def test_my_tool():
    result = await my_tool_impl(...)  # Tries to use real service

# ✅ GOOD - Mocking service
async def test_my_tool(mocker):
    mock_service = mocker.Mock()
    mocker.patch("luka_bot.services.my_service.get_my_service", return_value=mock_service)
    result = await my_tool_impl(...)
```

WHY troubleshooting section: Most issues stem from import timing, missing registrations, incorrect async handling, or inadequate testing. This section helps developers quickly identify and fix common problems.
</validation>

---

## Resources

- **Configuration Strategy**: `luka_agent/CONFIG.md` - How tools access external resources
- **Dependency Checking Guide**: `luka_agent/DEPENDENCY_CHECKING.md` - Error handling patterns
- **Sub-Agents Guide**: `luka_agent/sub_agents/README.md` - Creating guided experiences
- **Tool Template**: `luka_agent/tools/TEMPLATE.md` - Starter template for new tools
- **LangChain StructuredTool Docs**: https://python.langchain.com/docs/modules/agents/tools/custom_tools
- **Pydantic Field Docs**: https://docs.pydantic.dev/latest/concepts/fields/
- **Project Conventions**: `CLAUDE.md` in repo root

---

## Questions?

For issues or questions:
1. Check existing tools for similar patterns: `knowledge_base.py`, `youtube.py`, `sub_agent.py`
2. Review test suite: `luka_agent/tests/test_*_tools.py`
3. Check configuration docs: `luka_agent/CONFIG.md`
4. Check dependency docs: `luka_agent/DEPENDENCY_CHECKING.md`
5. Create GitHub issue with:
   - Tool name and purpose
   - Error logs
   - Steps to reproduce
   - Expected vs actual behavior

---

**Happy tool building! 🔧**
