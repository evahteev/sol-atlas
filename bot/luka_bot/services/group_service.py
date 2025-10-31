"""
Group service for managing Telegram group links and KB indices.

Handles:
- Creating/updating group links
- Managing group KB indices
- Listing user's groups
- Group membership tracking
- Group metadata collection and caching
"""
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger
from aiogram import Bot

from luka_bot.models.group_link import GroupLink
from luka_bot.models.group_metadata import GroupMetadata
from luka_bot.core.config import settings


class GroupService:
    """Service for managing group links and KB indices."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def create_group_link(
        self,
        user_id: int,
        group_id: int,
        group_title: str,
        language: str = "en",
        user_role: str = "member"
    ) -> GroupLink:
        """
        Create or update a group link.
        
        Ensures the group Thread exists first, then creates/updates the GroupLink
        to reference that thread.
        
        Args:
            user_id: User who added the bot to the group
            group_id: Telegram group ID
            group_title: Group title/name
            language: Default language for the group
            user_role: User's role in the group (member/admin/owner)
        
        Returns:
            GroupLink instance
        """
        try:
            # Import here to avoid circular import
            from luka_bot.services.thread_service import get_thread_service
            
            thread_service = get_thread_service()
            
            # Ensure group thread exists
            thread = await thread_service.get_group_thread(group_id)
            if not thread:
                # Create group thread
                thread = await thread_service.create_group_thread(
                    group_id=group_id,
                    group_title=group_title,
                    owner_id=user_id,
                    language=language
                )
                logger.info(f"✨ Created group thread: {thread.thread_id}")
            
            # Check if link already exists
            existing_link = await self.get_group_link(user_id, group_id)
            
            if existing_link:
                # Update existing link
                existing_link.thread_id = thread.thread_id
                existing_link.user_role = user_role
                existing_link.is_active = True
                
                # Save to Redis
                await self._save_group_link(existing_link)
                logger.info(f"✅ Updated group link: user={user_id}, group={group_id}")
                return existing_link
            
            # Create new link
            link = GroupLink(
                user_id=user_id,
                group_id=group_id,
                thread_id=thread.thread_id,
                user_role=user_role,
            )
            
            # Save to Redis
            await self._save_group_link(link)
            
            logger.info(f"✅ Created group link: user={user_id}, group={group_id}, thread={thread.thread_id}")
            return link
            
        except Exception as e:
            logger.error(f"❌ Error creating group link: {e}")
            raise
    
    async def get_group_link(self, user_id: int, group_id: int) -> Optional[GroupLink]:
        """
        Get a specific group link.
        
        Args:
            user_id: User ID
            group_id: Group ID
        
        Returns:
            GroupLink if exists, None otherwise
        """
        try:
            key = f"group_link:{user_id}:{group_id}"
            data = await self.redis.hgetall(key)
            
            if not data:
                return None
            
            # Decode Redis bytes to strings
            decoded_data = {
                k.decode() if isinstance(k, bytes) else k: 
                v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()
            }
            
            # Handle legacy GroupLink records (before thread_id was added)
            if "thread_id" not in decoded_data:
                logger.warning(f"⚠️ Legacy GroupLink found for user {user_id}, group {group_id} - migrating...")
                # Generate thread_id for legacy record
                decoded_data["thread_id"] = f"group_{group_id}"
                # Save the migrated record
                try:
                    migrated_link = GroupLink.from_dict(decoded_data)
                    await self._save_group_link(migrated_link)
                    logger.info(f"✅ Migrated legacy GroupLink: {key}")
                except Exception as migrate_error:
                    logger.error(f"❌ Failed to migrate legacy GroupLink: {migrate_error}")
            
            return GroupLink.from_dict(decoded_data)
            
        except Exception as e:
            logger.error(f"❌ Error getting group link: {e}", exc_info=True)
            return None
    
    async def list_user_groups(self, user_id: int, active_only: bool = True) -> List[GroupLink]:
        """
        List all groups linked by a user.
        
        Args:
            user_id: User ID
            active_only: If True, only return active groups
        
        Returns:
            List of GroupLink instances
        """
        try:
            # Get set of group IDs for this user
            set_key = GroupLink.get_user_groups_key(user_id)
            group_ids = await self.redis.smembers(set_key)
            
            if not group_ids:
                return []
            
            # Fetch each group link
            links = []
            for group_id_bytes in group_ids:
                group_id = int(group_id_bytes.decode())
                link = await self.get_group_link(user_id, group_id)
                
                if link:
                    if not active_only or link.is_active:
                        links.append(link)
            
            # Sort by created_at (newest first)
            links.sort(key=lambda x: x.created_at, reverse=True)
            
            logger.debug(f"📚 Listed {len(links)} groups for user {user_id}")
            return links
            
        except Exception as e:
            logger.error(f"❌ Error listing user groups: {e}")
            return []
    
    async def deactivate_group_link(self, user_id: int, group_id: int) -> bool:
        """
        Deactivate a group link (when bot is removed from group).
        
        Args:
            user_id: User ID
            group_id: Group ID
        
        Returns:
            True if successful
        """
        try:
            link = await self.get_group_link(user_id, group_id)
            
            if not link:
                logger.warning(f"⚠️  Group link not found: user={user_id}, group={group_id}")
                return False
            
            link.is_active = False
            await self._save_group_link(link)
            
            logger.info(f"✅ Deactivated group link: user={user_id}, group={group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deactivating group link: {e}")
            return False
    
    async def delete_group_link(self, user_id: int, group_id: int) -> bool:
        """
        Delete a group link completely.
        
        Args:
            user_id: User ID
            group_id: Group ID
        
        Returns:
            True if successful
        """
        try:
            # Remove from Redis hash
            key = f"group_link:{user_id}:{group_id}"
            await self.redis.delete(key)
            
            # Remove from user's groups set
            user_set_key = GroupLink.get_user_groups_key(user_id)
            await self.redis.srem(user_set_key, str(group_id))
            
            # Remove from group's users set
            group_set_key = GroupLink.get_group_users_key(group_id)
            await self.redis.srem(group_set_key, str(user_id))
            
            logger.info(f"✅ Deleted group link: user={user_id}, group={group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting group link: {e}")
            return False
    
    async def get_group_kb_index(self, group_id: int) -> Optional[str]:
        """
        Get the KB index for a group from its Thread.
        
        Args:
            group_id: Group ID
        
        Returns:
            KB index name or None
        """
        try:
            from luka_bot.services.thread_service import get_thread_service
            
            thread_service = get_thread_service()
            thread = await thread_service.get_group_thread(group_id)
            
            if not thread or not thread.knowledge_bases:
                return None
            
            # Return first KB index (groups typically have one KB)
            return thread.knowledge_bases[0]
            
        except Exception as e:
            logger.error(f"❌ Error getting group KB index: {e}")
            return None
    
    async def get_group_language(self, group_id: int) -> str:
        """
        Get the language setting for a group from its Thread.
        
        Args:
            group_id: Group ID
        
        Returns:
            Language code (en/ru), defaults to "en"
        """
        try:
            from luka_bot.services.thread_service import get_thread_service
            
            thread_service = get_thread_service()
            thread = await thread_service.get_group_thread(group_id)
            
            return thread.language if thread else "en"
            
        except Exception as e:
            logger.error(f"❌ Error getting group language: {e}")
            return "en"
    
    async def update_group_language(self, group_id: int, language: str) -> bool:
        """
        Update language for a group in its Thread.
        
        Args:
            group_id: Group ID
            language: Language code (en/ru)
        
        Returns:
            True if successful
        """
        try:
            from luka_bot.services.thread_service import get_thread_service
            
            thread_service = get_thread_service()
            thread = await thread_service.get_group_thread(group_id)
            
            if not thread:
                logger.warning(f"⚠️  No thread found for group {group_id}")
                return False
            
            # Update language in thread
            thread.language = language
            await thread_service.update_thread(thread)
            
            logger.info(f"🌍 Updated language to '{language}' for group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating group language: {e}")
            return False
    
    async def collect_group_metadata(
        self,
        group_id: int,
        bot: Bot,
        added_by_user_id: int = 0,
        added_by_username: Optional[str] = None,
        added_by_full_name: str = "Unknown"
    ) -> GroupMetadata:
        """
        Collect full metadata from Telegram API for a group.
        
        Collects:
        - Chat info (title, type, description, etc.)
        - Admin list with permissions
        - Member count
        - Bot's own permissions
        - Pinned message
        
        Args:
            group_id: Group ID to collect metadata for
            bot: Bot instance for API calls
            added_by_user_id: User who added the bot
            added_by_username: Username of user who added
            added_by_full_name: Full name of user who added
            
        Returns:
            GroupMetadata object with all collected data
        """
        logger.info(f"🔄 Collecting metadata for group {group_id}")
        
        metadata = GroupMetadata(group_id=group_id)
        metadata.added_by_user_id = added_by_user_id
        metadata.added_by_username = added_by_username
        metadata.added_by_full_name = added_by_full_name
        metadata.added_at = datetime.utcnow()
        
        # Get bot info for later comparison
        try:
            bot_info = await bot.get_me()
            metadata.bot_username = bot_info.username or ""
        except Exception as e:
            logger.warning(f"⚠️  Could not get bot info: {e}")
        
        # Collect chat information
        try:
            chat_info = await bot.get_chat(group_id)
            metadata.group_title = chat_info.title or f"Group {group_id}"
            metadata.group_username = chat_info.username
            metadata.group_type = chat_info.type
            metadata.description = chat_info.description
            metadata.invite_link = getattr(chat_info, "invite_link", None)
            metadata.slow_mode_delay = getattr(chat_info, "slow_mode_delay", 0)
            metadata.has_topics = getattr(chat_info, "is_forum", False)
            
            # Get photo info
            if chat_info.photo:
                metadata.photo_small_file_id = chat_info.photo.small_file_id
                metadata.photo_big_file_id = chat_info.photo.big_file_id
            
            # Get permissions
            if chat_info.permissions:
                metadata.permissions = {
                    "can_send_messages": chat_info.permissions.can_send_messages,
                    "can_send_media_messages": chat_info.permissions.can_send_media_messages,
                    "can_send_polls": chat_info.permissions.can_send_polls,
                    "can_send_other_messages": chat_info.permissions.can_send_other_messages,
                    "can_add_web_page_previews": chat_info.permissions.can_add_web_page_previews,
                    "can_change_info": chat_info.permissions.can_change_info,
                    "can_invite_users": chat_info.permissions.can_invite_users,
                    "can_pin_messages": chat_info.permissions.can_pin_messages,
                }
            
            # Get pinned message
            if chat_info.pinned_message:
                metadata.pinned_message_id = chat_info.pinned_message.message_id
                metadata.pinned_message_text = chat_info.pinned_message.text or ""
            
            logger.info(f"✅ Collected chat info: {metadata.group_title} ({metadata.group_type})")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not get chat info: {e}")
        
        # Collect member count
        try:
            member_count = await bot.get_chat_member_count(group_id)
            metadata.total_member_count = member_count
            metadata.last_member_count_update = datetime.utcnow()
            logger.info(f"📊 Member count: {member_count}")
        except Exception as e:
            logger.warning(f"⚠️  Could not get member count: {e}")
        
        # Collect admin list
        try:
            admins = await bot.get_chat_administrators(group_id)
            admin_list = []
            
            for admin in admins:
                admin_data = {
                    "user_id": admin.user.id,
                    "username": admin.user.username,
                    "full_name": admin.user.full_name,
                    "status": admin.status,
                    "custom_title": getattr(admin, "custom_title", None),
                    "is_bot": admin.user.is_bot,
                }
                
                # Collect admin permissions
                if hasattr(admin, "can_delete_messages"):
                    admin_data["permissions"] = {
                        "can_delete_messages": getattr(admin, "can_delete_messages", False),
                        "can_restrict_members": getattr(admin, "can_restrict_members", False),
                        "can_promote_members": getattr(admin, "can_promote_members", False),
                        "can_change_info": getattr(admin, "can_change_info", False),
                        "can_invite_users": getattr(admin, "can_invite_users", False),
                        "can_pin_messages": getattr(admin, "can_pin_messages", False),
                        "can_manage_topics": getattr(admin, "can_manage_topics", False),
                        "can_manage_chat": getattr(admin, "can_manage_chat", False),
                        "can_manage_video_chats": getattr(admin, "can_manage_video_chats", False),
                    }
                
                admin_list.append(admin_data)
                
                # Check if our bot is admin
                if admin.user.id == bot_info.id:
                    metadata.bot_is_admin = True
                    metadata.bot_admin_permissions = admin_data.get("permissions", {})
            
            metadata.admin_list = admin_list
            metadata.admin_count = len(admin_list)
            
            logger.info(f"👑 Found {len(admin_list)} admins, bot_is_admin={metadata.bot_is_admin}")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not get admin list: {e}")
        
        # Update timestamp
        metadata.last_metadata_update = datetime.utcnow()
        metadata.metadata_update_count = 1
        
        logger.info(f"✅ Metadata collection complete for group {group_id}")
        return metadata
    
    async def cache_group_metadata(
        self,
        metadata: GroupMetadata,
        ttl: int = 86400  # 24 hours default
    ) -> None:
        """
        Cache group metadata in Redis.
        
        Args:
            metadata: GroupMetadata to cache
            ttl: Time to live in seconds (default 24 hours)
        """
        try:
            key = metadata.get_redis_key()
            await self.redis.hset(key, mapping=metadata.to_dict())
            await self.redis.expire(key, ttl)
            logger.info(f"💾 Cached metadata for group {metadata.group_id} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"❌ Error caching metadata: {e}")
            raise
    
    async def get_cached_group_metadata(
        self,
        group_id: int
    ) -> Optional[GroupMetadata]:
        """
        Get cached group metadata from Redis.
        
        Args:
            group_id: Group ID
            
        Returns:
            GroupMetadata if cached, None otherwise
        """
        try:
            key = GroupMetadata.get_metadata_key(group_id)
            data = await self.redis.hgetall(key)
            
            if not data:
                logger.debug(f"📦 No cached metadata for group {group_id}")
                return None
            
            # Decode Redis bytes to strings (Redis returns bytes)
            decoded_data = {
                k.decode() if isinstance(k, bytes) else k: 
                v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()
            }
            
            # Validate that we have required data
            if "group_id" not in decoded_data:
                logger.warning(f"⚠️ Cached metadata for group {group_id} missing group_id, refreshing...")
                return None
            
            metadata = GroupMetadata.from_dict(decoded_data)
            logger.debug(f"📦 Retrieved cached metadata for group {group_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Error getting cached metadata for group {group_id}: {e}")
            return None
    
    async def refresh_group_metadata(
        self,
        group_id: int,
        bot: Bot,
        force: bool = False
    ) -> Optional[GroupMetadata]:
        """
        Refresh group metadata if stale or missing.
        
        Args:
            group_id: Group ID
            bot: Bot instance for API calls
            force: Force refresh even if cache is fresh
            
        Returns:
            Fresh GroupMetadata or None if failed
        """
        # Check if refresh needed
        if not force:
            cached = await self.get_cached_group_metadata(group_id)
            if cached and not self.is_metadata_stale(cached):
                logger.debug(f"📦 Using fresh cached metadata for group {group_id}")
                return cached
        
        # Collect fresh metadata
        logger.info(f"🔄 Refreshing metadata for group {group_id}")
        
        try:
            # Get existing metadata to preserve some fields
            old_metadata = await self.get_cached_group_metadata(group_id)
            
            # Collect new metadata
            metadata = await self.collect_group_metadata(
                group_id=group_id,
                bot=bot,
                added_by_user_id=old_metadata.added_by_user_id if old_metadata else 0,
                added_by_username=old_metadata.added_by_username if old_metadata else None,
                added_by_full_name=old_metadata.added_by_full_name if old_metadata else "Unknown"
            )
            
            # Preserve some fields from old metadata
            if old_metadata:
                metadata.added_at = old_metadata.added_at
                metadata.bot_name = old_metadata.bot_name
                metadata.kb_index = old_metadata.kb_index
                metadata.thread_id = old_metadata.thread_id
                metadata.initial_language = old_metadata.initial_language
                metadata.first_message_timestamp = old_metadata.first_message_timestamp
                metadata.total_messages_received = old_metadata.total_messages_received
                metadata.active_members_list = old_metadata.active_members_list
                metadata.metadata_update_count = old_metadata.metadata_update_count + 1
            
            # Cache refreshed metadata
            await self.cache_group_metadata(metadata)
            
            logger.info(f"✅ Metadata refreshed for group {group_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Error refreshing metadata: {e}")
            return None
    
    def is_metadata_stale(
        self,
        metadata: GroupMetadata,
        max_age_hours: int = 24
    ) -> bool:
        """
        Check if metadata needs refresh.
        
        Args:
            metadata: GroupMetadata to check
            max_age_hours: Maximum age before considering stale
            
        Returns:
            True if stale, False if fresh
        """
        age = datetime.utcnow() - metadata.last_metadata_update
        is_stale = age.total_seconds() > (max_age_hours * 3600)
        
        if is_stale:
            logger.debug(f"⏰ Metadata for group {metadata.group_id} is stale ({age.total_seconds() / 3600:.1f}h old)")
        
        return is_stale
    
    async def _save_group_link(self, link: GroupLink) -> None:
        """
        Save group link to Redis.
        
        Args:
            link: GroupLink instance
        """
        try:
            # Save to hash
            key = link.get_redis_key()
            await self.redis.hset(key, mapping=link.to_dict())
            
            # Add to user's groups set
            user_set_key = GroupLink.get_user_groups_key(link.user_id)
            await self.redis.sadd(user_set_key, str(link.group_id))
            
            # Add to group's users set
            group_set_key = GroupLink.get_group_users_key(link.group_id)
            await self.redis.sadd(group_set_key, str(link.user_id))
            
            logger.debug(f"💾 Saved group link: {key}")
            
        except Exception as e:
            logger.error(f"❌ Error saving group link: {e}")
            raise


# Singleton instance
_group_service: Optional[GroupService] = None


async def get_group_service() -> GroupService:
    """Get or create GroupService singleton."""
    global _group_service
    if _group_service is None:
        from luka_bot.core.loader import redis_client
        _group_service = GroupService(redis_client)
        logger.info("✅ GroupService singleton created")
    return _group_service
