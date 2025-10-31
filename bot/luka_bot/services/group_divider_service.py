"""
Group divider service - Show group context with inline controls.

Similar to divider_service.py but specifically for group navigation.
Shows group info, stats, and inline buttons for Settings/Delete.
"""
from typing import Optional, Tuple
from datetime import datetime
from loguru import logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.group_service import get_group_service
from luka_bot.services.user_profile_service import get_user_profile_service
from luka_bot.utils.i18n_helper import _


async def get_group_stats(group_id: int, bot=None) -> dict:
    """
    Get comprehensive group statistics for divider display.
    
    Args:
        group_id: Group ID
        bot: Bot instance (optional, for API calls)
        
    Returns:
        Dict with complete stats matching the stats page format
    """
    try:
        group_service = await get_group_service()
        thread_service = get_thread_service()
        
        # Get group thread for KB index
        thread = await thread_service.get_group_thread(group_id)
        kb_index = thread.knowledge_bases[0] if thread and thread.knowledge_bases else None
        
        # Initialize stats
        member_count = "?"
        message_count = 0
        size_mb = 0.0
        unique_users_week = 0
        messages_week = 0
        top_users_week = []
        
        # Get comprehensive KB stats from Elasticsearch (same as stats page)
        if kb_index:
            try:
                from luka_bot.services.elasticsearch_service import get_elasticsearch_service
                es_service = await get_elasticsearch_service()
                
                # Get index stats (message count and size)
                index_stats = await es_service.get_index_stats(kb_index)
                message_count = index_stats.get("message_count", 0)
                size_mb = index_stats.get("size_mb", 0.0)
                
                # Get weekly stats (same as stats page)
                weekly_stats = await es_service.get_group_weekly_stats(kb_index)
                unique_users_week = weekly_stats.get("unique_users_week", 0)
                messages_week = weekly_stats.get("total_messages_week", 0)
                top_users_week = weekly_stats.get("top_users_week", [])
                
            except Exception as kb_error:
                logger.debug(f"Could not get KB stats: {kb_error}")
        
        # Get group metadata for group type info
        group_type = "group"
        has_topics = False
        
        try:
            metadata = await group_service.get_cached_group_metadata(group_id)
            if metadata:
                group_type = metadata.group_type or "group"
                has_topics = metadata.has_topics or False
        except Exception as meta_error:
            logger.debug(f"Could not get metadata: {meta_error}")
        
        # Get live member count from Telegram API (same as stats page)
        if bot:
            try:
                member_count = await bot.get_chat_member_count(group_id)
            except Exception as api_error:
                logger.debug(f"Could not get member count from API: {api_error}")
        
        return {
            "member_count": member_count,
            "message_count": message_count,
            "kb_index": kb_index,
            "size_mb": size_mb,
            "unique_users_week": unique_users_week,
            "messages_week": messages_week,
            "top_users_week": top_users_week,
            "group_type": group_type,
            "has_topics": has_topics,
        }
    except Exception as e:
        logger.error(f"❌ Error getting group stats: {e}")
        return {
            "member_count": "?",
            "message_count": 0,
            "kb_index": None,
            "size_mb": 0.0,
            "unique_users_week": 0,
            "messages_week": 0,
            "top_users_week": [],
            "group_type": "group",
            "has_topics": False,
        }


