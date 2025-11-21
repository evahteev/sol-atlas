# Tool Template

**Use this template as a starting point for new tools. Replace all [PLACEHOLDERS] with your tool's specifics.**

---

```python
"""
[Tool Name] tool for luka_agent.

[Brief description of what the tool does and when to use it.]
"""

from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field


# =============================================================================
# Input Schema
# =============================================================================


class [ToolName]Input(BaseModel):
    """Input schema for [tool name] tool."""

    param1: str = Field(
        ...,  # Required field (use ... for required)
        description=(
            "[Clear description for LLM - explain when to use this parameter "
            "and what values are valid. Examples help!]"
        )
    )

    param2: int | None = Field(
        None,  # Optional field (use None for optional)
        description="[Description of optional parameter]"
    )

    param3: int = Field(
        10,  # Default value
        description="[Description with guidance on when to use different values]",
        ge=1,  # Validation: minimum value
        le=100  # Validation: maximum value
    )


# =============================================================================
# Implementation
# =============================================================================


async def [tool_name]_impl(
    param1: str,
    param2: int | None,
    param3: int,
    user_id: int,
    thread_id: str,
    language: str,
) -> str:
    """Implementation of [tool name] tool.

    Args:
        param1: [Description]
        param2: [Description]
        param3: [Description]
        user_id: User ID for context
        thread_id: Thread ID for context
        language: User's preferred language

    Returns:
        Result message or user-friendly error message
    """
    # Level 1: Check configuration (if feature uses external service)
    try:
        from luka_bot.core.config import settings
    except ImportError:
        logger.error("Unable to import settings - luka_bot config not available")
        return (
            "This feature is not configured. "
            "Please ensure luka_bot is properly installed."
        )

    # Check if feature is enabled (if applicable)
    if hasattr(settings, "[FEATURE]_ENABLED") and not settings.[FEATURE]_ENABLED:
        logger.warning("[FEATURE] is disabled in settings")
        return (
            "This feature is currently disabled. "
            "To enable it, set [FEATURE]_ENABLED=true in your .env file "
            "and restart the bot."
        )

    # Level 2: Check API key/credentials (if applicable)
    if hasattr(settings, "[API_KEY]") and not settings.[API_KEY]:
        logger.warning("[API_KEY] not configured")
        return (
            "This feature requires an API key. "
            "Please set [API_KEY] in your .env file. "
            "You can get an API key from [URL]."
        )

    # Level 3: Import service at runtime
    try:
        from luka_bot.services.[service_module] import get_[service]_service
    except ImportError as import_err:
        logger.error(f"Unable to import service: {import_err}")
        return (
            "Service is not available. "
            "Please ensure luka_bot services are installed correctly."
        )

    # Level 4: Check service health
    try:
        service = get_[service]_service()

        # Check if service is available (if service has is_available method)
        if hasattr(service, 'is_available') and not service.is_available():
            logger.warning("Service is unavailable")
            return (
                "Service is currently unavailable. "
                "Please try again later or check your configuration."
            )

    except Exception as e:
        logger.error(f"Service initialization error: {e}")
        return (
            "Unable to initialize service. "
            "Please check your configuration and try again."
        )

    # Level 5: Execute tool logic with specific error handling
    try:
        # Call service method
        result = await service.[method_name](
            param1=param1,
            param2=param2,
            param3=param3,
            # Add other params as needed
        )

        logger.debug(
            f"Tool '[tool_name]' executed successfully for user {user_id}: "
            f"param1='{param1[:50]}...'"
        )

        # Format result for LLM
        return format_result(result)

    except [SpecificException1] as e:
        # Handle specific known errors with targeted messages
        logger.warning(f"[SpecificException1] in [tool_name]: {e}")
        return (
            "[User-friendly error message for this specific error]. "
            "[How to fix or what to try next]."
        )

    except [SpecificException2] as e:
        logger.warning(f"[SpecificException2] in [tool_name]: {e}")
        return (
            "[User-friendly error message for this specific error]. "
            "[How to fix or what to try next]."
        )

    except Exception as e:
        # Catch all other exceptions
        logger.error(f"Unexpected error in '[tool_name]' for user {user_id}: {e}", exc_info=True)
        return (
            "An unexpected error occurred. "
            "Please try again or contact support if the issue persists."
        )


def format_result(result) -> str:
    """Format result for LLM consumption.

    Args:
        result: Raw result from service

    Returns:
        Formatted string for LLM
    """
    # Format result as needed for LLM
    # Examples:
    # - List results with numbers
    # - Add markdown formatting
    # - Include summary statistics
    # - Provide next action suggestions

    if not result:
        return "No results found. Try adjusting your search parameters."

    # Example formatting:
    formatted = f"Found {len(result)} results:\n\n"
    for i, item in enumerate(result[:10], 1):  # Limit to 10 results
        formatted += f"{i}. {item}\n"

    if len(result) > 10:
        formatted += f"\n... and {len(result) - 10} more results."

    return formatted


# =============================================================================
# Factory
# =============================================================================


def create_[tool]_tool(
    user_id: int,
    thread_id: str,
    language: str,
    # Add any additional context parameters needed
) -> StructuredTool:
    """Create [tool name] tool with user context bound.

    Args:
        user_id: User ID
        thread_id: Thread ID
        language: User's preferred language

    Returns:
        LangChain StructuredTool instance
    """
    return StructuredTool.from_function(
        name="[tool_name]",
        description=(
            "[Clear, concise description of what this tool does]. "
            "[When should the LLM use this tool? Be specific]. "
            "[What kind of queries or user requests trigger this tool?]"
        ),
        func=lambda param1, param2=None, param3=10: [tool_name]_impl(
            param1, param2, param3, user_id, thread_id, language
        ),
        coroutine=lambda param1, param2=None, param3=10: [tool_name]_impl(
            param1, param2, param3, user_id, thread_id, language
        ),
        args_schema=[ToolName]Input,
    )


__all__ = ["create_[tool]_tool"]
```

