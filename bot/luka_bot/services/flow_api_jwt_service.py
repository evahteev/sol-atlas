"""
Flow API JWT Service

Fetches JWT tokens from Flow API for WebSocket authentication.

Flow: camunda_user_id → get user → webapp_user_id → login → JWT token

Based on bot_server's JWT fetching logic.
"""
import httpx
from typing import Optional
from loguru import logger

from luka_bot.core.config import settings


async def get_flow_api_jwt_token(user_data: dict) -> Optional[str]:
    """
    Get JWT token from Flow API for WebSocket authentication.
    
    This token will be used for:
    - WebSocket connections
    - Real-time task updates
    - Other Flow API authenticated features
    
    Flow:
    1. Extract camunda_user_id from user data
    2. Call Flow API to get user details (including webapp_user_id)
    3. Call Flow API login endpoint with webapp_user_id
    4. Return JWT token
    
    Args:
        user_data: User data dict with camunda_user_id
        
    Returns:
        JWT token string or None if not available
        
    Note:
        Returns None gracefully if:
        - Flow API is unavailable
        - Login endpoint doesn't exist (404)
        - User doesn't have webapp_user_id
        - Any other error occurs
        
        This allows the bot to continue functioning without JWT features.
    """
    try:
        camunda_user_id = user_data.get("camunda_user_id")
        
        if not camunda_user_id:
            logger.warning("No camunda_user_id available for JWT fetch")
            return None
        
        logger.debug(f"Fetching JWT token for camunda_user_id: {camunda_user_id}")
        
        async with httpx.AsyncClient() as client:
            try:
                # Step 1: Get user details from Flow API
                user_url = f"{settings.FLOW_API_URL}/api/users"
                params = {"camunda_user_id": camunda_user_id}
                headers = {"X-SYS-KEY": settings.FLOW_API_SYS_KEY}
                
                response = await client.get(
                    user_url,
                    params=params,
                    headers=headers,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    user_data_response = response.json()
                    webapp_user_id = user_data_response.get("webapp_user_id")
                    
                    if not webapp_user_id:
                        logger.warning(f"No webapp_user_id found for user {camunda_user_id}")
                        return None
                    
                    logger.debug(f"Found webapp_user_id: {webapp_user_id}")
                    
                    # Step 2: Use webapp_user_id to get JWT token from login endpoint
                    login_url = f"{settings.FLOW_API_URL}/api/login/{webapp_user_id}"
                    login_response = await client.get(login_url, timeout=15.0)
                    
                    if login_response.status_code == 200:
                        auth_data = login_response.json()
                        jwt_token = auth_data.get("access_token")
                        
                        if jwt_token:
                            logger.info(f"✅ Got JWT token for user {camunda_user_id}")
                            return jwt_token
                        else:
                            logger.warning("No JWT token found in Flow API login response")
                            return None
                    elif login_response.status_code == 404:
                        logger.info("Flow API login endpoint not found (404) - JWT authentication not available")
                        return None
                    else:
                        logger.warning(
                            f"Flow API login failed for user {webapp_user_id}: "
                            f"status={login_response.status_code}"
                        )
                        return None
                        
                elif response.status_code == 404:
                    logger.warning(f"User not found in Flow API: {camunda_user_id}")
                    return None
                else:
                    logger.warning(
                        f"Flow API user lookup failed for {camunda_user_id}: "
                        f"status={response.status_code}"
                    )
                    return None
                    
            except httpx.ConnectError:
                logger.warning(
                    f"⚠️ Cannot connect to Flow API at {settings.FLOW_API_URL} - "
                    "JWT authentication not available"
                )
                return None
            except httpx.TimeoutException:
                logger.warning("⚠️ Flow API request timed out - JWT authentication not available")
                return None
            except Exception as e:
                logger.error(f"❌ Unexpected error during Flow API request: {e}")
                return None
                
    except Exception as e:
        logger.error(f"❌ Error getting JWT token from Flow API: {e}")
        return None

