"""
Group onboarding utilities for silent additions.

Handles sending welcome messages to user DMs when silent addition is enabled
and adds group context to user's thread for LLM awareness.
"""
from datetime import datetime
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from loguru import logger

from luka_bot.models.thread import Thread
from luka_bot.models.group_metadata import GroupMetadata
from luka_bot.services.thread_service import get_thread_service
from luka_bot.utils.i18n_helper import _


async def send_group_onboarding_to_dm(
    bot: Bot,
    user_id: int,
    group_id: int,
    group_title: str,
    welcome_text: str,
    inline_keyboard: InlineKeyboardMarkup,
    metadata: GroupMetadata,
    thread: Thread,
    language: str = "en"
) -> bool:
    """
    Send group welcome message + controls to user's DM.
    Also adds this message to user's /start thread for LLM context.
    
    This is called when user has silent_addition=True in their defaults,
    so the welcome message goes to their DM instead of the group.
    
    Args:
        bot: Bot instance
        user_id: User ID who added the bot
        group_id: Group ID
        group_title: Group title
        welcome_text: Generated welcome text from welcome_generator
        inline_keyboard: Admin controls keyboard
        metadata: Group metadata
        thread: Group thread
        language: Language code (en/ru)
        
    Returns:
        True if successful, False if DM failed
    """
    try:
        # Build DM message with context
        dm_text = f"""{_('group_onboarding.silent_addition_header', language, group_title=group_title)}

{_('group_onboarding.silent_explanation', language)}

{welcome_text}

{_('group_onboarding.dm_controls_info', language)}

{_('group_onboarding.find_in_groups', language, group_title=group_title)}

{_('group_onboarding.tools_coming_soon', language)}"""
        
        # Get updated groups list for reply keyboard
        from luka_bot.services.group_service import get_group_service
        from luka_bot.keyboards.groups_menu import get_groups_keyboard, get_empty_groups_keyboard
        
        group_service = get_group_service()
        user_groups = await group_service.list_user_groups(user_id)
        
        # Build groups reply keyboard with the newly added group
        if user_groups:
            groups_keyboard = await get_groups_keyboard(
                user_groups,
                current_group_id=group_id,
                language=language
            )
        else:
            groups_keyboard = await get_empty_groups_keyboard(language=language)
        
        # Send to user's DM with inline keyboard for settings
        dm_message = await bot.send_message(
            chat_id=user_id,
            text=dm_text,
            reply_markup=inline_keyboard,  # Inline keyboard for settings
            parse_mode="HTML"
        )
        
        # Send a follow-up message with the updated groups reply keyboard
        keyboard_text = f"✅ Group <b>{group_title}</b> added to your list!" if language == 'en' else f"✅ Группа <b>{group_title}</b> добавлена!"
        
        await bot.send_message(
            chat_id=user_id,
            text=keyboard_text,
            reply_markup=groups_keyboard,  # Reply keyboard with updated groups list
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Sent silent addition welcome + updated groups keyboard to user {user_id} DM for group {group_id}")
        
        # Add this message to user's /start thread for LLM context
        await add_onboarding_to_thread_context(
            user_id=user_id,
            group_id=group_id,
            group_title=group_title,
            metadata=metadata,
            thread=thread,
            language=language
        )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send onboarding DM to user {user_id}: {e}")
        # User may have blocked the bot or disabled DMs
        # This is not fatal - the group was still set up successfully
        return False


async def add_onboarding_to_thread_context(
    user_id: int,
    group_id: int,
    group_title: str,
    metadata: GroupMetadata,
    thread: Thread,
    language: str
) -> None:
    """
    Add group onboarding info to user's /start thread for LLM context.
    
    This allows the AI to know about groups the user manages and provide
    context-aware help when the user asks about group management.
    
    The LLM can then respond to queries like:
    - "How is my group doing?"
    - "Can you help me configure MyGroup?"
    - "Show me stats for the group I just added you to"
    
    Args:
        user_id: User ID
        group_id: Group ID
        group_title: Group title
        metadata: Group metadata
        thread: Group thread
        language: Language code
    """
    try:
        thread_service = get_thread_service()
        
        # Get user's active thread (DM thread) if exists
        active_thread_id = await thread_service.get_active_thread(user_id)
        if not active_thread_id:
            # No active thread - create one for onboarding context
            user_thread = await thread_service.create_thread(user_id, name="Welcome")
            logger.debug(f"Created new thread for user {user_id} onboarding")
        else:
            user_thread = await thread_service.get_thread(active_thread_id)
            if not user_thread:
                logger.warning(f"Active thread {active_thread_id} not found for user {user_id}")
                return
        
        # Note: Thread context addition is currently disabled as message_history service 
        # is not available. This is a nice-to-have feature for LLM context awareness.
        # TODO: Re-implement when proper message history service is available
        
        logger.debug(f"ℹ️ Thread context addition skipped for group {group_id} (feature disabled)")
        logger.info(f"✅ Onboarding process completed for user {user_id} and group {group_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to add onboarding to thread context: {e}")
        # Non-fatal - the DM was sent, context addition is a bonus feature
