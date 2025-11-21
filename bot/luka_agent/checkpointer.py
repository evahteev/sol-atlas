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


async def get_checkpointer(use_memory: bool | None = None) -> RedisSaver | MemorySaver:
    """
    Get or create the singleton checkpointer instance.

    The checkpointer type is determined by configuration:
    - Memory (default): Used by default for safety and compatibility
    - Redis (production): Used when explicitly enabled via env vars or parameters

    Args:
        use_memory: Optional override. If True, use MemorySaver. If False, use RedisSaver.
                   If None, use settings (defaults to True/MemorySaver).

    Returns:
        RedisSaver or MemorySaver instance

    Example:
        >>> checkpointer = await get_checkpointer()  # Uses default (MemorySaver)
        >>> checkpointer = await get_checkpointer(use_memory=False)  # Forces Redis
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

    # Determine whether to use memory checkpointer
    # Priority: function parameter > env var > default (True)
    should_use_memory = use_memory if use_memory is not None else getattr(settings, "LUKA_USE_MEMORY_CHECKPOINTER", True)

    if should_use_memory:
        logger.info("🧠 Using MemorySaver (configured)")
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