---

## Template Usage Instructions

### Step 1: Copy Template

```bash
cp luka_agent/tools/TEMPLATE.md luka_agent/tools/my_new_tool.py
```

### Step 2: Replace Placeholders

Search and replace all `[PLACEHOLDERS]`:

- `[Tool Name]` → e.g., "Twitter Search"
- `[tool name]` → e.g., "twitter search"
- `[tool_name]` → e.g., "twitter_search"
- `[ToolName]` → e.g., "TwitterSearch"
- `[tool]` → e.g., "twitter" (short form for factory name)
- `[FEATURE]` → e.g., "TWITTER" (for config var like TWITTER_ENABLED)
- `[API_KEY]` → e.g., "TWITTER_API_KEY"
- `[service_module]` → e.g., "twitter_service"
- `[service]` → e.g., "twitter"
- `[method_name]` → e.g., "search_tweets"
- `[SpecificException1]` → e.g., "RateLimitError"
- `[SpecificException2]` → e.g., "InvalidTokenError"

### Step 3: Customize

1. **Input Schema**: Add/remove parameters as needed
2. **Dependency Checks**: Keep all 5 levels, customize messages
3. **Service Integration**: Adjust service calls for your use case
4. **Error Handling**: Add specific exceptions your service might raise
5. **Result Formatting**: Customize format_result for your data
6. **Description**: Write clear LLM-friendly description

### Step 4: Register

Add to `luka_agent/tools/__init__.py`:

```python
from luka_agent.tools.my_new_tool import create_my_tool

tool_factories = {
    # ... existing tools ...
    "my_tool": lambda: create_my_tool(user_id, thread_id, language),
}
```

### Step 5: Test

Create `luka_agent/tests/test_my_new_tool.py`:

```python
import pytest
from luka_agent.tools.my_new_tool import create_my_tool, my_tool_impl

@pytest.mark.asyncio
async def test_my_tool_impl_success():
    """Test successful execution."""
    result = await my_tool_impl(
        param1="test",
        param2=None,
        param3=10,
        user_id=123,
        thread_id="test",
        language="en"
    )
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_my_tool_impl_service_unavailable(mocker):
    """Test error handling when service is down."""
    mock_service = mocker.Mock()
    mock_service.is_available.return_value = False
    mocker.patch(
        "luka_bot.services.my_service.get_my_service",
        return_value=mock_service
    )

    result = await my_tool_impl("test", None, 10, 123, "test", "en")
    assert "unavailable" in result.lower()

@pytest.mark.asyncio
async def test_my_tool_impl_import_error(mocker):
    """Test graceful handling of missing service."""
    mocker.patch(
        "luka_bot.services.my_service.get_my_service",
        side_effect=ImportError("Module not found")
    )

    result = await my_tool_impl("test", None, 10, 123, "test", "en")
    assert "not available" in result.lower()

def test_create_my_tool():
    """Test factory creates valid StructuredTool."""
    tool = create_my_tool(123, "test", "en")
    assert tool.name == "my_tool"
    assert tool.description != ""
    assert tool.args_schema is not None

@pytest.mark.asyncio
async def test_my_tool_in_factory():
    """Test tool appears in create_tools_for_user."""
    from luka_agent.tools import create_tools_for_user

    tools = create_tools_for_user(
        user_id=123,
        thread_id="test",
        knowledge_bases=["kb"],
        enabled_tools=["my_tool"],
        platform="telegram",
        language="en"
    )

    assert len(tools) >= 1
    assert any(t.name == "my_tool" for t in tools)
```

### Step 6: Format and Check

```bash
# Format code
ruff format luka_agent/tools/my_new_tool.py

# Check for issues
ruff check luka_agent/tools/my_new_tool.py

# Run tests
pytest luka_agent/tests/test_my_new_tool.py -v
```

---

## Tips

✅ **DO**:
- Keep all 5 dependency check levels
- Write LLM-friendly Field descriptions
- Provide specific error messages
- Log with user context
- Test all error paths

❌ **DON'T**:
- Import services at module level
- Skip dependency checks
- Return technical errors
- Use platform-specific code
- Forget to register in factory

---

**Need help?** Check `luka_agent/tools/README.md` for complete development guide.
