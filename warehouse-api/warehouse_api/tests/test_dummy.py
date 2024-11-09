import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from warehouse_api.db.dao.dummy_dao import DummyDAO


@pytest.mark.anyio
async def test_creation(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests dummy instance creation."""
    url = fastapi_app.url_path_for("handle_http_post")
    test_name = uuid.uuid4().hex
    response = await client.post(
        url,
        json={
            "query": "mutation($name: String!){createDummyModel(name: $name)}",
            "variables": {"name": test_name},
        },
    )
    assert response.status_code == status.HTTP_200_OK
    dao = DummyDAO(dbsession)
    instances = await dao.filter(name=test_name)
    assert instances[0].name == test_name


@pytest.mark.anyio
async def test_getting(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests dummy instance retrieval."""
    dao = DummyDAO(dbsession)
    test_name = uuid.uuid4().hex
    await dao.create_dummy_model(name=test_name)
    url = fastapi_app.url_path_for("handle_http_post")
    response = await client.post(
        url,
        json={"query": "query{dumies:getDummyModels{id name}}"},
    )
    dummies = response.json()["data"]["dumies"]

    assert response.status_code == status.HTTP_200_OK
    assert len(dummies) == 1
    assert dummies[0]["name"] == test_name
