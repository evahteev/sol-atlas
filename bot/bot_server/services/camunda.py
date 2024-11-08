import asyncio
from typing import Sequence

import httpx
import logging

from bot_server.core.config import settings
from camunda_client import CamundaEngineClient
from camunda_client.clients.dto import AuthData
from camunda_client.clients.engine.schemas import (
    ProcessInstanceQuerySchema,
    ProcessInstanceSchema,
    GetHistoryTasksFilterSchema,
)

logger = logging.getLogger(__name__)


async def start_process_instance(
    variables: list[dict],
    process_definition_key: str | None = None,
    business_key: str | None = None,
    camunda_user_id: str = settings.ENGINE_USERNAME,
    camunda_key: str = settings.ENGINE_PASSWORD,
) -> ProcessInstanceSchema:
    camunda_variables = {
        var["name"]: {"value": var["value"], "type": var["type"]} for var in variables
    }
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        # Start the process instance with the collected variables
        process_instance = await camunda_client.start_process(
            process_definition_key,
            business_key=business_key,
            variables=camunda_variables,
        )
        await camunda_client.close()
    return process_instance


async def get_process_instance(
    user_id: str,
    password: str,
    process_definition_name: str,
    business_key: str = "",
) -> ProcessInstanceSchema:
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=user_id, password=password),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        # Start the process instance with the collected variables
        process_instance = await camunda_client.get_process_instances(
            params=ProcessInstanceQuerySchema(
                business_key=business_key,
                process_definition_key=process_definition_name,
            )
        )
        await camunda_client.close()
    if process_instance:
        return process_instance[0]


async def get_or_create_process_instance(
    user_id: str,
    password: str,
    process_definition_name: str,
    variables: list[dict] | None = None,
    business_key: str = "",
) -> ProcessInstanceSchema:
    process_instance = await get_process_instance(
        user_id=user_id,
        password=password,
        process_definition_name=process_definition_name,
        business_key=business_key,
    )
    if process_instance:
        return process_instance
    else:
        logging.info(
            f"Starting generate process instance with business key: {business_key}"
        )
        process_instance = await start_process_instance(
            variables,
            business_key=business_key,
            process_definition_key=process_definition_name,
            camunda_user_id=user_id,
            camunda_key=password,
        )
    return process_instance
