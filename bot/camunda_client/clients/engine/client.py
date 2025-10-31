import asyncio
import base64
import json
from collections.abc import Sequence
from http import HTTPStatus
from typing import Any, Optional, List
from uuid import UUID

import aiohttp
import httpx
from bs4 import BeautifulSoup
from pydantic.type_adapter import TypeAdapter

from camunda_client.clients.dto import AuthData
from camunda_client.clients.endpoints import CamundaUrls
from camunda_client.clients.engine.schemas.body import (
    ClaimTaskSchema,
    SetAssigneeTaskSchema,
    CreateUserSchema,
)
from camunda_client.clients.engine.schemas.response import (
    HistoricTaskInstanceSchema,
    TaskSchema,
    VariableInstanceSchema,
    ProcessDefinitionSchema,
    ProcessVariablesSchema,
    ProfileSchema, HistoryProcessInstanceSchema, CamundaForm,
)
from camunda_client.clients.schemas import CountSchema, PaginationParams
from camunda_client.types_ import Variables, VariableValueSchema, TVariables
from camunda_client.utils import raise_for_status
from .schemas import (
    GetHistoryTasksFilterSchema,
    GetTasksFilterSchema,
    ProcessDefinitionQuerySchema,
    ProcessInstanceQuerySchema,
    ProcessInstanceSchema,
    StartProcessInstanceSchema,
    SendCorrelationMessageSchema,
)
from .schemas.query import FormVariablesQuerySchema, HistoryProcessInstanceQuerySchema


