"""
Flow API Authentication Integration

Fetches user data and JWT tokens from Flow API with Redis caching.
Based on luka_bot's flow_api_jwt_service.py architecture.
"""
import time
import orjson
from typing import Optional
import httpx
from loguru import logger
from fastapi import HTTPException

from ag_ui_gateway.config.settings import settings
from ag_ui_gateway.database import get_redis


# Cache TTL
USER_INFO_TTL = 3600  # 1 hour
JWT_TOKEN_TTL = 3300  # 55 minutes (5 min safety margin)


class FlowAuthService:
    """
    Flow API authentication service with Redis caching.
    
    Flow:
    1. Get user by telegram_user_id or camunda_user_id
    2. Extract webapp_user_id
    3. Call login endpoint to get JWT
    4. Cache everything in Redis
    """
    
    def __init__(self):
        self.base_url = settings.FLOW_API_URL
        self.sys_key = settings.FLOW_API_SYS_KEY
        self.timeout = 15.0
    
    async def authenticate_user(self, telegram_user_id: int, user_metadata: Optional[dict] = None) -> dict:
        """
        Authenticate user via Flow API.
        
        Args:
            telegram_user_id: Telegram user ID
            user_metadata: Optional user metadata (username, first_name, etc.)
        
        Returns:
            dict with jwt_token and user_info
            
        Raises:
            HTTPException: If authentication fails
        """
        redis = get_redis()
        
        # Check cache first
        cached_session = await self._get_cached_session(redis, telegram_user_id)
        if cached_session:
            logger.debug(f"Session cache hit for user {telegram_user_id}")
            return cached_session
        
        # Fetch from Flow API
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Step 1: Get or create user
                user_info = await self._get_or_create_user(
                    client, 
                    telegram_user_id, 
                    user_metadata
                )
                
                if not user_info:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to get user info from Flow API"
                    )
                
                # Step 2: Get JWT token
                jwt_token = await self._get_jwt_token(client, user_info)
                
                if not jwt_token:
                    # Generate fallback token if Flow API login unavailable
                    logger.warning(f"Flow API login unavailable, using fallback token for user {telegram_user_id}")
                    jwt_token = self._generate_fallback_token(user_info)
                
                # Step 3: Cache in Redis
                session_data = {
                    'jwt_token': jwt_token,
                    'user_info': user_info,
                    'cached_at': time.time()
                }
                
                await self._cache_session(redis, telegram_user_id, session_data)
                
                logger.info(f"✅ User {telegram_user_id} authenticated successfully")
                return session_data
                
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Flow API at {self.base_url}")
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
        except httpx.TimeoutException:
            logger.error("Flow API request timed out")
            raise HTTPException(
                status_code=504,
                detail="Authentication request timed out"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Authentication failed"
            )
    
    async def _get_or_create_user(
        self, 
        client: httpx.AsyncClient, 
        telegram_user_id: int,
        user_metadata: Optional[dict] = None
    ) -> Optional[dict]:
        """
        Get or create user in Flow API.
        
        Args:
            client: HTTP client
            telegram_user_id: Telegram user ID
            user_metadata: Optional user metadata
        
        Returns:
            User info dict or None
        """
        try:
            # Try to get existing user
            user_url = f"{self.base_url}/api/users"
            params = {"telegram_user_id": telegram_user_id}
            headers = {"X-SYS-KEY": self.sys_key}
            
            response = await client.get(user_url, params=params, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.debug(f"Found user in Flow API: telegram_id={telegram_user_id}")
                return user_data
            
            elif response.status_code == 404:
                # User not found, try to create
                logger.info(f"User not found, creating new user: telegram_id={telegram_user_id}")
                return await self._create_user(client, telegram_user_id, user_metadata)
            
            else:
                logger.warning(f"Flow API user lookup failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user from Flow API: {e}")
            return None
    
    async def _create_user(
        self, 
        client: httpx.AsyncClient, 
        telegram_user_id: int,
        user_metadata: Optional[dict] = None
    ) -> Optional[dict]:
        """
        Create new user in Flow API.
        
        Args:
            client: HTTP client
            telegram_user_id: Telegram user ID
            user_metadata: Optional user metadata
        
        Returns:
            Created user info or None
        """
        try:
            create_url = f"{self.base_url}/api/users"
            headers = {"X-SYS-KEY": self.sys_key}
            
            payload = {
                "telegram_user_id": telegram_user_id,
                "username": user_metadata.get("username") if user_metadata else None,
                "first_name": user_metadata.get("first_name") if user_metadata else None,
                "last_name": user_metadata.get("last_name") if user_metadata else None,
            }
            
            response = await client.post(create_url, json=payload, headers=headers)
            
            if response.status_code in (200, 201):
                user_data = response.json()
                logger.info(f"✅ Created new user: telegram_id={telegram_user_id}")
                return user_data
            else:
                logger.warning(f"Flow API user creation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating user in Flow API: {e}")
            return None
    
    async def _get_jwt_token(self, client: httpx.AsyncClient, user_info: dict) -> Optional[str]:
        """
        Get JWT token from Flow API login endpoint.
        
        Based on luka_bot's flow_api_jwt_service.py logic:
        1. Extract webapp_user_id or camunda_user_id
        2. Call /api/login/{user_id}
        3. Return JWT token
        
        Args:
            client: HTTP client
            user_info: User info from Flow API
        
        Returns:
            JWT token string or None
        """
        try:
            # Try webapp_user_id first, fall back to camunda_user_id
            user_id = user_info.get("webapp_user_id") or user_info.get("camunda_user_id")
            
            if not user_id:
                logger.warning("No webapp_user_id or camunda_user_id found in user info")
                return None
            
            login_url = f"{self.base_url}/api/login/{user_id}"
            response = await client.get(login_url)
            
            if response.status_code == 200:
                auth_data = response.json()
                jwt_token = auth_data.get("access_token")
                
                if jwt_token:
                    logger.debug(f"✅ Got JWT token from Flow API for user_id={user_id}")
                    return jwt_token
                else:
                    logger.warning("No access_token in Flow API login response")
                    return None
            
            elif response.status_code == 404:
                logger.info("Flow API login endpoint not found (404) - JWT auth not available")
                return None
            
            else:
                logger.warning(f"Flow API login failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting JWT token from Flow API: {e}")
            return None
    
    def _generate_fallback_token(self, user_info: dict) -> str:
        """
        Generate fallback JWT token when Flow API is unavailable.
        
        Args:
            user_info: User info dict
        
        Returns:
            JWT token string
        """
        from jose import jwt
        
        payload = {
            'sub': str(user_info.get('telegram_user_id')),
            'telegram_user_id': user_info.get('telegram_user_id'),
            'camunda_user_id': user_info.get('camunda_user_id'),
            'type': 'authenticated',
            'fallback': True,
            'exp': int(time.time()) + JWT_TOKEN_TTL
        }
        
        return jwt.encode(payload, settings.AUTHJWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    async def _get_cached_session(self, redis, telegram_user_id: int) -> Optional[dict]:
        """Get cached session from Redis."""
        try:
            key = f"flow_session:{telegram_user_id}"
            data = await redis.get(key)
            
            if data:
                session = orjson.loads(data)
                
                # Check if session is still valid (TTL handled by Redis, but double-check)
                cached_at = session.get("cached_at", 0)
                if time.time() - cached_at < JWT_TOKEN_TTL:
                    return session
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached session: {e}")
            return None
    
    async def _cache_session(self, redis, telegram_user_id: int, session_data: dict):
        """Cache session in Redis with TTL."""
        try:
            key = f"flow_session:{telegram_user_id}"
            await redis.setex(
                key,
                USER_INFO_TTL,
                orjson.dumps(session_data)
            )
            logger.debug(f"💾 Cached session for user {telegram_user_id}")
            
        except Exception as e:
            logger.error(f"Error caching session: {e}")
    
    async def clear_session(self, telegram_user_id: int):
        """Clear user session from cache."""
        try:
            redis = get_redis()
            key = f"flow_session:{telegram_user_id}"
            await redis.delete(key)
            logger.info(f"🗑️  Cleared session for user {telegram_user_id}")
        except Exception as e:
            logger.error(f"Error clearing session: {e}")


# Singleton instance
_flow_auth_service: Optional[FlowAuthService] = None


def get_flow_auth_service() -> FlowAuthService:
    """Get or create FlowAuthService singleton."""
    global _flow_auth_service
    if _flow_auth_service is None:
        _flow_auth_service = FlowAuthService()
    return _flow_auth_service
