"""
Sub-agent tools for luka_agent.

Sub-agents are specialized, domain-specific agents with their own:
- Context and documentation
- System prompts
- Tool descriptions
- Step-by-step guidance

Previously called "workflows", but the term "sub-agent" better reflects
their nature as autonomous, guided experiences.

Examples:
- sol_atlas_onboarding - Onboarding sub-agent for SOL Atlas
- trip_planner_onboarding - Trip planning sub-agent
- defi_onboarding - DeFi education sub-agent
"""

from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field

# =============================================================================
# Sub-Agent Discovery & Context Tools
# =============================================================================


async def get_available_sub_agents_impl() -> str:
    """Get a summary of all available sub-agents.

    Returns:
        Summary of all sub-agents with their capabilities
    """
    # Step 1: Try to import service
    try:
        from luka_bot.services.workflow_context_service import get_workflow_context_service
    except ImportError as import_err:
        logger.error(f"Unable to import workflow_context_service: {import_err}")
        return "Sub-agent system is not configured. Please ensure luka_bot services are installed correctly."

    # Step 2: Get service and check availability
    try:
        context_service = get_workflow_context_service()
        summary = await context_service.get_all_workflows_summary()

        # Check if any sub-agents are configured
        if not summary or summary.strip() == "" or "No workflows found" in summary:
            logger.warning("No sub-agents configured in system")
            return (
                "No sub-agents are currently configured. "
                "Sub-agents should be defined in luka_agent/sub_agents/ directory. "
                "Please check the configuration or contact your administrator."
            )

        logger.debug("Retrieved available sub-agents summary")
        return summary

    except Exception as exc:
        logger.error(f"Error getting available sub-agents: {exc}")
        return "Unable to retrieve available sub-agents. Please check your configuration and try again."


async def get_sub_agent_details_impl(domain: str, include_full_documentation: bool = True) -> str:
    """Get detailed information about a specific sub-agent.

    Args:
        domain: Sub-agent domain identifier
        include_full_documentation: Include README.md content

    Returns:
        Sub-agent details and documentation
    """
    # Step 1: Try to import service
    try:
        from luka_bot.services.workflow_context_service import get_workflow_context_service
    except ImportError as import_err:
        logger.error(f"Unable to import workflow_context_service: {import_err}")
        return "Sub-agent system is not configured. Please ensure luka_bot services are installed correctly."

    # Step 2: Get details
    try:
        context_service = get_workflow_context_service()
        context = await context_service.get_workflow_context(domain, include_full_documentation)

        if context:
            logger.debug(f"Retrieved sub-agent details for domain '{domain}'")
            return context

        # Provide helpful error with available options
        try:
            available = await context_service.get_all_workflows_summary()
            return f"Sub-agent '{domain}' not found.\n\nAvailable sub-agents:\n{available}"
        except Exception:
            return f"Sub-agent '{domain}' not found. Use get_available_sub_agents to see what's available."

    except Exception as exc:
        logger.error(f"Error getting sub-agent details for '{domain}': {exc}")
        return f"Unable to retrieve sub-agent details for '{domain}'. Please verify the domain name and try again."


async def suggest_sub_agent_impl(user_query: str) -> str:
    """Suggest the most appropriate sub-agent based on user query.

    Args:
        user_query: User's query or intent

    Returns:
        Suggested sub-agent with context
    """
    # Step 1: Try to import service
    try:
        from luka_bot.services.workflow_context_service import get_workflow_context_service
    except ImportError as import_err:
        logger.error(f"Unable to import workflow_context_service: {import_err}")
        return "Sub-agent system is not configured. Please ensure luka_bot services are installed correctly."

    # Step 2: Get suggestion
    try:
        context_service = get_workflow_context_service()
        suggested_context = await context_service.get_workflow_for_user_intent(user_query)

        if suggested_context:
            logger.debug(f"Suggested sub-agent based on query: '{user_query[:50]}...'")
            return f"Based on your query, I recommend this sub-agent:\n\n{suggested_context}"

        all_workflows = await context_service.get_all_workflows_summary()
        return f"I couldn't find a perfect match. Here are available sub-agents:\n\n{all_workflows}"

    except Exception as exc:
        logger.error(f"Error suggesting sub-agent for query '{user_query}': {exc}")
        return (
            "Unable to suggest a sub-agent at this time. "
            "Please try using get_available_sub_agents to browse all options."
        )


