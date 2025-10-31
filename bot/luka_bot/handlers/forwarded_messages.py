"""
Forwarded messages handler.

Handles messages that are forwarded to the bot, extracting and displaying
the original source information and passing it to the LLM for analysis.
Also automatically adds groups to user's list when forwarding from groups
where the bot is integrated.
"""
from aiogram import Bot, F, Router
from aiogram.enums import ChatAction, ChatType
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from luka_bot.services.llm_service import get_llm_service
from luka_bot.services.message_state_service import get_message_state_service
from luka_bot.services.messaging_service import edit_and_send_parts
from luka_bot.services.thread_service import get_thread_service
from luka_bot.utils.formatting import escape_html
from luka_bot.utils.i18n_helper import get_user_language

router = Router()


# Note: Custom PrivateChatFilter removed in favor of aiogram's built-in F.chat.type filter
# The custom filter was unreliable and caused group messages to leak through to DM handlers
# See: /docs/issues/group-message-filter-bug.md


def extract_forward_info(message: Message) -> dict:
    """
    Extract forwarding information from a message.
    
    Returns dict with:
        - origin_type: 'user', 'channel', 'chat', 'hidden_user'
        - origin_id: Chat/user ID if available
        - origin_name: Name of origin
        - origin_username: Username if available
        - thread_id: Message thread ID if from supergroup topic
        - message_id: Original message ID if available
        - date: Original message date
    """
    info = {
        "origin_type": None,
        "origin_id": None,
        "origin_name": None,
        "origin_username": None,
        "thread_id": None,
        "message_id": None,
        "date": None,
    }

    if not message.forward_origin:
        return info

    forward = message.forward_origin
    info["date"] = forward.date

    # Handle different forward origin types
    if forward.type == "user":
        # Forwarded from a user
        info["origin_type"] = "user"
        if forward.sender_user:
            info["origin_id"] = forward.sender_user.id
            info["origin_name"] = forward.sender_user.full_name
            info["origin_username"] = forward.sender_user.username

    elif forward.type == "hidden_user":
        # Forwarded from a user who hides their account
        info["origin_type"] = "hidden_user"
        info["origin_name"] = forward.sender_user_name

    elif forward.type == "chat":
        # Forwarded from a group/supergroup
        info["origin_type"] = "chat"
        if forward.sender_chat:
            info["origin_id"] = forward.sender_chat.id
            info["origin_name"] = forward.sender_chat.title
            info["origin_username"] = getattr(forward.sender_chat, "username", None)
        # Check for message thread ID (topic in supergroup)
        if hasattr(forward, "message_id"):
            info["message_id"] = forward.message_id

    elif forward.type == "channel":
        # Forwarded from a channel
        info["origin_type"] = "channel"
        if forward.chat:
            info["origin_id"] = forward.chat.id
            info["origin_name"] = forward.chat.title
            info["origin_username"] = getattr(forward.chat, "username", None)
        if hasattr(forward, "message_id"):
            info["message_id"] = forward.message_id

    # Check if the forwarded message itself has a thread_id (from topic)
    if hasattr(message, "forward_from_message_id"):
        info["message_id"] = message.forward_from_message_id

    return info


async def extract_forward_info_with_verification(message: Message, bot: Bot) -> dict:
    """
    Enhanced version of extract_forward_info that also verifies bot membership in the group.
    
    Returns the same dict as extract_forward_info plus:
        - bot_is_member: True if bot is a member of the forwarded group
    """
    info = extract_forward_info(message)

    # If forwarded from a group, verify bot is a member
    if info["origin_type"] == "chat" and info["origin_id"]:
        try:
            # Check if bot is a member of the group
            bot_member = await bot.get_chat_member(info["origin_id"], bot.id)
            info["bot_is_member"] = bot_member.status in ["member", "administrator", "creator"]
            logger.debug(f"Bot membership in group {info['origin_id']}: {info['bot_is_member']}")
        except Exception as e:
            logger.debug(f"Could not verify bot membership in group {info['origin_id']}: {e}")
            info["bot_is_member"] = False
    else:
        info["bot_is_member"] = False

    return info


