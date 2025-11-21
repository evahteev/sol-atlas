"""
Redis checkpointer configuration for LangGraph state persistence.

This module provides a singleton Redis checkpointer instance that is shared
across all graph executions. It handles automatic state persistence and
retrieval from Redis.
"""

from typing import Optional
from loguru import logger

from langgraph.checkpoint.redis import RedisSaver
from langgraph.checkpoint.memory import MemorySaver

# Try to import settings, but don't fail if luka_agent isn't configured
# This allows luka_agent to work standalone (e.g., CLI usage)
try:
    from luka_agent.core.config import settings
    _has_settings = True
except ImportError:
    # This is expected in standalone/CLI mode - use DEBUG level
    logger.debug("luka_agent settings not available, will use MemorySaver (standalone mode)")
    settings = None
    _has_settings = False

# Global checkpointer instance
_checkpointer: Optional[RedisSaver | MemorySaver] = None


async def get_checkpointer() -> RedisSaver | MemorySaver:
    """
    Get or create the singleton checkpointer instance.

    The checkpointer type is determined by configuration:
    - Redis (default): Used in production for persistent state
    - Memory (testing/CLI): Used in tests, CLI, or when luka_bot config unavailable

    Returns:
        RedisSaver or MemorySaver instance

    Example:
        >>> checkpointer = await get_checkpointer()
        >>> # Use in graph builder
        >>> graph = builder.compile(checkpointer=checkpointer)
    """
    global _checkpointer

    if _checkpointer is not None:
        return _checkpointer

    # Use MemorySaver if settings not available (CLI/standalone mode)
    if not _has_settings or settings is None:
        logger.info("🧠 Using MemorySaver (luka_bot config not available)")
        _checkpointer = MemorySaver()
        return _checkpointer

    # Check if we should use memory checkpointer (testing mode)
    if getattr(settings, "LUKA_USE_MEMORY_CHECKPOINTER", False):
        logger.info("🧠 Using MemorySaver (testing mode)")
        _checkpointer = MemorySaver()
        return _checkpointer

    # Build Redis URL
    logger.info("💾 Creating Redis checkpointer")
    if settings.REDIS_PASS:
        redis_url = f"redis://:{settings.REDIS_PASS}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DATABASE}"
    else:
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DATABASE}"

    logger.debug(f"Redis URL: redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DATABASE}")

    # Create RedisSaver checkpointer with URL
    _checkpointer = RedisSaver(redis_url)

    return _checkpointer


async def close_checkpointer() -> None:
    """
    Close the checkpointer and cleanup resources.

    This should be called on application shutdown.
    """
    global _checkpointer

    if _checkpointer is not None and isinstance(_checkpointer, RedisSaver):
        # Close Redis connection
        await _checkpointer.conn.aclose()
        _checkpointer = None


__all__ = ["get_checkpointer", "close_checkpointer"]
