from fastapi.routing import APIRouter

from warehouse_api.web.api import docs, monitoring, users, websocket, resources

api_router = APIRouter()
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(monitoring.router)
api_router.include_router(users.router)
api_router.include_router(docs.router)
api_router.include_router(resources.router)
