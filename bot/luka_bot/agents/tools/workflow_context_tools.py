"""
Workflow context helper tools for Luka bot.
Provides utilities for agents to access workflow documentation and guidance.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from luka_bot.services.workflow_context_service import get_workflow_context_service, WorkflowContextService

_workflow_context_service: Optional[WorkflowContextService] = None


async def _get_service() -> WorkflowContextService:
    """Lazy-load workflow context service."""
    global _workflow_context_service

    if _workflow_context_service is None:
        _workflow_context_service = get_workflow_context_service()
    return _workflow_context_service


async def get_available_workflows() -> str:
    """Get a summary of all available workflows that can be used to guide users."""
    try:
        context_service = await _get_service()
        summary = await context_service.get_all_workflows_summary()

        logger.debug("Retrieved available workflows summary for Luka agent")
        return summary

    except Exception as exc:
        logger.error(f"Error getting available workflows: {exc}")
        return "Error: Unable to retrieve available workflows at this time."


async def get_workflow_details(domain: str, include_full_documentation: bool = True) -> str:
    """
    Get detailed information about a specific workflow including documentation.
    """
    try:
        context_service = await _get_service()
        context = await context_service.get_workflow_context(domain, include_full_documentation)

        if context:
            logger.debug(f"Retrieved workflow details for domain '{domain}'")
            return context
        return f"Workflow '{domain}' not found. Use get_available_workflows() to see what's available."

    except Exception as exc:
        logger.error(f"Error getting workflow details for '{domain}': {exc}")
        return f"Error: Unable to retrieve workflow details for '{domain}'."


async def suggest_workflow_for_user_query(user_query: str) -> str:
    """Suggest the most appropriate workflow based on a user's query or intent."""
    try:
        context_service = await _get_service()
        suggested_context = await context_service.get_workflow_for_user_intent(user_query)

        if suggested_context:
            logger.debug(f"Suggested workflow based on query: '{user_query[:50]}...'")
            return f"Based on your query, I recommend this workflow:\n\n{suggested_context}"

        all_workflows = await context_service.get_all_workflows_summary()
        return f"I couldn't find a perfect match for your request. Here are the available workflows:\n\n{all_workflows}"

    except Exception as exc:
        logger.error(f"Error suggesting workflow for query '{user_query}': {exc}")
        return "Error: Unable to suggest a workflow at this time."


async def get_workflow_step_guidance(domain: str, step_id: str) -> str:
    """Get specific guidance for executing a particular step in a workflow."""
    try:
        context_service = await _get_service()
        guidance = await context_service.get_workflow_step_guidance(domain, step_id)

        if guidance:
            logger.debug(f"Retrieved step guidance for '{domain}:{step_id}'")
            return guidance
        return f"Step '{step_id}' not found in workflow '{domain}'. Check the workflow details for available steps."

    except Exception as exc:
        logger.error(f"Error getting step guidance for '{domain}:{step_id}': {exc}")
        return f"Error: Unable to retrieve step guidance for '{domain}:{step_id}'."


WORKFLOW_CONTEXT_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_available_workflows",
        "description": "Get a summary of all available workflows",
        "function": get_available_workflows,
        "parameters": {},
    },
    {
        "name": "get_workflow_details",
        "description": "Get detailed information about a specific workflow",
        "function": get_workflow_details,
        "parameters": {
            "domain": {"type": "string", "description": "Workflow domain"},
            "include_full_documentation": {
                "type": "boolean",
                "description": "Include README.md content",
                "default": True,
            },
        },
    },
    {
        "name": "suggest_workflow_for_user_query",
        "description": "Suggest appropriate workflow based on user query",
        "function": suggest_workflow_for_user_query,
        "parameters": {
            "user_query": {"type": "string", "description": "User's query or intent"},
        },
    },
    {
        "name": "get_workflow_step_guidance",
        "description": "Get guidance for a specific workflow step",
        "function": get_workflow_step_guidance,
        "parameters": {
            "domain": {"type": "string", "description": "Workflow domain"},
            "step_id": {"type": "string", "description": "Step identifier"},
        },
    },
]


def get_workflow_tools_for_agent() -> List[Dict[str, Any]]:
    """Get workflow context tools for LLM agent integration."""
    return WORKFLOW_CONTEXT_TOOLS


__all__ = [
    "get_workflow_tools_for_agent",
    "WORKFLOW_CONTEXT_TOOLS",
]
