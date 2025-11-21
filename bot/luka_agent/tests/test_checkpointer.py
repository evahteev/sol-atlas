"""
Tests for luka_agent checkpointer (Redis-based state persistence).

Tests validate checkpointer creation, singleton pattern, and basic functionality.
Note: These tests use MemorySaver instead of Redis for test isolation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from luka_agent.checkpointer import get_checkpointer, close_checkpointer


class TestCheckpointerCreation:
    """Test checkpointer creation and initialization."""

    @pytest.mark.asyncio
    async def test_get_checkpointer_returns_checkpointer(self):
        """Test get_checkpointer returns a checkpointer instance."""
        # Use memory checkpointer for testing
        with patch('luka_agent.checkpointer.settings') as mock_settings:
            mock_settings.LUKA_USE_MEMORY_CHECKPOINTER = True

            # Reset singleton
            import luka_agent.checkpointer as checkpointer_module
            checkpointer_module._checkpointer = None

            checkpointer = await get_checkpointer()

            assert checkpointer is not None

    @pytest.mark.asyncio
    async def test_checkpointer_has_required_methods(self):
        """Test checkpointer has required LangGraph methods."""
        with patch('luka_agent.checkpointer.settings') as mock_settings:
            mock_settings.LUKA_USE_MEMORY_CHECKPOINTER = True

            # Reset singleton
            import luka_agent.checkpointer as checkpointer_module
            checkpointer_module._checkpointer = None

            checkpointer = await get_checkpointer()

            # Check for LangGraph checkpointer interface
            assert hasattr(checkpointer, 'get') or hasattr(checkpointer, 'aget')
            assert hasattr(checkpointer, 'put') or hasattr(checkpointer, 'aput')


class TestCheckpointerSingleton:
    """Test checkpointer singleton pattern."""

    @pytest.mark.asyncio
    async def test_get_checkpointer_returns_same_instance(self):
        """Test get_checkpointer returns same instance (singleton)."""
        with patch('luka_agent.checkpointer.settings') as mock_settings:
            mock_settings.LUKA_USE_MEMORY_CHECKPOINTER = True

            # Reset singleton
            import luka_agent.checkpointer as checkpointer_module
            checkpointer_module._checkpointer = None

            # Get checkpointer twice
            checkpointer1 = await get_checkpointer()
            checkpointer2 = await get_checkpointer()

            # Should be same instance
            assert checkpointer1 is checkpointer2

    @pytest.mark.asyncio
    async def test_checkpointer_singleton_persists_across_calls(self):
        """Test singleton persists across multiple calls."""
        with patch('luka_agent.checkpointer.settings') as mock_settings:
            mock_settings.LUKA_USE_MEMORY_CHECKPOINTER = True

            # Reset singleton
            import luka_agent.checkpointer as checkpointer_module
            checkpointer_module._checkpointer = None

            # Get checkpointer multiple times
            instances = []
            for _ in range(5):
                checkpointer = await get_checkpointer()
                instances.append(checkpointer)

            # All should be same instance
            assert all(instance is instances[0] for instance in instances)


class TestCheckpointerCleanup:
    """Test checkpointer cleanup."""

    @pytest.mark.skip(reason="Skipped until integration is complete")
    @pytest.mark.asyncio
    async def test_close_checkpointer_clears_singleton(self):
        """Test close_checkpointer clears global instance."""
        with patch('luka_agent.checkpointer.settings') as mock_settings:
            mock_settings.LUKA_USE_MEMORY_CHECKPOINTER = True

            # Reset singleton
            import luka_agent.checkpointer as checkpointer_module
            checkpointer_module._checkpointer = None

            # Get checkpointer
            checkpointer1 = await get_checkpointer()
            assert checkpointer1 is not None

            # Close it
            await close_checkpointer()

            # Global should be reset
            assert checkpointer_module._checkpointer is None

            # Getting checkpointer again should create new instance
            checkpointer2 = await get_checkpointer()
            assert checkpointer2 is not None
            # Note: With MemorySaver, instances may be different after close


class TestCheckpointerMode:
    """Test checkpointer mode selection."""

    @pytest.mark.asyncio
    async def test_memory_checkpointer_in_test_mode(self):
        """Test memory checkpointer is used when configured."""
        from langgraph.checkpoint.memory import MemorySaver

        with patch('luka_agent.checkpointer.settings') as mock_settings:
            mock_settings.LUKA_USE_MEMORY_CHECKPOINTER = True

            # Reset singleton
            import luka_agent.checkpointer as checkpointer_module
            checkpointer_module._checkpointer = None

            checkpointer = await get_checkpointer()

            # Should be MemorySaver in test mode
            assert isinstance(checkpointer, MemorySaver)

    @pytest.mark.skip(reason="Skipped until integration is complete")
    @pytest.mark.asyncio
    async def test_redis_checkpointer_in_production_mode(self):
        """Test Redis checkpointer is created when not in test mode."""
        from langgraph.checkpoint.redis import RedisSaver
        from redis.asyncio import ConnectionPool, Redis

        # Mock Redis components
        with patch('redis.asyncio.ConnectionPool') as mock_pool:
            with patch('redis.asyncio.Redis') as mock_redis:
                with patch('luka_agent.checkpointer.settings') as mock_settings:
                    mock_settings.LUKA_USE_MEMORY_CHECKPOINTER = False
                    mock_settings.redis_settings.host = "localhost"
                    mock_settings.redis_settings.port = 6379
                    mock_settings.redis_settings.db = 0
                    mock_settings.redis_settings.password = None

                    # Mock Redis client
                    mock_redis_client = AsyncMock()
                    mock_redis.return_value = mock_redis_client

                    # Reset singleton
                    import luka_agent.checkpointer as checkpointer_module
                    checkpointer_module._checkpointer = None

                    checkpointer = await get_checkpointer()

                    # Should be RedisSaver in production mode
                    assert isinstance(checkpointer, RedisSaver)


class TestCheckpointerConfiguration:
    """Test checkpointer configuration."""

    @pytest.mark.skip(reason="Skipped until integration is complete")
    @pytest.mark.asyncio
    async def test_redis_connection_uses_settings(self):
        """Test Redis connection uses correct settings."""
        from redis.asyncio import ConnectionPool, Redis

        with patch('redis.asyncio.ConnectionPool') as mock_pool:
            with patch('redis.asyncio.Redis') as mock_redis:
                with patch('luka_agent.checkpointer.settings') as mock_settings:
                    mock_settings.LUKA_USE_MEMORY_CHECKPOINTER = False
                    mock_settings.redis_settings.host = "test-host"
                    mock_settings.redis_settings.port = 6380
                    mock_settings.redis_settings.db = 5
                    mock_settings.redis_settings.password = "test-pass"

                    mock_redis_client = AsyncMock()
                    mock_redis.return_value = mock_redis_client

                    # Reset singleton
                    import luka_agent.checkpointer as checkpointer_module
                    checkpointer_module._checkpointer = None

                    await get_checkpointer()

                    # Verify ConnectionPool was called with correct params
                    mock_pool.assert_called_once()
                    call_kwargs = mock_pool.call_args[1]

                    assert call_kwargs["host"] == "test-host"
                    assert call_kwargs["port"] == 6380
                    assert call_kwargs["db"] == 5
                    assert call_kwargs["password"] == "test-pass"