async def verify_user_in_group(bot: Bot, group_id: int, user_id: int) -> bool:
    """
    Verify that the user is a member of the group.
    
    Args:
        bot: Bot instance
        group_id: Group ID to check
        user_id: User ID to verify
        
    Returns:
        True if user is a member, False otherwise
    """
    try:
        member = await bot.get_chat_member(group_id, user_id)
        is_member = member.status in ["member", "administrator", "creator"]
        logger.debug(f"User {user_id} membership in group {group_id}: {is_member} (status: {member.status})")
        return is_member
    except Exception as e:
        logger.debug(f"Could not verify user {user_id} membership in group {group_id}: {e}")
        return False


async def can_auto_add_group(user_id: int, group_id: int, bot: Bot) -> tuple[bool, str]:
    """
    Check if group can be auto-added with privacy considerations.
    
    Args:
        user_id: User ID
        group_id: Group ID
        bot: Bot instance
        
    Returns:
        Tuple of (can_add: bool, reason: str)
    """
    try:
        # Check if bot is a member
        bot_member = await bot.get_chat_member(group_id, bot.id)
        if bot_member.status not in ["member", "administrator", "creator"]:
            return False, "Bot is not a member of this group"

        # Check if user is a member
        user_member = await bot.get_chat_member(group_id, user_id)
        if user_member.status not in ["member", "administrator", "creator"]:
            return False, "User is not a member of this group"

        # Check if group is accessible
        try:
            chat = await bot.get_chat(group_id)
            # Additional privacy checks can be added here if needed
        except Exception as e:
            return False, f"Cannot access group information: {e}"

        return True, "OK"

    except Exception as e:
        return False, f"Verification failed: {e}"


async def auto_add_group_from_forward(
    user_id: int,
    group_id: int,
    group_name: str,
    bot: Bot
) -> bool:
    """
    Automatically add group to user's list if conditions are met.
    
    Args:
        user_id: User ID
        group_id: Group ID
        group_name: Group name/title
        bot: Bot instance
        
    Returns:
        True if group was added successfully, False otherwise
    """
    try:
        from luka_bot.services.group_service import get_group_service

        group_service = await get_group_service()

        # Check if group link already exists
        existing_link = await group_service.get_group_link(user_id, group_id)
        if existing_link and existing_link.is_active:
            logger.debug(f"Group {group_id} already linked to user {user_id}")
            return True

        # Verify conditions for auto-addition
        can_add, reason = await can_auto_add_group(user_id, group_id, bot)
        if not can_add:
            logger.info(f"Cannot auto-add group {group_id} to user {user_id}: {reason}")
            return False

        # Get user's role in the group
        user_role = "member"  # Default
        try:
            member = await bot.get_chat_member(group_id, user_id)
            if member.status in ["administrator", "creator"]:
                user_role = "admin" if member.status == "administrator" else "owner"
        except Exception as e:
            logger.debug(f"Could not get user role for {user_id} in group {group_id}: {e}")

        # Create group link
        await group_service.create_group_link(
            user_id=user_id,
            group_id=group_id,
            group_title=group_name,
            user_role=user_role
        )

        logger.info(f"✅ Auto-added group {group_id} ({group_name}) to user {user_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Error auto-adding group {group_id} to user {user_id}: {e}")
        return False


async def show_group_addition_notification(
    message: Message,
    forward_info: dict,
    group_added: bool,
    lang: str
) -> None:
    """
    Show appropriate notification based on group addition result.
    
    Args:
        message: Original message object
        forward_info: Forward information dict
        group_added: Whether group was successfully added
        lang: User language
    """
    if group_added:
        # Group was successfully added
        notification = f"""✅ <b>Group Added to Your List!</b>

📁 <b>{escape_html(forward_info['origin_name'])}</b> has been automatically added to your groups.

💡 <b>What's next?</b>
• Use /groups to see all your groups
• Chat with this group's AI assistant
• Access group knowledge base and settings

<i>This group was added because you forwarded a message from it and the bot is integrated there.</i>"""
    else:
        # Group couldn't be added (user not member, bot not member, etc.)
        notification = f"""ℹ️ <b>Group Not Added</b>

📁 <b>{escape_html(forward_info['origin_name'])}</b> could not be added to your groups.

<i>This might be because:
• You're no longer a member of this group
• The bot is not integrated in this group
• The group was already in your list</i>"""

    await message.answer(notification, parse_mode="HTML")


