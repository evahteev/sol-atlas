"""
Background Moderation Handler - V2 Architecture.

This module implements true background moderation that doesn't block
the main message flow. Messages are evaluated in parallel while the bot
responds immediately to user interactions.

Key Features:
- Fire-and-forget moderation (no blocking)
- Retroactive message deletion (user + bot reply)
- User reputation updates
- Achievement notifications
- Auto-banning based on violations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from luka_bot.models.group_settings import GroupSettings
from luka_bot.services.moderation_service import get_moderation_service
from luka_bot.services.reply_tracker_service import get_reply_tracker_service
from luka_bot.core.loader import bot
from luka_bot.utils.background_tasks import create_background_task


async def process_moderation_in_background(
    message_id: int,
    chat_id: int,
    user_id: int,
    message_text: str,
    group_settings: GroupSettings
) -> None:
    """
    Process moderation in true background (fire-and-forget).
    
    This function is called via asyncio.create_task() and runs independently
    without blocking the main message handler. It can take as long as needed.
    
    Args:
        message_id: User's message ID
        chat_id: Telegram chat ID
        user_id: User ID who sent message
        message_text: Message content
        group_settings: Group moderation settings
        
    Flow:
        1. Evaluate message with LLM (no timeout, take as long as needed)
        2. Update user reputation
        3. Take action if violation detected (delete, warn)
        4. Check for achievements
        5. Ban user if threshold exceeded
        
    Note:
        - This runs in parallel to bot responses (no blocking)
        - Can delete bot's reply retroactively if violation found
        - All errors are caught and logged (no crash)
    """
    try:
        logger.debug(f"🛡️ [Background] Starting moderation for message {message_id} from user {user_id}")
        
        moderation_service = await get_moderation_service()
        reply_tracker = get_reply_tracker_service()
        
        # Check if admins should be moderated
        if not group_settings.moderate_admins_enabled:
            # Check if user is an admin
            from luka_bot.utils.permissions import is_user_admin_in_group
            try:
                is_admin = await is_user_admin_in_group(bot, chat_id, user_id)
                if is_admin:
                    logger.debug(f"⏭️  [Background] User {user_id} is admin, skipping moderation (moderate_admins disabled)")
                    return  # Skip moderation for admins
            except Exception as e:
                logger.warning(f"Failed to check admin status for user {user_id}: {e}")
                # Continue with moderation if check fails (safe fallback)
        
        # ========================================================================
        # STEP 1: Evaluate message with LLM (no timeout, can take as long as needed)
        # ========================================================================
        try:
            result = await moderation_service.evaluate_message_moderation(
                message_text=message_text,
                group_settings=group_settings,
                user_id=user_id,
                group_id=chat_id
            )
            logger.debug(f"🛡️ [Background] Moderation result: {result.get('action')} - {result.get('violation')}")
        except Exception as e:
            logger.error(f"❌ [Background] Moderation evaluation failed: {e}", exc_info=True)
            result = {"helpful": None, "violation": None, "action": "none"}
        
        # ========================================================================
        # STEP 2: Update user reputation
        # ========================================================================
        try:
            reputation = await moderation_service.update_user_reputation(
                user_id=user_id,
                group_id=chat_id,
                moderation_result=result,
                group_settings=group_settings
            )
            logger.debug(f"📊 [Background] User {user_id} reputation: {reputation.points} points, {reputation.violations} violations")
        except Exception as e:
            logger.error(f"❌ [Background] Failed to update reputation: {e}")
            reputation = None
        
        # ========================================================================
        # STEP 3: Take action if violation detected
        # ========================================================================
        action = result.get("action", "none")
        violation = result.get("violation")
        
        if action in ["delete", "warn"] and violation:
            # Get bot's reply to this message (if bot replied)
            bot_reply_id = await reply_tracker.get_bot_reply(chat_id, message_id)
            
            if action == "delete":
                logger.warning(f"🚫 [Background] Deleting violating message {message_id}: {violation}")
                
                # Delete user's original message
                try:
                    await bot.delete_message(chat_id, message_id)
                    logger.info(f"🗑️ [Background] Deleted user message {message_id}")
                except Exception as e:
                    logger.debug(f"⚠️ [Background] Could not delete user message: {e}")
                
                # Delete bot's reply (if exists)
                if bot_reply_id:
                    try:
                        await bot.delete_message(chat_id, bot_reply_id)
                        logger.info(f"🗑️ [Background] Also deleted bot reply {bot_reply_id}")
                    except Exception as e:
                        logger.debug(f"⚠️ [Background] Could not delete bot reply: {e}")
                
                # Notify user in DM (optional, best effort)
                try:
                    reason = result.get('reason', 'Violation detected')
                    await bot.send_message(
                        user_id,
                        f"⚠️ <b>Message Removed</b>\n\n"
                        f"Your message was removed from the group.\n"
                        f"<b>Reason:</b> {reason}\n"
                        f"<b>Type:</b> {violation}\n\n"
                        f"<i>Please review group rules.</i>",
                        parse_mode="HTML"
                    )
                    logger.debug(f"📬 [Background] Sent deletion notice to user {user_id}")
                except Exception as e:
                    logger.debug(f"⚠️ [Background] Could not notify user: {e}")
            
            elif action == "warn":
                logger.warning(f"⚠️ [Background] Warning user {user_id}: {violation}")
                
                # Send warning to user (don't delete message)
                try:
                    reason = result.get('reason', 'Please review')
                    await bot.send_message(
                        user_id,
                        f"⚠️ <b>Warning</b>\n\n"
                        f"Your message may violate group rules.\n"
                        f"<b>Reason:</b> {reason}\n"
                        f"<b>Type:</b> {violation}\n\n"
                        f"<i>Please be mindful of group guidelines.</i>",
                        parse_mode="HTML"
                    )
                    logger.debug(f"📬 [Background] Sent warning to user {user_id}")
                except Exception as e:
                    logger.debug(f"⚠️ [Background] Could not send warning: {e}")
        
        # ========================================================================
        # STEP 4: Check for ban threshold
        # ========================================================================
        if reputation and (
            reputation.is_banned or 
            (group_settings.auto_ban_enabled and reputation.violations >= group_settings.ban_threshold)
        ):
            logger.warning(f"🚫 [Background] User {user_id} exceeded ban threshold")
            
            # Update reputation to banned status
            try:
                await moderation_service.ban_user(
                    user_id=user_id,
                    group_id=chat_id,
                    reason="Exceeded violation threshold",
                    duration_hours=group_settings.ban_duration_hours
                )
                logger.info(f"🚫 [Background] Marked user {user_id} as banned in database")
            except Exception as e:
                logger.error(f"❌ [Background] Failed to mark user as banned: {e}")
            
            # Ban in Telegram
            try:
                ban_until = datetime.utcnow() + timedelta(hours=group_settings.ban_duration_hours)
                await bot.ban_chat_member(chat_id, user_id, until_date=ban_until)
                logger.info(f"🚫 [Background] Banned user {user_id} in Telegram for {group_settings.ban_duration_hours}h")
            except Exception as e:
                logger.warning(f"⚠️ [Background] Could not ban user in Telegram: {e}")
        
        # ========================================================================
        # STEP 5: Check for achievements
        # ========================================================================
        if reputation:
            try:
                new_achievements = await moderation_service.check_achievements(
                    user_id=user_id,
                    group_id=chat_id,
                    group_settings=group_settings
                )
                if new_achievements:
                    # Announce first achievement only (avoid spam)
                    achievement = new_achievements[0]
                    try:
                        await bot.send_message(
                            chat_id,
                            f"🏆 <b>Achievement Unlocked!</b>\n\n"
                            f"{achievement['icon']} <b>{achievement['name']}</b>\n"
                            f"+{achievement['points']} points\n\n"
                            f"<i>Congratulations!</i>",
                            parse_mode="HTML"
                        )
                        logger.info(f"🏆 [Background] Announced achievement for user {user_id}: {achievement['name']}")
                    except Exception as e:
                        logger.debug(f"⚠️ [Background] Could not announce achievement: {e}")
            except Exception as e:
                logger.error(f"❌ [Background] Failed to check achievements: {e}")
        
        logger.debug(f"✅ [Background] Moderation complete for message {message_id}")
        
    except Exception as e:
        logger.error(f"❌ [Background] Fatal error in moderation: {e}", exc_info=True)


def fire_moderation_task(
    message_id: int,
    chat_id: int,
    user_id: int,
    message_text: str,
    group_settings: GroupSettings
) -> asyncio.Task:
    """
    Fire a moderation task in the background (non-blocking).
    
    This is the main entry point for V2 background moderation.
    Call this from the message handler and immediately continue.
    
    Args:
        message_id: User's message ID
        chat_id: Telegram chat ID
        user_id: User ID
        message_text: Message content
        group_settings: Group settings
        
    Returns:
        asyncio.Task (for tracking, but you can ignore it)
        
    Example:
        # In message handler:
        if group_settings and group_settings.moderation_enabled:
            fire_moderation_task(
                message_id=message.message_id,
                chat_id=message.chat.id,
                user_id=user_id,
                message_text=message_text,
                group_settings=group_settings
            )
            # Continue immediately - no waiting!
        
        # Bot processes message normally (no blocking)
        
    Note:
        - Returns immediately (no blocking)
        - Moderation happens in parallel
        - Can delete bot's reply retroactively
    """
    task = create_background_task(
        process_moderation_in_background(
            message_id=message_id,
            chat_id=chat_id,
            user_id=user_id,
            message_text=message_text,
            group_settings=group_settings
        ),
        name=f"moderation_u{user_id}_m{message_id}",
        track=True
    )
    
    logger.debug(f"🔥 Fired moderation task for message {message_id} (non-blocking)")
    return task

