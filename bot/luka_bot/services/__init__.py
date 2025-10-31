"""
Luka bot services package with lazy accessors to avoid heavy imports at module load.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from luka_bot.services.elasticsearch_service import LukaElasticsearchService
    from luka_bot.services.message_state_service import MessageStateService
    from luka_bot.services.workflow_service import WorkflowService
    from luka_bot.services.workflow_discovery_service import WorkflowDiscoveryService
    from luka_bot.services.workflow_context_service import WorkflowContextService
    from luka_bot.services.workflow_definition_service import WorkflowDefinitionService


def get_elasticsearch_service():
    from luka_bot.services.elasticsearch_service import get_elasticsearch_service as _get

    return _get()


def get_message_state_service():
    from luka_bot.services.message_state_service import get_message_state_service as _get

    return _get()


def get_workflow_service():
    from luka_bot.services.workflow_service import get_workflow_service as _get

    return _get()


def get_workflow_discovery_service():
    from luka_bot.services.workflow_discovery_service import get_workflow_discovery_service as _get

    return _get()


def get_workflow_context_service():
    from luka_bot.services.workflow_context_service import get_workflow_context_service as _get

    return _get()


def get_workflow_definition_service():
    from luka_bot.services.workflow_definition_service import get_workflow_definition_service as _get

    return _get()


__all__ = [
    "get_elasticsearch_service",
    "get_message_state_service",
    "get_workflow_service",
    "get_workflow_discovery_service",
    "get_workflow_context_service",
    "get_workflow_definition_service",
]
