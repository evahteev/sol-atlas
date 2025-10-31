"""
Reply Tracker Service - Track bot replies for retroactive moderation.

This service maintains a temporary cache of bot replies to user messages,
enabling retroactive deletion if moderation detects violations after the bot
has already responded.

Key Features:
- Track bot reply message IDs
- TTL-based cleanup (5 minutes default)
- Fast Redis-based storage
- Support for retroactive moderation
"""

from typing import Optional
from loguru import logger

from luka_bot.core.loader import redis_client


class ReplyTrackerService:
    """
    Track bot replies to user messages for retroactive moderation.
    
    Use Case:
    1. User mentions bot in group
    2. Bot replies immediately (no waiting for moderation)
    3. Moderation evaluates in background
    4. If violation detected, delete BOTH messages
    
    Example:
        tracker = get_reply_tracker_service()
        
        # After bot replies:
        await tracker.track_reply(
            chat_id=-1001234,
            user_message_id=123,
            bot_reply_id=124
        )
        
        # Later, in moderation handler:
        bot_reply_id = await tracker.get_bot_reply(
            chat_id=-1001234,
            user_message_id=123
        )
        if bot_reply_id:
            await bot.delete_message(chat_id, bot_reply_id)
    """
    
    def __init__(self, redis_client):
        """Initialize with Redis client."""
        self.redis = redis_client
    
    async def track_reply(
        self,
        chat_id: int,
        user_message_id: int,
        bot_reply_id: int,
        ttl: int = 300  # 5 minutes default
    ) -> bool:
        """
        Track that bot replied to a user message.
        
        Args:
            chat_id: Telegram chat ID
            user_message_id: User's original message ID
            bot_reply_id: Bot's reply message ID
            ttl: Time-to-live in seconds (default 5 minutes)
            
        Returns:
            True if tracked successfully, False otherwise
            
        Note:
            TTL ensures old replies don't accumulate in Redis.
            5 minutes is enough for moderation to complete and take action.
        """
        try:
            key = f"bot_reply:{chat_id}:{user_message_id}"
            await self.redis.setex(key, ttl, str(bot_reply_id))
            return True
        except Exception as e:
            logger.error(f"❌ Failed to track reply: {e}")
            return False
    
    async def get_bot_reply(
        self,
        chat_id: int,
        user_message_id: int
    ) -> Optional[int]:
        """
        Get bot's reply message ID for a user message.
        
        Args:
            chat_id: Telegram chat ID
            user_message_id: User's original message ID
            
        Returns:
            Bot's reply message ID if exists, None otherwise
            
        Note:
            Returns None if:
            - No reply was tracked
            - TTL expired (>5 minutes old)
            - Error occurred
        """
        try:
            key = f"bot_reply:{chat_id}:{user_message_id}"
            result = await self.redis.get(key)
            
            if result:
                return int(result)
            else:
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get reply: {e}")
            return None
    
    async def clear_reply(
        self,
        chat_id: int,
        user_message_id: int
    ) -> bool:
        """
        Clear a tracked reply (manual cleanup).
        
        Args:
            chat_id: Telegram chat ID
            user_message_id: User's original message ID
            
        Returns:
            True if cleared, False otherwise
            
        Note:
            Usually not needed (TTL handles cleanup automatically),
            but can be used for immediate cleanup after moderation action.
        """
        try:
            key = f"bot_reply:{chat_id}:{user_message_id}"
            deleted = await self.redis.delete(key)
            return bool(deleted)
        except Exception as e:
            logger.error(f"❌ Failed to clear reply: {e}")
            return False
    
    async def get_stats(self) -> dict:
        """
        Get statistics about tracked replies.
        
        Returns:
            Dictionary with stats (total tracked, etc.)
            
        Note:
            Useful for monitoring and debugging.
        """
        try:
            pattern = "bot_reply:*"
            # Scan for all reply tracking keys
            cursor = 0
            total_tracked = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                total_tracked += len(keys)
                if cursor == 0:
                    break
            
            return {
                "total_tracked": total_tracked,
                "ttl": 300,  # 5 minutes
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {"error": str(e)}


# Singleton instance
_reply_tracker_service: Optional[ReplyTrackerService] = None


def get_reply_tracker_service() -> ReplyTrackerService:
    """
    Get or create ReplyTrackerService singleton.
    
    Returns:
        ReplyTrackerService instance
        
    Note:
        Uses global singleton pattern for efficient resource usage.
    """
    global _reply_tracker_service
    if _reply_tracker_service is None:
        _reply_tracker_service = ReplyTrackerService(redis_client)
    return _reply_tracker_service

