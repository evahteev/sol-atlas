"""
Rate Limiting Middleware

Redis-based rate limiting for API and WebSocket endpoints.
"""
import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from ag_ui_gateway.database import get_redis
from ag_ui_gateway.config.settings import settings


class RateLimitMiddleware:
    """
    Redis-based rate limiting middleware.
    
    Tracks requests per user/IP and enforces limits.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        guest_requests_per_minute: int = 20
    ):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.guest_requests_per_minute = guest_requests_per_minute
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/health/ready", "/health/live", "/metrics"]:
            return await call_next(request)
        
        if request.url.path.startswith("/assets/"):
            return await call_next(request)
        
        try:
            # Get user identifier (IP or user ID from auth)
            user_id = await self._get_user_identifier(request)
            is_guest = await self._is_guest_user(request)
            
            # Check rate limit
            allowed, remaining, reset_time = await self._check_rate_limit(
                user_id,
                is_guest
            )
            
            if not allowed:
                logger.warning(f"⚠️  Rate limit exceeded: {user_id}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": reset_time
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(reset_time)
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Rate limit middleware error: {e}")
            # Don't block requests if rate limiting fails
            return await call_next(request)
    
    async def _get_user_identifier(self, request: Request) -> str:
        """Get user identifier (user ID or IP address)."""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def _is_guest_user(self, request: Request) -> bool:
        """Check if user is a guest."""
        token_type = getattr(request.state, "token_type", None)
        return token_type == "guest"
    
    async def _check_rate_limit(
        self,
        identifier: str,
        is_guest: bool
    ) -> tuple[bool, int, int]:
        """
        Check rate limit for user.
        
        Args:
            identifier: User identifier (user:123 or ip:1.2.3.4)
            is_guest: Whether user is a guest
        
        Returns:
            Tuple of (allowed, remaining_requests, reset_timestamp)
        """
        try:
            redis = get_redis()
            current_time = int(time.time())
            
            # Use different limits for guests
            limit = self.guest_requests_per_minute if is_guest else self.requests_per_minute
            
            # Minute window key
            minute_key = f"ratelimit:minute:{identifier}:{current_time // 60}"
            
            # Increment counter
            count = await redis.incr(minute_key)
            
            # Set expiry on first request
            if count == 1:
                await redis.expire(minute_key, 60)
            
            # Calculate remaining and reset time
            remaining = max(0, limit - count)
            reset_time = ((current_time // 60) + 1) * 60
            
            # Check if limit exceeded
            allowed = count <= limit
            
            if not allowed:
                logger.debug(f"Rate limit exceeded: {identifier} ({count}/{limit})")
            
            return allowed, remaining, reset_time
            
        except Exception as e:
            logger.error(f"❌ Error checking rate limit: {e}")
            # Allow request on error
            return True, limit, int(time.time()) + 60


async def check_websocket_rate_limit(
    user_id: Optional[int],
    is_guest: bool = False
) -> tuple[bool, str]:
    """
    Check rate limit for WebSocket connections.
    
    Args:
        user_id: User ID (None for guests)
        is_guest: Whether user is a guest
    
    Returns:
        Tuple of (allowed, error_message)
    """
    try:
        redis = get_redis()
        current_time = int(time.time())
        
        identifier = f"user:{user_id}" if user_id else f"guest:{int(time.time())}"
        limit = settings.GUEST_RATE_LIMIT_PER_MINUTE if is_guest else 60
        
        # Minute window key
        minute_key = f"ratelimit:ws:minute:{identifier}:{current_time // 60}"
        
        # Increment counter
        count = await redis.incr(minute_key)
        
        # Set expiry on first request
        if count == 1:
            await redis.expire(minute_key, 60)
        
        # Check if limit exceeded
        if count > limit:
            reset_time = ((current_time // 60) + 1) * 60
            wait_seconds = reset_time - current_time
            return False, f"Rate limit exceeded. Try again in {wait_seconds}s."
        
        return True, ""
        
    except Exception as e:
        logger.error(f"❌ Error checking WebSocket rate limit: {e}")
        # Allow connection on error
        return True, ""

