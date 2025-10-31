"""
Streaming DM handler - Phase 3 with lazy thread creation.

Phase 2: Basic streaming
Phase 3: Thread-scoped conversations + lazy thread creation
Phase 4: Groups navigation support
Phase 5: Configurable streaming with throttling
"""
import asyncio
import time
from datetime import datetime

from aiogram import F, Router
from aiogram.enums import ChatAction, ChatType
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from luka_bot.core.config import settings
from luka_bot.core.loader import redis_client
from luka_bot.handlers.keyboard_actions import ThreadCreationStates
from luka_bot.handlers.states import NavigationStates
from luka_bot.keyboards.threads_menu import get_threads_keyboard
from luka_bot.services.divider_service import send_thread_divider
from luka_bot.services.group_service import get_group_service
from luka_bot.services.group_thread_service import get_group_thread_service
from luka_bot.services.llm_service import get_llm_service
from luka_bot.services.message_state_service import get_message_state_service
from luka_bot.services.messaging_service import edit_and_send_parts
from luka_bot.services.thread_name_generator import generate_thread_name
from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.user_profile_service import get_user_profile_service
from luka_bot.utils.formatting import escape_html
from luka_bot.utils.i18n_helper import _


# Form filtering is handled by handler registration order and backup guard
# processes_router (form handlers) is registered before streaming_router
# If a form handler matches, it consumes the update before streaming handlers run


router = Router()


# Note: Custom PrivateChatFilter removed in favor of aiogram's built-in F.chat.type filter
# The custom filter was unreliable and caused group messages to leak through to DM handlers
# See: /docs/issues/group-message-filter-bug.md


async def handle_group_selection_in_streaming(message: Message, state: FSMContext, group_id: int) -> None:
    """
    Handle group selection when detected in streaming handler.
    
    This is a fallback when GroupSelectionFilter doesn't catch the message.
    """
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return

    logger.info(f"🔀 Handling group selection in streaming: user {user_id}, group {group_id}")

    try:
        # Get user language
        from luka_bot.utils.i18n_helper import get_user_language
        lang = await get_user_language(user_id)

        # Create or get user's thread for this group
        group_thread_service = await get_group_thread_service()
        user_group_thread = await group_thread_service.get_or_create_user_group_thread(
            user_id=user_id,
            group_id=group_id
        )

        # Set as active thread
        thread_service = get_thread_service()
        await thread_service.set_active_thread(user_id, user_group_thread.thread_id)

        # IMPORTANT: Ensure we stay in groups_mode
        await state.set_state(NavigationStates.groups_mode)

        # Update state with current group
        await state.update_data(current_group_id=group_id)

        # Rebuild keyboard with new selection
        group_service = await get_group_service()
        groups = await group_service.list_user_groups(user_id, active_only=True)

        from luka_bot.keyboards.groups_menu import get_groups_keyboard
        keyboard = await get_groups_keyboard(
            groups=groups,
            current_group_id=group_id,
            language=lang
        )

        from luka_bot.utils.i18n_helper import _
        intro_text = _('groups.intro', lang, count=len(groups))
        await message.answer(intro_text, parse_mode="HTML", reply_markup=keyboard)

        # Send GROUP divider with updated inline controls
        from luka_bot.services.group_divider_service import send_group_divider
        await send_group_divider(
            user_id=user_id,
            group_id=group_id,
            divider_type="switch",
            bot=message.bot
        )

        logger.info(f"✅ Switched to group {group_id} for user {user_id} (via streaming handler)")

    except Exception as e:
        logger.error(f"❌ Error switching group in streaming handler: {e}", exc_info=True)
        await message.answer("❌ Error switching group. Please try again.")


