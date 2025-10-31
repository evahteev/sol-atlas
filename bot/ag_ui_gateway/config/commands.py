"""
Command-to-Workflow Configuration

Maps bot commands to optional Camunda BPMN workflows with execution settings.
"""
from typing import Optional, List
from pydantic import BaseModel


class CommandWorkflowConfig(BaseModel):
    """Configuration for command-to-workflow mapping."""
    command: str
    workflow_key: Optional[str] = None
    auto_execute: bool = False
    description: str
    requires_auth: bool = True
    show_in_menu: bool = True
    parameters: List[dict] = []


# Command registry
COMMAND_WORKFLOWS = {
    "start": CommandWorkflowConfig(
        command="start",
        workflow_key="chatbot_start",
        auto_execute=True,
        description="Main menu with Quick Actions",
        requires_auth=False,  # Allow guest access for testing
        show_in_menu=True
    ),
    "tasks": CommandWorkflowConfig(
        command="tasks",
        workflow_key=None,
        auto_execute=False,
        description="View and manage tasks",
        requires_auth=True,
        show_in_menu=True
    ),
    "search": CommandWorkflowConfig(
        command="search",
        workflow_key=None,
        auto_execute=False,
        description="Search knowledge bases",
        requires_auth=True,
        show_in_menu=True
    ),
    "profile": CommandWorkflowConfig(
        command="profile",
        workflow_key=None,
        auto_execute=False,
        description="View profile and settings",
        requires_auth=True,
        show_in_menu=True
    ),
    "chat": CommandWorkflowConfig(
        command="chat",
        workflow_key=None,
        auto_execute=False,
        description="Manage conversation threads",
        requires_auth=True,
        show_in_menu=True
    ),
    "groups": CommandWorkflowConfig(
        command="groups",
        workflow_key=None,
        auto_execute=False,
        description="Manage groups",
        requires_auth=True,
        show_in_menu=True
    ),
    "catalog": CommandWorkflowConfig(
        command="catalog",
        workflow_key=None,
        auto_execute=False,
        description="Browse knowledge base catalog",
        requires_auth=False,  # Guest allowed
        show_in_menu=True
    ),
    "select_language": CommandWorkflowConfig(
        command="select_language",
        workflow_key=None,
        auto_execute=False,
        description="Select interface language",
        requires_auth=False,  # Guest allowed
        show_in_menu=False
    ),
    "set_language": CommandWorkflowConfig(
        command="set_language",
        workflow_key=None,
        auto_execute=False,
        description="Set specific language",
        requires_auth=False,  # Guest allowed
        show_in_menu=False
    ),
    "back_to_onboarding": CommandWorkflowConfig(
        command="back_to_onboarding",
        workflow_key=None,
        auto_execute=False,
        description="Return to onboarding form",
        requires_auth=False,  # Guest allowed
        show_in_menu=False
    )
}


def get_command_config(command: str) -> Optional[CommandWorkflowConfig]:
    """Get command configuration."""
    return COMMAND_WORKFLOWS.get(command)