async def get_sub_agent_step_guidance_impl(domain: str, step_id: str) -> str:
    """Get guidance for a specific sub-agent step.

    Args:
        domain: Sub-agent domain
        step_id: Step identifier

    Returns:
        Step guidance and instructions
    """
    # Step 1: Try to import service
    try:
        from luka_bot.services.workflow_context_service import get_workflow_context_service
    except ImportError as import_err:
        logger.error(f"Unable to import workflow_context_service: {import_err}")
        return "Sub-agent system is not configured. Please ensure luka_bot services are installed correctly."

    # Step 2: Get guidance
    try:
        context_service = get_workflow_context_service()
        guidance = await context_service.get_workflow_step_guidance(domain, step_id)

        if guidance:
            logger.debug(f"Retrieved step guidance for '{domain}:{step_id}'")
            return guidance

        return (
            f"Step '{step_id}' not found in sub-agent '{domain}'. "
            "Please verify the step ID or use get_sub_agent_details to see available steps."
        )

    except Exception as exc:
        logger.error(f"Error getting step guidance for '{domain}:{step_id}': {exc}")
        return (
            f"Unable to retrieve step guidance for '{domain}:{step_id}'. "
            "Please verify the domain and step ID are correct."
        )


# =============================================================================
# Sub-Agent Execution Tool
# =============================================================================


class ExecuteSubAgentInput(BaseModel):
    """Input schema for sub-agent execution tool."""

    domain: str = Field(
        ...,
        description="Sub-agent domain identifier (e.g., 'sol_atlas_onboarding')",
    )


class GetSubAgentDetailsInput(BaseModel):
    """Input schema for get_sub_agent_details tool."""

    domain: str = Field(..., description="Sub-agent domain identifier")
    include_full_documentation: bool = Field(True, description="Include README.md content")


class SuggestSubAgentInput(BaseModel):
    """Input schema for suggest_sub_agent tool."""

    user_query: str = Field(..., description="User's query or intent")


class GetStepGuidanceInput(BaseModel):
    """Input schema for get_sub_agent_step_guidance tool."""

    domain: str = Field(..., description="Sub-agent domain")
    step_id: str = Field(..., description="Step identifier")


async def execute_sub_agent_impl(
    domain: str,
    user_id: int,
    thread_id: str,
    language: str,
) -> str:
    """Execute or manage sub-agent instances.

    Args:
        domain: Sub-agent domain identifier
        user_id: User ID
        thread_id: Thread ID for sub-agent context
        language: User's language

    Returns:
        Sub-agent execution status and next steps
    """
    # Step 1: Try to import services
    try:
        from luka_bot.services import (
            get_workflow_discovery_service,
            get_workflow_service,
        )
        from luka_bot.utils.i18n_helper import _
    except ImportError as import_err:
        logger.error(f"Unable to import workflow services: {import_err}")
        return (
            "Sub-agent execution system is not configured. "
            "Please ensure luka_bot workflow services are installed correctly."
        )

    # Step 2: Execute sub-agent
    try:
        logger.info(f"🤖 Executing sub-agent '{domain}' for user {user_id}")

        workflow_service = get_workflow_service()
        discovery_service = get_workflow_discovery_service()

        # Initialize services
        try:
            await discovery_service.initialize()
        except Exception as init_err:
            logger.error(f"Failed to initialize discovery service: {init_err}")
            return "Unable to initialize sub-agent discovery service. Please check your configuration and try again."

        if not workflow_service._initialized:  # pylint: disable=protected-access
            try:
                await workflow_service.initialize()
            except Exception as init_err:
                logger.error(f"Failed to initialize workflow service: {init_err}")
                return "Unable to initialize sub-agent workflow service. Please check your configuration and try again."

        workflow_def = discovery_service.get_workflow(domain)

        if not workflow_def:
            return _(
                f"Sub-agent with domain '{domain}' not found. Use get_available_sub_agents to see available options.",
                language=language,
            )

        # Check if user already has an active sub-agent for this domain
        existing_workflow = await workflow_service.get_active_workflow_for_user(user_id=user_id, domain=domain)

        if existing_workflow:
            # User already has an active sub-agent - return current step instruction
            logger.info(f"User {user_id} already has active sub-agent for {domain}, returning step instruction")

            # Get current step instruction
            current_step_id = existing_workflow.current_step
            if current_step_id:
                steps = workflow_def.tool_chain.get("steps", [])
                current_step = next((step for step in steps if step.get("id") == current_step_id), None)

                if current_step:
                    instruction = current_step.get("instruction", "").strip()
                    if instruction:
                        return _(
                            f"You're already in the {workflow_def.name} sub-agent. Current step: {instruction}",
                            language=language,
                        )

            return _(
                f"You have an active {workflow_def.name} sub-agent. Continue where you left off!",
                language=language,
            )

        # Start new sub-agent
        workflow_id = await workflow_service.start_workflow(
            user_id=user_id,
            domain=domain,
            workflow_name=workflow_def.name,
        )

        logger.info(f"Started sub-agent {workflow_id} for user {user_id}")

        # Get first step
        steps = workflow_def.tool_chain.get("steps", [])
        if steps:
            first_step = steps[0]
            instruction = first_step.get("instruction", "").strip()
            if instruction:
                return _(
                    f"Started {workflow_def.name} sub-agent!\n\n{instruction}",
                    language=language,
                )

        return _(
            f"Started {workflow_def.name} sub-agent! Let's begin.",
            language=language,
        )

    except Exception as e:
        logger.error(f"Error in execute_sub_agent: {e}", exc_info=True)
        return f"Error executing sub-agent: {str(e)}"


