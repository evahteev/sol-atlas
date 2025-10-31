"""
Workflow tools for Luka bot dialog workflow integration.
Ported from bot_server implementation with Luka-specific context handling.
"""

from typing import List
from loguru import logger
from pydantic import Field
from pydantic_ai import Tool, RunContext

from luka_bot.utils.i18n_helper import _, get_user_language
from luka_bot.agents.context import ConversationContext
from luka_bot.services import (
    get_workflow_discovery_service,
    get_workflow_service,
    get_workflow_context_service,
)


def _localized_value(key: str, fallback: str, language: str | None) -> str:
    """Return localized value with fallback support."""
    if not language:
        return fallback

    localized = _(key, language=language)
    if not localized or localized == key:
        return fallback
    return localized


def _is_tool_enabled(ctx: ConversationContext, tool_name: str) -> bool:
    """Check whether a workflow tool is enabled for the current context."""
    try:
        return ctx.has_tool_enabled(tool_name)
    except AttributeError:
        # Backward compatibility with minimal context
        return True


def get_prompt_description() -> str:
    """Get workflow-specific prompt additions."""
    try:
        prompt = _("workflow_tools_prompt")
        if prompt == "workflow_tools_prompt" or len(prompt) < 20:
            raise LookupError("Translation key not resolved")
        return prompt
    except (LookupError, Exception):
        # Fallback for test environment
        return (
            "**Workflow Execution**: You can discover, explore, and execute predefined workflows for "
            "common tasks like psychology sessions and project planning. "
            "Use list_available_workflows to see options, get_workflow_details for specifics, "
            "and execute_workflow to run them."
        )


async def list_available_workflows(
    ctx: RunContext[ConversationContext],
) -> str:
    """List all available workflows that can be executed."""
    conv_ctx = ctx.deps
    try:
        language = await get_user_language(conv_ctx.user_id)
    except Exception:
        language = None

    if not _is_tool_enabled(conv_ctx, "workflow"):
        return _("Workflow tools are disabled for this conversation.", language=language)

    logger.info(f"Listing available workflows for user {conv_ctx.user_id}")

    try:
        discovery_service = get_workflow_discovery_service()
        await discovery_service.initialize()
        workflows = discovery_service.get_all_workflows()

        if not workflows:
            return _("No workflows are currently available.", language=language)

        result_lines = [_("Available workflows:", language=language), ""]

        for domain, workflow in workflows.items():
            localized_name = _localized_value(f"workflow.{domain}.name", workflow.name, language)
            localized_description = _localized_value(
                f"workflow.{domain}.description", workflow.description, language
            )

            result_lines.append(f"📋 **{localized_name}** (v{workflow.version})")
            result_lines.append(f"   {_('Domain', language=language)}: `{domain}`")
            result_lines.append(f"   {localized_description}")
            if workflow.estimated_duration:
                result_lines.append(
                    f"   ⏱️ {_('Estimated time', language=language)}: {workflow.estimated_duration}"
                )
            result_lines.append("")

        result_lines.append(
            _("Use execute_workflow with the domain name to run a workflow.", language=language)
        )
        return "\n".join(result_lines)

    except Exception as exc:
        logger.error(f"Error listing workflows: {exc}")
        return _("Failed to list available workflows. Please try again later.", language=language)


async def get_workflow_details(
    ctx: RunContext[ConversationContext],
    domain: str = Field(description="Workflow domain identifier"),
) -> str:
    """Get detailed information about a specific workflow."""
    conv_ctx = ctx.deps
    try:
        language = await get_user_language(conv_ctx.user_id)
    except Exception:
        language = None

    if not _is_tool_enabled(conv_ctx, "workflow"):
        return _("Workflow tools are disabled for this conversation.", language=language)

    logger.info(f"Getting workflow details for domain '{domain}'")

    try:
        context_service = get_workflow_context_service()
        details = await context_service.get_workflow_context(domain, include_documentation=True)

        if not details:
            return _(f"Workflow with domain '{domain}' not found.", language=language)

        return details

    except Exception as exc:
        logger.error(f"Error getting workflow details for domain '{domain}': {exc}")
        return _("Failed to get workflow details. Please try again later.", language=language)