def format_forward_info_message(info: dict, lang: str = "en") -> str:
    """Format forwarding information for display to user."""
    if not info["origin_type"]:
        return ""

    lines = ["📨 <b>Forwarded Message</b>\n"]

    if info["origin_type"] == "user":
        name = escape_html(info["origin_name"] or "Unknown User")
        if info["origin_username"]:
            lines.append(f"👤 <b>From User:</b> {name} (@{info['origin_username']})")
        else:
            lines.append(f"👤 <b>From User:</b> {name}")
        if info["origin_id"]:
            lines.append(f"🆔 <b>User ID:</b> <code>{info['origin_id']}</code>")

    elif info["origin_type"] == "hidden_user":
        name = escape_html(info["origin_name"] or "Unknown")
        lines.append(f"👤 <b>From User:</b> {name} (account hidden)")

    elif info["origin_type"] == "chat":
        name = escape_html(info["origin_name"] or "Unknown Chat")
        if info["origin_username"]:
            lines.append(f"👥 <b>From Group:</b> {name} (@{info['origin_username']})")
        else:
            lines.append(f"👥 <b>From Group:</b> {name}")
        if info["origin_id"]:
            lines.append(f"🆔 <b>Chat ID:</b> <code>{info['origin_id']}</code>")

    elif info["origin_type"] == "channel":
        name = escape_html(info["origin_name"] or "Unknown Channel")
        if info["origin_username"]:
            lines.append(f"📢 <b>From Channel:</b> {name} (@{info['origin_username']})")
        else:
            lines.append(f"📢 <b>From Channel:</b> {name}")
        if info["origin_id"]:
            lines.append(f"🆔 <b>Channel ID:</b> <code>{info['origin_id']}</code>")

    if info["message_id"]:
        lines.append(f"📝 <b>Original Message ID:</b> <code>{info['message_id']}</code>")

    if info["thread_id"]:
        lines.append(f"🧵 <b>Thread ID:</b> <code>{info['thread_id']}</code>")

    if info["date"]:
        date_str = info["date"].strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"📅 <b>Original Date:</b> {date_str}")

    return "\n".join(lines)


def format_forward_context_for_llm(info: dict, message_text: str) -> str:
    """Format forwarding information as context for the LLM."""
    if not info["origin_type"]:
        return message_text

    context_parts = ["[FORWARDED MESSAGE CONTEXT]"]

    if info["origin_type"] == "user":
        context_parts.append(f"Source: User {info['origin_name']}")
        if info["origin_username"]:
            context_parts.append(f"Username: @{info['origin_username']}")
        if info["origin_id"]:
            context_parts.append(f"User ID: {info['origin_id']}")

    elif info["origin_type"] == "hidden_user":
        context_parts.append(f"Source: User {info['origin_name']} (privacy settings enabled)")

    elif info["origin_type"] == "chat":
        context_parts.append(f"Source: Group/Chat '{info['origin_name']}'")
        if info["origin_username"]:
            context_parts.append(f"Username: @{info['origin_username']}")
        if info["origin_id"]:
            context_parts.append(f"Chat ID: {info['origin_id']}")

    elif info["origin_type"] == "channel":
        context_parts.append(f"Source: Channel '{info['origin_name']}'")
        if info["origin_username"]:
            context_parts.append(f"Username: @{info['origin_username']}")
        if info["origin_id"]:
            context_parts.append(f"Channel ID: {info['origin_id']}")

    if info["message_id"]:
        context_parts.append(f"Original Message ID: {info['message_id']}")

    if info["thread_id"]:
        context_parts.append(f"Thread/Topic ID: {info['thread_id']}")

    if info["date"]:
        context_parts.append(f"Original Date: {info['date'].strftime('%Y-%m-%d %H:%M:%S')}")

    context_parts.append("\n[FORWARDED MESSAGE CONTENT]")
    context_parts.append(message_text)
    context_parts.append("\n[END FORWARDED MESSAGE]")
    context_parts.append("\nPlease analyze this forwarded message, taking into account its source and context.")

    return "\n".join(context_parts)


