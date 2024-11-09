from aio_pika import Channel
from aio_pika.pool import Pool
from fastapi import Depends
from redis.asyncio import ConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext

from warehouse_api.db.dependencies import get_db_session
from warehouse_api.services.rabbit.dependencies import get_rmq_channel_pool
from warehouse_api.services.redis.dependency import get_redis_pool


class Context(BaseContext):
    """Global graphql context."""

    def __init__(
        self,
        redis_pool: ConnectionPool = Depends(get_redis_pool),
        rabbit: Pool[Channel] = Depends(get_rmq_channel_pool),
        db_connection: AsyncSession = Depends(get_db_session),
    ) -> None:
        self.redis_pool = redis_pool
        self.rabbit = rabbit
        self.db_connection = db_connection
        pass  # noqa: WPS420


def get_context(context: Context = Depends(Context)) -> Context:
    """
    Get custom context.

    :param context: graphql context.
    :return: context
    """
    return context
