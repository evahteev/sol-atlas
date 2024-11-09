import asyncio
import logging

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractRobustConnection
from aio_pika.pool import Pool
from fastapi import FastAPI
import ujson

from warehouse_api.settings import settings

logger = logging.getLogger(__name__)


async def rabbitmq_listener(app: FastAPI):
    try:
        async with app.state.rmq_channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange(
                settings.rabbit_exchange,
                aio_pika.ExchangeType.DIRECT,
                durable=True,
            )
            queue = await channel.declare_queue(settings.rabbit_queue, durable=True)
            await queue.bind(exchange, routing_key=settings.rabbit_routing_key)
            logger.info(
                f"Queue bound to exchange with routing key '{settings.rabbit_routing_key}'"
            )

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            event = ujson.loads(message.body.decode())
                            logger.info(f"Received message: {event}")

                            # Filter for task events
                            if event.get("taskId") and event["taskId"].strip():
                                process_instance_id = event.get("processInstanceId")
                                await app.state.websocket_manager.broadcast(
                                    ujson.dumps(event), process_instance_id
                                )

                            # Filter for variable events
                            if (
                                event.get("variableName")
                                and event["variableName"].strip()
                            ):
                                process_instance_id = event.get("processInstanceId")
                                await app.state.websocket_manager.broadcast(
                                    ujson.dumps(event), process_instance_id
                                )
                        except Exception as e:
                            logger.info(f"Error processing message: {e}")
    except asyncio.CancelledError:
        logger.info("RabbitMQ listener task cancelled.")
    except Exception as e:
        logger.info(f"Error in RabbitMQ listener: {e}")


def init_rabbit(app: FastAPI) -> None:  # pragma: no cover
    """
    Initialize rabbitmq pools.

    :param app: current FastAPI application.
    """

    async def get_connection() -> AbstractRobustConnection:  # noqa: WPS430
        """
        Creates connection to RabbitMQ using url from settings.

        :return: async connection to RabbitMQ.
        """
        return await aio_pika.connect_robust(str(settings.rabbit_url))

    # This pool is used to open connections.
    connection_pool: Pool[AbstractRobustConnection] = Pool(
        get_connection,
        max_size=settings.rabbit_pool_size,
    )

    async def get_channel() -> AbstractChannel:  # noqa: WPS430
        """
        Open channel on connection.

        Channels are used to actually communicate with rabbitmq.

        :return: connected channel.
        """
        async with connection_pool.acquire() as connection:
            return await connection.channel()

    # This pool is used to open channels.
    channel_pool: Pool[aio_pika.Channel] = Pool(
        get_channel,
        max_size=settings.rabbit_channel_pool_size,
    )

    app.state.rmq_pool = connection_pool
    app.state.rmq_channel_pool = channel_pool
    asyncio.create_task(rabbitmq_listener(app))


async def shutdown_rabbit(app: FastAPI) -> None:  # pragma: no cover
    """
    Close all connection and pools.

    :param app: current application.
    """
    await app.state.rmq_channel_pool.close()
    await app.state.rmq_pool.close()
