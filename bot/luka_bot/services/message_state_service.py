"""
Message State Service - Track bot messages for editing during streaming.

Minimal implementation focused on streaming message tracking.
Enables real-time updates (e.g., "..." → "🔍" → [results]).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from luka_bot.core.loader import redis_client


class MessageState(BaseModel):
    """Model for tracking streaming messages"""
    user_id: int
    message_id: int
    chat_id: int
    message_type: str  # "thinking", "streaming", "final"
    original_text: str
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageStateService:
    """
    Service for tracking bot messages to enable real-time editing.
    
    Use case: Update "..." to "🔍" when tool executes.
    """
    
    MESSAGE_TTL = 3600  # 1 hour in seconds
    KEY_PREFIX = "luka:message_state"
    
    def __init__(self):
        self._redis = None
    
    @property
    def redis(self):
        if self._redis is None:
            self._redis = redis_client
        return self._redis
    
    def _get_key(self, user_id: int) -> str:
        """Generate Redis key for user's current streaming message"""
        return f"{self.KEY_PREFIX}:{user_id}:current"
    
    async def save_message(
        self,
        user_id: int,
        chat_id: int,
        message_id: int,
        message_type: str,
        original_text: str
    ) -> None:
        """
        Save message state for future editing.
        
        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            message_id: Telegram message ID to edit later
            message_type: Type of message ("thinking", "streaming", "final")
            original_text: Original message text
        """
        try:
            message_state = MessageState(
                user_id=user_id,
                message_id=message_id,
                chat_id=chat_id,
                message_type=message_type,
                original_text=original_text,
                created_at=datetime.utcnow()
            )
            
            # Save to Redis with TTL
            key = self._get_key(user_id)
            await self.redis.setex(
                key,
                self.MESSAGE_TTL,
                message_state.json()
            )
            
            logger.debug(
                f"📝 Saved message state for user {user_id}, "
                f"message {message_id}, type: {message_type}"
            )
            
        except Exception as e:
            logger.error(f"Failed to save message state: {e}")
    
    async def get_message(self, user_id: int) -> Optional[MessageState]:
        """
        Retrieve current streaming message for user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            MessageState object or None if not found
        """
        try:
            key = self._get_key(user_id)
            data = await self.redis.get(key)
            
            if data:
                return MessageState.parse_raw(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get message state: {e}")
            return None
    
    async def clear_message(self, user_id: int) -> None:
        """
        Clear tracked message after streaming completes.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            key = self._get_key(user_id)
            await self.redis.delete(key)
            logger.debug(f"🗑️  Cleared message state for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to clear message state: {e}")


# Global instance
_message_state_service: Optional[MessageStateService] = None


def get_message_state_service() -> MessageStateService:
    """Get or create MessageStateService instance"""
    global _message_state_service
    if _message_state_service is None:
        _message_state_service = MessageStateService()
        logger.info("✅ MessageStateService initialized")
    return _message_state_service