async def create_group_divider(
    group_id: int,
    user_id: int,
    divider_type: str = "switch",
    bot = None
) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Create group divider message with inline buttons.
    
    Args:
        group_id: Target group ID
        user_id: User ID
        divider_type: "switch", "initial", or "refresh"
        bot: Bot instance (optional, for API calls)
        
    Returns:
        Tuple of (message_text, inline_keyboard)
    """
    thread_service = get_thread_service()
    thread = await thread_service.get_group_thread(group_id)
    
    if not thread:
        logger.warning(f"⚠️  Group thread for {group_id} not found for divider")
        return ("─────────────────", InlineKeyboardMarkup(inline_keyboard=[]))
    
    # Get user language
    profile_service = get_user_profile_service()
    language = await profile_service.get_language(user_id)
    
    # Get comprehensive group stats (same as stats page)
    stats = await get_group_stats(group_id, bot=bot)
    
    # Get group service for language and metadata
    from luka_bot.services.group_service import get_group_service
    group_service = await get_group_service()
    current_language = await group_service.get_group_language(group_id)
    
    # Get group name from metadata or API
    group_name = thread.agent_name or 'Group'
    try:
        metadata = await group_service.get_cached_group_metadata(group_id)
        if metadata and metadata.group_title:
            group_name = metadata.group_title
        elif bot:
            # Fallback to bot API if metadata not available
            try:
                chat = await bot.get_chat(group_id)
                if chat and chat.title:
                    group_name = chat.title
            except Exception as api_error:
                logger.debug(f"Could not get group name from API: {api_error}")
    except Exception as meta_error:
        logger.debug(f"Could not get group metadata: {meta_error}")
    
    # Use i18n for all labels
    title = f"🏘 <b>{group_name}</b>"
    stats_header = _("groups.divider.stats_header", current_language)
    members_label = _("groups.divider.members_label", current_language)
    messages_label = _("groups.divider.messages_label", current_language)
    activity_label = _("groups.divider.activity_label", current_language)
    activity_active = _("groups.divider.activity_active", current_language)
    activity_messages = _("groups.divider.activity_messages", current_language)
    kb_label = _("groups.divider.kb_label", current_language)
    kb_not_configured = _("groups.divider.kb_not_configured", current_language)
    features_header = _("groups.divider.features_header", current_language)
    feature_1 = _("groups.divider.feature_1", current_language)
    feature_2 = _("groups.divider.feature_2", current_language)
    feature_3 = _("groups.divider.feature_3", current_language)
    
    # Build compact, user-friendly overview with prominent group name
    divider = f"""{title}
━━━━━━━━━━━━━━━━━━
{stats_header}
{members_label}: <b>{stats['member_count']}</b> | {messages_label}: <b>{stats['message_count']:,}</b>
{activity_label}: <b>{stats['unique_users_week']}</b> {activity_active}, <b>{stats['messages_week']}</b> {activity_messages}
{kb_label}: <code>{stats['kb_index'] or kb_not_configured}</code>
{features_header}
{feature_1}
{feature_2}
{feature_3}"""
    
    # Create inline keyboard with Scheduled Content, Stats, and Settings buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("groups.divider.btn_scheduled_content", language),
                callback_data=f"scheduled_content:{group_id}"
            ),
            InlineKeyboardButton(
                text=_("groups.divider.btn_stats", language),
                callback_data=f"group_stats:{group_id}"
            ),
            InlineKeyboardButton(
                text=_("groups.divider.btn_settings", language),
                callback_data=f"group_admin_menu:{group_id}"
            )
        ]
    ])
    
    return (divider, keyboard)


async def send_group_divider(
    user_id: int,
    group_id: int,
    divider_type: str = "switch",
    bot = None
) -> None:
    """
    Send group divider message to user with inline buttons.
    
    Args:
        user_id: Telegram user ID
        group_id: Group ID
        divider_type: "switch", "initial", or "refresh"
        bot: Bot instance
        reply_markup: Optional reply keyboard (groups menu) to attach
    """
    if not bot:
        from luka_bot.core.loader import bot as default_bot
        bot = default_bot
    
    try:
        # Create divider with inline buttons (pass bot for live stats)
        divider_text, inline_keyboard = await create_group_divider(group_id, user_id, divider_type, bot=bot)
        
        # Send divider with BOTH keyboards:
        # - reply_markup: Groups reply keyboard (always visible)
        # - inline_keyboard: Settings/Delete buttons (in message)
        
        await bot.send_message(
            chat_id=user_id,
            text=divider_text,
            parse_mode="HTML",
            reply_markup=inline_keyboard
        )
        
        logger.info(f"📍 Sent {divider_type} divider for group {group_id} to user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send group divider: {e}")


async def get_user_language(user_id: int) -> str:
    """Helper to get user language."""
    from luka_bot.utils.i18n_helper import get_user_language as get_lang
    return await get_lang(user_id)
