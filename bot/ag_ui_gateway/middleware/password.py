"""
Password authentication middleware for AG-UI Gateway.

When LUKA_PASSWORD_ENABLED is True, users must provide the password
before they can interact with the agent.
"""
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
import json

# Import settings from luka_bot (shared config)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from luka_bot.core.config import settings


class PasswordAuthError(Exception):
    """Raised when password authentication fails."""
    pass


async def verify_password_for_session(
    session_token: Optional[str],
    password: Optional[str] = None,
    user_id: Optional[str] = None
) -> bool:
    """
    Verify password for a session.
    
    Args:
        session_token: Guest token or JWT token
        password: Password attempt (if authenticating)
        
    Returns:
        True if authenticated, False otherwise
        
    Raises:
        PasswordAuthError: If password is required but missing/wrong
    """
    # Skip if password protection is disabled
    if not settings.LUKA_PASSWORD_ENABLED:
        return True
    
    # Skip if no password configured
    if not settings.LUKA_PASSWORD:
        logger.warning("⚠️ LUKA_PASSWORD_ENABLED=True but LUKA_PASSWORD is empty!")
        return True
    
    # Normalize identifiers
    normalized_token = session_token.strip() if session_token else None
    normalized_user_id = str(user_id).strip() if user_id not in (None, "") else None
    
    # Get Redis connection
    from ag_ui_gateway.database import get_redis
    redis = get_redis()
    
    # Check if session is already password-authenticated
    ttl_seconds = 60 * 60 * 24 * 7  # 7 days
    token_key = f"password_auth:token:{normalized_token}" if normalized_token else None
    user_key = f"password_auth:user:{normalized_user_id}" if normalized_user_id else None
    candidate_keys = [key for key in (token_key, user_key) if key]
    
    try:
        # Fast path: any stored authentication marks session as trusted
        for key in candidate_keys:
            if await redis.get(key):
                # Refresh session token cache if only user key existed
                if token_key and key != token_key:
                    await redis.setex(token_key, ttl_seconds, "1")
                return True
        
        # Not authenticated - check if password provided
        if password is None:
            # No password provided
            raise PasswordAuthError("Password required")
        
        # Verify password
        if password.strip() == settings.LUKA_PASSWORD:
            # Correct password - store authentication for token and user
            if not candidate_keys:
                logger.warning("⚠️ Password verified but no session/user key to store state")
                return True
            
            for key in candidate_keys:
                await redis.setex(key, ttl_seconds, "1")
            logger.info("✅ Session authenticated with password")
            return True
        else:
            # Wrong password
            logger.warning(f"❌ Session {session_token[:20]}... failed password authentication")
            raise PasswordAuthError("Incorrect password")
            
    except PasswordAuthError:
        raise
    except Exception as e:
        logger.error(f"Error checking password authentication: {e}")
        # On error, allow access (graceful degradation)
        return True


async def require_password_auth(request: Request) -> None:
    """
    FastAPI dependency that enforces password authentication.
    
    Usage:
        @router.post("/protected", dependencies=[Depends(require_password_auth)])
        async def protected_endpoint():
            ...
    """
    # Skip if password protection is disabled
    if not settings.LUKA_PASSWORD_ENABLED or not settings.LUKA_PASSWORD:
        return
    
    # Extract session token from request
    token = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    if not token:
        # No token - check if it's an auth request
        if request.url.path.endswith(("/auth/guest", "/auth/login")):
            # Auth endpoints handle password themselves
            return
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Check password authentication
    try:
        await verify_password_for_session(token, password=None)
    except PasswordAuthError as e:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "password_required",
                "message": "Password authentication required",
                "hint": "Include 'password' in your request body or authenticate first"
            }
        )


async def check_password_on_agent_request(request: Request, token: str, password: Optional[str] = None):
    """
    Check password authentication for agent requests.
    
    This is called from the agent endpoint to verify password before processing.
    
    Args:
        request: FastAPI request
        token: Session token
        password: Optional password from request body
        
    Raises:
        HTTPException: If password is required but not provided or wrong
    """
    # Skip if password protection is disabled
    if not settings.LUKA_PASSWORD_ENABLED or not settings.LUKA_PASSWORD:
        return
    
    try:
        await verify_password_for_session(token, password)
    except PasswordAuthError as e:
        if "required" in str(e).lower():
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "password_required",
                    "message": "This bot is password-protected. Please provide the password.",
                    "hint": "Add 'password' field to your request"
                }
            )
        else:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "invalid_password",
                    "message": "Incorrect password. Please try again."
                }
            )
