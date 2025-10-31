"""
Database connection management for AG-UI Gateway.

Provides:
- Redis client for caching and sessions
- PostgreSQL async connection pool  
- Elasticsearch client for KB search
- Lifecycle management (startup/shutdown)
"""
from typing import Optional
from contextlib import asynccontextmanager

from redis.asyncio import ConnectionPool, Redis
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
try:
    from sqlalchemy.ext.asyncio import async_sessionmaker
except ImportError:
    # Fallback for older SQLAlchemy < 2.0
    from sqlalchemy.orm import sessionmaker as async_sessionmaker
from loguru import logger

from ag_ui_gateway.config.settings import settings


# Global clients
_redis_client: Optional[Redis] = None
_es_client: Optional[AsyncElasticsearch] = None
_db_engine: Optional[AsyncEngine] = None
_async_session_maker: Optional[async_sessionmaker] = None


async def init_database_connections():
    """
    Initialize all database connections on application startup.
    
    Should be called from FastAPI lifespan context manager.
    """
    global _redis_client, _es_client, _db_engine, _async_session_maker
    
    logger.info("🔌 Initializing database connections...")
    
    # Initialize Redis
    try:
        _redis_client = Redis(
            connection_pool=ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASS,
                db=settings.REDIS_DATABASE,
                retry_on_timeout=True,
                retry_on_error=[
                    ConnectionError,
                    TimeoutError,
                    ConnectionResetError,
                    ConnectionRefusedError,
                    ConnectionAbortedError,
                ],
                health_check_interval=30,
            ),
        )
        
        # Test connection
        await _redis_client.ping()
        logger.info(f"✅ Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        raise
    
    # Initialize Elasticsearch
    if settings.ELASTICSEARCH_ENABLED:
        try:
            _es_client = AsyncElasticsearch(
                settings.ELASTICSEARCH_URL,
                request_timeout=settings.ELASTICSEARCH_TIMEOUT,
                verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS
            )
            
            # Test connection
            info = await _es_client.info()
            logger.info(f"✅ Elasticsearch connected: {info['version']['number']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
            # Don't raise - ES is optional
            _es_client = None
    else:
        logger.info("⏭️  Elasticsearch disabled (ELASTICSEARCH_ENABLED=False)")
    
    # Initialize PostgreSQL
    if settings.POSTGRES_ENABLED:
        try:
            database_url = (
                f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
                f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
            )
            
            _db_engine = create_async_engine(
                database_url,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_pre_ping=True,
                echo=settings.DB_ECHO
            )
            
            # Create session maker
            _async_session_maker = async_sessionmaker(
                _db_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with _db_engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            logger.info(
                f"✅ PostgreSQL connected: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
    else:
        logger.info("⏭️  PostgreSQL disabled (POSTGRES_ENABLED=False)")
    
    logger.info("🎉 All database connections initialized")


async def close_database_connections():
    """
    Close all database connections on application shutdown.
    
    Should be called from FastAPI lifespan context manager.
    """
    global _redis_client, _es_client, _db_engine
    
    logger.info("🔌 Closing database connections...")
    
    # Close Redis
    if _redis_client:
        try:
            await _redis_client.aclose()
            logger.info("✅ Redis connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing Redis: {e}")
    
    # Close Elasticsearch
    if _es_client:
        try:
            await _es_client.close()
            logger.info("✅ Elasticsearch connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing Elasticsearch: {e}")
    
    # Close PostgreSQL
    if _db_engine:
        try:
            await _db_engine.dispose()
            logger.info("✅ PostgreSQL connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing PostgreSQL: {e}")
    
    logger.info("🎉 All database connections closed")


def get_redis() -> Redis:
    """
    Get Redis client instance.
    
    Returns:
        Redis client
        
    Raises:
        RuntimeError: If Redis is not initialized
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_database_connections() first.")
    return _redis_client


def get_elasticsearch() -> Optional[AsyncElasticsearch]:
    """
    Get Elasticsearch client instance.
    
    Returns:
        Elasticsearch client or None if disabled
    """
    return _es_client


async def get_db_session() -> AsyncSession:
    """
    Get database session for dependency injection.
    
    Usage in FastAPI:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session
        
    Raises:
        RuntimeError: If PostgreSQL is not initialized
    """
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_database_connections() first.")
    
    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session_context():
    """
    Get database session for use in context manager.
    
    Usage:
        async with get_db_session_context() as session:
            result = await session.execute(select(Item))
            items = result.scalars().all()
    
    Yields:
        AsyncSession: Database session
    """
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_database_connections() first.")
    
    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Health check functions
async def check_redis_health() -> bool:
    """Check if Redis is healthy."""
    try:
        if _redis_client:
            await _redis_client.ping()
            return True
        return False
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


async def check_elasticsearch_health() -> bool:
    """Check if Elasticsearch is healthy."""
    try:
        if _es_client:
            await _es_client.ping()
            return True
        return False
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        return False


async def check_postgres_health() -> bool:
    """Check if PostgreSQL is healthy."""
    try:
        if _db_engine:
            async with _db_engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        return False
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return False

