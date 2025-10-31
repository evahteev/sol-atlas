"""
Global WebSocket connection manager.
Maintains per-user WebSocket connections with thread-safe access.
"""
import asyncio
from typing import Dict, Optional
from loguru import logger

from luka_bot.services.task_websocket_connection import TaskWebSocketConnection
from luka_bot.core.config import settings


class WebSocketManager:
    """
    Manages per-user WebSocket connections globally.
    Singleton pattern - one instance for entire bot.
    """
    
    def __init__(self):
        """Initialize WebSocket manager."""
        # user_id → WebSocket connection
        self._connections: Dict[int, TaskWebSocketConnection] = {}
        
        # Per-user locks for thread-safe connection creation
        self._locks: Dict[int, asyncio.Lock] = {}
        
        logger.debug("WebSocketManager initialized")
    
    def _get_lock(self, user_id: int) -> asyncio.Lock:
        """
        Get or create lock for user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            asyncio.Lock for the user
        """
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]
    
    async def get_or_create_connection(
        self, 
        user_id: int, 
        jwt_token: str
    ) -> TaskWebSocketConnection:
        """
        Get existing WebSocket connection or create new one.
        Thread-safe and idempotent.
        
        Args:
            user_id: Telegram user ID
            jwt_token: JWT token for authentication
            
        Returns:
            TaskWebSocketConnection instance
        """
        # Check if WebSocket connections are disabled
        from luka_bot.core.config import settings
        if not settings.WAREHOUSE_WS_ENABLED:
            logger.debug(f"WebSocket connections disabled, skipping for user {user_id}")
            return None
        lock = self._get_lock(user_id)
        
        async with lock:
            # Check if connection exists and is healthy
            if user_id in self._connections:
                conn = self._connections[user_id]
                
                if conn.is_connected:
                    # Reusing connection is routine, no need to log
                    
                    # Update token if changed
                    if conn.jwt_token != jwt_token:
                        conn.update_jwt_token(jwt_token)
                    
                    return conn
                else:
                    # Connection exists but not connected - clean it up
                    logger.info(f"🧹 Cleaning up stale WebSocket for user {user_id}")
                    try:
                        await conn.disconnect()
                    except Exception as e:
                        logger.warning(f"⚠️  Error disconnecting stale connection: {e}")
                    del self._connections[user_id]
            
            # Create new connection
            logger.info(f"🆕 Creating WebSocket connection for user {user_id}")
            
            conn = TaskWebSocketConnection(user_id, jwt_token)
            await conn.connect()
            
            self._connections[user_id] = conn
            
            return conn
    
    def get_connection(self, user_id: int) -> Optional[TaskWebSocketConnection]:
        """
        Get existing connection without creating new one.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Connection if exists and connected, None otherwise
        """
        conn = self._connections.get(user_id)
        
        if conn and conn.is_connected:
            return conn
        
        return None
    
    async def disconnect_user(self, user_id: int):
        """
        Disconnect and remove user's WebSocket.
        
        Args:
            user_id: Telegram user ID
        """
        if user_id in self._connections:
            logger.info(f"🔌 Disconnecting WebSocket for user {user_id}")
            try:
                await self._connections[user_id].disconnect()
            except Exception as e:
                logger.warning(f"⚠️  Error disconnecting user {user_id}: {e}")
            
            del self._connections[user_id]
            
            if user_id in self._locks:
                del self._locks[user_id]
    
    async def disconnect_all(self):
        """Disconnect all active WebSocket connections."""
        total = len(self._connections)
        logger.info(f"🔌 Disconnecting all WebSocket connections ({total} active)")
        
        # Create list of user IDs to avoid modifying dict during iteration
        user_ids = list(self._connections.keys())
        
        for user_id in user_ids:
            try:
                await self.disconnect_user(user_id)
            except Exception as e:
                logger.error(f"❌ Error disconnecting user {user_id}: {e}")
        
        logger.info("✅ All WebSocket connections disconnected")
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get WebSocket manager statistics.
        
        Returns:
            Dictionary with statistics
        """
        active_connections = sum(1 for conn in self._connections.values() if conn.is_connected)
        
        return {
            "total_connections": len(self._connections),
            "active_connections": active_connections,
            "users": list(self._connections.keys()),
            "warehouse_enabled": settings.WAREHOUSE_ENABLED,
            "warehouse_ws_url": settings.WAREHOUSE_WS_URL,
        }
    
    def get_connection_status(self, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get detailed status for specific user connection.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Status dictionary or None if no connection
        """
        conn = self._connections.get(user_id)
        
        if conn:
            return conn.get_status()
        
        return None


# Global singleton instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """
    Get global WebSocket manager singleton.
    
    Returns:
        WebSocketManager instance
    """
    global _websocket_manager
    
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
        logger.info("✅ WebSocket manager initialized")
    
    return _websocket_manager


async def shutdown_websocket_manager():
    """Shutdown WebSocket manager and disconnect all connections."""
    global _websocket_manager
    
    if _websocket_manager:
        await _websocket_manager.disconnect_all()
        _websocket_manager = None
        logger.info("✅ WebSocket manager shut down")

