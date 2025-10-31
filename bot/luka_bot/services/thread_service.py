"""
Thread Service - Phase 3.

Redis-based thread management (CRUD operations).
Phase 4 will add Camunda integration.
"""
import json
import uuid
from typing import List, Optional
from datetime import datetime
from loguru import logger

from luka_bot.core.loader import redis_client
from luka_bot.models.thread import Thread


class ThreadService:
    """
    Service for managing conversation threads.
    
    Phase 3: Redis storage only
    Phase 4: Will integrate with Camunda
    """
    
    def __init__(self):
        self.redis = redis_client
    
    # ============================================================================
    # Thread ID helpers
    # ============================================================================
    
    @staticmethod
    def _get_group_thread_id(group_id: int) -> str:
        """Generate thread_id for a group conversation."""
        return f"group_{group_id}"
    
    @staticmethod
    def _get_topic_thread_id(group_id: int, topic_id: int) -> str:
        """Generate thread_id for a topic conversation."""
        return f"group_{group_id}_topic_{topic_id}"
    
    # ============================================================================
    # DM Thread methods
    # ============================================================================
    
    async def create_thread(
        self,
        user_id: int,
        name: Optional[str] = None
    ) -> Thread:
        """
        Create a new DM thread for user.
        
        Args:
            user_id: Telegram user ID
            name: Thread name (auto-generated if None)
            
        Returns:
            Created thread
        """
        from luka_bot.utils.uuid_utils import UUIDUtils
        thread_id = UUIDUtils.generate_clean_uuid()
        
        if name is None:
            # Count existing threads for default name
            existing = await self.list_threads(user_id)
            name = f"Chat {len(existing) + 1}"
        
        thread = Thread(
            thread_id=thread_id,
            owner_id=user_id,
            name=name,
            thread_type="dm"
        )
        
        await self._save_thread(thread)
        
        # Set as active thread
        await self.set_active_thread(user_id, thread_id)
        
        logger.info(f"✨ Created DM thread {thread_id} for user {user_id}: {name}")
        return thread
    
    # ============================================================================
    # Group Thread methods
    # ============================================================================
    
    async def get_group_thread(self, group_id: int) -> Optional[Thread]:
        """
        Get the thread for a group conversation.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Thread or None if not found
        """
        thread_id = self._get_group_thread_id(group_id)
        return await self.get_thread(thread_id)
    
    async def create_group_thread(
        self,
        group_id: int,
        group_title: str,
        owner_id: int,
        language: str = "en",
        **kwargs
    ) -> Thread:
        """
        Create a new thread for a group conversation.
        
        Args:
            group_id: Telegram group ID
            group_title: Group name/title
            owner_id: User who added the bot (for ownership tracking)
            language: Default language for the group
            **kwargs: Additional thread configuration (agent_name, system_prompt, etc.)
            
        Returns:
            Created thread
        """
        thread_id = self._get_group_thread_id(group_id)
        
        # Check if thread already exists
        existing = await self.get_thread(thread_id)
        if existing:
            logger.warning(f"⚠️ Group thread {thread_id} already exists")
            return existing
        
        # Create KB index for this group
        kb_index = f"tg-kb-group-{abs(group_id)}"
        
        thread = Thread(
            thread_id=thread_id,
            owner_id=owner_id,
            name=group_title,
            thread_type="group",
            group_id=group_id,
            language=language,
            knowledge_bases=[kb_index],
            **kwargs
        )
        
        await self._save_thread(thread)
        
        logger.info(f"✨ Created group thread {thread_id} for group {group_id} ({group_title})")
        return thread
    
    # ============================================================================
    # Topic Thread methods
    # ============================================================================
    
    async def get_topic_thread(self, group_id: int, topic_id: int) -> Optional[Thread]:
        """
        Get the thread for a topic conversation.
        
        Args:
            group_id: Telegram group ID
            topic_id: Telegram message_thread_id (topic ID)
            
        Returns:
            Thread or None if not found
        """
        thread_id = self._get_topic_thread_id(group_id, topic_id)
        return await self.get_thread(thread_id)
    
    async def create_topic_thread(
        self,
        group_id: int,
        topic_id: int,
        topic_name: str,
        owner_id: int,
        **kwargs
    ) -> Thread:
        """
        Create a new thread for a topic conversation.
        
        Args:
            group_id: Telegram group ID
            topic_id: Telegram message_thread_id
            topic_name: Topic name/title
            owner_id: User who created/owns this topic tracking
            **kwargs: Additional thread configuration (inherits from group by default)
            
        Returns:
            Created thread
        """
        thread_id = self._get_topic_thread_id(group_id, topic_id)
        
        # Check if thread already exists
        existing = await self.get_thread(thread_id)
        if existing:
            logger.warning(f"⚠️ Topic thread {thread_id} already exists")
            return existing
        
        # Get parent group thread to inherit settings
        group_thread = await self.get_group_thread(group_id)
        
        # Create separate KB index for this topic
        kb_index = f"tg-kb-group-{abs(group_id)}-topic-{topic_id}"
        
        # Inherit language and other settings from group (can be overridden by kwargs)
        thread_config = {
            "language": group_thread.language if group_thread else "en",
            "agent_name": group_thread.agent_name if group_thread else None,
            "system_prompt": group_thread.system_prompt if group_thread else None,
            "llm_provider": group_thread.llm_provider if group_thread else None,
            "model_name": group_thread.model_name if group_thread else None,
        }
        thread_config.update(kwargs)
        
        thread = Thread(
            thread_id=thread_id,
            owner_id=owner_id,
            name=topic_name,
            thread_type="topic",
            group_id=group_id,
            topic_id=topic_id,
            knowledge_bases=[kb_index],
            **thread_config
        )
        
        await self._save_thread(thread)
        
        logger.info(f"✨ Created topic thread {thread_id} for group {group_id}, topic {topic_id} ({topic_name})")
        return thread
    
    # ============================================================================
    # General Thread methods
    # ============================================================================
    
    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        """
        Get thread by ID.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread or None if not found
        """
        key = f"thread:{thread_id}"
        
        try:
            data = await self.redis.hgetall(key)
            if not data:
                return None
            
            # Convert bytes to strings
            data = {k.decode(): v.decode() for k, v in data.items()}
            return Thread.from_dict(data)
            
        except Exception as e:
            logger.error(f"❌ Error getting thread {thread_id}: {e}")
            return None
    
    async def list_threads(
        self,
        user_id: int,
        include_inactive: bool = False,
        exclude_group_threads: bool = True
    ) -> List[Thread]:
        """
        List all threads for user.
        
        Args:
            user_id: Telegram user ID
            include_inactive: Include inactive threads
            exclude_group_threads: Exclude user-group threads (they're in /groups, not /chat)
            
        Returns:
            List of threads (sorted by updated_at desc)
        """
        index_key = f"user_threads:{user_id}"
        
        try:
            thread_ids = await self.redis.smembers(index_key)
            threads = []
            
            for thread_id_bytes in thread_ids:
                thread_id = thread_id_bytes.decode()
                
                # Skip user-group threads (they appear in /groups menu, not /chat)
                if exclude_group_threads and thread_id.startswith(f"user_{user_id}_group_"):
                    continue
                
                thread = await self.get_thread(thread_id)
                
                if thread and (include_inactive or thread.is_active):
                    threads.append(thread)
            
            # Sort by updated_at (newest first)
            threads.sort(key=lambda t: t.updated_at, reverse=True)
            
            logger.info(f"📚 Listed {len(threads)} threads for user {user_id} (excluded group threads: {exclude_group_threads})")
            return threads
            
        except Exception as e:
            logger.error(f"❌ Error listing threads for user {user_id}: {e}")
            return []
    
    async def update_thread(self, thread: Thread) -> None:
        """
        Update thread metadata.
        
        Args:
            thread: Thread to update
        """
        thread.updated_at = datetime.utcnow()
        await self._save_thread(thread)
        logger.info(f"💾 Updated thread {thread.thread_id}")
    
    async def delete_thread(self, thread_id: str, user_id: int) -> bool:
        """
        Delete thread.
        
        Args:
            thread_id: Thread ID
            user_id: User ID (for validation)
            
        Returns:
            True if deleted, False otherwise
        """
        # Get thread to validate ownership
        thread = await self.get_thread(thread_id)
        if not thread or thread.owner_id != user_id:
            logger.warning(f"⚠️  Cannot delete thread {thread_id}: not found or not owned by user {user_id}")
            return False
        
        # Delete thread data
        thread_key = f"thread:{thread_id}"
        await self.redis.delete(thread_key)
        
        # Remove from user index
        index_key = f"user_threads:{user_id}"
        await self.redis.srem(index_key, thread_id)
        
        # Delete thread history
        history_key = f"thread_history:{thread_id}"
        await self.redis.delete(history_key)
        
        logger.info(f"🗑️  Deleted thread {thread_id}")
        return True
    
    async def get_active_thread(self, user_id: int) -> Optional[str]:
        """
        Get user's currently active thread ID.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Thread ID or None
        """
        key = f"user_active_thread:{user_id}"
        thread_id = await self.redis.get(key)
        return thread_id.decode() if thread_id else None
    
    async def clear_active_thread(self, user_id: int) -> None:
        """
        Clear active thread pointer for user.
        
        Used when starting new thread creation flow (lazy creation).
        
        Args:
            user_id: Telegram user ID
        """
        key = f"user_active_thread:{user_id}"
        await self.redis.delete(key)
        logger.info(f"🔄 Cleared active thread for user {user_id}")
    
    async def set_active_thread(self, user_id: int, thread_id: str) -> None:
        """
        Set user's active thread.
        
        Args:
            user_id: Telegram user ID
            thread_id: Thread ID to activate
        """
        key = f"user_active_thread:{user_id}"
        await self.redis.set(key, thread_id)
        logger.info(f"🔀 Set active thread for user {user_id}: {thread_id}")
    
    async def rename_thread(self, thread_id: str, new_name: str, user_id: int) -> bool:
        """
        Rename a thread.
        
        Args:
            thread_id: Thread ID
            new_name: New name
            user_id: User ID (for validation)
            
        Returns:
            True if renamed, False otherwise
        """
        thread = await self.get_thread(thread_id)
        if not thread or thread.owner_id != user_id:
            return False
        
        thread.name = new_name
        await self.update_thread(thread)
        logger.info(f"✏️  Renamed thread {thread_id} to: {new_name}")
        return True
    
    async def _save_thread(self, thread: Thread) -> None:
        """Save thread to Redis."""
        # Save thread data
        thread_key = f"thread:{thread.thread_id}"
        await self.redis.hset(thread_key, mapping=thread.to_dict())
        
        # Add to user index
        index_key = f"user_threads:{thread.owner_id}"
        await self.redis.sadd(index_key, thread.thread_id)
        
        # Set TTL (30 days)
        await self.redis.expire(thread_key, 30 * 24 * 60 * 60)


# Global service instance
_thread_service: Optional[ThreadService] = None


def get_thread_service() -> ThreadService:
    """Get or create thread service instance."""
    global _thread_service
    if _thread_service is None:
        _thread_service = ThreadService()
    return _thread_service

