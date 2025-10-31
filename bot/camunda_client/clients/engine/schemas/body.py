from datetime import datetime
from typing import List
from uuid import UUID

from camunda_client.types_ import BaseSchema, Variables
from .enums import SortOrder, TaskQuerySortEnum
from .response import ProfileSchema


class StartProcessInstanceSchema(BaseSchema):
    business_key: str | None = None
    variables: Variables | None = None


class ClaimTaskSchema(BaseSchema):
    user_id: str


class SortSchema(BaseSchema):
    sort_by: TaskQuerySortEnum | None = None
    sort_order: SortOrder | None = None


class GetTasksFilterSchema(BaseSchema):
    assignee: str | None = None
    candidate_group: str | None = None
    candidate_user: str | None = None
    sorting: list[SortSchema] | None = None
    task_id: str | None = None
    process_instance_id: UUID | None = None
    process_instance_business_key: str | None = None
    process_instance_business_key_in: list[str] | None = None
    process_definition_key: str | None = None
    process_definition_key_in: list[str] | None = None
    case_instance_id: str | None = None
    case_execution_id: str | None = None
    case_definition_id: str | None = None
    task_definition_key: str | None = None
    task_name: str | None = None
    task_name_like: str | None = None
    task_description: str | None = None
    task_description_like: str | None = None
    task_owner: str | None = None
    task_priority: int | None = None
    task_due_date: datetime | None = None
    task_due_date_before: datetime | None = None
    task_due_date_after: datetime | None = None
    task_follow_up_date: datetime | None = None
    task_follow_up_date_before: datetime | None = None
    task_follow_up_date_after: datetime | None = None
    tenant_id_in: List[str] | None = None
    without_tenant_id: bool | None = None


class GetHistoryTasksFilterSchema(BaseSchema):
    task_assignee: str | None = None
    finished: bool = False
    process_instance_id: UUID | None = None
    task_had_candidate_group: str | None = None
    process_instance_business_key: str | None = None


class SetAssigneeTaskSchema(BaseSchema):
    user_id: str


class SendCorrelationMessageSchema(BaseSchema):
    message_name: str
    business_key: str | None = None
    process_instance_id: UUID | None = None

    tenant_id: str | None = None
    without_tenant_id: bool = False

    correlation_keys: Variables | None = None
    local_correlation_keys: Variables | None = None
    process_variables: Variables | None = None
    process_variables_local: Variables | None = None

    all: bool = False
    result_enabled: bool = False
    variables_in_result_enabled: bool = False


class CredentialsSchema(BaseSchema):
    password: str


class CreateUserSchema(BaseSchema):
    profile: ProfileSchema
    credentials: CredentialsSchema


class CreateGroupMemberSchema(BaseSchema):
    user_id: str
    group_id: str
