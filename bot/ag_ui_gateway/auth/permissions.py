"""
Permission System

Defines permissions and access control decorators.
"""
from enum import Enum
from typing import Optional
from fastapi import Depends, HTTPException, Header
from loguru import logger

from ag_ui_gateway.auth.tokens import TokenManager


class Permission(str, Enum):
    """Permission definitions."""
    # Public (guest allowed)
    READ_PUBLIC_KB = "read:public_kb"
    CHAT_EPHEMERAL = "chat:ephemeral"
    SEARCH_PUBLIC_KB = "search:public_kb"
    
    # Authenticated only
    READ_PRIVATE_KB = "read:private_kb"
    WRITE_KB = "write:kb"
    EXECUTE_WORKFLOWS = "execute:workflows"
    VIEW_TASKS = "view:tasks"
    VIEW_PROFILE = "view:profile"
    UPLOAD_FILES = "upload:files"


async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get current user from token (optional)."""
    if not authorization:
        return None
    
    token = authorization.replace("Bearer ", "")
    token_manager = TokenManager()
    
    user_data = await token_manager.validate_token(token)
    return user_data


async def require_authenticated(authorization: str = Header(...)) -> dict:
    """Require authenticated user."""
    token = authorization.replace("Bearer ", "")
    token_manager = TokenManager()
    
    user_data = await token_manager.validate_token(token)
    
    if not user_data or user_data['token_type'] == 'guest':
        raise HTTPException(
            status_code=403,
            detail={
                "error": "UPGRADE_REQUIRED",
                "message": "This feature requires authentication",
                "upgrade_url": "/api/auth/telegram-miniapp"
            }
        )
    
    return user_data