async def execute_workflow(
    ctx: RunContext[ConversationContext],
    domain: str = Field(description="Workflow domain identifier to execute"),
) -> str:
    """Execute a workflow for the user."""
    conv_ctx = ctx.deps
    try:
        language = await get_user_language(conv_ctx.user_id)
    except Exception:
        language = None

    if not _is_tool_enabled(conv_ctx, "workflow"):
        return _("Workflow tools are disabled for this conversation.", language=language)

    logger.info(f"Executing workflow '{domain}' for user {conv_ctx.user_id}")

    try:
        workflow_service = get_workflow_service()
        discovery_service = get_workflow_discovery_service()
        await discovery_service.initialize()
        workflow_def = discovery_service.get_workflow(domain)

        if not workflow_def:
            return _(
                f"Workflow with domain '{domain}' not found. "
                "Use list_available_workflows to see available options."
            , language=language)

        if not workflow_service._initialized:  # pylint: disable=protected-access
            await workflow_service.initialize()

        workflow_id = await workflow_service.start_workflow(
            user_id=conv_ctx.user_id,
            domain=domain,
        )

        status = await workflow_service.get_workflow_status(workflow_id)
        if status is None:
            return _("Failed to retrieve workflow status. Please try again later.", language=language)

        localized_name = _localized_value(f"workflow.{domain}.name", workflow_def.name, language)

        result_lines = [
            f"🚀 **{_('Started Workflow', language=language)}**: {localized_name}",
            "",
            f"**{_('Workflow ID', language=language)}**: `{workflow_id}`",
            f"**{_('Status', language=language)}**: {status.state.title()}",
            f"**{_('Progress', language=language)}**: {status.progress:.0%}",
        ]

        if status.current_step:
            result_lines.append(f"**{_('Current Step', language=language)}**: {status.current_step}")
        if workflow_def.estimated_duration:
            result_lines.append(
                f"**{_('Estimated Duration', language=language)}**: {workflow_def.estimated_duration}"
            )
        result_lines.append("")

        try:
            await workflow_service.execute_workflow_step(
                workflow_id=workflow_id,
                step_name="initialize",
                context={"user_id": conv_ctx.user_id, "domain": domain},
            )

            updated_status = await workflow_service.get_workflow_status(workflow_id)
            if updated_status:
                result_lines.append(f"✅ **{_('Initialization Step Completed', language=language)}**")
                result_lines.append(
                    f"**{_('Updated Progress', language=language)}**: {updated_status.progress:.0%}"
                )
                result_lines.append("")

                if updated_status.state == "completed":
                    result_lines.append(
                        f"🎉 **{_('Workflow Completed Successfully!', language=language)}**"
                    )
                elif updated_status.state == "running":
                    result_lines.append(f"▶️ **{_('Workflow is now running...', language=language)}**")
                    result_lines.append(
                        _(
                            "The workflow will continue processing. You can check its status later.",
                            language=language,
                        )
                    )
                    result_lines.append("")

        except Exception as step_error:  # pragma: no cover - logging path
            logger.error(f"Error executing workflow step: {step_error}")
            result_lines.append(f"⚠️ **Step Execution Warning**: {step_error}")
            result_lines.append(
                _("Workflow started but the first step encountered issues.", language=language)
            )
            result_lines.append("")

        result_lines.append(f"📋 **{_('What happens next:', language=language)}**")
        steps = workflow_def.tool_chain.get("steps", [])

        if steps:
            result_lines.append(
                _("This workflow has {count} total steps:", language=language).format(count=len(steps))
            )
            for idx, step in enumerate(steps[:3], 1):
                step_name = step.get("name", f"Step {idx}")
                result_lines.append(f"   {idx}. {step_name}")
            if len(steps) > 3:
                result_lines.append(
                    _("   ... and {count} more steps", language=language).format(count=len(steps) - 3)
                )

        result_lines.append("")
        result_lines.append(
            f"💡 **{_('Tip', language=language)}**: "
            + _(
                "You can ask me about the workflow progress or request specific guidance for each step!",
                language=language,
            )
        )

        return "\n".join(result_lines)

    except Exception as exc:
        logger.error(f"Error executing workflow '{domain}': {exc}")
        return _(f"Failed to execute workflow '{domain}'. Error: {str(exc)}", language=language)


def get_tools() -> List[Tool]:
    """Get workflow-related tools for Luka bot."""
    return [
        Tool(
            list_available_workflows,
            name="list_available_workflows",
            description="List all available workflows that can be executed",
        ),
        Tool(
            get_workflow_details,
            name="get_workflow_details",
            description="Get detailed information about a specific workflow",
        ),
        Tool(
            execute_workflow,
            name="execute_workflow",
            description="Execute a workflow for the user",
        ),
    ]


__all__ = [
    "get_prompt_description",
    "list_available_workflows",
    "get_workflow_details",
    "execute_workflow",
    "get_tools",
]