@router.message(~F.chat.type.in_({"group", "supergroup", "channel"}), F.forward_origin)
async def handle_forwarded_message(message: Message, state: FSMContext) -> None:
    """
    Handle forwarded messages in private chat.

    Extracts forwarding information, displays it to the user,
    and passes it to the LLM for analysis with full context.

    Note: Uses negation filter ~F.chat.type.in_() to explicitly exclude groups/supergroups/channels.
    This is more reliable than equality checks with ChatType.PRIVATE in aiogram 3.x.
    Previous approaches (custom filter and F.chat.type == ChatType.PRIVATE) both failed.
    """
    user_id = message.from_user.id if message.from_user else None

    if not user_id:
        return

    # WORKAROUND: If this is a group message, route it to the group handler
    if message.chat.type in ("group", "supergroup"):
        logger.warning(f"⚠️ FORWARDED_MESSAGES received group message - routing to group handler")
        logger.warning(f"   chat_id={message.chat.id}, type={message.chat.type}")

        # Import and call the group handler directly
        from luka_bot.handlers.group_messages import handle_group_message
        await handle_group_message(message)
        return

    # Debug: Log successful private chat forwarded message acceptance
    logger.debug(f"✅ FORWARDED_MESSAGES: Accepted private chat forwarded message from user {user_id}")

    # Extract text from message
    text = message.text or message.caption or ""

    if not text:
        # Handle messages without text (photos, videos, etc.)
        await message.answer(
            "📨 I received a forwarded message, but it doesn't contain text to analyze. "
            "Please forward messages with text content."
        )
        return

    logger.info(f"📨 Forwarded message from user {user_id}: {text[:50]}...")

    # Extract forwarding information with bot membership verification
    forward_info = await extract_forward_info_with_verification(message, message.bot)

    # Log the forwarding details
    logger.info(
        f"📨 Forward details: type={forward_info['origin_type']}, "
        f"name={forward_info['origin_name']}, "
        f"id={forward_info['origin_id']}, "
        f"thread_id={forward_info['thread_id']}, "
        f"bot_is_member={forward_info.get('bot_is_member', False)}"
    )

    # Get user language
    lang = await get_user_language(user_id)

    # Display forwarding information to user
    forward_display = format_forward_info_message(forward_info, lang)
    if forward_display:
        await message.answer(forward_display, parse_mode="HTML")
    else:
        # If no forward info extracted (shouldn't happen, but just in case)
        await message.answer("📨 <b>Forwarded Message Received</b>", parse_mode="HTML")

    # Auto-add group if conditions are met
    group_added = False
    if (forward_info["origin_type"] == "chat" and
        forward_info["origin_id"] and
        forward_info.get("bot_is_member", False)):

        logger.info(f"🤖 Attempting to auto-add group {forward_info['origin_id']} to user {user_id}")

        group_added = await auto_add_group_from_forward(
            user_id=user_id,
            group_id=forward_info["origin_id"],
            group_name=forward_info["origin_name"] or f"Group {forward_info['origin_id']}",
            bot=message.bot
        )

        if group_added:
            # Show notification to user
            await show_group_addition_notification(message, forward_info, True, lang)
        else:
            # Show why group wasn't added (optional - can be removed for cleaner UX)
            logger.debug(f"Group {forward_info['origin_id']} was not auto-added for user {user_id}")

    # Note: If forwarded from a group where bot is NOT a member, Telegram doesn't
    # provide group ID for privacy reasons. Only the user who forwarded it is visible.
    # Group/thread ID will only show if the bot is a member of that group.

    # Show typing indicator
    try:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    except Exception as e:
        logger.debug(f"Skipped typing action: {e}")

    try:
        # Get services
        llm_service = get_llm_service()
        thread_service = get_thread_service()
        message_state_service = get_message_state_service()

        # Get or create active thread
        thread_id = await thread_service.get_active_thread(user_id)

        if not thread_id:
            # Create new thread for forwarded message analysis
            thread = await thread_service.create_thread(user_id, "Forwarded Messages")
            thread_id = thread.thread_id
            logger.info(f"✨ Created new thread for forwarded messages: {thread_id}")

        # Get thread object
        thread = await thread_service.get_thread(thread_id)

        # Format message with forwarding context for LLM
        llm_input = format_forward_context_for_llm(forward_info, text)

        logger.info(f"🤖 Sending forwarded message to LLM with context: {len(llm_input)} chars")

        # Send "thinking" message
        bot_message = await message.answer("🤔")

        # Track this message for updates
        await message_state_service.save_message(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=bot_message.message_id,
            message_type="thinking",
            original_text="🤔"
        )

        # Stream LLM response with configurable streaming
        full_response = ""  # Initialize accumulator
        last_tool_emoji = None

        # Throttling variables for streaming mode
        import time
        last_update_time = time.time()
        last_update_length = 0
        last_sent_text = ""
        edit_count = 0

        async for chunk in llm_service.stream_response(llm_input, user_id, thread_id, thread=thread):
            # Check if chunk is a tool notification dict
            if isinstance(chunk, dict) and chunk.get("type") == "tool_notification":
                # Edit message to show tool emoji
                tool_emoji = chunk.get("text", "🔧")
                last_tool_emoji = tool_emoji

                try:
                    await message.bot.edit_message_text(
                        text=tool_emoji,
                        chat_id=message.chat.id,
                        message_id=bot_message.message_id
                    )
                    logger.info(f"✏️  Edited message to show tool: {chunk.get('tool_name')} ({tool_emoji})")
                except Exception as e:
                    if "message is not modified" not in str(e).lower():
                        logger.debug(f"Failed to edit message: {e}")
                continue

            # Regular text chunk (string) - ACCUMULATE, don't replace!
            if isinstance(chunk, str):
                full_response += chunk

                # STREAMING MODE: Check if we should send an intermediate update
                from luka_bot.core.config import settings
                if settings.STREAMING_ENABLED:
                    current_time = time.time()
                    # Don't escape HTML if response contains KB snippets (they have proper HTML formatting)
                    has_kb_snippets = '━━━━━━━━━━━━━━━━━━━━' in full_response
                    current_text = full_response if has_kb_snippets else escape_html(full_response)
                    time_elapsed = current_time - last_update_time
                    length_delta = len(current_text) - last_update_length

                    # Update if:
                    # 1. Enough time has passed AND enough chars accumulated
                    # 2. AND the formatted text actually changed (avoid duplicate edits)
                    if (time_elapsed >= settings.STREAMING_UPDATE_INTERVAL and
                        length_delta >= settings.STREAMING_MIN_CHUNK_SIZE and
                        current_text != last_sent_text):

                        try:
                            await edit_and_send_parts(bot_message, current_text)
                            last_update_time = current_time
                            last_update_length = len(current_text)
                            last_sent_text = current_text
                            edit_count += 1
                            logger.debug(f"🔄 Streaming update #{edit_count}: {len(current_text)} chars ({length_delta} delta)")
                        except Exception as edit_error:
                            logger.debug(f"Skipped streaming edit: {edit_error}")

                # NON-STREAMING MODE: Just accumulate, don't send intermediate updates
                # (final update happens below)

        # Clear tracked message
        await message_state_service.clear_message(user_id)

        # Final update with complete response (always, regardless of streaming mode)
        try:
            from luka_bot.core.config import settings
            # Don't escape HTML if response contains KB snippets (they have proper HTML formatting)
            has_kb_snippets = '━━━━━━━━━━━━━━━━━━━━' in full_response
            if has_kb_snippets:
                # KB snippets already have proper HTML formatting with <a href> tags
                formatted_response = full_response
            else:
                # Regular response - escape HTML for safety
                formatted_response = escape_html(full_response)

            # Only send if text changed from last update (avoid duplicate)
            if formatted_response != last_sent_text:
                await edit_and_send_parts(bot_message, formatted_response)
                edit_count += 1

            # Log summary
            if settings.STREAMING_ENABLED:
                logger.info(f"✅ Forwarded message analysis complete: {len(full_response)} chars, {edit_count} edits")
            else:
                logger.info(f"✅ Forwarded message analysis complete: {len(full_response)} chars, non-streaming mode")
        except Exception as e:
            logger.warning(f"⚠️  Failed final update: {e}")

        # Update thread activity
        if thread:
            thread.update_activity()
            await thread_service.update_thread(thread)

    except Exception as e:
        logger.error(f"❌ Error handling forwarded message: {e}", exc_info=True)
        await message.answer(
            "❌ Sorry, I encountered an error while analyzing the forwarded message. Please try again."
        )

