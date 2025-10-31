"""
Token Management

Handles JWT and guest token creation, validation, and session management.
"""
import secrets
import time
import json
from typing import Optional
from jose import jwt, JWTError
from loguru import logger
import httpx

from ag_ui_gateway.config.settings import settings


class TokenType:
    """Token types."""
    GUEST = "guest"
    AUTHENTICATED = "authenticated"


class GuestToken:
    """Guest token utilities."""
    
    @staticmethod
    def generate() -> str:
        """Generate cryptographically secure guest token."""
        return f"guest_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def is_guest_token(token: str) -> bool:
        """Check if token is guest token."""
        return token.startswith("guest_")


class TokenManager:
    """Token management with Redis integration."""
    
    async def create_guest_session(self) -> dict:
        """Create guest session with limited permissions."""
        from ag_ui_gateway.database import get_redis
        
        token = GuestToken.generate()
        
        session_data = {
            'token': token,
            'token_type': TokenType.GUEST,
            'created_at': time.time(),
            'message_count': 0,
            'permissions': [
                'read:public_kb',
                'chat:ephemeral',
                'search:public_kb'
            ],
            'expires_in': settings.GUEST_TOKEN_EXPIRY_SECONDS
        }
        
        # Store in Redis
        try:
            redis = get_redis()
            await redis.setex(
                f"guest_session:{token}",
                settings.GUEST_TOKEN_EXPIRY_SECONDS,
                json.dumps(session_data)
            )
            logger.info(f"✅ Created guest session: {token[:20]}...")
        except Exception as e:
            logger.error(f"Failed to store guest session in Redis: {e}")
        
        return session_data
    
    async def validate_token(self, token: str) -> Optional[dict]:
        """Validate JWT or guest token."""
        if GuestToken.is_guest_token(token):
            return await self._validate_guest_token(token)
        else:
            return await self._validate_jwt_token(token)
    
    async def _validate_guest_token(self, token: str) -> Optional[dict]:
        """Validate guest token by fetching from Redis."""
        from ag_ui_gateway.database import get_redis
        
        try:
            redis = get_redis()
            data = await redis.get(f"guest_session:{token}")
            
            if data:
                session = json.loads(data)
                
                # Check message limit
                message_count = session.get('message_count', 0)
                if message_count >= settings.GUEST_TOTAL_MESSAGES:
                    logger.warning(f"Guest session exceeded message limit: {token[:20]}...")
                    return None
                
                return {
                    'token_type': TokenType.GUEST,
                    'user_id': None,
                    'permissions': session.get('permissions', []),
                    'message_count': message_count,
                    'token': token
                }
            else:
                logger.debug(f"Guest session not found or expired: {token[:20]}...")
                return None
                
        except Exception as e:
            logger.error(f"Error validating guest token: {e}")
            return None
    
    async def _exchange_thirdweb_token_for_flow_jwt(self, thirdweb_token: str) -> Optional[str]:
        """
        Exchange Thirdweb JWT for Flow API JWT.

        Thirdweb JWT contains webapp_user_id but not telegram_user_id.
        We call Flow API GET /api/login/{webapp_user_id} to exchange tokens.

        :param thirdweb_token: JWT from Thirdweb authentication
        :return: Flow API access_token (JWT with telegram_user_id)
        """
        try:
            logger.info("🔄 Attempting to exchange Thirdweb token for Flow API JWT...")

            # Decode Thirdweb JWT to extract webapp_user_id (without verification)
            decoded = jwt.decode(
                thirdweb_token,
                settings.AUTHJWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            webapp_user_id = decoded.get("sub") or decoded.get("storedToken", {}).get("authDetails", {}).get("userWalletId")

            if not webapp_user_id:
                logger.error("❌ No webapp_user_id found in Thirdweb JWT")
                return None

            logger.info(f"📝 Extracted webapp_user_id: {webapp_user_id}")

            # Call Flow API to exchange token
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.FLOW_API_URL}/api/login/{webapp_user_id}",
                    headers={
                        "Authorization": f"Bearer {thirdweb_token}",
                        "x-sys-key": settings.FLOW_API_SYS_KEY,
                    },
                    timeout=10.0,
                )

                if response.status_code != 200:
                    logger.error(f"❌ Flow API returned status {response.status_code}: {response.text}")
                    return None

                login_data = response.json()
                access_token = login_data.get("access_token")

                if not access_token:
                    logger.error("❌ No access_token in Flow API response")
                    return None

                logger.info("✅ Successfully exchanged Thirdweb token for Flow API JWT")
                return access_token

        except httpx.RequestError as e:
            logger.error(f"❌ HTTP error during token exchange: {e}")
            return None
        except Exception as e:
            logger.error(f"💥 Unexpected error during token exchange: {e}")
            return None

    async def _validate_jwt_token(self, token: str) -> Optional[dict]:
        """Validate JWT token."""
        try:
            # First, check if this is a Thirdweb token that needs to be exchanged
            try:
                # Decode without verification to check token type
                decoded_token = jwt.decode(
                    token,
                    settings.AUTHJWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM]
                )
                has_telegram_user_id = "telegram_user_id" in decoded_token

                if not has_telegram_user_id:
                    logger.info("🔄 Detected Thirdweb token (no telegram_user_id), exchanging for Flow API JWT...")
                    exchanged_token = await self._exchange_thirdweb_token_for_flow_jwt(token)
                    if exchanged_token:
                        token = exchanged_token
                        logger.info("✅ Successfully exchanged token")
                    else:
                        logger.error("❌ Token exchange failed")
                        return None
                else:
                    logger.debug("✅ Detected Flow API token (has telegram_user_id)")
            except Exception as e:
                logger.warning(f"⚠️ Could not detect token type: {e}, proceeding with validation...")

            # Now validate the token (either original Flow API token or exchanged token)
            payload = jwt.decode(
                token,
                settings.AUTHJWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            telegram_user_id = payload.get('telegram_user_id')
            if not telegram_user_id:
                logger.error("❌ No telegram_user_id in token payload")
                return None

            return {
                'token_type': TokenType.AUTHENTICATED,
                'user_id': telegram_user_id,
                'permissions': ['*'],  # All permissions
                'token': token
            }
        except JWTError as e:
            logger.debug(f"JWT validation error: {e}")
            return None
    
    async def increment_guest_message_count(self, token: str) -> bool:
        """Increment message count for guest session."""
        from ag_ui_gateway.database import get_redis
        
        try:
            redis = get_redis()
            key = f"guest_session:{token}"
            data = await redis.get(key)
            
            if data:
                session = json.loads(data)
                session['message_count'] = session.get('message_count', 0) + 1
                
                # Get remaining TTL to preserve expiration
                ttl = await redis.ttl(key)
                if ttl > 0:
                    await redis.setex(key, ttl, json.dumps(session))
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error incrementing guest message count: {e}")
            return False
    
    async def refresh_jwt_token(self, token: str) -> Optional[dict]:
        """
        Refresh JWT token.
        
        For now, returns None - client should re-authenticate.
        TODO: Implement token refresh with Flow API
        """
        return None


# Singleton instance
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """Get or create TokenManager singleton."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
