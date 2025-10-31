"""
Authentication API Endpoints

Handles Telegram Mini App authentication, guest sessions, and token refresh.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from loguru import logger

from ag_ui_gateway.auth.telegram_miniapp import validate_telegram_webapp_data
from ag_ui_gateway.auth.flow_auth import get_flow_auth_service
from ag_ui_gateway.auth.tokens import get_token_manager, GuestToken
from ag_ui_gateway.config.settings import settings

router = APIRouter()


class TelegramAuthRequest(BaseModel):
    """Telegram Mini App authentication request."""
    initData: str


class AuthResponse(BaseModel):
    """Authentication response."""
    jwt_token: str
    expires_in: int
    user: dict


@router.post("/telegram-miniapp", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def authenticate_telegram_miniapp(request: TelegramAuthRequest):
    """
    Authenticate user via Telegram Mini App initData.
    
    Validates Telegram signature, fetches user from Flow API,
    generates JWT token, and returns user data.
    """
    try:
        # Validate Telegram signature
        user_data = validate_telegram_webapp_data(
            request.initData,
            settings.BOT_TOKEN
        )
        
        telegram_user_id = user_data['telegram_user_id']
        logger.info(f"Telegram auth request for user {telegram_user_id}")
        
        # Authenticate with Flow API
        flow_auth = get_flow_auth_service()
        auth_result = await flow_auth.authenticate_user(telegram_user_id, user_data)
        
        return AuthResponse(
            jwt_token=auth_result['jwt_token'],
            expires_in=settings.JWT_EXPIRY_SECONDS,
            user=auth_result['user']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/guest", status_code=status.HTTP_201_CREATED)
async def create_guest_session():
    """
    Create guest session for anonymous browsing.
    
    Returns guest token with limited permissions.
    """
    try:
        token_manager = get_token_manager()
        session = await token_manager.create_guest_session()
        
        logger.info(f"Guest session created: {session['token'][:20]}...")
        
        return {
            "token": session['token'],
            "token_type": "guest",
            "expires_in": session['expires_in'],
            "message": "Guest session created. Sign in for full features.",
            "upgrade_url": "/api/auth/telegram-miniapp",
            "permissions": session['permissions']
        }
        
    except Exception as e:
        logger.error(f"Guest session creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create guest session"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(token: str):
    """
    Refresh JWT token.
    
    Allows refreshing tokens that are expired but not older than 7 days.
    """
    try:
        token_manager = get_token_manager()
        new_token = await token_manager.refresh_jwt_token(token)
        
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh not available, please re-authenticate"
            )
        
        return AuthResponse(
            jwt_token=new_token['jwt_token'],
            expires_in=settings.JWT_EXPIRY_SECONDS,
            user=new_token['user']
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

