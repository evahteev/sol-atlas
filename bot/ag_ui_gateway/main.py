"""
AG-UI Gateway - FastAPI Application Entry Point

This is the main application file that sets up:
- FastAPI app with CORS middleware
- WebSocket routes
- REST API routes
- Health check endpoints
- Static file serving (production)
- Database connections (startup/shutdown)
"""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from ag_ui_gateway.config.settings import settings
from ag_ui_gateway.database import init_database_connections, close_database_connections
from ag_ui_gateway.api import auth, catalog, profile, files, health, agent
from ag_ui_gateway.websocket import chat
from ag_ui_gateway.monitoring.logging_config import setup_logging

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lintainer fespan context manager.
    
    Handles application startup and shutdown events.
    """
    # Startup
    logger.info("🚀 AG-UI Gateway starting...")
    logger.info(f"🔧 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔗 Flow API: {settings.FLOW_API_URL}")
    logger.info(f"🔗 Warehouse WS: {settings.WAREHOUSE_WS_URL}")
    logger.info(f"🌍 CORS Origins: {settings.ALLOWED_ORIGINS}")
    
    # Initialize database connections
    await init_database_connections()
    
    logger.info("✅ AG-UI Gateway started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 AG-UI Gateway shutting down...")
    
    # Close database connections
    await close_database_connections()
    
    logger.info("✅ AG-UI Gateway shut down successfully")


# Create FastAPI app with lifespan
app = FastAPI(
    title="AG-UI Gateway API",
    description="REST + WebSocket API for Luka Bot with AG-UI protocol support",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS Configuration (development only)
if settings.DEBUG:
    logger.info("🌍 CORS enabled for development")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(catalog.router, prefix="/api", tags=["catalog"])
app.include_router(profile.router, prefix="/api", tags=["profile"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(health.router, tags=["health"])
app.include_router(agent.router, prefix="/api", tags=["agent"])

# WebSocket routes
app.add_websocket_route("/ws/chat", chat.websocket_chat)


# Serve static files in production
if not settings.DEBUG:
    static_dir = Path(__file__).parent.parent / "web_app" / "dist"
    
    if static_dir.exists():
        logger.info(f"📁 Serving static files from {static_dir}")
        
        # Serve static assets (JS, CSS, images)
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
        
        # Serve index.html for all other routes (SPA fallback)
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """Serve React SPA for all non-API routes."""
            # Skip API, WebSocket, and utility routes
            if full_path.startswith(("api/", "ws/", "health", "metrics")):
                raise HTTPException(status_code=404, detail="Not found")
            
            index_file = static_dir / "index.html"
            return FileResponse(index_file)
    else:
        logger.warning(f"⚠️  Static files not found at {static_dir}")
        logger.warning("⚠️  Run 'cd web_app && npm run build' to create production build")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AG-UI Gateway API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "ag_ui_gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )

