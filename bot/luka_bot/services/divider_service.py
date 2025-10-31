"""
Thread divider service for luka_bot.

Creates organic divider messages when switching between threads,
showing thread context and last message.
"""
from datetime import datetime
from typing import Optional
from loguru import logger

from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.user_profile_service import get_user_profile_service
from luka_bot.core.loader import redis_client
from luka_bot.utils.i18n_helper import _


async def get_last_message_preview(thread_id: str, max_length: int = 80) -> Optional[str]:
    """
    Get preview of last message in thread.
    
    Args:
        thread_id: Thread ID
        max_length: Maximum preview length
        
    Returns:
        Message preview or None
    """
    try:
        # Get thread history
        history_key = f"thread_history:{thread_id}"
        last_messages = await redis_client.lrange(history_key, -2, -1)
        
        if not last_messages:
            return None
        
        # Parse last message
        import json
        for msg_raw in reversed(last_messages):
            try:
                msg = json.loads(msg_raw)
                content = msg.get("content", "")
                role = msg.get("role", "")
                
                # Skip empty messages
                if not content or not content.strip():
                    continue
                
                # Clean content
                preview = content.strip()
                
                # Truncate if needed
                if len(preview) > max_length:
                    preview = preview[:max_length-3] + "..."
                
                # Add role indicator
                if role == "user":
                    return f"You: {preview}"
                elif role == "assistant":
                    return f"Bot: {preview}"
                else:
                    return preview
                    
            except Exception as e:
                logger.debug(f"Failed to parse message: {e}")
                continue
        
        return None
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to get last message preview: {e}")
        return None


async def create_thread_divider(
    thread_id: str,
    user_id: int,
    divider_type: str = "switch"
) -> str:
    """
    Create thread divider message.
    
    Args:
        thread_id: Target thread ID
        user_id: User ID
        divider_type: "switch", "new", or "continue"
        
    Returns:
        Formatted divider message (HTML)
    """
    thread_service = get_thread_service()
    thread = await thread_service.get_thread(thread_id)
    
    if not thread:
        logger.warning(f"⚠️  Thread {thread_id} not found for divider")
        return "─────────────────"
    
    # Get user language
    profile_service = get_user_profile_service()
    language = await profile_service.get_language(user_id)
    
    # Get last message preview
    last_message = await get_last_message_preview(thread_id)
    
    # Get time info
    time_diff = datetime.utcnow() - thread.updated_at
    if time_diff.total_seconds() < 60:
        time_ago = _("divider.time_just_now", language)
    elif time_diff.total_seconds() < 3600:
        minutes = int(time_diff.total_seconds() / 60)
        time_ago = _("divider.time_minutes_ago", language, minutes=minutes)
    elif time_diff.total_seconds() < 86400:
        hours = int(time_diff.total_seconds() / 3600)
        time_ago = _("divider.time_hours_ago", language, hours=hours)
    else:
        days = int(time_diff.total_seconds() / 86400)
        time_ago = _("divider.time_days_ago", language, days=days)
    
    # Build divider based on type
    if divider_type == "switch":
        # Switching to existing thread
        icon = "🔀"
        action = _("divider.action_switched", language)
    elif divider_type == "new":
        # Starting new thread
        icon = "✨"
        action = _("divider.action_started", language)
    else:  # continue
        # Continuing in thread
        icon = "📝"
        action = _("divider.action_continuing", language)
    
    # Build message
    divider = f"""━━━━━━━━━━━━━━━━━━━━

{icon} <b>{action}: {thread.name}</b>"""
    
    # Add message count if > 0
    if thread.message_count > 0:
        divider += "\n💬 <i>" + _("divider.messages_count", language, count=thread.message_count)
        if time_ago:
            divider += " • " + _("divider.last_activity", language, time_ago=time_ago)
        divider += "</i>"
    
    # Add last message preview if available
    if last_message and divider_type == "switch":
        divider += "\n\n<i>" + last_message + "</i>"
    
    divider += "\n\n━━━━━━━━━━━━━━━━━━━━"
    
    return divider


async def send_thread_divider(
    user_id: int,
    thread_id: str,
    divider_type: str = "switch",
    bot = None,
    reply_markup = None
) -> None:
    """
    Send thread divider message to user.
    
    Args:
        user_id: Telegram user ID
        thread_id: Thread ID
        divider_type: "switch", "new", or "continue"
        bot: Bot instance
        reply_markup: Optional keyboard to attach
    """
    if not bot:
        from luka_bot.core.loader import bot as default_bot
        bot = default_bot
    
    try:
        # Create divider
        divider_text = await create_thread_divider(thread_id, user_id, divider_type)
        
        # Send divider with optional keyboard
        await bot.send_message(
            chat_id=user_id,
            text=divider_text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        
        logger.info(f"📍 Sent {divider_type} divider for thread {thread_id[:8]}... to user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send divider: {e}")


async def send_simple_divider(
    user_id: int,
    text: str,
    bot = None
) -> None:
    """
    Send simple text divider.
    
    Args:
        user_id: Telegram user ID
        text: Divider text
        bot: Bot instance
    """
    if not bot:
        from luka_bot.core.loader import bot as default_bot
        bot = default_bot
    
    try:
        divider = f"""━━━━━━━━━━━━━━━━━━━━

{text}

━━━━━━━━━━━━━━━━━━━━"""
        
        await bot.send_message(
            chat_id=user_id,
            text=divider,
            parse_mode="HTML"
        )
        
        logger.info(f"📍 Sent simple divider to user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send simple divider: {e}")

