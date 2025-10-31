from datetime import datetime
from typing import Union, Optional, List, Any
from uuid import UUID

from camunda_client.types_ import (
    BaseSchema,
    MayBeNullableList,
    Variables,
    VariableValueSchema,
)
from camunda_client.utils import get_value

from .enums import DelegationState


class LinkSchema(BaseSchema):
    rel: str | None = None
    href: str | None = None
    method: str | None = None


class ProcessInstanceSchema(BaseSchema):
    id: str
    definition_id: Optional[str] = None
    links: Optional[List[LinkSchema]] = []
    business_key: Optional[str] = None
    case_instance_id: Optional[str] = None
    suspended: Optional[bool] = False
    tenant_id: Optional[str] = None
    process_definition_id: Optional[str] = None
    process_definition_key: Optional[str] = None
    process_definition_name: Optional[str] = None
    process_definition_version: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    removal_time: Optional[datetime] = None
    duration_in_millis: Optional[int] = None
    start_user_id: Optional[str] = None
    start_activity_id: Optional[str] = None
    delete_reason: Optional[str] = None
    root_process_instance_id: Optional[UUID] = None
    super_process_instance_id: Optional[str] = None
    super_case_instance_id: Optional[str] = None
    state: Optional[str] = None


class VariableValueInfo(BaseSchema):
    # Assuming valueInfo might be expanded in the future,
    # but leaving it empty as per the provided example.
    pass


class Variable(BaseSchema):
    type: str
    value: Optional[Any]  # Assuming values can be of different types based on the "type" field
    valueInfo: VariableValueInfo


class ProcessVariablesSchema(BaseSchema):
    name: str
    value: Variable
    # Add more variables as needed


class ProcessDefinitionSchema(BaseSchema):
    id: str
    key: str | None = None
    category: str | None = None
    description: str | None = None
    name: str | None = None
    version: int | None = None
    resource: str | None = None
    deployment_id: str | None = None
    diagram: str | None = None
    suspended: bool | None = None
    tenant_id: str | None = None
    version_tag: str | None = None
    history_time_to_live: int | None = None
    startable_in_task_list: bool | None = None
    variables: Variables | None = None


class ProfileSchema(BaseSchema):
    id: str
    first_name: str | None
    last_name: str | None
    email: str | None


class CamundaFormRefSchema(BaseSchema):
    key: str | None = None
    binding: str | None = None
    value: str | None = None


class TaskSchema(BaseSchema):
    id: UUID
    name: str
    assignee: str | None = None
    owner: str | None = None
    created: datetime
    due: datetime | None = None
    last_updated: datetime | None = None
    delegation_state: DelegationState | None = None
    description: str | None = None
    execution_id: UUID
    parent_task_id: str | None = None
    priority: int
    process_definition_id: str
    process_instance_id: UUID
    case_execution_id: str | None = None
    case_definition_id: str | None = None
    case_instance_id: str | None = None
    task_definition_key: str | None = None
    camundaFormRef: CamundaFormRefSchema | None = None
    suspended: bool
    tenant_id: str | None
    state: str | None = None

    @property
    def assignee_uuid(self) -> UUID:
        return UUID(get_value(self.assignee))


class Layout(BaseSchema):
    row: str
    columns: Optional[int] = None
    components: Optional[List['Component']] = None


class Component(BaseSchema):
    label: Optional[str] = None
    type: str
    layout: Layout
    id: str
    key: Optional[str] = None
    description: Optional[str] = None
    defaultValue: Optional[Union[str, int]] = None
    action: Optional[str] = None
    properties: Optional[dict[str, Any]] = None


# Rebuild forward references so Layout can include nested Components
Layout.model_rebuild()


class Exporter(BaseSchema):
    name: str
    version: str


class CamundaForm(BaseSchema):
    components: list[Component]
    type: str
    id: str
    exporter: Exporter
    executionPlatform: str
    executionPlatformVersion: str
    schemaVersion: int


class HistoryProcessInstanceSchema(BaseSchema):
    id: str
    business_key: str | None = None
    process_definition_id: str
    process_definition_key: str
    process_definition_name: str | None = None
    process_definition_version: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    removal_time: datetime | None = None
    duration_in_millis: int | None = None
    start_user_id: str | None = None
    start_activity_id: str | None = None
    delete_reason: str | None = None
    root_process_instance_id: UUID | None = None
    super_process_instance_id: str | None = None
    super_case_instance_id: str | None = None
    case_instance_id: str | None = None
    tenant_id: str | None = None
    state: str | None = None


class HistoricTaskInstanceSchema(BaseSchema):
    id: UUID
    process_definition_key: str
    process_definition_id: str
    process_instance_id: UUID
    execution_id: str
    case_definition_key: str | None = None
    case_definition_id: str | None = None
    case_instance_id: str | None = None
    case_execution_id: str | None = None
    activity_instance_id: str | None = None
    name: str | None = None
    description: str | None = None
    delete_reason: str | None = None
    owner: str | None = None
    assignee: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration: int | None = None
    task_definition_key: str
    priority: int | None = None
    due: datetime | None = None
    parent_task_id: str | None = None
    follow_up: datetime | None = None
    tenant_id: str | None = None
    removal_time: datetime | None = None
    root_process_instance_id: UUID | None = None


class VariableInstanceSchema(VariableValueSchema):
    id: str
    name: str
    process_definition_id: str
    process_instance_id: UUID
    execution_id: str
    case_instance_id: str | None = None
    case_execution_id: str | None = None
    task_id: str | None = None
    batch_id: str | None = None
    activity_instance_id: str | None = None
    tenant_id: str | None = None
    error_message: str | None = None
