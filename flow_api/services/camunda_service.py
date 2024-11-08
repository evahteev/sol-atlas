import asyncio
import json
import logging
import uuid

import httpx
from aiocache import cached

from camunda_client import CamundaEngineClient, Variables
from camunda_client.clients.dto import AuthData
from camunda_client.clients.engine.schemas import (
    ProcessDefinitionQuerySchema,
    GetTasksFilterSchema, GetHistoryTasksFilterSchema,
)
from camunda_client.clients.engine.schemas.body import CreateUserSchema, CredentialsSchema
from camunda_client.clients.engine.schemas.query import (
    FormVariablesQuerySchema,
    ProcessInstanceQuerySchema, HistoryProcessInstanceQuerySchema,
)
from camunda_client.clients.engine.schemas.response import HistoryProcessInstanceSchema, ProcessInstanceSchema, \
    ProfileSchema
from camunda_client.clients.schemas import PaginationParams
from camunda_client.exceptions import CamundaClientError
from configs.app_config import settings
from flow_api.flow_models import Flow
from flow_api.models import User
from flow_api.utils import DECORATOR_CACHE_CONFIG

ENGINE_URL = settings.ENGINE_URL


@cached(ttl=60, **DECORATOR_CACHE_CONFIG)
async def get_process_definitions(
    camunda_user_id: str,
    camunda_key: str,
    prefix: str | None = None,
    variables: dict | None = None,
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        all_process_definitions = await camunda_client.get_process_definitions(
            ProcessDefinitionQuerySchema(**variables)
        )
    filtered_process_definitions = {}
    for process_definition in all_process_definitions:
        if filtered_process_definitions.get(process_definition.key):
            if process_definition.version > filtered_process_definitions[process_definition.key].version:
                filtered_process_definitions[process_definition.key] = process_definition
        if prefix and process_definition.key.startswith(prefix):
            filtered_process_definitions[process_definition.name] = process_definition
        elif not prefix:
            filtered_process_definitions[process_definition.name] = process_definition
    return list(filtered_process_definitions.values())


@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def start_process_instance(
    camunda_user_id: str,
    camunda_key: str,
    key: str,
    variables: dict,
    business_key: str = None,
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        process_instance = await camunda_client.start_process(
            process_key=key,
            business_key=business_key,
            variables=variables,
        )
    return process_instance


# @cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def get_tasks_for_user(
    camunda_user_id: str,
    camunda_key: str,
    include_history: bool = True,
    schema: GetTasksFilterSchema | None = None,
    pagination: PaginationParams | None = None,
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        if not schema:
            schema = GetTasksFilterSchema(
                assignee=camunda_user_id,
            )
        else:
            schema.assignee = camunda_user_id
        if not pagination:
            pagination = PaginationParams(
                limit=100,
                offset=0,
            )
        tasks = await camunda_client.get_tasks(
            schema=schema,
            pagination=pagination,
        )
        history_tasks = []
        if include_history:
            if not schema:
                history_tasks_schema = GetHistoryTasksFilterSchema(
                    task_assignee=camunda_user_id,
                    finished=True,
                )
            else:
                history_tasks_schema = GetHistoryTasksFilterSchema(
                    **schema.dict(),
                )
                history_tasks_schema.task_assignee = camunda_user_id
            history_tasks = await camunda_client.get_history_tasks(
                schema=history_tasks_schema,
                pagination=pagination,
            )
    resulting_tasks = []
    for task in tasks:
        resulting_tasks.append(
            {**task.dict(), **{'state': 'ACTIVE'}}
        )

    for history_task in history_tasks:
        resulting_tasks.append(
            {
             'id': history_task.id,
             'name': history_task.name,
             'assignee': history_task.assignee,
             'owner': history_task.owner,
             'created': history_task.start_time,
             'due': history_task.due,
             'last_updated': history_task.end_time,
             'delegation_state': None,
             'description': history_task.description,
             'execution_id': history_task.execution_id,
             'parent_task_id': history_task.parent_task_id,
             'priority': 0,
             'process_definition_id': history_task.process_definition_id,
             'process_instance_id': history_task.process_instance_id,
             'case_execution_id': history_task.case_execution_id,
             'case_definition_id': history_task.case_definition_id,
             'case_instance_id': history_task.case_instance_id,
             'task_definition_key': history_task.task_definition_key,
             'suspended': False,
             'tenant_id': history_task.tenant_id,
             'state': 'COMPLETED'
             }
        )

    return resulting_tasks


@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def get_task_form_variables(
    camunda_user_id: str,
    camunda_key: str,
    task_id: str,
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        form_variables = await camunda_client.get_task_form_variables(
            task_id=task_id,
        )
    return form_variables


@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def get_task_form_variables_new(
    camunda_user_id: str,
    camunda_key: str,
    task_id: str,
    params: dict | None = None,
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        if params:
            form_variables_query = FormVariablesQuerySchema(**params)
        else:
            form_variables_query = None
        form_variables = await camunda_client.get_task_form_variables(
            task_id=task_id,
            params=form_variables_query,
        )
    return form_variables


@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def complete_task(
    camunda_user_id: str,
    camunda_key: str,
    task_id: str,
    variables: dict | None = None,
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        await camunda_client.complete_task(
            task_id=task_id,
            variables=variables,
        )


@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def modify_task_variables(
    camunda_user_id: str,
    camunda_key: str,
    task_id: str,
    variables: dict | None = None,
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        await camunda_client.modify_task_form_variables(
            task_id=task_id,
            variables=variables,
        )


@cached(ttl=2, **DECORATOR_CACHE_CONFIG)
async def get_process_instances(
    camunda_user_id: str,
    camunda_key: str,
    business_key: str | None = None,
    params: dict | None = None,
):
    params = params or {}
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        history_request_params = {**params, **{"active": True}}
        if business_key:
            params['business_key'] = business_key
            history_request_params["process_instance_business_key"] = business_key
        process_instances = await camunda_client.get_process_instances(params=ProcessInstanceQuerySchema(**params))
        history_process_instances = await camunda_client.get_history_process_instances(
            params=HistoryProcessInstanceQuerySchema(**history_request_params),
        )
        result_history_process_instances = {}
        for history_process_instance in history_process_instances:
            history_process_instance: HistoryProcessInstanceSchema
            result_history_process_instances[history_process_instance.id] = history_process_instance.dict()

        resulting_process_instances = []
        for process_instance in process_instances:
            process_instance: ProcessInstanceSchema

            if result_history_process_instances.get(process_instance.id):
                resulting_process_instances.append({
                    **process_instance.dict(),
                    **result_history_process_instances[process_instance.id]})

    return resulting_process_instances


@cached(ttl=2, **DECORATOR_CACHE_CONFIG)
async def get_process_instance(
    camunda_user_id: str, camunda_key: str, process_instance_id: str
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        process_instance = await camunda_client.get_process_instance(
            process_instance_id=process_instance_id
        )
        history_process_instance = await camunda_client.get_history_process_instance(
            process_instance_id=process_instance_id
        )
        resulting_process_instance = {**process_instance.dict(), **history_process_instance.dict()}
    return resulting_process_instance


@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def get_process_instance_variables(
    camunda_user_id: str, camunda_key: str, process_instance_id: str
) -> Variables:
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        process_instance = await camunda_client.get_variables_for_process_instance(
            process_instance_id=process_instance_id,
            deserialize_values=True,
        )
    return process_instance


@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def get_process_instances_count(
    camunda_user_id: str,
    camunda_key: str,
    params: dict | None = None,
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        task_count = await camunda_client.get_process_instances_count(
            params=ProcessInstanceQuerySchema(**params)
        )
    return task_count


@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def delete_process_instance(
    camunda_user_id: str,
    camunda_key: str,
    process_instance_id: str,
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        await camunda_client.delete_process(
            process_instance_id=process_instance_id,
        )


@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def update_suspension_state(
    camunda_user_id: str,
    camunda_key: str,
    instance_id: str,
    suspended: bool,
):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        process_instance = await camunda_client.update_suspension_state_by_id(
            process_instance_id=instance_id,
            suspended=suspended,
        )
    return process_instance


@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def get_start_form_variables(
    camunda_user_id: str,
    camunda_key: str,
    definition_key: str,
    params: dict | None = None,
):
    if not params:
        form_variables = None
    else:
        form_variables = FormVariablesQuerySchema(**params)
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        variables = await camunda_client.get_process_definition_start_form(
            process_definition_key=definition_key,
            params=form_variables,
        )
    return variables


async def create_deployment(
    camunda_user_id: str,
    camunda_key: str,
    deployment_data: dict,
    file_bytes: bytes,
    file_name: str,
):
    auth_data = AuthData(username=camunda_user_id, password=camunda_key)
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=auth_data,
            base_url=ENGINE_URL,
            transport=transport,
        )

        response = await camunda_client.create_deployment(
            tenant_id=deployment_data.get("tenant-id"),
            deployment_source=deployment_data.get("deployment-source"),
            deploy_changed_only=deployment_data.get("deploy-changed-only", False),
            enable_duplicate_filtering=deployment_data.get(
                "enable-duplicate-filtering", False
            ),
            deployment_name=deployment_data.get("deployment-name"),
            deployment_activation_time=deployment_data.get("deployment-activation-time"),
            file_bytes=file_bytes,
            file_name=file_name,
        )

    if (
        "deployedProcessDefinitions" not in response
        or len(response["deployedProcessDefinitions"]) == 0
    ):
        raise Exception("Deployment failed or no process definitions deployed.")

    # Extract the deployed process definition key
    deployed_definitions = response["deployedProcessDefinitions"]
    deployed_definition = next(iter(deployed_definitions.values()))
    definition_key = deployed_definition["key"]
    definition_name = deployed_definition["name"]

    user, created = await User.get_or_create(
        camunda_user_id=camunda_user_id,
        defaults={
            "username": camunda_user_id,
            "first_name": "",
            "last_name": "",
            "email": "",
            "language_code": "en",
            "is_admin": False,
            "is_suspicious": False,
            "camunda_key": uuid.uuid4(),
            "telegram_user_id": None,
            "webapp_user_id": uuid.uuid4(),
            "is_block": False,
            "is_premium": False,
        },
    )

    await Flow.create(
        name=definition_name,
        key=definition_key,
        description=deployment_data.get("description", ""),
        img_picture=deployment_data.get("img_picture", ""),
        type=deployment_data.get("type", "automation"),
        parent_id=deployment_data.get("parent_id", uuid.uuid4()),
        user=user,
        reference_id=deployment_data.get("reference_id", uuid.uuid4()),
    )

    return response


@cached(ttl=1, **DECORATOR_CACHE_CONFIG)
async def proxy_request_to_camunda(
    camunda_user_id: str,
    camunda_key: str,
    method: str,
    path: str,
    query_params: dict,
    body: bytes,
):
    url = f"{settings.ENGINE_URL}/{path}"

    auth_data = AuthData(username=camunda_user_id, password=camunda_key)
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            base_url=settings.ENGINE_URL,
            auth_data=auth_data,
            transport=transport,
        )

        response = await camunda_client._http_client.request(
            method=method,
            url=url,
            params=query_params,
            content=body,
        )
        response.raise_for_status()

    return response


async def create_camunda_user(new_user: User) -> User:
    async with httpx.AsyncHTTPTransport() as transport:

        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=settings.ENGINE_USERNAME, password=settings.ENGINE_PASSWORD),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        try:
            camunda_user_id = new_user.camunda_user_id
            camunda_key = new_user.camunda_key
            await camunda_client.create_user(
                CreateUserSchema(
                    profile=ProfileSchema(id=camunda_user_id,
                                          first_name=new_user.first_name,
                                          last_name=new_user.last_name,
                                          email=new_user.email),
                    credentials=CredentialsSchema(password=str(camunda_key)),
                )
            )
            await camunda_client.group_create_member(group_id=settings.ENGINE_USERS_GROUP_ID,
                                                     user_id=camunda_user_id)
            return new_user
        except Exception as e:
            raise e
