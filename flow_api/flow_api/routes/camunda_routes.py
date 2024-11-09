import logging
from datetime import datetime
from typing import Annotated, Optional, List

import re

from fastapi import APIRouter, Depends, Path, Body, Query, UploadFile, Form, File
from starlette.requests import Request
from starlette.responses import JSONResponse

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from camunda_client import Variables
from camunda_client.clients.engine.schemas import GetTasksFilterSchema, TaskSchema
from camunda_client.clients.engine.schemas.response import (
    ProcessInstanceSchema,
    ProcessDefinitionSchema,
)
from camunda_client.clients.schemas import PaginationParams, CountSchema
from camunda_client.types_ import VariablesFixed
from configs.app_config import settings
from flow_api.dependencies import sys_key_depends, sys_key_or_jwt_depends
from flow_api.rest_models.api_rest_models import ORMBaseModel
from services import camunda_service

router = APIRouter()


async def process_definitions_query_params(
    processDefinitionId: str = Query(
        None, description="Filter by process definition id"
    ),
    processDefinitionIdIn: str = Query(
        None, description="Filter by a comma-separated list of process definition ids."
    ),
    name: str = Query(None, description="Filter by the name of the process definition."),
    nameLike: str = Query(
        None, description="Filter by the name that the parameter is a substring of."
    ),
    deploymentId: str = Query(
        None, description="Filter by the deployment the id belongs to."
    ),
    deployedAfter: str = Query(
        None,
        description="Filter by the deployment date after a given date. Format yyyy-MM-dd'T'HH:mm:ss.SSSZ",
    ),
    deployedAt: str = Query(
        None,
        description="Filter by the deployment date before a given date. Format yyyy-MM-dd'T'HH:mm:ss.SSSZ",
    ),
    key: str = Query(None, description="Filter by the key of the process definition."),
    keysIn: str = Query(None, description="Filter by a comma-separated list of keys."),
    keyLike: str = Query(
        None, description="Filter by the key that the parameter is a substring of."
    ),
    category: str = Query(
        None, description="Filter by the category of the process definition."
    ),
    categoryLike: str = Query(
        None, description="Filter by the category that the parameter is a substring of."
    ),
    version: int = Query(
        None, description="Filter by the version of the process definition."
    ),
    latestVersion: bool = Query(
        None, description="Filter by the latest version of the process definition."
    ),
    resourceName: str = Query(
        None, description="Filter by the name of the process definition resource."
    ),
    resourceNameLike: str = Query(
        None,
        description="Filter by the name of the process definition resource that the parameter is a substring of.",
    ),
    startableBy: str = Query(
        None, description="Filter by a user name who is allowed to start the process."
    ),
    active: bool = Query(
        None, description="Filter by the activation state of the process definition."
    ),
    suspended: bool = Query(
        None, description="Filter by the suspension state of the process definition."
    ),
    incidentId: str = Query(None, description="Filter by the incident id."),
    incidentType: str = Query(None, description="Filter by the incident type."),
    incidentMessage: str = Query(None, description="Filter by the incident message."),
    incidentMessageLike: str = Query(
        None,
        description="Filter by the incident message that the parameter is a substring of.",
    ),
    tenantIdIn: str = Query(
        None, description="Filter by a comma-separated list of tenant ids."
    ),
    withoutTenantId: bool = Query(
        None,
        description="Only include process definitions which belong to no tenant. Value may only be true, as false is the default behavior.",
    ),
    includeProcessDefinitionsWithoutTenantId: bool = Query(
        None,
        description="Include process definitions which belong to no tenant. Can be used in combination with tenantIdIn. Value may only be true, as false is the default behavior.",
    ),
    versionTag: str = Query(
        None, description="Filter by the version tag of the process definition."
    ),
    versionTagLike: str = Query(
        None,
        description="Filter by the version tag that the parameter is a substring of.",
    ),
    withoutVersionTag: bool = Query(
        None,
        description="Only include process definitions without a version tag. Value may only be true, as false is the default behavior.",
    ),
    startableInTasklist: bool = Query(
        None, description="Filter by the startable state of the process definition."
    ),
    notStartableInTasklist: bool = Query(
        None, description="Filter by the not startable state of the process definition."
    ),
    startablePermissionCheck: bool = Query(
        None,
        description="Filter by the startable permission check state of the process definition.",
    ),
    sortBy: str = Query(
        None,
        description='Enum: "category" "key" "id" "name" "version" "deploymentId" "deployTime" "tenantId " "versionTag".',
    ),
    sortOrder: str = Query(None, description='Enum: "asc" "desc".'),
    firstResult: int = Query(
        None,
        description="Pagination of results. Specifies the index of the first result to return.",
    ),
    maxResults: int = Query(
        None,
        description="Pagination of results. Specifies the maximum number of results to return.",
    ),
):
    return locals()


