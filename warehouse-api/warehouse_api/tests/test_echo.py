import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status


@pytest.mark.anyio
async def test_echo(fastapi_app: FastAPI, client: AsyncClient) -> None:
    """
    Tests that echo route works.

    :param fastapi_app: current application.
    :param client: client for the app.
    """
    url = fastapi_app.url_path_for("handle_http_post")
    message = uuid.uuid4().hex
    response = await client.post(
        url,
        json={
            "query": "query($message: String!){echo(message: $message)}",
            "variables": {
                "message": message,
            },
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["echo"] == message
