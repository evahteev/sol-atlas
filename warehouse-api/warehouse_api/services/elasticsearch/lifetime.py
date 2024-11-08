import elasticsearch_dsl
from fastapi import FastAPI

from warehouse_api.services.elasticsearch.elasticsearch_client import ElasticsearchClient
from warehouse_api.settings import settings


async def init_elasticsearch(app: FastAPI) -> None:  # pragma: no cover
    """
    Creates connection pool for redis.

    :param app: current fastapi application.
    """
    connection = elasticsearch_dsl.async_connections.create_connection(
        hosts=[settings.elasticsearch_url]
    )
    app.state.elasticsearch = ElasticsearchClient(connection)


async def shutdown_elasticsearch(app: FastAPI) -> None:  # pragma: no cover
    """
    Closes redis connection pool.

    :param app: current FastAPI app.
    """
    await app.state.elasticsearch.close()
