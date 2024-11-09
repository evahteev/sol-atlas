from fastapi import APIRouter
from fastapi.params import Path, Body
from starlette.requests import Request

router = APIRouter(prefix='/resources', tags=['resources'])


@router.post('/{item_type}')
async def store_item(
    request: Request,
    item_type: str = Path(...),
    body: dict = Body(...),
):
    """Store item in Elasticsearch.

    :param request: FastAPI request object
    :param item_type: Index name in Elasticsearch
    :param body: JSON object to store in Elasticsearch
    """
    elasticsearch = request.app.state.elasticsearch
    res = await elasticsearch.create(item_type, body)
    return res


@router.get('/{item_type}')
async def get_items(
    request: Request,
    item_type: str = Path(...),
    limit: int = 100,
    offset: int = 0,
):
    """Get items from elasticsearch.

    :param request: FastAPI request object
    :param item_type: index name in Elasticsearch
    :param limit: Number of items to return
    :param offset: Offset from start of items to return

    Passed query params interpreted as filter fields.

    Returns:
        list[dict]
    """
    query_params = dict(request.query_params)
    query_params.pop('limit', None)
    query_params.pop('offset', None)
    elasticsearch = request.app.state.elasticsearch
    res = await elasticsearch.get(item_type, query_params, limit=limit, offset=offset)
    return res


@router.patch('/{item_type}/{id}')
async def update_item(
    request: Request,
    item_type: str = Path(...),
    id_: str = Path(..., alias='id'),
    body: dict = Body(...),
):
    """
    Update item in elasticsearch.
    :param request: FastAPI request object
    :param item_type: index name in Elasticsearch
    :param id_: object id in Elasticsearch
    :param body: Key-value fields to update in Elasticsearch


    """
    elasticsearch = request.app.state.elasticsearch
    res = await elasticsearch.update(item_type, id_, body)
    return res


@router.delete('/{item_type}/{id}')
async def delete_item(
    request: Request,
    item_type: str = Path(...),
    id_: str = Path(..., alias='id'),
):
    """Delete item from elasticsearch.
    :param request: FastAPI request object
    :param item_type: index name in Elasticsearch
    :param id_: object id in Elasticsearch
    """
    elasticsearch = request.app.state.elasticsearch
    res = await elasticsearch.delete(item_type, id_)
    return res
