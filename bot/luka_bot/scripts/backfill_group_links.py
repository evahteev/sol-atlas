"""
Backfill GroupLinks from Elasticsearch KB data.

Scans group KB indices and creates GroupLinks for all users who have
posted messages in those groups.
"""
from loguru import logger
from typing import Optional
import asyncio

from luka_bot.services.group_service import get_group_service
from luka_bot.services.elasticsearch_service import get_elasticsearch_service
from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.user_profile_service import UserProfileService
from luka_bot.core.config import settings


async def backfill_single_group(group_id: int) -> dict:
    """
    Backfill GroupLinks for a single group.
    
    Args:
        group_id: Group ID to backfill
        
    Returns:
        Dict with stats: created, updated, errors
    """
    stats = {"created": 0, "updated": 0, "errors": 0, "skipped": 0}
    
    try:
        group_service = await get_group_service()
        es_service = await get_elasticsearch_service()
        thread_service = get_thread_service()
        profile_service = UserProfileService()
        
        # Get group thread
        group_thread = await thread_service.get_group_thread(group_id)
        if not group_thread:
            logger.warning(f"⚠️ No group thread for {group_id}, skipping")
            stats["errors"] += 1
            return stats
        
        group_title = group_thread.name or f"Group {group_id}"
        kb_index = f"tg-kb-group-{abs(group_id)}"
        
        logger.info(f"🔄 Backfilling group {group_id} ({group_title})")
        
        # Get unique users from KB
        unique_users = await es_service.get_unique_users_in_index(kb_index)
        
        if not unique_users:
            logger.info(f"📭 No users found in KB for group {group_id}")
            return stats
        
        logger.info(f"👥 Found {len(unique_users)} unique users in group {group_id}")
        
        # Create GroupLinks for each user
        for user_id_str in unique_users:
            try:
                user_id = int(user_id_str)
                
                # Create minimal profile if needed
                await profile_service.get_or_create_minimal_profile(user_id, None)
                
                # Check if link exists
                existing_link = await group_service.get_group_link(user_id, group_id)
                
                if existing_link:
                    stats["skipped"] += 1
                    continue
                
                # Create link
                await group_service.create_group_link(
                    user_id=user_id,
                    group_id=group_id,
                    group_title=group_title,
                    language=group_thread.language or "en",
                    user_role="member"  # Default role for backfill
                )
                
                stats["created"] += 1
                logger.debug(f"✨ Created GroupLink: user={user_id}, group={group_id}")
                
            except Exception as e:
                logger.error(f"❌ Error creating link for user {user_id_str}: {e}")
                stats["errors"] += 1
        
        logger.info(f"✅ Backfill complete for group {group_id}: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error backfilling group {group_id}: {e}")
        stats["errors"] += 1
        return stats


async def backfill_all_groups() -> dict:
    """
    Backfill GroupLinks for all groups.
    
    Returns:
        Dict with overall stats
    """
    overall_stats = {"groups": 0, "created": 0, "updated": 0, "errors": 0, "skipped": 0}
    
    try:
        es_service = await get_elasticsearch_service()
        
        # Get all group KB indices
        indices = await es_service.list_indices("tg-kb-group-*")
        
        logger.info(f"📚 Found {len(indices)} group KB indices")
        
        for index_info in indices:
            index_name = index_info["index"]
            # Extract group_id from index name: tg-kb-group-1234567890
            group_id_str = index_name.split("-")[-1]
            group_id = -int(group_id_str)  # Make negative for group ID
            
            stats = await backfill_single_group(group_id)
            
            overall_stats["groups"] += 1
            overall_stats["created"] += stats["created"]
            overall_stats["updated"] += stats["updated"]
            overall_stats["errors"] += stats["errors"]
            overall_stats["skipped"] += stats["skipped"]
        
        logger.info(f"✅ Backfill complete for all groups: {overall_stats}")
        return overall_stats
        
    except Exception as e:
        logger.error(f"❌ Error backfilling all groups: {e}")
        overall_stats["errors"] += 1
        return overall_stats


# CLI interface
if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            # Backfill specific group
            group_id = int(sys.argv[1])
            logger.info(f"🚀 Starting backfill for group {group_id}")
            stats = await backfill_single_group(group_id)
            logger.info(f"✅ Done: {stats}")
        else:
            # Backfill all groups
            logger.info("🚀 Starting backfill for all groups")
            stats = await backfill_all_groups()
            logger.info(f"✅ Done: {stats}")
    
    asyncio.run(main())

