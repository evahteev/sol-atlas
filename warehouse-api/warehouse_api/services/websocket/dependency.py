from starlette.websockets import WebSocket
from taskiq import TaskiqDepends

from warehouse_api.services.websocket.lifetime import WebSocketManager


async def get_websocket_manager(
    websocket: WebSocket = TaskiqDepends(),
) -> WebSocketManager:  # pragma: no cover
    """
    Returns websocket manager.

    You can use it like this:

    >>> from starlette.websockets import WebSocket
    >>>
    >>> async def handler(websocket_manager: WebSocketManager = Depends(get_websocket_manager)):
    >>>     await websocket_manager.broadcast('message')

    :param websocket: current ws request.
    :returns:  websocket manager.
    """
    return websocket.app.state.websocket_manager
