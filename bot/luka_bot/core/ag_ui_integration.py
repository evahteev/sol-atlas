"""
AG-UI Integration Module

This module provides integration between luka_bot and the AG-UI Gateway,
running the AG-UI FastAPI server in the same process as luka_bot.

When AG_UI_ENABLED=True:
- In POLLING mode: AG-UI runs on separate FastAPI server (port 8000)
- In WEBHOOK mode: AG-UI routes are mounted on the webhook aiohttp app (same port)

REST API: /api/auth, /api/catalog, /api/profile, /api/files, /api/agent/luka
WebSocket: /ws/chat  
Health: /health/ping, /health/status

This allows:
1. Integrated mode (default): Both services in one process
2. Separate mode: Run ag_ui_gateway/main.py standalone
"""

import asyncio
from loguru import logger
from aiohttp import web

from luka_bot.core.config import settings

# AG-UI FastAPI app instance (created on demand)
_ag_ui_app = None
_ag_ui_server_task = None


async def mount_ag_ui_on_webhook(webhook_app: web.Application = None):
    """
    Mount AG-UI Gateway on an existing aiohttp webhook server via internal proxy.

    This starts AG-UI on a separate internal port (8001) and returns a proxy handler.
    The caller MUST register the proxy handler as a catch-all route AFTER registering
    all specific routes (webhook, metrics, etc.) to ensure proper route priority.

    CRITICAL: The returned proxy handler must be registered LAST (after webhook handler)
    to avoid intercepting Telegram webhook requests.

    Args:
        webhook_app: The aiohttp application (currently unused, kept for compatibility).

    Returns:
        Proxy handler function to be registered as catch-all route, or None if AG-UI is disabled.
    """
    global _ag_ui_app, _ag_ui_server_task

    if not settings.AG_UI_ENABLED:
        logger.info("ℹ️  AG-UI server disabled (AG_UI_ENABLED=False)")
        return None
    
    try:
        import httpx
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from contextlib import asynccontextmanager
        
        # Import AG-UI components
        from ag_ui_gateway.database import init_database_connections, close_database_connections
        from ag_ui_gateway.api import agent, auth, catalog, profile, files, health
        from ag_ui_gateway.websocket import chat
        
        # Create lifespan context manager
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """AG-UI Gateway lifespan."""
            logger.info("🚀 AG-UI Gateway initializing...")
            await init_database_connections()
            logger.info("✅ AG-UI Gateway ready")
            yield
            logger.info("🛑 AG-UI Gateway shutting down...")
            await close_database_connections()
            logger.info("✅ AG-UI Gateway closed")
        
        # Create FastAPI app
        _ag_ui_app = FastAPI(
            title="AG-UI Gateway (Integrated with luka_bot)",
            description="REST + WebSocket API for Luka Bot with AG-UI protocol support",
            version="1.0.0",
            docs_url="/docs" if settings.DEBUG else None,
            redoc_url="/redoc" if settings.DEBUG else None,
            lifespan=lifespan,
        )
        
        # Add CORS middleware for development
        if settings.DEBUG:
            logger.info(f"🌍 AG-UI CORS enabled: {settings.AG_UI_ALLOWED_ORIGINS}")
            _ag_ui_app.add_middleware(
                CORSMiddleware,
                allow_origins=settings.AG_UI_ALLOWED_ORIGINS,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # Include routers (API routes have priority)
        _ag_ui_app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
        _ag_ui_app.include_router(catalog.router, prefix="/api", tags=["catalog"])
        _ag_ui_app.include_router(profile.router, prefix="/api", tags=["profile"])
        _ag_ui_app.include_router(files.router, prefix="/api", tags=["files"])
        _ag_ui_app.include_router(health.router, tags=["health"])
        _ag_ui_app.include_router(agent.router, prefix="/api", tags=["agent"])
        
        # WebSocket routes
        _ag_ui_app.add_websocket_route("/ws/chat", chat.websocket_chat)
        
        # Proxy to Dojo Next.js server (if configured)
        if settings.AG_UI_DOJO_ENABLED and settings.AG_UI_DOJO_URL:
            from fastapi import Request
            from fastapi.responses import StreamingResponse
            
            logger.info(f"🔗 Proxying root path to Dojo Next.js server at {settings.AG_UI_DOJO_URL}")
            
            @_ag_ui_app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
            async def proxy_to_dojo(request: Request, full_path: str):
                """Proxy all non-API/WS routes to Dojo Next.js server."""
                # Skip API, WebSocket, health, docs, and metrics routes
                if full_path.startswith(("api/", "ws/", "health", "docs", "redoc", "openapi.json", "metrics")):
                    from fastapi import HTTPException
                    raise HTTPException(status_code=404, detail="Not found")
                
                # Build target URL
                target_url = f"{settings.AG_UI_DOJO_URL}/{full_path}"
                if request.url.query:
                    target_url = f"{target_url}?{request.url.query}"
                
                # Forward headers (except host)
                headers = dict(request.headers)
                headers.pop("host", None)
                
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        # Forward the request to Next.js server
                        response = await client.request(
                            method=request.method,
                            url=target_url,
                            headers=headers,
                            content=await request.body(),
                        )
                        
                        # Prepare response headers
                        # IMPORTANT: httpx automatically decompresses responses, so we must
                        # remove Content-Encoding and related headers to prevent the browser
                        # from trying to decompress already-decompressed content
                        response_headers = dict(response.headers)
                        response_headers.pop("content-encoding", None)  # Remove compression headers
                        response_headers.pop("content-length", None)  # Length changed after decompression
                        response_headers.pop("transfer-encoding", None)  # Avoid chunking issues
                        
                        # Return the response
                        return StreamingResponse(
                            response.aiter_bytes(),
                            status_code=response.status_code,
                            headers=response_headers,
                            media_type=response.headers.get("content-type")
                        )
                except httpx.RequestError as e:
                    logger.error(f"Error proxying to Dojo: {e}")
                    from fastapi import HTTPException
                    raise HTTPException(status_code=502, detail=f"Dojo server unavailable: {str(e)}")
            
            logger.info("✅ Dojo proxy configured at root path")
        else:
            # Fallback root endpoint when Dojo is not configured
            @_ag_ui_app.get("/")
            async def root():
                return {
                    "name": "AG-UI Gateway (Integrated)",
                    "version": "1.0.0",
                    "status": "running",
                }
        
        logger.info("✅ AG-UI routes configured:")
        logger.info("   Backend API:")
        logger.info("     • POST   /api/auth/login")
        logger.info("     • POST   /api/auth/guest")
        logger.info("     • GET    /api/catalog")
        logger.info("     • POST   /api/catalog/search")
        logger.info("     • GET    /api/profile")
        logger.info("     • PUT    /api/profile")
        logger.info("     • POST   /api/files/upload")
        logger.info("     • POST   /api/agent/luka")
        logger.info("     • POST   /api/copilotkit/luka (alias)")
        logger.info("     • GET    /api/agent/luka/health")
        logger.info("     • GET    /health/ping")
        logger.info("     • GET    /health/status")
        logger.info("     • WS     /ws/chat")
        if settings.AG_UI_DOJO_ENABLED:
            logger.info("   Frontend:")
            logger.info(f"     • GET    /* → Proxied to Dojo at {settings.AG_UI_DOJO_URL}")
        else:
            logger.info("   Frontend:")
            logger.info("     • GET    / → API info (Dojo proxy disabled)")
        
        # Start AG-UI on internal port 8001 (only accessible via localhost)
        config = uvicorn.Config(
            app=_ag_ui_app,
            host="127.0.0.1",  # Only accessible internally
            port=8001,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(config)
        _ag_ui_server_task = asyncio.create_task(server.serve())
        
        logger.info("✅ AG-UI Gateway started on internal port 127.0.0.1:8001")
        
        # Create proxy handler for aiohttp to forward requests to FastAPI
        async def proxy_to_ag_ui(request):
            """Proxy aiohttp requests to internal AG-UI FastAPI server."""
            # Build target URL
            target_url = f"http://127.0.0.1:8001{request.path}"
            if request.query_string:
                target_url = f"{target_url}?{request.query_string.decode()}"
            
            # Forward headers
            headers = dict(request.headers)
            headers.pop("Host", None)  # Remove host header
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Forward the request
                    response = await client.request(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        content=await request.read(),
                    )
                    
                    # Return aiohttp response
                    return web.Response(
                        body=response.content,
                        status=response.status_code,
                        headers=dict(response.headers)
                    )
            except httpx.RequestError as e:
                logger.error(f"Error proxying to AG-UI: {e}")
                return web.Response(text=f"AG-UI server unavailable: {str(e)}", status=502)
        
        # Return the proxy handler to be registered by caller
        # IMPORTANT: Caller must register this as catch-all route AFTER webhook handler
        logger.info("✅ AG-UI Gateway started on internal port 127.0.0.1:8001")
        logger.info("📌 Proxy handler ready to be registered (register AFTER webhook handler!)")

        return proxy_to_ag_ui

    except ImportError as e:
        logger.warning(f"⚠️  AG-UI Gateway not available: {e}")
        logger.warning("   Install ag_ui_gateway dependencies or disable AG_UI_ENABLED")
        raise
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"❌ Failed to mount AG-UI on webhook server ({error_type}): {error_msg}", exc_info=True)
        raise


async def start_ag_ui_server(webhook_app: web.Application = None) -> None:
    """
    Start the AG-UI Gateway server in polling mode (separate server on port 8000).
    
    NOTE: For webhook mode, use mount_ag_ui_on_webhook() instead, which must be called
    BEFORE aiogram's setup_application() to ensure proper route priority.
    
    Args:
        webhook_app: Ignored (legacy parameter, webhook mode now uses mount_ag_ui_on_webhook)
    """
    global _ag_ui_app, _ag_ui_server_task
    
    if not settings.AG_UI_ENABLED:
        logger.info("ℹ️  AG-UI server disabled (AG_UI_ENABLED=False)")
        return
    
    if webhook_app is not None:
        logger.warning("⚠️  start_ag_ui_server called with webhook_app in webhook mode")
        logger.warning("   Use mount_ag_ui_on_webhook() instead for webhook mode")
        logger.warning("   Skipping AG-UI server start (should be already mounted)")
        return
    
    logger.info("🔧 Starting AG-UI Gateway in polling mode (separate server on port 8000)...")
    
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from contextlib import asynccontextmanager
        
        # Import AG-UI components
        from ag_ui_gateway.database import init_database_connections, close_database_connections
        from ag_ui_gateway.api import agent, auth, catalog, profile, files, health
        from ag_ui_gateway.websocket import chat
        
        # Create lifespan context manager
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """AG-UI Gateway lifespan."""
            logger.info("🚀 AG-UI Gateway initializing...")
            await init_database_connections()
            logger.info("✅ AG-UI Gateway ready")
            yield
            logger.info("🛑 AG-UI Gateway shutting down...")
            await close_database_connections()
            logger.info("✅ AG-UI Gateway closed")
        
        # Create FastAPI app
        _ag_ui_app = FastAPI(
            title="AG-UI Gateway (Integrated with luka_bot)",
            description="REST + WebSocket API for Luka Bot with AG-UI protocol support",
            version="1.0.0",
            docs_url="/docs" if settings.DEBUG else None,
            redoc_url="/redoc" if settings.DEBUG else None,
            lifespan=lifespan,
        )
        
        # Add CORS middleware for development
        if settings.DEBUG:
            logger.info(f"🌍 AG-UI CORS enabled: {settings.AG_UI_ALLOWED_ORIGINS}")
            _ag_ui_app.add_middleware(
                CORSMiddleware,
                allow_origins=settings.AG_UI_ALLOWED_ORIGINS,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # Include routers (API routes have priority)
        _ag_ui_app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
        _ag_ui_app.include_router(catalog.router, prefix="/api", tags=["catalog"])
        _ag_ui_app.include_router(profile.router, prefix="/api", tags=["profile"])
        _ag_ui_app.include_router(files.router, prefix="/api", tags=["files"])
        _ag_ui_app.include_router(health.router, tags=["health"])
        _ag_ui_app.include_router(agent.router, prefix="/api", tags=["agent"])
        
        # WebSocket routes
        _ag_ui_app.add_websocket_route("/ws/chat", chat.websocket_chat)
        
        # Proxy to Dojo Next.js server (if configured)
        if settings.AG_UI_DOJO_ENABLED and settings.AG_UI_DOJO_URL:
            import httpx
            from fastapi import Request
            from fastapi.responses import StreamingResponse
            
            logger.info(f"🔗 Proxying root path to Dojo Next.js server at {settings.AG_UI_DOJO_URL}")
            
            @_ag_ui_app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
            async def proxy_to_dojo(request: Request, full_path: str):
                """Proxy all non-API/WS routes to Dojo Next.js server."""
                # Skip API, WebSocket, health, docs, and metrics routes
                if full_path.startswith(("api/", "ws/", "health", "docs", "redoc", "openapi.json", "metrics")):
                    from fastapi import HTTPException
                    raise HTTPException(status_code=404, detail="Not found")
                
                # Build target URL
                target_url = f"{settings.AG_UI_DOJO_URL}/{full_path}"
                if request.url.query:
                    target_url = f"{target_url}?{request.url.query}"
                
                # Forward headers (except host)
                headers = dict(request.headers)
                headers.pop("host", None)
                
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        # Forward the request to Next.js server
                        response = await client.request(
                            method=request.method,
                            url=target_url,
                            headers=headers,
                            content=await request.body(),
                        )
                        
                        # Prepare response headers
                        # IMPORTANT: httpx automatically decompresses responses, so we must
                        # remove Content-Encoding and related headers to prevent the browser
                        # from trying to decompress already-decompressed content
                        response_headers = dict(response.headers)
                        response_headers.pop("content-encoding", None)  # Remove compression headers
                        response_headers.pop("content-length", None)  # Length changed after decompression
                        response_headers.pop("transfer-encoding", None)  # Avoid chunking issues
                        
                        # Return the response
                        return StreamingResponse(
                            response.aiter_bytes(),
                            status_code=response.status_code,
                            headers=response_headers,
                            media_type=response.headers.get("content-type")
                        )
                except httpx.RequestError as e:
                    logger.error(f"Error proxying to Dojo: {e}")
                    from fastapi import HTTPException
                    raise HTTPException(status_code=502, detail=f"Dojo server unavailable: {str(e)}")
            
            logger.info("✅ Dojo proxy configured at root path")
            logger.info(f"   Proxying to: {settings.AG_UI_DOJO_URL}")
        else:
            # Fallback root endpoint when Dojo is not configured
            @_ag_ui_app.get("/")
            async def root():
                return {
                    "name": "AG-UI Gateway (Integrated)",
                    "version": "1.0.0",
                    "status": "running",
                    "docs": "/docs" if settings.DEBUG else None,
                    "health": "/health",
                    "dojo": {
                        "enabled": False,
                        "note": "Set AG_UI_DOJO_ENABLED=true and AG_UI_DOJO_URL to enable Dojo app proxy"
                    }
                }
        
        logger.info("✅ AG-UI routes registered:")
        logger.info("   Backend API:")
        logger.info("     • POST   /api/auth/login")
        logger.info("     • POST   /api/auth/guest")
        logger.info("     • GET    /api/catalog")
        logger.info("     • POST   /api/catalog/search")
        logger.info("     • GET    /api/profile")
        logger.info("     • PUT    /api/profile")
        logger.info("     • POST   /api/files/upload")
        logger.info("     • POST   /api/agent/luka")
        logger.info("     • POST   /api/copilotkit/luka (alias)")
        logger.info("     • GET    /api/agent/luka/health")
        logger.info("     • GET    /health/ping")
        logger.info("     • GET    /health/status")
        logger.info("     • WS     /ws/chat")
        if settings.AG_UI_DOJO_ENABLED:
            logger.info("   Frontend:")
            logger.info(f"     • GET    /* → Proxied to Dojo at {settings.AG_UI_DOJO_URL}")
        else:
            logger.info("   Frontend:")
            logger.info("     • GET    / → API info (Dojo proxy disabled)")
        
        # Polling mode: Start separate FastAPI server
        import uvicorn
        
        # Configure uvicorn
        config = uvicorn.Config(
            app=_ag_ui_app,
            host="0.0.0.0",
            port=8000,
            log_level="info" if settings.DEBUG else "warning",
            access_log=settings.DEBUG,
        )
        server = uvicorn.Server(config)
        
        # Start server in background task
        _ag_ui_server_task = asyncio.create_task(server.serve())
        
        logger.info("🌐 AG-UI Gateway server started on http://0.0.0.0:8000")
        if settings.DEBUG:
            logger.info("📚 API docs available at http://localhost:8000/docs")
        
    except ImportError as e:
        logger.warning(f"⚠️  AG-UI Gateway not available: {e}")
        logger.warning("   Install ag_ui_gateway dependencies or disable AG_UI_ENABLED")
    except Exception as e:
        # Convert exception to string first to avoid format string conflicts
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Skip non-error exceptions (aiohttp-asgi internals)
        if "ASGIResource" in error_msg or "ASGIResource" in error_type:
            logger.debug(f"AG-UI initialization detail: {error_msg}")
            return
        
        logger.error(f"❌ Failed to start AG-UI server ({error_type}): {error_msg}", exc_info=True)


async def stop_ag_ui_server() -> None:
    """
    Stop the AG-UI FastAPI server.
    
    Called during luka_bot shutdown if AG_UI_ENABLED=True.
    """
    global _ag_ui_server_task
    
    if not settings.AG_UI_ENABLED or _ag_ui_server_task is None:
        return
    
    logger.info("🛑 Stopping AG-UI Gateway server...")
    
    try:
        # Cancel the server task
        _ag_ui_server_task.cancel()
        
        try:
            await _ag_ui_server_task
        except asyncio.CancelledError:
            pass  # Expected
        
        logger.info("✅ AG-UI Gateway server stopped")
        
    except Exception as e:
        logger.error(f"❌ Failed to stop AG-UI server: {e}", exc_info=True)

