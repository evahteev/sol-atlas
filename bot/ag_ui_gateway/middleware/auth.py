"""
Authentication Middleware

Token validation and user context injection for requests.
"""
from typing import Callable, Optional
from fastapi import Request, Response
from loguru import logger

from ag_ui_gateway.auth.tokens import get_token_manager


class AuthMiddleware:
    """
    Authentication middleware for REST API.
    
    Validates tokens and injects user context into request state.
    Does not block unauthenticated requests - just adds context.
    """
    
    def __init__(self, app):
        self.app = app
        self.token_manager = get_token_manager()
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with authentication."""
        
        # Skip auth for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        try:
            # Extract token from Authorization header
            token = self._extract_token(request)
            
            if token:
                # Validate token
                user_data = await self.token_manager.validate_token(token)
                
                if user_data:
                    # Inject user context into request state
                    request.state.user_id = user_data.get("user_id")
                    request.state.token_type = user_data.get("token_type")
                    request.state.permissions = user_data.get("permissions", [])
                    request.state.authenticated = True
                    
                    logger.debug(
                        f"✅ Authenticated request: user={request.state.user_id}, "
                        f"type={request.state.token_type}"
                    )
                else:
                    # Invalid token
                    request.state.authenticated = False
                    logger.debug("⚠️  Invalid token in request")
            else:
                # No token provided
                request.state.authenticated = False
            
            # Process request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"❌ Auth middleware error: {e}")
            # Don't block requests if auth fails
            request.state.authenticated = False
            return await call_next(request)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract token from Authorization header or query params."""
        # Try Authorization header first (Bearer token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        # Try query parameter (for WebSocket upgrades)
        token = request.query_params.get("token")
        if token:
            return token
        
        # Try cookie
        token = request.cookies.get("auth_token")
        if token:
            return token
        
        return None
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (doesn't require auth)."""
        public_paths = [
            "/",
            "/health",
            "/health/ready",
            "/health/live",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/guest",
            "/api/auth/telegram-miniapp",
        ]
        
        # Check exact matches
        if path in public_paths:
            return True
        
        # Check prefixes
        public_prefixes = [
            "/assets/",
            "/static/",
        ]
        
        for prefix in public_prefixes:
            if path.startswith(prefix):
                return True
        
        return False


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Dependency to get current user (optional).
    
    Returns None if not authenticated.
    """
    if not getattr(request.state, "authenticated", False):
        return None
    
    return {
        "user_id": getattr(request.state, "user_id", None),
        "token_type": getattr(request.state, "token_type", None),
        "permissions": getattr(request.state, "permissions", [])
    }

