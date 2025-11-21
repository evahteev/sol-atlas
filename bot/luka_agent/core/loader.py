"""
luka_agent loader - Redis initialization.

Simplified version of luka_bot loader, focusing only on what's needed for the agent.
"""
from redis.asyncio import ConnectionPool, Redis
from luka_agent.core.config import settings

# Redis client for caching and state
redis_client = Redis(
    connection_pool=ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASS,
        db=settings.REDIS_DATABASE,
        retry_on_timeout=True,
        retry_on_error=[
            ConnectionError,
            TimeoutError,
            ConnectionResetError,
            ConnectionRefusedError,
            ConnectionAbortedError,
        ],
        health_check_interval=30,
    ),
)