async def handle_group_aware_message(message: Message, state: FSMContext) -> None:
    """
    Handle messages when user is in groups mode.

    Converses with group-aware AI agent that has:
    - Group knowledge base access
    - Group context (info, stats, recent messages)
    - User's question history in this group context
    """
    user_id = message.from_user.id if message.from_user else None
    text = message.text or ""

    if not user_id or not text:
        return

    # SAFETY CHECK: This handler should ONLY be called for private chats
    # Group-aware mode means user is chatting about a group FROM their DM
    if message.chat.type in ("group", "supergroup"):
        logger.error(f"🚨 CRITICAL: handle_group_aware_message called with GROUP message! chat_id={message.chat.id}")
        logger.error("🚨 This should NEVER happen - responses would go to the group instead of DM!")
        return

    logger.info(f"💬🏘 Group-aware message from user {user_id}: {text[:50]}...")
    logger.debug(f"🔍 Group-aware message source: chat_id={message.chat.id}, chat_type={message.chat.type}")

    # Skip all keyboard button filtering if user is filling a form
    # Check for TRUTHY values, not just key existence (keys may exist with None values after form completion)
    data = await state.get_data()
    if data.get("form_context") or data.get("start_form") or data.get("task_dialog"):
        logger.info(f"⏭️ GROUP_AWARE: Skipping button filters - user {user_id} is filling a form (text='{text[:50]}')")
        return  # Let the form handler process it

    # Filter out keyboard button texts - don't send to LLM
    if text:
        # Check if message is a keyboard button selection
        from luka_bot.keyboards.groups_menu import is_control_button
        from luka_bot.keyboards.threads_menu import is_thread_button

        # Get user's groups and threads for comparison
        group_service = await get_group_service()
        groups = await group_service.list_user_groups(user_id, active_only=True)

        thread_service = get_thread_service()
        threads = await thread_service.list_threads(user_id)

        # Check if text matches any keyboard button
        if is_control_button(text):
            logger.info(f"⚠️ Filtered control button from LLM: {text}")
            return

        # Check if text is a group selection button
        from luka_bot.keyboards.groups_menu import is_group_button
        group_id = await is_group_button(text, groups)
        if group_id:
            logger.info(f"🔀 Group selection detected: {text} -> group {group_id}")
            # Handle group selection here instead of filtering it out
            await handle_group_selection_in_streaming(message, state, group_id)
            return

        # Check if text is a thread selection button
        if is_thread_button(text, threads):
            logger.info(f"⚠️ Filtered thread selection from LLM: {text}")
            return

        # Check for common keyboard button patterns
        button_patterns = [
            "💬", "📋", "👤", "🏠", "❌",  # Navigation emojis
            "⚙️", "🌐", "🎯",  # Scope controls
            "➕ New", "➕ Начать",  # New item buttons
            "🏘 Groups", "🏘 Группы",  # Section headers
        ]
        if any(pattern in text for pattern in button_patterns):
            logger.info(f"⚠️ Filtered keyboard button from LLM: {text}")
            return

    try:
        # Get current group from state
        state_data = await state.get_data()
        current_group_id = state_data.get("current_group_id")

        if not current_group_id:
            logger.warning(f"⚠️ No current group ID in state for user {user_id}")
            await message.answer("⚠️ Please select a group first.")
            return

        # Get services
        llm_service = get_llm_service()
        thread_service = get_thread_service()
        group_thread_service = await get_group_thread_service()

        # Get user-group thread
        user_group_thread = await group_thread_service.get_or_create_user_group_thread(
            user_id=user_id,
            group_id=current_group_id
        )

        thread_id = user_group_thread.thread_id

        # Send initial message
        bot_message = await message.answer("🤔")

        # Track message for editing
        message_state_service = get_message_state_service()
        await message_state_service.save_message(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=bot_message.message_id,
            message_type="thinking",
            original_text="🤔"
        )

        # Stream response with group context
        response_chunks = []

        # Throttling variables for streaming mode
        last_update_time = time.time()
        last_update_length = 0
        last_sent_text = ""
        edit_count = 0

        async for chunk in llm_service.stream_response(
            user_message=text,
            user_id=user_id,
            thread_id=thread_id,
            thread=user_group_thread,  # Pass thread with group context
            save_history=True
        ):
            # Handle tool notifications (dicts)
            if isinstance(chunk, dict) and chunk.get("type") == "tool_notification":
                tool_emoji = chunk.get("text", "🔧")
                try:
                    await bot_message.edit_text(tool_emoji)
                except Exception as e:
                    logger.debug(f"Skipped tool notification edit: {e}")
                continue

            # Only collect string chunks
            if isinstance(chunk, str):
                response_chunks.append(chunk)

                # STREAMING MODE: Check if we should send an intermediate update
                if settings.STREAMING_ENABLED:
                    current_time = time.time()
                    full_response_so_far = "".join(response_chunks)
                    # Don't escape HTML if response contains KB snippets (they have proper HTML formatting)
                    has_kb_snippets = '━━━━━━━━━━━━━━━━━━━━' in full_response_so_far
                    current_text = full_response_so_far if has_kb_snippets else escape_html(full_response_so_far)
                    time_elapsed = current_time - last_update_time
                    length_delta = len(current_text) - last_update_length

                    # Update if:
                    # 1. Enough time has passed AND enough chars accumulated
                    # 2. AND the formatted text actually changed (avoid duplicate edits)
                    if (time_elapsed >= settings.STREAMING_UPDATE_INTERVAL and
                        length_delta >= settings.STREAMING_MIN_CHUNK_SIZE and
                        current_text != last_sent_text):

                        try:
                            await edit_and_send_parts(
                                initial_message=bot_message,
                                html_text=current_text
                            )
                            last_update_time = current_time
                            last_update_length = len(current_text)
                            last_sent_text = current_text
                            edit_count += 1
                            logger.debug(f"🔄 Streaming update #{edit_count}: {len(current_text)} chars ({length_delta} delta)")
                        except Exception as edit_error:
                            logger.debug(f"Skipped streaming edit: {edit_error}")

                # NON-STREAMING MODE: Just accumulate, don't send intermediate updates
                # (final update happens below)

        # Final response (only string chunks)
        final_response = "".join(response_chunks)
        # Don't escape HTML if response contains KB snippets (they have proper HTML formatting)
        has_kb_snippets = '━━━━━━━━━━━━━━━━━━━━' in final_response
        if has_kb_snippets:
            # KB snippets already have proper HTML formatting with <a href> tags
            formatted_response = final_response
        else:
            # Regular response - escape HTML for safety
            formatted_response = escape_html(final_response)

        # Send final message (always, regardless of streaming mode)
        try:
            # Only send if text changed from last update (avoid duplicate)
            if formatted_response != last_sent_text:
                await edit_and_send_parts(
                    initial_message=bot_message,
                    html_text=formatted_response
                )
                edit_count += 1

            # Log summary
            if settings.STREAMING_ENABLED:
                logger.info(f"✅🏘 Group-aware streaming complete: {len(final_response)} chars, {edit_count} edits")
            else:
                logger.info(f"✅🏘 Group-aware response complete: {len(final_response)} chars, non-streaming mode")
        except Exception:
            pass  # Best effort

        # Update thread metadata (timestamp)
        thread = await thread_service.get_thread(thread_id)
        if thread:
            from datetime import datetime
            thread.updated_at = datetime.utcnow()
            thread.message_count += 1
            await thread_service.update_thread(thread)

        logger.info(f"✅🏘 Group-aware conversation complete for user {user_id} in group {current_group_id}")

    except Exception as e:
        logger.error(f"❌ Error in group-aware message handling: {e}", exc_info=True)
        try:
            await message.answer("❌ Sorry, I encountered an error. Please try again.")
        except:
            pass