# =============================================================================
# Tool Factories
# =============================================================================


def create_sub_agent_tools(
    user_id: int,
    thread_id: str,
    language: str,
) -> list[StructuredTool]:
    """Create all sub-agent tools with user context.

    This returns 5 tools:
    1. get_available_sub_agents - List all sub-agents
    2. get_sub_agent_details - Get details about a specific sub-agent
    3. suggest_sub_agent - AI-powered sub-agent recommendation
    4. get_sub_agent_step_guidance - Get help for a specific step
    5. execute_sub_agent - Start/manage a sub-agent instance

    Args:
        user_id: User ID
        thread_id: Thread ID for sub-agent context
        language: User's language

    Returns:
        List of 5 LangChain StructuredTools for sub-agent management
    """
    return [
        # Discovery tools (no user binding needed)
        StructuredTool.from_function(
            name="get_available_sub_agents",
            description=(
                "Get a summary of all available sub-agents (guided experiences). "
                "Sub-agents are specialized assistants for specific tasks like onboarding, "
                "trip planning, or learning. Use this when user asks 'what can you help with?' "
                "or 'what sub-agents exist?'"
            ),
            func=lambda: get_available_sub_agents_impl(),
            coroutine=lambda: get_available_sub_agents_impl(),
        ),
        StructuredTool.from_function(
            name="get_sub_agent_details",
            description=(
                "Get detailed information about a specific sub-agent including documentation. "
                "Use this when user asks for details about a specific sub-agent or guided experience."
            ),
            func=lambda domain, include_full_documentation=True: get_sub_agent_details_impl(
                domain, include_full_documentation
            ),
            args_schema=GetSubAgentDetailsInput,
            coroutine=lambda domain, include_full_documentation=True: get_sub_agent_details_impl(
                domain, include_full_documentation
            ),
        ),
        StructuredTool.from_function(
            name="suggest_sub_agent",
            description=(
                "Suggest the most appropriate sub-agent based on user's query or intent. "
                "Use this when user describes a goal but doesn't know which sub-agent to use."
            ),
            func=lambda user_query: suggest_sub_agent_impl(user_query),
            args_schema=SuggestSubAgentInput,
            coroutine=lambda user_query: suggest_sub_agent_impl(user_query),
        ),
        StructuredTool.from_function(
            name="get_sub_agent_step_guidance",
            description=(
                "Get specific guidance for executing a particular step in a sub-agent. "
                "Use this when user is stuck on a sub-agent step and needs help."
            ),
            func=lambda domain, step_id: get_sub_agent_step_guidance_impl(domain, step_id),
            args_schema=GetStepGuidanceInput,
            coroutine=lambda domain, step_id: get_sub_agent_step_guidance_impl(domain, step_id),
        ),
        # Execution tool (user context bound)
        StructuredTool.from_function(
            name="execute_sub_agent",
            description=(
                "Start, manage, or complete a sub-agent (guided experience). "
                "Sub-agents provide step-by-step guidance for specific tasks like onboarding, "
                "tutorials, or complex workflows. Use this when the user wants to begin "
                "a structured process or guided experience."
            ),
            func=lambda domain: execute_sub_agent_impl(
                domain=domain,
                user_id=user_id,
                thread_id=thread_id,
                language=language,
            ),
            args_schema=ExecuteSubAgentInput,
            coroutine=lambda domain: execute_sub_agent_impl(
                domain=domain,
                user_id=user_id,
                thread_id=thread_id,
                language=language,
            ),
        ),
    ]


__all__ = ["create_sub_agent_tools"]
