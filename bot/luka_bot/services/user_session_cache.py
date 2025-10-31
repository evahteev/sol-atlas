"""
User Session Cache Service

Manages user session data in Redis with TTL management.
Caches user info (including Camunda credentials) and JWT tokens.

Based on bot_server's session cache architecture, adapted for luka_bot.
"""
import time
import orjson
from typing import Dict, Any, Optional
from loguru import logger

from luka_bot.core.loader import redis_client


# Constants
SESSION_TTL_SECONDS = 3600  # 1 hour
JWT_SAFETY_MARGIN = 300  # 5 minutes - expire JWT early for safety


class UserSessionCache:
    """
    Manages user session data in Redis.
    
    Session structure:
    {
        "active": True,
        "cached_at": timestamp,
        "expires_at": timestamp,
        "user_info": {
            "id": "uuid",
            "username": "user",
            "telegram_user_id": 123,
            "camunda_user_id": "user_abc",
            "camunda_key": "secret",
            "webapp_user_id": "uuid",
            ...
        },
        "jwt_token_data": {
            "token": "eyJ...",
            "expires_at": timestamp,
            "cached_at": timestamp
        }
    }
    """
    
    def __init__(self):
        """Initialize session cache with Redis client."""
        self.redis = redis_client
        self.ttl_seconds = SESSION_TTL_SECONDS
    
    def _get_cache_key(self, user_id: int) -> str:
        """
        Generate Redis key for user session.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Redis key string
        """
        return f"user_session:{user_id}"
    
    async def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user session from Redis cache.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Session data dict or None if expired/missing
        """
        try:
            key = self._get_cache_key(user_id)
            data = await self.redis.get(key)
            
            if data:
                session_data = orjson.loads(data)
                
                # Check if session is still valid
                if session_data.get("expires_at", 0) > time.time():
                    # Session cache hit is routine, no need to log
                    return session_data
                else:
                    # Session expired - clean up
                    await self.redis.delete(key)
                    logger.debug(f"🕒 Session expired: user {user_id}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting session for user {user_id}: {e}")
            return None
    
    async def set_session(self, user_id: int, session_data: Dict[str, Any]):
        """
        Save user session to Redis with expiration.
        
        Args:
            user_id: Telegram user ID
            session_data: Session data to cache
        """
        try:
            key = self._get_cache_key(user_id)
            
            # Add metadata
            session_data["expires_at"] = time.time() + self.ttl_seconds
            session_data["cached_at"] = time.time()
            session_data["active"] = True
            
            # Save with TTL
            await self.redis.setex(
                key,
                self.ttl_seconds,
                orjson.dumps(session_data)
            )
            
            logger.debug(f"💾 Cached session: user {user_id} (TTL: {self.ttl_seconds}s)")
            
        except Exception as e:
            logger.error(f"❌ Error saving session for user {user_id}: {e}")
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cached user info from session.
        
        User info includes Camunda credentials:
        - camunda_user_id
        - camunda_key
        - webapp_user_id
        - etc.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User info dict or None if not cached
        """
        session = await self.get_session(user_id)
        if session:
            return session.get("user_info")
        return None
    
    async def set_user_info(self, user_id: int, user_info: Dict[str, Any]):
        """
        Update user info in session.
        
        Args:
            user_id: Telegram user ID
            user_info: User info dict (from Flow API)
        """
        session = await self.get_session(user_id) or {}
        session["user_info"] = user_info
        await self.set_session(user_id, session)
        logger.debug(f"💾 Cached user info: user {user_id}")
    
    async def get_jwt_token(self, user_id: int) -> Optional[str]:
        """
        Get cached JWT token if still valid.
        
        Checks token expiration with safety margin (5 min).
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            JWT token string or None if expired/missing
        """
        session = await self.get_session(user_id)
        if session:
            jwt_data = session.get("jwt_token_data", {})
            
            # Check validity with safety margin
            if jwt_data.get("expires_at", 0) > time.time() + JWT_SAFETY_MARGIN:
                # JWT cache hit is routine, no need to log
                return jwt_data.get("token")
            else:
                logger.debug(f"🕒 JWT expired for user {user_id}")
        
        return None
    
    async def set_jwt_token(
        self,
        user_id: int,
        token: str,
        expires_in: int = SESSION_TTL_SECONDS
    ):
        """
        Cache JWT token with expiration.
        
        Args:
            user_id: Telegram user ID
            token: JWT token string
            expires_in: Token expiration time in seconds
        """
        session = await self.get_session(user_id) or {}
        
        session["jwt_token_data"] = {
            "token": token,
            "expires_at": time.time() + expires_in,
            "cached_at": time.time()
        }
        
        await self.set_session(user_id, session)
        logger.info(f"✅ Cached JWT token: user {user_id} (expires in {expires_in}s)")
    
    async def clear_session(self, user_id: int):
        """
        Clear user session from cache.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            key = self._get_cache_key(user_id)
            await self.redis.delete(key)
            logger.info(f"🗑️  Cleared session: user {user_id}")
        except Exception as e:
            logger.error(f"❌ Error clearing session for user {user_id}: {e}")
    
    async def get_session_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get session statistics for debugging.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Stats dict with session info
        """
        session = await self.get_session(user_id)
        if not session:
            return {"cached": False}
        
        stats = {
            "cached": True,
            "session_age": time.time() - session.get("cached_at", 0),
            "expires_in": session.get("expires_at", 0) - time.time(),
            "has_user_info": "user_info" in session,
            "has_jwt": "jwt_token_data" in session
        }
        
        if "jwt_token_data" in session:
            jwt_data = session["jwt_token_data"]
            stats["jwt_expires_in"] = jwt_data.get("expires_at", 0) - time.time()
        
        return stats


# Singleton instance
_user_session_cache: Optional[UserSessionCache] = None


def get_user_session_cache() -> UserSessionCache:
    """
    Get or create UserSessionCache singleton.
    
    Returns:
        UserSessionCache instance
    """
    global _user_session_cache
    if _user_session_cache is None:
        _user_session_cache = UserSessionCache()
        logger.info("✅ UserSessionCache singleton created")
    return _user_session_cache


# Convenience helper functions
async def get_cached_user_info(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Helper to get cached user info.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        User info dict or None
    """
    cache = get_user_session_cache()
    return await cache.get_user_info(user_id)


async def cache_user_info(user_id: int, user_info: Dict[str, Any]):
    """
    Helper to cache user info.
    
    Args:
        user_id: Telegram user ID
        user_info: User info dict
    """
    cache = get_user_session_cache()
    await cache.set_user_info(user_id, user_info)


async def get_cached_jwt_token(user_id: int) -> Optional[str]:
    """
    Helper to get cached JWT token.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        JWT token string or None
    """
    cache = get_user_session_cache()
    return await cache.get_jwt_token(user_id)


async def cache_jwt_token(user_id: int, token: str, expires_in: int = SESSION_TTL_SECONDS):
    """
    Helper to cache JWT token.
    
    Args:
        user_id: Telegram user ID
        token: JWT token string
        expires_in: Token expiration time in seconds
    """
    cache = get_user_session_cache()
    await cache.set_jwt_token(user_id, token, expires_in)