class FlowsRest(ORMBaseModel):
    id: str
    key: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    img_picture: str | None = None
    name: Optional[str] = None
    version: Optional[int] = None
    resource: Optional[str] = None
    deployment_id: Optional[str] = None
    diagram: Optional[str] = None
    suspended: Optional[bool] = None
    user_id: Optional[str] = None
    reference_id: str
    startable_in_tasklist: Optional[bool]
    reward: float = 0


async def flows_query_params(
    flowId: str = Query(None, description="Filter by process flow id."),
    name: str = Query(None, description="Filter by the flow."),
    nameLike: str = Query(
        None, description="Filter by the name that the parameter is a substring of."
    ),
    deploymentId: str = Query(
        None, description="Filter by the deployment the id belongs to."
    ),
    key: str = Query(None, description="Filter by the flow key."),
    keyLike: str = Query(
        None, description="Filter by the key that the parameter is a substring of."
    ),
    category: str = Query(None, description="Filter by the category of the flow."),
    startableBy: str = Query(
        None, description="Filter by a user name who is allowed to start the flow."
    ),
    startableInTasklist: bool = Query(
        None, description="Filter by the startable state of the flow."
    ),
    sortBy: str = Query(
        None,
        description='Enum: "category" "key" "name" "deploymentId".',
    ),
    sortOrder: str = Query(None, description='Enum: "asc" "desc".'),
    firstResult: int = Query(
        None,
        description="Pagination of results. Specifies the index of the first result to return.",
    ),
    maxResults: int = Query(
        None,
        description="Pagination of results. Specifies the maximum number of results to return.",
    ),
):
    return locals()


def filter_modal_rendered_variables(variable_name) -> bool:
    # Generate Meme temporary:
    if variable_name in [
        "gen_art_id",
        "is_regenerate",
        "gen_token_description",
        "gen_token_name",
        "gen_token_tags",
        "gen_post",
        "mints",
        "burns",
        "vote_duration",
    ]:
        return True
    # Signup process temporary:
    if variable_name in ["rewards", "account_age", "is_premium"]:
        return True
    if (
        variable_name.startswith("form_")
        or variable_name.startswith("collection_")
        or variable_name.startswith("text_")
        or variable_name.startswith("link_")
        or variable_name.startswith("img_")
        or variable_name.startswith("action_")
        or variable_name.startswith("txhash_")
        or variable_name.startswith("addrhash_")
    ):
        return True
    return False


@router.get(
    "/flows",
    response_model_by_alias=True,
    response_model=list[FlowsRest],
)
async def get_flows(
    query_params: Annotated[dict, Depends(flows_query_params)],
):
    pass
    return {"status": "Camunda is running"}


class FlowsFormVariablesRest(ORMBaseModel):
    name: str
    value: Optional[str] = None
    type: str
    constraints: Optional[list[str]] = (
        None  # required, minLength, maxLength, min, max, readonly
    )
    is_default: bool
    is_complete: bool
    is_visible: bool
    label: Optional[str] = None


@router.get(
    "/flows/def/{key}/start/variables",
    response_model_by_alias=True,
    response_model=list[FlowsFormVariablesRest],
)
async def get_flows_start_form_variables(
    key: str = Path(..., title="Flow key"),
):
    pass
    return {"status": "Camunda is running"}


class RunningFlowSchema(ORMBaseModel):
    id: str
    definition_id: Optional[str] = None
    definition_key: Optional[str] = None
    definition_name: Optional[str] = None
    definition_version: Optional[int] = None
    business_key: Optional[str] = None
    case_instance_id: Optional[str] = None
    suspended: Optional[bool] = False
    tenant_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    removal_time: Optional[datetime] = None
    duration_in_millis: Optional[int] = None
    start_user_id: Optional[str] = None
    start_activity_id: Optional[str] = None
    root_process_instance_id: Optional[str] = None
    super_process_instance_id: Optional[str] = None
    state: Optional[str] = None


@router.post(
    "/flows/def/{key}/start",
    response_model_by_alias=True,
    response_model=list[RunningFlowSchema],
)
async def start_flow(
    key: str = Path(..., title="Flow key"),
    variables: Variables = None,
    business_key: str | None = Body(None, description="Business key"),
):
    pass
    return {"status": "Camunda is running"}


@router.get(
    "/flows/instance",
    response_model_by_alias=True,
    response_model=list[FlowsFormVariablesRest],
)
async def get_instances(
    key: str = Body(None, title="Flow key"),
    business_key: str | None = Body(None, description="Business key"),
):
    pass
    return {"status": "Camunda is running"}