@router.message(~F.chat.type.in_({"group", "supergroup", "channel"}), F.text)
async def handle_streaming_message(message: Message, state: FSMContext) -> None:
    """
    Handle text messages in DM with streaming LLM responses.

    Phase 3: Thread-scoped conversations + lazy thread creation
    - Creates thread ONLY on first message (lazy creation)
    - Generates thread name from first message
    - Uses active thread for context
    - Updates thread activity

    Phase 4: Groups navigation support
    - Detects groups_mode and routes to group-aware handler

    Note: Uses negation filter ~F.chat.type.in_() to explicitly exclude groups/supergroups/channels.
    This is more reliable than equality checks with ChatType.PRIVATE in aiogram 3.x.
    Previous approaches (custom filter and F.chat.type == ChatType.PRIVATE) both failed.
    
    Phase 5: Form input exclusion
    - Uses NotFillingFormFilter() to prevent matching when user is filling a form
    - This allows form handlers to process the message instead
    """
    user_id = message.from_user.id if message.from_user else None
    text = message.text or ""

    if not user_id or not text:
        return

    # CHECK: If form is active, log and skip LLM processing
    # Form handlers in processes_router should match first (registered before streaming_router)
    # However, if this handler matched first, we log it and skip processing
    # Check for TRUTHY values, not just key existence (keys may exist with None values after form completion)
    data = await state.get_data()
    if data.get("form_context") or data.get("start_form") or data.get("task_dialog"):
        logger.warning(
            f"⚠️ STREAMING_DM: Handler matched while form active for user {user_id} "
            f"(text length={len(text)}). This shouldn't happen - form handler should match first. "
            f"Update has been consumed by this handler."
        )
        return  # Skip processing but update is already consumed

    # WORKAROUND: If this is a group message, route it to the group handler
    if message.chat.type in ("group", "supergroup"):
        logger.warning(f"⚠️ STREAMING_DM received group message - routing to group handler")
        logger.warning(f"   chat_id={message.chat.id}, type={message.chat.type}, text='{text[:50]}'")

        # Import and call the group handler directly
        from luka_bot.handlers.group_messages import handle_group_message
        await handle_group_message(message)
        return
    
    # Debug: Log successful private chat message acceptance
    logger.debug(f"✅ STREAMING_DM: Accepted private chat message from user {user_id}: {text[:50]}...")

    logger.info(f"💬 Streaming message from user {user_id}: {text[:50]}...")
    logger.debug(f"🔍 Message source: chat_id={message.chat.id}, chat_type={message.chat.type}")

    # Show typing indicator (with rate limit protection)
    try:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    except Exception as e:
        logger.debug(f"Skipped typing action: {e}")

    try:
        # Get services
        llm_service = get_llm_service()
        thread_service = get_thread_service()

        # Check FSM state - are we waiting for first message?
        current_state = await state.get_state()

        # NEW: Check if user is in groups mode - route to group-aware handler
        if current_state == NavigationStates.groups_mode:
            await handle_group_aware_message(message, state)
            return

        if current_state == ThreadCreationStates.waiting_for_first_message:
            # LAZY THREAD CREATION - User's first message!
            logger.info(f"✨ First message detected for user {user_id} - creating thread")

            # Use Redis lock to prevent race conditions
            lock_key = f"thread_creation_lock:{user_id}"

            # Try to acquire lock
            lock_acquired = await redis_client.set(lock_key, "locked", ex=5, nx=True)

            if lock_acquired:
                try:
                    # FIX 4: Create thread with temporary name FIRST (before streaming)
                    # This prevents interference with LLM streaming
                    temp_thread_name = "New Chat"
                    thread = await thread_service.create_thread(user_id, temp_thread_name)
                    thread_id = thread.thread_id

                    # Clear FSM state
                    await state.clear()

                    # Get user language for Step 2 confirmation
                    profile_service = get_user_profile_service()
                    lang = await profile_service.get_language(user_id)

                    # Send Step 2 confirmation (onboarding completion)
                    step2_text = _('onboarding.step2_confirmation', lang)
                    await message.answer(step2_text, parse_mode="HTML")

                    # Prepare keyboard with new thread
                    threads = await thread_service.list_threads(user_id)
                    keyboard = await get_threads_keyboard(threads, thread_id, lang)

                    # Send divider for new thread with updated keyboard
                    await send_thread_divider(
                        user_id,
                        thread_id,
                        divider_type="new",
                        bot=message.bot,
                        reply_markup=keyboard
                    )

                    logger.info(f"✅ Created thread {thread_id}, sent Step 2 confirmation, will generate real name after streaming")

                finally:
                    # Release lock
                    await redis_client.delete(lock_key)
            else:
                # Lock not acquired - another request is creating thread
                # Wait a moment and get the thread
                logger.info(f"⏳ Waiting for thread creation lock for user {user_id}")
                await asyncio.sleep(0.5)
                thread_id = await thread_service.get_active_thread(user_id)

                if not thread_id:
                    # Fallback: create with generic name
                    thread = await thread_service.create_thread(user_id, "Quick Chat")
                    thread_id = thread.thread_id
                    logger.warning(f"⚠️  Fallback thread created for user {user_id}")

        else:
            # Normal flow - get active thread
            thread_id = await thread_service.get_active_thread(user_id)

            if not thread_id:
                # Shouldn't happen, but fallback just in case
                thread = await thread_service.create_thread(user_id, "New Chat")
                thread_id = thread.thread_id
                logger.warning(f"⚠️  No active thread found, created fallback for user {user_id}")

        # Get thread object for settings (Phase 4)
        thread = await thread_service.get_thread(thread_id) if thread_id else None

        # Send initial message
        bot_message = await message.answer("🤔")

        # Track message for editing (Phase 4+: Tool notifications)
        message_state_service = get_message_state_service()
        await message_state_service.save_message(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=bot_message.message_id,
            message_type="thinking",
            original_text="🤔"
        )

        # Stream response with thread context and settings (Phase 4)
        # Phase 5: Configurable streaming with throttling
        full_response = ""  # Initialize accumulator
        last_tool_emoji = None

        # Throttling variables for streaming mode
        last_update_time = time.time()
        last_update_length = 0
        last_sent_text = ""
        edit_count = 0

        async for chunk in llm_service.stream_response(text, user_id, thread_id, thread=thread):
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
                    # Ignore "message is not modified" errors
                    if "message is not modified" not in str(e).lower():
                        logger.debug(f"Failed to edit message: {e}")
                continue

            # Regular text chunk (string) - ACCUMULATE, don't replace!
            if isinstance(chunk, str):
                full_response += chunk

                # STREAMING MODE: Check if we should send an intermediate update
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

        # Clear tracked message after streaming
        await message_state_service.clear_message(user_id)

        # Final update with complete response (always, regardless of streaming mode)
        try:
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
                logger.info(f"✅ Streaming complete: {len(full_response)} chars, {edit_count} edits")
            else:
                logger.info(f"✅ Response complete: {len(full_response)} chars, non-streaming mode")
        except Exception as e:
            logger.warning(f"⚠️  Failed final update: {e}")

        # FIX 4: Generate thread name AFTER streaming completes (for first messages)
        # This avoids interference with the LLM streaming process
        # Note: We check the thread name instead of FSM state since state was cleared earlier
        try:
            thread = await thread_service.get_thread(thread_id)
            if thread and thread.name == "New Chat":
                # Generate proper thread name from first message
                thread_name = await generate_thread_name(text, language="en")
                logger.info(f"📝 Generated thread name AFTER streaming: '{thread_name}' from '{text[:30]}...'")

                # Update thread with real name
                thread.name = thread_name
                await thread_service.update_thread(thread)
                logger.info(f"✅ Updated thread {thread_id} with generated name")
        except Exception as e:
            logger.warning(f"⚠️  Failed to generate/update thread name: {e}")

        # Update thread activity and keyboard
        try:
            thread = await thread_service.get_thread(thread_id)
            if thread:
                thread.update_activity()
                await thread_service.update_thread(thread)

                # Update reply keyboard to show updated thread info
                # Send as invisible update by editing user's original message keyboard
                threads = await thread_service.list_threads(user_id)
                keyboard = await get_threads_keyboard(threads, thread_id)

                try:
                    # Try to update the keyboard on user's message
                    await message.edit_reply_markup(reply_markup=keyboard)
                except:
                    # If that fails (message too old), keyboard will update on next user message
                    pass
        except Exception as e:
            logger.warning(f"⚠️  Failed to update thread activity: {e}")
        
        # Double-write: Index message to ES and send to Camunda
        try:
            # Import utilities for double-write
            from luka_bot.utils.document_id_generator import DocumentIDGenerator
            from luka_bot.services.camunda_service import get_camunda_service
            from luka_bot.services.elasticsearch_service import get_elasticsearch_service
            from luka_bot.services.user_profile_service import get_user_profile_service
            
            # Check if ES is enabled
            if not settings.ELASTICSEARCH_ENABLED:
                logger.debug("⏭️ ES disabled, skipping double-write")
                return
            
            # Get user KB index
            profile_service = get_user_profile_service()
            user_profile = await profile_service.get_profile(user_id)
            kb_index = user_profile.kb_index
            
            # Generate document ID upfront
            kb_doc_id = DocumentIDGenerator.generate_dm_message_id(
                user_id=user_id,
                thread_id=thread_id,
                telegram_message_id=message.message_id
            )
            
            # Prepare message data
            # Extract parent message details for replies
            parent_message_text = None
            parent_message_id = None
            parent_message_user_id = None
            if message.reply_to_message:
                parent_message_text = message.reply_to_message.text or message.reply_to_message.caption
                parent_message_id = str(message.reply_to_message.message_id)
                parent_message_user_id = str(message.reply_to_message.from_user.id) if message.reply_to_message.from_user else None

            message_data = {
                "message_id": kb_doc_id,  # Use generated document ID
                "user_id": str(user_id),
                "thread_id": thread_id,
                "telegram_topic_id": None,  # DMs don't have topics
                "role": "user",  # DM messages are always from users
                "message_text": text,
                "message_date": message.date.isoformat() if message.date else datetime.utcnow().isoformat(),
                "sender_name": message.from_user.full_name if message.from_user else "Unknown",
                "reply_to_message_id": str(message.reply_to_message.message_id) if message.reply_to_message else "",
                "parent_message_text": parent_message_text,
                "parent_message_id": parent_message_id,
                "parent_message_user_id": parent_message_user_id,
                "mentions": [],  # DM messages don't have mentions
                "hashtags": [],  # DM messages don't have hashtags
                "urls": [],  # DM messages don't have URLs
                "media_type": message.content_type or "text",
            }
            
            # Enhance message data with thread context
            camunda_service = get_camunda_service()
            enhanced_message_data = await camunda_service._build_enhanced_message_data(message_data, thread)
            
            # Double-write: Call both services asynchronously
            es_task = None
            camunda_task = None
            
            try:
                # Start both operations asynchronously
                if settings.ELASTICSEARCH_ENABLED:
                    es_service = await get_elasticsearch_service()
                    es_task = asyncio.create_task(
                        es_service.index_message_immediate(
                            index_name=kb_index,
                            message_data=enhanced_message_data,
                            document_id=kb_doc_id
                        )
                    )
                
                if settings.CAMUNDA_ENABLED and settings.CAMUNDA_MESSAGE_CORRELATION_ENABLED:
                    camunda_task = asyncio.create_task(
                        camunda_service.correlate_message(
                            telegram_user_id=user_id,
                            message_data=enhanced_message_data,
                            message_type="DM_MESSAGE",
                            kb_doc_id=kb_doc_id
                        )
                    )
                
                # Wait for both to complete
                es_success = False
                camunda_success = False
                
                if es_task:
                    es_success = await es_task
                if camunda_task:
                    camunda_success = await camunda_task
                
                # Log results
                if es_success and camunda_success:
                    logger.info(f"✅ Double-write successful: {kb_doc_id}")
                elif es_success:
                    logger.warning(f"⚠️ ES success, Camunda failed: {kb_doc_id}")
                elif camunda_success:
                    logger.warning(f"⚠️ Camunda success, ES failed: {kb_doc_id}")
                else:
                    logger.error(f"❌ Double-write failed: {kb_doc_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error in double-write: {e}")
                # Cancel any pending tasks
                if es_task and not es_task.done():
                    es_task.cancel()
                if camunda_task and not camunda_task.done():
                    camunda_task.cancel()
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to perform double-write: {e}")

    except Exception as e:
        logger.error(f"❌ Streaming error: {e}")

        # Send error message
        error_msg = """❌ Sorry, I encountered an error processing your message.

Please try again or use /start to restart."""

        try:
            if 'bot_message' in locals():
                await bot_message.edit_text(error_msg)
            else:
                await message.answer(error_msg)
        except:
            pass

