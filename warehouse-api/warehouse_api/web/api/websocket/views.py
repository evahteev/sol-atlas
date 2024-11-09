from fastapi import APIRouter, Path
from starlette.websockets import WebSocket

router = APIRouter()


@router.websocket("/ws/{process_instance_id}")
async def websocket_endpoint(websocket: WebSocket, process_instance_id: str = Path(...)):
    ws_manager = websocket.app.state.websocket_manager
    await ws_manager.connect(websocket, process_instance_id)
    try:
        while True:
            await websocket.receive()
    except Exception:
        ws_manager.disconnect(websocket, process_instance_id)