class CamundaEngineClient:
    def __init__(
            self,
            base_url: str,
            auth_data: AuthData,
            transport: httpx.AsyncHTTPTransport,
            urls: CamundaUrls | None = None,
    ) -> None:
        self._http_client = httpx.AsyncClient(
            base_url=base_url,
            transport=transport,
            timeout=60,
            auth=httpx.BasicAuth(
                username=str(auth_data.username),
                password=str(auth_data.password),
            ),
            headers={"Content-Type": "application/json"},
        )
        self._base_url = base_url
        self._auth_data = auth_data
        self._urls = urls or CamundaUrls()
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Basic {base64.b64encode(f'{auth_data.username}:{auth_data.password}'.encode()).decode()}"}
        )

    async def close(self):
        """Close the HTTP client sessions"""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._http_client:
            await self._http_client.aclose()

    async def __aenter__(self):
        """Context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()

    async def create_deployment(
            self,
            tenant_id: Optional[str],
            deployment_source: Optional[str],
            deploy_changed_only: bool,
            enable_duplicate_filtering: bool,
            deployment_name: Optional[str],
            deployment_activation_time: Optional[str],
            file_bytes: bytes,
            file_name: str
    ) -> dict:

        url = f"{self._http_client.base_url}deployment/create"

        form_data = aiohttp.FormData()
        form_data.add_field('deploy-changed-only', str(deploy_changed_only).lower())
        form_data.add_field('enable-duplicate-filtering', str(enable_duplicate_filtering).lower())
        form_data.add_field('data', file_bytes, filename=file_name, content_type='application/octet-stream')
        if tenant_id:
            form_data.add_field('tenant-id', tenant_id)
        if deployment_source:
            form_data.add_field('deployment-source', deployment_source)
        if deployment_name:
            form_data.add_field('deployment-name', deployment_name)
        if deployment_activation_time:
            form_data.add_field('deployment-activation-time', deployment_activation_time)

        async with self._session.post(url, data=form_data) as response:
            response.raise_for_status()
            return await response.json()

    async def start_process(
            self,
            process_key: str,
            business_key: str | None = None,
            variables: Variables | None = None,
            tenant_id: str | None = None,
    ) -> ProcessInstanceSchema:
        """
        Instantiates a given process definition, starts the latest
        version of the process definition which belongs to no tenant.
        Process variables and business key may be supplied in the request body
        """

        url = self._urls.get_start_process_instance(process_key, tenant_id)
        schema = StartProcessInstanceSchema(
            business_key=business_key,
            variables=variables,
        )
        content = schema.model_dump_json(by_alias=True)
        response = await self._http_client.post(url, content=content)
        raise_for_status(response)
        return ProcessInstanceSchema.model_validate(response.json())

    async def get_process_definitions(
            self, params: ProcessDefinitionQuerySchema | None = None
    ) -> Sequence[ProcessDefinitionSchema]:
        """
        Queries for process definitions that fulfill given parameters.
        Parameters may be static as well as dynamic runtime properties
        of process instances. The size of the result set can be
        retrieved by using the Get Definitions Count method
        """
        params = (
            params.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            )
            if params
            else {}
        )
        response = await self._http_client.get(
            self._urls.process_definitions,
            params=params,
        )
        raise_for_status(response)
        adapter = TypeAdapter(list[ProcessDefinitionSchema])
        return adapter.validate_python(response.json())

    async def get_process_definition_start_form(
            self, process_definition_key: str, params: FormVariablesQuerySchema | None = None
    ) -> Sequence[ProcessVariablesSchema]:
        """
        Queries for process definitions start form that fulfill given parameters.
        Parameters may be static as well as dynamic runtime properties
        of process instances. The size of the result set can be
        retrieved by using the Get Definitions Count method
        """
        params = (
            params.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            )
            if params
            else {}
        )

        response = await self._http_client.get(
            self._urls.get_rendered_start_form(process_definition_key),
            params=params,
        )
        raise_for_status(response)
        
        # Log raw HTML for debugging
        from loguru import logger
        logger.debug(f"📄 Raw HTML form for {process_definition_key}:\n{response.text[:500]}...")
        
        variables = self.parse_form_to_json(response.text)
        
        # Log parsed variables with labels
        logger.debug(f"📝 Parsed form variables: {list(variables.keys())}")
        for var_name, var_data in variables.items():
            logger.debug(f"   {var_name}: label='{var_data.get('label', 'NO_LABEL')}', type={var_data.get('type')}")
        
        adapter = TypeAdapter(Variables)
        return adapter.validate_python(variables)

    @staticmethod
    def parse_form_to_json(html):
        import re
        from html import unescape
        
        soup = BeautifulSoup(html, 'html.parser')
        form_data = {}

        # Find all input elements within the form
        inputs = soup.find_all('input')

        # Loop through each input element
        for input_elem in inputs:
            name = input_elem.get('cam-variable-name')
            value = input_elem.get('value')
            input_type = input_elem.get('cam-variable-type')
            label = input_elem.find_previous('label')
            if label:
                label = label.text.strip()
            else:
                label = ""

            # Clean value: convert HTML to Telegram-compatible format
            if value:
                value = CamundaEngineClient._clean_html_for_telegram(value)
                
            # Create the JSON structure for each input
            form_data[name] = {
                "value": value,
                "type": input_type,
                "label": label,
                "valueInfo": {}
            }

        return form_data
    
    @staticmethod
    def _clean_html_for_telegram(text: str) -> str:
        """
        Clean HTML content to be compatible with Telegram's HTML parser.
        
        Telegram supports only: <b>, <strong>, <i>, <em>, <u>, <ins>, <s>, <strike>, 
        <del>, <code>, <pre>, <a href="...">
        
        This method:
        1. Decodes HTML entities (e.g., &lt;br/&gt; -> <br/>)
        2. Converts <br/> tags to newlines
        3. Keeps Telegram-supported tags
        4. Removes unsupported tags
        
        Args:
            text: Raw HTML text from form
            
        Returns:
            str: Cleaned text compatible with Telegram HTML
        """
        import re
        from html import unescape
        
        if not text:
            return text
            
        # Decode HTML entities first (e.g., &lt;br/&gt; -> <br/>)
        text = unescape(text)
        
        # Convert <br>, <br/>, <br /> to newlines (Telegram doesn't support br tags)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        
        # Remove common unsupported tags
        # List of tags to strip (not supported by Telegram)
        unsupported_tags = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                           'table', 'tr', 'td', 'th', 'ul', 'ol', 'li', 'font', 
                           'style', 'script', 'html', 'body', 'head']
        
        for tag in unsupported_tags:
            # Remove opening and closing tags
            text = re.sub(f'<{tag}[^>]*>', '', text, flags=re.IGNORECASE)
            text = re.sub(f'</{tag}>', '', text, flags=re.IGNORECASE)
        
        return text

    async def get_task_form_variables(
            self, task_id: str) -> Sequence[ProcessVariablesSchema]:
        """
        Queries for task form variables that fulfill given parameters.
        """

        # "http://{host}:{port}/{contextPath}/task/{task_id}/rendered_form"
        rendered_form = await self._http_client.get(
            self._urls.get_rendered_form(task_id)
        )

        raise_for_status(rendered_form)

        variables = self.parse_form_to_json(rendered_form.text)

        adapter = TypeAdapter(Variables)

        return adapter.validate_python(variables)

    async def get_deployed_form(
            self, task_id: str) -> CamundaForm:
        """
        Queries for task form variables that fulfill given parameters.
        """

        # "http://{host}:{port}/{contextPath}/task/{task_id}/rendered_form"
        rendered_form = await self._http_client.get(
            self._urls.get_deployed_form(task_id)
        )

        raise_for_status(rendered_form)

        variables = rendered_form.json()

        return variables

    async def modify_task_form_variables(
            self, task_id: str, variables: Variables
    ) -> None:
        """
        Modifies task form variables that fulfill given parameters.
        """
        content = json.dumps(
            {
                "variables": {
                    key: value.model_dump(mode="json", by_alias=True)
                    for key, value in variables.items()
                },
            },
        )
        response = await self._http_client.post(
            self._urls.get_task_form_variables(task_id),
            content=content,
        )
        raise_for_status(response)

    async def get_process_instances(
            self,
            params: ProcessInstanceQuerySchema,
            pagination: PaginationParams | None = None,
    ) -> Sequence[ProcessInstanceSchema]:
        """
        Queries for process instances that fulfill given parameters.
        Parameters may be static as well as dynamic runtime properties
        of process instances. The size of the result set can be
        retrieved by using the Get Instance Count method
        """
        params = params or GetTasksFilterSchema()
        pagination_params = (
            pagination.model_dump(mode="json", by_alias=True) if pagination else {}
        )
        response = await self._http_client.post(
            self._urls.process_instances,
            params=pagination_params,
            content=params.model_dump_json(by_alias=True, exclude_none=True),
        )

        raise_for_status(response)
        adapter = TypeAdapter(list[ProcessInstanceSchema])
        return adapter.validate_python(response.json())

    async def get_history_process_instances(
            self,
            params: HistoryProcessInstanceQuerySchema,
            pagination: PaginationParams | None = None,
    ) -> Sequence[HistoryProcessInstanceSchema]:
        """
        Queries for process instances that fulfill given parameters.
        Parameters may be static as well as dynamic runtime properties
        of process instances. The size of the result set can be
        retrieved by using the Get Instance Count method
        """
        params = params or GetTasksFilterSchema()
        pagination_params = (
            pagination.model_dump(mode="json", by_alias=True) if pagination else {}
        )
        response = await self._http_client.post(
            self._urls.history_process_instances,
            params=pagination_params,
            content=params.model_dump_json(by_alias=True, exclude_none=True),
        )

        raise_for_status(response)
        adapter = TypeAdapter(list[HistoryProcessInstanceSchema])
        return adapter.validate_python(response.json())

    async def get_history_process_instance(
            self,
            process_instance_id: str,
    ) -> HistoryProcessInstanceSchema:
        url = self._urls.get_history_instance(process_instance_id)
        response = await self._http_client.get(url)

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        raise_for_status(response)
        return HistoryProcessInstanceSchema.model_validate(response.json())

    async def get_process_instance(
            self,
            process_instance_id: str,
    ) -> ProcessInstanceSchema | None:
        """Retrieves a process instance by id"""

        url = self._urls.get_process_instance(process_instance_id)
        response = await self._http_client.get(url)

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        raise_for_status(response)
        return ProcessInstanceSchema.model_validate(response.json())

    async def delete_process(self, process_instance_id: str) -> None:
        """Deletes a running process instance by id"""

        url = self._urls.get_process_instance(process_instance_id)
        response = await self._http_client.delete(
            url,
            params={"skipCustomListeners": "true", "skipIoMappings": "true"},
        )
        raise_for_status(response)

    async def get_tasks(
            self,
            schema: GetTasksFilterSchema | None = None,
            pagination: PaginationParams | None = None,
    ) -> Sequence[TaskSchema]:
        """Queries for tasks that fulfill a given filter"""
        schema = schema or GetTasksFilterSchema()
        pagination_params = (
            pagination.model_dump(mode="json", by_alias=True) if pagination else {}
        )

        response = await self._http_client.post(
            self._urls.task,
            params=pagination_params,
            content=schema.model_dump_json(by_alias=True, exclude_none=True),
        )
        raise_for_status(response)
        adapter = TypeAdapter(list[TaskSchema])
        return adapter.validate_python(response.json())

    async def get_tasks_count(
            self,
            schema: GetTasksFilterSchema | None = None,
    ) -> CountSchema:
        """
        Retrieves the number of tasks that fulfill the given filter.
        Corresponds to the size of the result set of the Get Tasks (POST) method and takes the same parameters.
        """
        schema = schema or GetTasksFilterSchema()
        response = await self._http_client.post(
            self._urls.tasks_count,
            content=schema.model_dump_json(by_alias=True, exclude_none=True),
        )
        raise_for_status(response)
        return CountSchema.model_validate(response.json())

    async def get_task(
            self,
            ident: UUID,
    ) -> TaskSchema | None:
        """Retrieves a task by id"""

        url = self._urls.get_task_by_id(str(ident))
        response = await self._http_client.get(url)

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        raise_for_status(response)
        return TaskSchema.model_validate(response.json())

    async def get_history_tasks(
            self,
            schema: GetHistoryTasksFilterSchema,
            pagination: PaginationParams | None = None,
    ) -> Sequence[HistoricTaskInstanceSchema]:
        pagination_params = (
            pagination.model_dump(mode="json", by_alias=True) if pagination else {}
        )

        content = schema.model_dump_json(by_alias=True, exclude_none=True)
        response = await self._http_client.post(
            self._urls.history_task,
            params=pagination_params,
            content=content,
        )
        raise_for_status(response)
        adapter = TypeAdapter(list[HistoricTaskInstanceSchema])
        return adapter.validate_python(response.json())

    async def get_variable_instances(
            self,
            *,
            process_instance_id: UUID | str,
            deserialize_values: bool = False,
    ) -> Sequence[VariableInstanceSchema]:
        response = await self._http_client.get(
            self._urls.variable_instances,
            params={
                "processInstanceId": str(process_instance_id),
                "deserializeValues": deserialize_values,
            },
        )
        raise_for_status(response)
        adapter = TypeAdapter(list[VariableInstanceSchema])
        return adapter.validate_python(response.json())

    async def get_variables_for_process_instance(
            self,
            process_instance_id: UUID | str,
            deserialize_values: bool = False,
    ) -> Variables:
        response = await self._http_client.get(
            self._urls.get_process_instance_variable(process_instance_id),
            params={
                "processInstanceId": str(process_instance_id),
                "deserializeValues": deserialize_values,
            },
        )
        raise_for_status(response)
        return response.json()

    async def submit_task_form(
            self,
            task_id: UUID,
            variables: Variables | None = None,
    ) -> None:
        """
        Completes a task and updates process variables using a form submit.
        """
        variables = variables or {}
        try:
            content = json.dumps(
                {
                    "variables": {
                        key: value.model_dump(mode="json", by_alias=True)
                        for key, value in variables.items()
                    },
                },
            )
        except Exception as e:
            return
        response = await self._http_client.post(
            self._urls.submit_task_form(str(task_id)),
            content=content,
        )
        raise_for_status(response)

    async def complete_task(
            self,
            task_id: UUID | str,
            variables: dict = None,
    ) -> None:
        """
        Completes a task and updates process variables using a form submit.
        """
        response = await self._http_client.post(
            self._urls.complete_task(str(task_id)),
            content=json.dumps(variables),
        )
        raise_for_status(response)

    async def claim_task(
            self,
            task_id: UUID,
            user_id: UUID,
    ) -> None:
        """
        Claims a task for a specific user.
        """
        response = await self._http_client.post(
            self._urls.claim_task(str(task_id)),
            content=ClaimTaskSchema(user_id=str(user_id)).model_dump_json(
                by_alias=True,
            ),
        )
        raise_for_status(response)

    async def unclaim_task(
            self,
            task_id: UUID,
    ) -> None:
        """
        Claims a task for a specific user.
        """
        response = await self._http_client.post(self._urls.unclaim_task(str(task_id)))
        raise_for_status(response)

    async def set_assignee_task(
            self,
            task_id: UUID,
            user_id: UUID,
    ) -> None:
        """
        Changes the assignee of a task to a specific user.
        """
        response = await self._http_client.post(
            self._urls.set_assignee_task(str(task_id)),
            content=SetAssigneeTaskSchema(user_id=str(user_id)).model_dump_json(
                by_alias=True,
            ),
        )
        raise_for_status(response)

    async def send_correlation_message(
            self,
            schema: SendCorrelationMessageSchema,
    ) -> dict[str, Any] | None:
        """
        Correlates a message to the process engine to either trigger
        a message start event or an intermediate message catching event.
        """
        response = await self._http_client.post(
            self._urls.message_send,
            content=schema.model_dump_json(by_alias=True, exclude_none=True),
        )
        raise_for_status(response)

        if response.status_code == HTTPStatus.NO_CONTENT:
            return None

        # if schema.result_enabled is true
        return response.json()

    async def group_create_member(
            self,
            group_id: str,
            user_id: str,
    ) -> None:
        """
        Changes the assignee of a task to a specific user.
        """
        response = await self._http_client.put(
            self._urls.group_create_member(str(group_id), str(user_id))
        )
        raise_for_status(response)

    async def create_user(
            self,
            schema: CreateUserSchema,
    ) -> dict[str, Any] | None:
        """
        Creates user
        """
        response = await self._http_client.post(
            self._urls.user_create,
            content=schema.model_dump_json(by_alias=True, exclude_none=True),
        )
        raise_for_status(response)

        if response.status_code == HTTPStatus.NO_CONTENT:
            return None

        # if schema.result_enabled is true
        return response.json()

    async def get_user_profile(
            self,
            ident: UUID,
    ) -> ProfileSchema | None:
        """Retrieves a task by id"""

        url = self._urls.get_profile_by_user_id(str(ident))
        response = await self._http_client.get(url)

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        raise_for_status(response)
        return ProfileSchema.model_validate(response.json())

    async def update_suspension_state_by_id(
            self,
            process_instance_id: UUID | str,
            suspended: bool,
    ) -> None:
        """
        Activates or suspends a given process instance by id.
        """
        url = self._urls.get_process_instance_suspend(str(process_instance_id))
        response = await self._http_client.put(
            url,
            content=json.dumps({"suspended": suspended}),
        )
        raise_for_status(response)

    async def get_process_instances_count(
            self,
            params: ProcessInstanceQuerySchema,
    ) -> CountSchema:
        response = await self._http_client.get(
            self._urls.get_url_process_instances_count(),
            params=params.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            ),
        )
        raise_for_status(response)
        return CountSchema.model_validate(response.json())

    async def get_current_activity(
            self,
            process_instance_id: str,
    ) -> List[dict]:
        """
        Retrieves the IDs of activities where the token is currently located
        for the given process instance.
        """
        url = self._urls.history_activity_instance
        params = {
            "processInstanceId": process_instance_id,
            "unfinished": True,  # Fetch only ongoing activity instances
        }

        response = await self._http_client.get(url, params=params)
        raise_for_status(response)

        # Parse and extract activity IDs
        activity_instances = response.json()
        return activity_instances


    async def get_start_form(
            self,
            process_definitnon_key: str,
    ) -> List[dict]:

        """
        Get start form for a process definition by key.
        """
        response = await self._http_client.get(
            self._urls.get_process_definition_start_form(process_definitnon_key=process_definitnon_key)
        )
        raise_for_status(response)

        return response.json()


    async def get_deployed_start_form(
            self,
            process_definitnon_key: str,
    ) -> List[dict]:

        """
        Get deployed start form for a process definition by key.
        """
        response = await self._http_client.get(
            self._urls.get_deployed_start_form(process_definitnon_key=process_definitnon_key)
        )
        raise_for_status(response)

        return response.json()
