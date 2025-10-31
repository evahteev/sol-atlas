"""
Group Thread Service - Per-user threads with group context.

Creates unique threads for each user-group combination where users can have
conversations with group-aware AI agents that have access to:
- Group knowledge base (all group messages)
- Group statistics and metadata
- Recent group context (last N messages)
- Group moderation rules
"""
from typing import Optional, List
from datetime import datetime
from loguru import logger

from luka_bot.models.thread import Thread
from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.group_service import get_group_service
from luka_bot.services.moderation_service import get_moderation_service
from luka_bot.core.config import settings


class GroupThreadService:
    """Service for managing per-user group-aware threads."""
    
    def __init__(self):
        pass
    
    async def get_or_create_user_group_thread(
        self,
        user_id: int,
        group_id: int
    ) -> Thread:
        """
        Get or create user's personal thread for a group.
        
        This creates a unique thread for each user-group combination that:
        - Has access to the group's knowledge base
        - Contains group context in system prompt
        - Maintains conversation history specific to this user's questions about the group
        
        Args:
            user_id: User ID
            group_id: Group ID
            
        Returns:
            Thread instance for user-group conversation
        """
        # Thread ID format: user_{user_id}_group_{group_id}
        thread_id = f"user_{user_id}_group_{group_id}"
        
        thread_service = get_thread_service()
        
        # Try to get existing thread
        existing_thread = await thread_service.get_thread(thread_id)
        if existing_thread:
            logger.debug(f"📖 Found existing user-group thread: {thread_id}")
            # Refresh system prompt to get updated message count from Elasticsearch
            try:
                new_prompt = await self.build_group_context_prompt(group_id, user_id)
                existing_thread.system_prompt = new_prompt
                existing_thread.updated_at = datetime.utcnow()
                await thread_service._save_thread(existing_thread)
                logger.debug(f"🔄 Refreshed system prompt for existing thread: {thread_id}")
            except Exception as e:
                logger.warning(f"⚠️ Could not refresh system prompt for thread {thread_id}: {e}")
            return existing_thread
        
        # Create new thread
        group_service = await get_group_service()
        group_thread = await thread_service.get_group_thread(group_id)
        
        if not group_thread:
            logger.error(f"❌ Group thread not found for group {group_id}")
            raise ValueError(f"Group {group_id} not found")
        
        # Get group info
        group_name = group_thread.name or f"Group {group_id}"
        group_kb = group_thread.knowledge_bases[0] if group_thread.knowledge_bases else None
        language = group_thread.language or "en"
        
        # Build system prompt with group context
        system_prompt = await self.build_group_context_prompt(group_id, user_id)
        
        # Create thread
        thread = Thread(
            thread_id=thread_id,
            owner_id=user_id,
            name=f"{group_name} (Group Chat)",
            thread_type="user_group",  # New type for user-group threads
            group_id=group_id,
            language=language,
            knowledge_bases=[group_kb] if group_kb else [],
            system_prompt=system_prompt,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            message_count=0,
        )
        
        # Save thread
        await thread_service._save_thread(thread)
        
        logger.info(f"✨ Created user-group thread: {thread_id} for user {user_id} in group {group_name}")
        return thread
    
    async def build_group_context_prompt(
        self,
        group_id: int,
        user_id: int
    ) -> str:
        """
        Build system prompt with group context.
        
        Includes:
        - Agent name and role
        - Group information (title, member count, admins)
        - Group statistics (message count, active users)
        - Moderation rules (from GroupSettings.moderation_prompt)
        - Recent messages context (last 10 messages)
        
        Args:
            group_id: Group ID
            user_id: User ID
            
        Returns:
            System prompt string
        """
        thread_service = get_thread_service()
        group_service = await get_group_service()
        moderation_service = await get_moderation_service()
        
        # Get group thread for basic info
        group_thread = await thread_service.get_group_thread(group_id)
        if not group_thread:
            return settings.LUKA_DEFAULT_SYSTEM_PROMPT
        
        group_name = group_thread.name or f"Group {group_id}"
        agent_name = group_thread.agent_name or settings.LUKA_NAME
        
        # Get group metadata
        metadata = await group_service.get_cached_group_metadata(group_id)
        member_count = metadata.total_member_count if metadata else "unknown"
        
        # Get message count from Elasticsearch knowledge base
        message_count = 0
        try:
            from luka_bot.services.elasticsearch_service import get_elasticsearch_service
            
            if settings.ELASTICSEARCH_ENABLED and group_thread.knowledge_bases:
                kb_index = group_thread.knowledge_bases[0]
                es_service = await get_elasticsearch_service()
                
                try:
                    index_stats = await es_service.es.count(index=kb_index)
                    message_count = index_stats.get('count', 0)
                    logger.debug(f"📊 Indexed message count for {kb_index}: {message_count}")
                except Exception as e:
                    logger.debug(f"Could not get indexed message count: {e}")
                    message_count = 0
        except Exception as e:
            logger.debug(f"Could not query Elasticsearch for message count: {e}")
            message_count = 0
        
        # Get moderation settings
        group_settings = await moderation_service.get_group_settings(group_id)
        moderation_prompt = group_settings.moderation_prompt if group_settings else None
        
        # Get last messages
        last_messages = await self.get_last_group_messages(group_id, limit=10)
        
        # Build context sections
        prompt_parts = []
        
        # Header
        prompt_parts.append(f"You are {agent_name}, an AI assistant with access to the knowledge base of the Telegram group '{group_name}'.")
        
        # Group info
        prompt_parts.append(f"\n## Group Information")
        prompt_parts.append(f"- **Group Name**: {group_name}")
        prompt_parts.append(f"- **Members**: {member_count}")
        prompt_parts.append(f"- **Total Messages Indexed**: {message_count}")
        
        # Your role
        prompt_parts.append(f"\n## Your Role")
        prompt_parts.append(f"You help users understand and navigate the group's discussions. You can:")
        prompt_parts.append(f"- Answer questions about topics discussed in the group")
        prompt_parts.append(f"- Summarize conversations and key points")
        prompt_parts.append(f"- Find relevant information from the group's message history")
        prompt_parts.append(f"- Provide insights on group activity and trends")
        prompt_parts.append(f"- Help with moderation insights if the user is an admin")
        
        # Moderation context (if exists)
        if moderation_prompt:
            prompt_parts.append(f"\n## Group Moderation Rules")
            prompt_parts.append(moderation_prompt.strip())
        
        # Recent messages context
        if last_messages:
            prompt_parts.append(f"\n## Recent Group Activity (Last 10 Messages)")
            for i, msg in enumerate(last_messages, 1):
                sender = msg.get("sender_name", "Unknown")
                text = msg.get("message_text", "")[:100]  # Truncate long messages
                timestamp = msg.get("message_date", "")
                
                if text:
                    prompt_parts.append(f"{i}. **{sender}** ({timestamp}): {text}")
        
        # Guidelines
        prompt_parts.append(f"\n## Guidelines")
        prompt_parts.append(f"- Be helpful and informative about the group's discussions")
        prompt_parts.append(f"- Use the knowledge base to provide accurate information")
        prompt_parts.append(f"- If you don't know something, say so - don't make up information")
        prompt_parts.append(f"- Respect user privacy - only share information that's in the public group")
        prompt_parts.append(f"- Be objective and fair when discussing group content")
        
        return "\n".join(prompt_parts)
    
    async def get_last_group_messages(
        self,
        group_id: int,
        limit: int = 10
    ) -> List[dict]:
        """
        Fetch last N messages from group knowledge base.
        
        Args:
            group_id: Group ID
            limit: Number of messages to fetch
            
        Returns:
            List of message dicts with sender, text, date
        """
        try:
            from luka_bot.services.elasticsearch_service import get_elasticsearch_service
            
            if not settings.ELASTICSEARCH_ENABLED:
                logger.warning("⚠️ Elasticsearch not enabled, cannot fetch group messages")
                return []
            
            es_service = await get_elasticsearch_service()
            
            # Get KB index for this group
            kb_index = f"tg-kb-group-{abs(group_id)}"
            
            # Fetch recent messages
            messages = await es_service.get_recent_messages(kb_index, limit=limit)
            
            logger.debug(f"📚 Fetched {len(messages)} recent messages from {kb_index}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error fetching last group messages: {e}")
            return []
    
    async def refresh_group_context(
        self,
        user_id: int,
        group_id: int
    ) -> bool:
        """
        Refresh the group context in an existing user-group thread.
        
        Updates the system prompt with fresh group stats and recent messages.
        
        Args:
            user_id: User ID
            group_id: Group ID
            
        Returns:
            True if successful
        """
        try:
            thread_id = f"user_{user_id}_group_{group_id}"
            thread_service = get_thread_service()
            
            thread = await thread_service.get_thread(thread_id)
            if not thread:
                logger.warning(f"⚠️ Thread {thread_id} not found for refresh")
                return False
            
            # Rebuild system prompt
            new_prompt = await self.build_group_context_prompt(group_id, user_id)
            thread.system_prompt = new_prompt
            thread.updated_at = datetime.utcnow()
            
            # Save updated thread
            await thread_service._save_thread(thread)
            
            logger.info(f"🔄 Refreshed group context for thread {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error refreshing group context: {e}")
            return False


# Singleton instance
_group_thread_service: Optional[GroupThreadService] = None


async def get_group_thread_service() -> GroupThreadService:
    """Get or create singleton GroupThreadService instance."""
    global _group_thread_service
    
    if _group_thread_service is None:
        _group_thread_service = GroupThreadService()
        logger.info("✅ GroupThreadService singleton created")
    
    return _group_thread_service
