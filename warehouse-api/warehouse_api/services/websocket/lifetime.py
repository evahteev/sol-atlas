import logging

from fastapi import FastAPI
from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, process_instance_id: str):
        await websocket.accept()
        if process_instance_id not in self.active_connections:
            self.active_connections[process_instance_id] = []
        self.active_connections[process_instance_id].append(websocket)
        logger.debug(
            f"WebSocket connected: {websocket.client} to processInstanceId: {process_instance_id}"
        )

    def disconnect(self, websocket: WebSocket, process_instance_id: str):
        self.active_connections[process_instance_id].remove(websocket)
        if not self.active_connections[process_instance_id]:
            del self.active_connections[process_instance_id]
        logger.debug(
            f"WebSocket disconnected: {websocket.client} from processInstanceId: {process_instance_id}"
        )

    async def broadcast(self, message: str, process_instance_id: str):
        if process_instance_id in self.active_connections:
            for connection in self.active_connections[process_instance_id]:
                await connection.send_text(message)
                logger.debug(
                    f"Broadcasting message: {message} to processInstanceId: {process_instance_id}"
                )


def init_websocket_manager(app: FastAPI) -> None:  # pragma: no cover
    """
    Initialize websocket.

    :param app: current application.
    """
    app.state.websocket_manager = WebSocketManager()
