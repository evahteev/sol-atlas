"""
Per-user WebSocket connection to Warehouse API.
Handles authentication, reconnection, and event processing for task notifications.
"""
import asyncio
import json
import time
from typing import Optional, Dict, Any
from websockets import connect, WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException
from loguru import logger

from luka_bot.core.config import settings


class TaskWebSocketConnection:
    """
    WebSocket connection for receiving task events from Warehouse API.
    One instance per user, persists across bot interactions.
    """
    
    def __init__(self, user_id: int, jwt_token: str):
        """
        Initialize WebSocket connection for user.
        
        Args:
            user_id: Telegram user ID
            jwt_token: JWT token for authentication
        """
        self.user_id = user_id
        self.jwt_token = jwt_token
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.is_connected = False
        self.is_stopping = False
        
        # Background tasks
        self._listen_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Reconnection settings
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = settings.WAREHOUSE_WS_MAX_RECONNECT_ATTEMPTS
        self.reconnect_delay = settings.WAREHOUSE_WS_RECONNECT_DELAY
        
        # Circuit breaker for server errors
        self.server_error_count = 0
        self.max_server_errors = 5  # Max consecutive server errors before backing off
        self.server_error_backoff = 60  # Back off for 60 seconds after max errors
    
    async def connect(self):
        """Establish WebSocket connection to Warehouse API."""
        if self.is_connected:
            logger.debug(f"WebSocket already connected for user {self.user_id}")
            return
        
        ws_url = f"{settings.WAREHOUSE_WS_URL}/api/ws/tasks"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        
        try:
            logger.info(f"🔌 Connecting WebSocket for user {self.user_id}...")
            self.websocket = await connect(ws_url, additional_headers=headers)
            self.is_connected = True
            self.reconnect_attempts = 0
            self.server_error_count = 0  # Reset server error count on successful connection
            
            logger.info(f"✅ WebSocket connected: user {self.user_id} → {ws_url}")
            
            # Start background tasks
            self._listen_task = asyncio.create_task(self._listen_loop())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed for user {self.user_id}: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Disconnect WebSocket and cleanup."""
        logger.info(f"🔌 Disconnecting WebSocket for user {self.user_id}")
        self.is_stopping = True
        self.is_connected = False
        
        # Cancel background tasks
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning(f"⚠️  Error closing WebSocket: {e}")
            self.websocket = None
        
        logger.info(f"✅ WebSocket disconnected for user {self.user_id}")
    
    async def _listen_loop(self):
        """Background task to listen for WebSocket messages."""
        try:
            while not self.is_stopping and self.websocket:
                try:
                    message = await self.websocket.recv()
                    await self._handle_message(message)
                    
                except ConnectionClosed:
                    logger.warning(f"⚠️  WebSocket connection closed for user {self.user_id}")
                    self.is_connected = False
                    
                    if not self.is_stopping:
                        await self._attempt_reconnect()
                    break
                    
        except asyncio.CancelledError:
            logger.debug(f"Listen loop cancelled for user {self.user_id}")
        except Exception as e:
            logger.error(f"❌ Error in listen loop for user {self.user_id}: {e}")
            self.is_connected = False
    
    async def _heartbeat_loop(self):
        """Send periodic pings to keep connection alive."""
        try:
            while not self.is_stopping and self.is_connected:
                await asyncio.sleep(settings.WAREHOUSE_WS_HEARTBEAT_INTERVAL)
                
                if self.websocket and self.is_connected:
                    try:
                        await self.websocket.ping()
                        # Heartbeat is routine, don't log unless there's an error
                    except Exception as e:
                        logger.warning(f"⚠️  Heartbeat failed for user {self.user_id}: {e}")
                        
        except asyncio.CancelledError:
            logger.debug(f"Heartbeat loop cancelled for user {self.user_id}")
    
    async def _attempt_reconnect(self):
        """Attempt to reconnect after connection loss."""
        if self.is_stopping:
            return
        
        # Check if we've exceeded max attempts (-1 means infinite)
        if self.max_reconnect_attempts >= 0 and self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"❌ Max reconnect attempts ({self.max_reconnect_attempts}) reached for user {self.user_id}")
            return
        
        self.reconnect_attempts += 1
        
        # Exponential backoff: 5s, 10s, 20s, 40s, 80s, then cap at 160s
        # Add extra delay if we've been getting server errors
        base_delay = self.reconnect_delay * (2 ** min(self.reconnect_attempts - 1, 5))
        if self.server_error_count >= self.max_server_errors:
            delay = max(base_delay, self.server_error_backoff)
        else:
            delay = base_delay
        
        logger.info(
            f"🔄 Reconnecting WebSocket for user {self.user_id} "
            f"(attempt {self.reconnect_attempts}, delay {delay}s)"
        )
        
        await asyncio.sleep(delay)
        
        try:
            await self.connect()
        except Exception as e:
            logger.error(f"❌ Reconnect failed for user {self.user_id}: {e}")
            # Will try again on next iteration if listen_loop is still running
    
    async def _handle_message(self, message: str):
        """Process incoming WebSocket message."""
        try:
            event = json.loads(message)
            await self._process_task_event(event)
            
        except json.JSONDecodeError as e:
            # Check if this is a server error that we should handle gracefully
            if "Internal server error" in message:
                self.server_error_count += 1
                
                if self.server_error_count >= self.max_server_errors:
                    logger.warning(f"⚠️  Too many server errors ({self.server_error_count}) for user {self.user_id}, backing off for {self.server_error_backoff}s")
                    # Close connection to trigger reconnection with backoff
                    if self.websocket:
                        await self.websocket.close()
                    return
                else:
                    logger.warning(f"⚠️  Warehouse API server error for user {self.user_id} ({self.server_error_count}/{self.max_server_errors})")
                    return
            
            # Reset server error count on successful JSON parsing
            self.server_error_count = 0
            logger.warning(f"⚠️  Invalid JSON from WebSocket for user {self.user_id}: {e}")
            logger.debug(f"Message content: {message[:200]}...")
        except Exception as e:
            logger.error(f"❌ Error handling WebSocket message for user {self.user_id}: {e}")
    
    async def _process_task_event(self, event: Dict[str, Any]):
        """
        Process task event and trigger appropriate action.
        
        Event structure:
        {
            "eventType": "create" | "complete" | "update" | "delete",
            "taskId": "task-uuid",
            "taskName": "Task Name",
            "assignee": "922705",  # telegram_user_id
            "processInstanceId": "process-uuid",
            "processDefinitionKey": "chatbot_group_import_history",
            "timestamp": 1234567890,
            "variables": {...}
        }
        """
        event_type = event.get('eventType', '').lower()
        task_id = event.get('taskId')
        task_name = event.get('taskName', 'Unknown Task')
        assignee = event.get('assignee')
        process_id = event.get('processInstanceId')
        process_definition_key = event.get('processDefinitionKey')
        
        # Filter: Only process tasks from chatbot_* process definitions
        if not process_definition_key or not process_definition_key.startswith('chatbot_'):
            logger.info(
                f"🚫 Skipping task from non-chatbot process\n"
                f"   Task: {task_name} ({task_id})\n"
                f"   Process Definition: {process_definition_key}"
            )
            return
        
        logger.info(
            f"📬 Task Event: {event_type.upper()}\n"
            f"   Task: {task_name} ({task_id})\n"
            f"   Process: {process_id}\n"
            f"   Process Definition: {process_definition_key}\n"
            f"   User: {assignee}"
        )
        
        # Route to appropriate handler
        # Pass self.user_id (Telegram user ID) since this connection is authenticated for this user
        from luka_bot.services.task_service import get_task_service
        task_service = get_task_service()
        
        try:
            if event_type == 'create':
                await task_service.handle_task_created_event(event, self.user_id)
            elif event_type == 'complete':
                await task_service.handle_task_completed_event(event, self.user_id)
            elif event_type == 'update':
                await task_service.handle_task_updated_event(event, self.user_id)
            elif event_type == 'delete':
                await task_service.handle_task_deleted_event(event, self.user_id)
            else:
                logger.warning(f"⚠️  Unknown event type: {event_type}")
        except Exception as e:
            logger.error(f"❌ Error processing {event_type} event for task {task_id}: {e}")
    
    def update_jwt_token(self, new_token: str):
        """
        Update JWT token (for token refresh).
        Note: This updates the token but doesn't reconnect.
        Reconnection will happen automatically if needed.
        
        Args:
            new_token: New JWT token
        """
        if self.jwt_token != new_token:
            self.jwt_token = new_token
            logger.info(f"🔑 Updated JWT token for user {self.user_id}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get connection status information.
        
        Returns:
            Dictionary with connection status
        """
        return {
            "user_id": self.user_id,
            "is_connected": self.is_connected,
            "is_stopping": self.is_stopping,
            "reconnect_attempts": self.reconnect_attempts,
            "listen_task_running": self._listen_task and not self._listen_task.done() if self._listen_task else False,
            "heartbeat_task_running": self._heartbeat_task and not self._heartbeat_task.done() if self._heartbeat_task else False,
        }