@router.get(
    "/flows/instance/{instance_id}",
    response_model_by_alias=True,
    response_model=list[FlowsFormVariablesRest],
)
async def get_instance(
    instance_id: str = Path(..., title="Instance id"),
):
    pass
    return {"status": "Camunda is running"}


@router.get(
    "/flows/task/",
    response_model_by_alias=True,
    response_model=list[FlowsFormVariablesRest],
)
async def get_tasks(
    business_key: str | None = Body(None, description="Business key"),
):
    pass
    return {"status": "Camunda is running"}


@router.get(
    "/process-definition",
    response_model=list[ProcessDefinitionSchema],
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def get_process_definitions(
    request: Request,
    query_params: Annotated[dict, Depends(process_definitions_query_params)],
    auth: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
):
    user_claims = await auth.get_raw_jwt()
    process_definitions = await camunda_service.get_process_definitions(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        variables=query_params,
    )
    return process_definitions


@router.post("/process-definition/key/{key}/start", response_model=ProcessInstanceSchema)
async def start_process_instance_by_key(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
    key: str = Path(..., title="Process definition key"),
    variables: Variables = None,
    business_key: str | None = Body(None, description="Business key"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    # form_variables = await camunda_service.get_start_form_variables(
    #     user_claims["camunda_user_id"],
    #     user_claims["camunda_key"],
    #     key
    # )
    # form_variables_dict = {
    #     var["name"]: {"value": var["value"], "type": var["type"]} for var in form_variables
    # }
    if not business_key:
        business_key = user_claims["id"]
    start_variables = {}
    # for name, form_variable in form_variables_dict.items():
    #     if name in variables:
    #         start_variables[name] = variables[name]
    #         continue
    #     if name.startswith("def_"):
    #         start_variables[name] = form_variable

    process_instance = await camunda_service.start_process_instance(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        key,
        business_key=business_key,
        variables=variables,
    )
    return process_instance


@router.get("/task", description="Get User's Tasks", response_model=list[TaskSchema])
async def get_tasks(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    limit: int | None = Query(None, description="Limit pagination parameters"),
    offset: int | None = Query(None, description="Offset pagination parameters"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    if limit is None:
        limit = 10
    if offset is None:
        offset = 0
    pagination_params = PaginationParams(
        limit=limit,
        offset=offset,
    )
    tasks = await camunda_service.get_tasks_for_user(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        pagination=pagination_params,
    )
    # TODO: There are cases when returned other list, dop double fixing
    return tasks


@router.post("/task", description="Filter User's Task", response_model=list[TaskSchema])
async def filter_tasks(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    include_history: bool = Body(False, description="Include history tasks"),
    schema: GetTasksFilterSchema | None = Body(None, description="Filter user's tasks"),
    pagination: PaginationParams | None = Body(
        None, description="Pagination parameters"
    ),
):
    user_claims = await auth.get_raw_jwt()
    tasks = await camunda_service.get_tasks_for_user(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        include_history=include_history,
        schema=schema,
        pagination=pagination,
    )
    # TODO: There are cases when returned other list, dop double fixing
    return tasks


def format_label(input_string):
    # Split the string at the first underscore and keep only the part after it
    input_string = input_string.split("_", 1)[-1]
    # Replace any remaining underscores with spaces
    input_string = input_string.replace("_", " ")
    # Insert a space before any uppercase letter (except the first letter)
    input_string = re.sub(r"(?<!^)(?=[A-Z])", " ", input_string)
    # Capitalize each word
    return input_string.title()


@router.get("/task/{task_id}/form-variables", response_model=Variables)
async def get_task_form_variables(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
    task_id: str = Path(..., title="Task ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    try:
        form_variables = await camunda_service.get_task_form_variables(
            user_claims["camunda_user_id"],
            user_claims["camunda_key"],
            task_id=task_id,
        )
    except Exception as e:
        logging.error(f"Error while getting task form variables: {e}")
        return JSONResponse({"message": str(e)}, status_code=400)
    return form_variables


@router.post("/task/{task_id}/complete")
async def complete_task(
    request: Request,
    variables: VariablesFixed = Body(None),
    auth: AuthJWT = Depends(AuthJWTBearer()),
    task_id: str = Path(..., title="Task ID"),
):
    await auth.jwt_required()
    try:
        json_dict = await request.json()
    except Exception:
        json_dict = {}
    user_claims = await auth.get_raw_jwt()
    await camunda_service.complete_task(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        task_id=task_id,
        variables=json_dict,
    )
    return {"message": "Task completed successfully"}


@router.post("/task/{task_id}/variables", response_model=Variables)
async def modify_task_variables(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
    task_id: str = Path(..., title="Task ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    variables = {**request.query_params}
    variables = await camunda_service.modify_task_variables(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        task_id=task_id,
        variables=variables,
    )
    return variables


@router.get("/process-instance", response_model=List[ProcessInstanceSchema])
async def get_process_instances(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
    business_key: Optional[str] = Query(None),
    process_definition_key: Optional[str] = Query(None),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()

    # Use the provided business_key or fallback to the user's id from claims
    if not business_key:
        business_key = user_claims["id"]

    # Prepare query parameters for the service
    query_params = {
        "business_key": business_key,
        "process_definition_key": process_definition_key,
        **request.query_params,
    }

    # Fetch process instances based on the query params
    process_instances = await camunda_service.get_process_instances(
        business_key=business_key,
        camunda_user_id=user_claims["camunda_user_id"],
        camunda_key=user_claims["camunda_key"],
        params=query_params,
    )

    return process_instances


@router.get("/process-instance/count", response_model=CountSchema)
async def get_process_instance_count(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    query_params = {**request.query_params}
    count = await camunda_service.get_process_instances_count(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        params=query_params,
    )
    return count


@router.get("/process-instance/{instance_id}", response_model=ProcessInstanceSchema)
async def get_process_instance(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    instance_id: str = Path(..., title="Process instance ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    process_instance = await camunda_service.get_process_instance(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        instance_id,
    )
    return process_instance


@router.get(
    "/process-instance/{instance_id}/variables",
    response_model=Variables,
)
async def get_process_instance_variables(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    instance_id: str = Path(..., title="Process instance ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    variables = await camunda_service.get_process_instance_variables(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        instance_id,
    )
    return variables


@router.delete("/process-instance/{process_id}")
async def delete_process_instance(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    process_id: str = Path(..., title="Process instance ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    await camunda_service.delete_process_instance(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        process_id,
    )
    return {"message": "Process instance deleted successfully"}


@router.put("/process-instance/{instance_id}/suspended")
async def update_suspension_state_by_id(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    instance_id: str = Path(..., title="Process instance ID"),
    suspended: bool = Body(..., title="Suspended state", embed=True),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    await camunda_service.update_suspension_state(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        instance_id,
        suspended,
    )
    return {"message": "Suspension state updated successfully"}


@router.get(
    "/process-definition/{definition_key}/form-variables", response_model=Variables
)
async def get_start_form_variables(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
    definition_key: str = Path(..., title="Definition Key"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    params = {**request.query_params}
    variables = await camunda_service.get_start_form_variables(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        definition_key,
        params=params,
    )
    resulting_variables = {}
    for variable in variables:
        if filter_modal_rendered_variables(variable.name):
            variable_value = variable.dict()["value"]
            variable_value["label"] = format_label(variable.name)
            resulting_variables[variable.name] = variable_value
    return resulting_variables


@router.post(
    "/deployment/create", response_model={}, dependencies=[Depends(sys_key_depends)]
)
async def create_deployment(
    token: Annotated[str, Depends(sys_key_depends)],
    tenant_id: Optional[str] = Form(None),
    deployment_source: Optional[str] = Form(None),
    deploy_changed_only: Optional[bool] = Form(False),
    enable_duplicate_filtering: Optional[bool] = Form(False),
    deployment_name: Optional[str] = Form(None),
    deployment_activation_time: Optional[str] = Form(None),
    data: UploadFile = File(...),
):
    deployment_data = {
        "tenant-id": tenant_id,
        "deployment-source": deployment_source,
        "deploy-changed-only": deploy_changed_only,
        "enable-duplicate-filtering": enable_duplicate_filtering,
        "deployment-name": deployment_name,
        "deployment-activation-time": deployment_activation_time,
    }

    file_bytes = await data.read()
    file_name = data.filename
    response = await camunda_service.create_deployment(
        settings.ENGINE_USERNAME,
        settings.ENGINE_PASSWORD,
        deployment_data,
        file_bytes,
        file_name,
    )

    return JSONResponse(content=response)


@router.api_route(
    "/proxy/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def proxy_all_requests(
    request: Request,
    full_path: str,
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
):
    user_claims = await auth.get_raw_jwt()

    camunda_user_id = user_claims["camunda_user_id"]
    camunda_key = user_claims["camunda_key"]

    body = await request.body()

    response = await camunda_service.proxy_request_to_camunda(
        camunda_user_id,
        camunda_key,
        request.method,
        full_path,
        request.query_params,
        body,
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)
