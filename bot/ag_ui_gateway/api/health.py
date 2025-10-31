"""
Health Check Endpoints
"""
from fastapi import APIRouter
from datetime import datetime
from loguru import logger

from ag_ui_gateway.database import (
    check_redis_health,
    check_postgres_health,
    check_elasticsearch_health
)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint with database status.
    
    Returns:
        Health status and timestamp
    """
    # Check all database connections
    redis_ok = await check_redis_health()
    postgres_ok = await check_postgres_health()
    es_ok = await check_elasticsearch_health()
    
    # Overall status
    overall_status = "healthy" if (redis_ok and postgres_ok) else "degraded"
    if not redis_ok and not postgres_ok:
        overall_status = "unhealthy"
    
    response = {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "redis": "healthy" if redis_ok else "unhealthy",
            "postgres": "healthy" if postgres_ok else "unhealthy",
            "elasticsearch": "healthy" if es_ok else "unhealthy"
        }
    }
    
    return response


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes.
    
    Returns 200 if ready to accept traffic, 503 otherwise.
    """
    redis_ok = await check_redis_health()
    postgres_ok = await check_postgres_health()
    
    if redis_ok and postgres_ok:
        return {"status": "ready"}
    else:
        from fastapi import Response
        return Response(
            content='{"status": "not_ready"}',
            status_code=503,
            media_type="application/json"
        )


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes.
    
    Returns 200 if application is alive.
    """
    return {"status": "alive"}


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # TODO: Implement Prometheus metrics
    return "# HELP http_requests_total Total HTTP requests\n"
