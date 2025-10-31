"""
Permission utilities for group management.
"""
from aiogram import Bot
from loguru import logger


async def is_user_admin_in_group(bot: Bot, chat_id: int, user_id: int) -> bool:
    """
    Check if user is admin in the group.
    
    Args:
        bot: Bot instance
        chat_id: Group chat ID
        user_id: User ID to check
        
    Returns:
        True if user is creator or administrator, False otherwise
    """
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ["creator", "administrator"]
        logger.debug(f"User {user_id} in chat {chat_id}: status={member.status}, is_admin={is_admin}")
        return is_admin
    except Exception as e:
        logger.error(f"Failed to check admin status for user {user_id} in chat {chat_id}: {e}")
        return False


async def is_user_registered(user_id: int) -> bool:
    """
    Check if user has completed bot onboarding.
    
    Args:
        user_id: User ID to check
        
    Returns:
        True if user has a profile (completed onboarding), False otherwise
    """
    try:
        from luka_bot.services.user_profile_service import get_user_profile_service
        profile_service = get_user_profile_service()
        profile = await profile_service.get_profile(user_id)
        is_registered = profile is not None
        logger.debug(f"User {user_id} registration status: {is_registered}")
        return is_registered
    except Exception as e:
        logger.error(f"Failed to check registration status for user {user_id}: {e}")
        return False

