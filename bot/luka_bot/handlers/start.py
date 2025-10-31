"""
/start command handler - Phase 4 with onboarding check.

Shows welcome message or onboarding for new users.
Phase 4: Check UserProfile.is_blocked for onboarding state.
Phase 4: i18n support via i18n_helper.
"""
import asyncio
from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.core.config import settings
from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.user_profile_service import get_user_profile_service
from luka_bot.services.welcome_prompts import get_welcome_message
from luka_bot.services.prompt_pool_service import get_prompt_pool_service, PromptOption
from luka_bot.services.user_kb_scope_service import get_user_kb_scope_service
from luka_bot.services.chatbot_boot_service import ensure_chatbot_start_running
from luka_bot.keyboards.threads_menu import get_threads_keyboard, get_empty_state_keyboard
from luka_bot.keyboards.mode_reply import get_start_mode_keyboard
from luka_bot.handlers.keyboard_actions import ThreadCreationStates
from luka_bot.handlers.states import NavigationStates
from luka_bot.utils.i18n_helper import _, get_error_message

router = Router()


# Old inline keyboard functions removed - now using reply keyboard
# See luka_bot/keyboards/start_menu.py for new implementation


async def _delete_keyboard_setup_message(msg) -> None:
    """Helper to delete keyboard setup message after a delay."""
    await asyncio.sleep(2)  # Wait 2 seconds
    try:
        await msg.delete()
    except Exception:
        pass  # Ignore if already deleted


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext, command: CommandObject = None) -> None:
    """
    Handle /start command with onboarding check and deep link support.
    
    Phase 4: Check if user needs onboarding first.
    If onboarding needed (is_blocked = False), show welcome + language selector.
    Otherwise, show threads or actions menu.
    
    Deep link support:
    - /start group_{group_id} - User came from a group
    - /start admin_{group_id} - Admin came from a group
    - /start topic_{group_id}_{topic_id} - User came from a topic
    """
    user_id = message.from_user.id if message.from_user else None
    username = message.from_user.username if message.from_user else "User"
    first_name = message.from_user.first_name if message.from_user else ""
    
    if not user_id:
        return
    
    # Parse deep link payload
    payload = command.args if command and command.args else None
    logger.info(f"👋 /start from user {user_id} (@{username}), payload: {payload}")
    
    # Check if this is a guest user (user_id = 0 means guest)
    if user_id == 0:
        await handle_guest_start(message, state)
        return
    
    try:
        # Get or create user profile (Phase 4)
        profile_service = get_user_profile_service()
        profile = await profile_service.get_or_create_profile(user_id, message.from_user)
        
        # Check if user needs onboarding
        if profile.needs_onboarding():
            # Show onboarding welcome message (with context if from group)
            logger.info(f"✨ New user {user_id} needs onboarding")
            await show_onboarding_welcome(message, profile, payload)
            return
        
        # Handle deep link payloads for registered users
        if payload:
            handled = await handle_deep_link_payload(message, state, payload, profile)
            if handled:
                return
        
        # User has completed onboarding - show simplified onboarding intro + compact menu
        logger.info(f"📋 User {user_id} has completed onboarding - showing simplified start menu")
        
        # Clear any form state to prevent stuck/mixed states
        data = await state.get_data()
        form_state_cleared = False
        if "form_context" in data or "start_form" in data or "task_dialog" in data:
            logger.info(f"🧹 Clearing form state for user {user_id} (triggered by /start)")
            data_copy = dict(data)
            # Remove all form-related keys
            data_copy.pop("form_context", None)
            data_copy.pop("start_form", None)
            data_copy.pop("task_dialog", None)
            await state.set_data(data_copy)
            form_state_cleared = True
        
        # Set navigation state to groups_mode (since we show groups keyboard)
        await state.set_state(NavigationStates.groups_mode)
        
        if form_state_cleared:
            logger.debug(f"✅ Form state cleared - user {user_id} can now interact normally")
        
        bot_name = settings.LUKA_NAME
        lang = profile.language
        
        # Build welcome text (no Quick Actions here)
        welcome_text = f"""{_('actions.welcome', lang, first_name=first_name)}

{_('actions.intro', lang, bot_name=bot_name)}"""
        
        # Get groups for KB scope and prompts personalization
        from luka_bot.services.group_service import get_group_service
        
        group_service = await get_group_service()
        group_links = await group_service.list_user_groups(user_id, active_only=True)
        
        # Add quick prompt keyboard and KB scope functionality
        try:
            # Check if chatbot_start process exists before trying to start it
            from luka_bot.services.process_definition_cache import get_process_definition_cache

            process_cache = get_process_definition_cache()
            has_chatbot_start = process_cache.has_process("chatbot_start")

            if has_chatbot_start:
                # Start chatbot_start BPMN in background
                asyncio.create_task(ensure_chatbot_start_running(
                    user_id=str(user_id),
                    telegram_user_id=user_id,
                    chat_id=message.chat.id
                ))
            else:
                logger.debug(f"chatbot_start process not deployed - skipping process start for user {user_id}")

            # Get group names for prompt personalization
            group_names = []
            for link in group_links:
                try:
                    metadata = await group_service.get_cached_group_metadata(link.group_id)
                    if metadata and metadata.group_title:
                        group_names.append(metadata.group_title)
                except Exception as e:
                    logger.debug(f"Could not get metadata for group {link.group_id}: {e}")
                    # Fallback to group ID if metadata unavailable
                    group_names.append(f"Group {link.group_id}")
            
            # Get quick prompts
            prompt_service = get_prompt_pool_service()
            prompt_options = await prompt_service.get_quick_prompts(
                locale=lang, 
                group_names=group_names, 
                count=3
            )
            
            # Store prompts in FSM state for callback handling
            if prompt_options:
                await state.update_data(quick_prompts=[option.text for option in prompt_options])
            else:
                await state.update_data(quick_prompts=[])
            
            # Set up KB scope
            scope_service = get_user_kb_scope_service()
            available_group_ids = [str(link.group_id) for link in group_links if link.group_id]
            scope = await scope_service.refresh_scope_from_groups(user_id, available_group_ids)
            await state.update_data(kb_scope=scope.to_dict())
            
            # Build and send start reply keyboard (prompts + emoji scope controls)
            from luka_bot.keyboards.start_menu import build_start_reply_keyboard
            
            start_keyboard = await build_start_reply_keyboard(
                prompt_options or [],
                include_scope_controls=bool(group_links),
                language=lang
            )
            
            # Fetch Camunda tasks first (before sending welcome message)
            tasks_inline = None
            if has_chatbot_start:
                try:
                    from luka_bot.keyboards.camunda_tasks_inline import build_camunda_tasks_inline_keyboard
                    from luka_bot.services.camunda_service import CamundaService

                    camunda_service = CamundaService.get_instance()
                    # Filter tasks to only show chatbot_start tasks
                    user_tasks = await camunda_service.get_user_tasks(
                        user_id,
                        process_definition_key="chatbot_start"
                    )

                    tasks_inline = await build_camunda_tasks_inline_keyboard(
                        user_tasks,
                        language=lang
                    )

                    logger.info(f"📋 Built inline keyboard with {len(user_tasks)} chatbot_start tasks for user {user_id}")
                except Exception as camunda_error:
                    logger.warning(f"Failed to fetch Camunda tasks for user {user_id}: {camunda_error}")
                    tasks_inline = None
            
            # Send welcome message with tasks inline keyboard (if available)
            if tasks_inline:
                # Send welcome message with tasks inline keyboard attached
                welcome_msg = await message.answer(
                    welcome_text,
                    reply_markup=tasks_inline,
                    parse_mode="HTML"
                )
                logger.info(f"📋 Sent welcome message with tasks inline keyboard to user {user_id}")
            else:
                # No tasks - send welcome with reply keyboard only
                welcome_msg = await message.answer(
                    welcome_text,
                    reply_markup=start_keyboard,
                    parse_mode="HTML"
                )
                logger.info(f"📝 Sent welcome message with start reply keyboard to user {user_id}")
            
            # Set reply keyboard at chat level (separate from inline keyboard)
            # Reply keyboards persist at chat level, so we set it separately
            if tasks_inline:
                # Tasks menu is on welcome message, so set reply keyboard separately
                # Send minimal message to activate reply keyboard (will be auto-deleted)
                kb_msg = await message.answer(
                    " ",  # Minimal space character
                    reply_markup=start_keyboard
                )
                # Delete the keyboard setup message after a brief delay
                # (Bot can't delete its own message immediately)
                asyncio.create_task(_delete_keyboard_setup_message(kb_msg))
        
        except Exception as e:
            logger.warning(f"Failed to add quick prompts for user {user_id}: {e}")
    
    except Exception as e:
        logger.error(f"❌ Error in /start handler: {e}")
        error_msg = get_error_message("generic", "en")  # Fallback to EN if profile unavailable
        await message.answer(error_msg)
    
    logger.info(f"✅ /start completed for user {user_id}")


# ============================================================================
# Phase 4: Onboarding
# ============================================================================

async def handle_deep_link_payload(message: Message, state: FSMContext, payload: str, profile) -> bool:
    """
    Handle deep link payloads for registered users.
    
    Args:
        message: Telegram message
        state: FSM context
        payload: Deep link payload (e.g., "group_123", "admin_456")
        profile: UserProfile instance
        
    Returns:
        True if handled, False otherwise
    """
    user_id = profile.user_id
    lang = profile.language
    
    try:
        if payload.startswith("group_"):
            # Check if this is a group authentication request
            if "_auth" in payload:
                # Handle group authentication deep link: group_{group_id}_auth&user_from={user_id}&group_connect={group_id}&thread_id={thread_id}
                logger.info(f"🔗 Deep link accessed by user {user_id}: {payload}")
                
                # Parse the enhanced deep link format
                parts = payload.split("&")
                group_part = parts[0]  # group_{group_id}_auth
                group_id_str = group_part.replace("group_", "").replace("_auth", "")
                group_id = -int(group_id_str)  # Convert back to negative
                
                # Parse metadata
                user_from = None
                group_connect = None
                thread_id = None
                
                for part in parts[1:]:  # Skip the first part (group info)
                    if "=" in part:
                        key, value = part.split("=", 1)
                        if key == "user_from":
                            user_from = int(value)
                        elif key == "group_connect":
                            group_connect = int(value)
                        elif key == "thread_id":
                            thread_id = int(value)
                
                logger.info(f"🔐 Deep link metadata - user_from: {user_from}, group_connect: {group_connect}, thread_id: {thread_id}")
                
                # Validate group_connect matches group_id
                if group_connect and group_connect != abs(group_id):
                    logger.warning(f"⚠️ Group ID mismatch: link={group_connect}, expected={abs(group_id)}")
                
                # Fetch group info
                from luka_bot.services.thread_service import get_thread_service
                thread_service = get_thread_service()
                group_thread = await thread_service.get_group_thread(group_id)
                
                if group_thread:
                    group_title = group_thread.name or f"Group {group_id}"
                    
                    # Store enhanced group context in state for password middleware
                    await state.update_data(
                        password_prompt_sent=True,
                        password_prompt_context={
                            "group_id": group_id,
                            "group_title": group_title,
                            "is_group_auth": True,
                            "user_from": user_from,
                            "group_connect": group_connect,
                            "thread_id": thread_id,
                            "deep_link_accessed": True
                        }
                    )
                    
                    # Send confirmation message that deep link was read
                    confirmation_text = f"✅ <b>Deep link accessed successfully!</b>\n\n"
                    confirmation_text += f"🔗 <b>Group:</b> {group_title}\n"
                    confirmation_text += f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
                    if user_from:
                        confirmation_text += f"👤 <b>From user:</b> {user_from}\n"
                    if thread_id:
                        confirmation_text += f"🧵 <b>Thread ID:</b> {thread_id}\n"
                    confirmation_text += f"\n🔐 <b>Password required for {group_title}</b>\n\n"
                    confirmation_text += f"Please enter the password:"
                    
                    await message.answer(confirmation_text, parse_mode="HTML")
                    
                    logger.info(f"✅ Deep link confirmation sent to user {user_id} for group {group_id}")
                    return True
                else:
                    # Group not found in thread service - try to add it automatically
                    logger.info(f"🔗 Group {group_id} not found in thread service, attempting to add it automatically")
                    
                    try:
                        # Try to get group info from Telegram API
                        chat = await message.bot.get_chat(group_id)
                        group_title = chat.title or f"Group {group_id}"
                        
                        # Add group to user's list using group service
                        from luka_bot.services.group_service import get_group_service
                        group_service = await get_group_service()
                        
                        # Add the group to user's list using create_group_link
                        await group_service.create_group_link(
                            user_id=user_id,
                            group_id=group_id,
                            group_title=group_title,
                            language="en"  # Default, will be customizable later
                        )
                        logger.info(f"✅ Automatically added group {group_id} ({group_title}) to user {user_id}'s list")
                        
                        # Store enhanced group context in state for password middleware
                        await state.update_data(
                            password_prompt_sent=True,
                            password_prompt_context={
                                "group_id": group_id,
                                "group_title": group_title,
                                "is_group_auth": True,
                                "user_from": user_from,
                                "group_connect": group_connect,
                                "thread_id": thread_id,
                                "deep_link_accessed": True,
                                "auto_added": True
                            }
                        )
                        
                        # Send confirmation message that group was auto-added
                        confirmation_text = f"✅ <b>Group automatically added!</b>\n\n"
                        confirmation_text += f"🔗 <b>Group:</b> {group_title}\n"
                        confirmation_text += f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
                        if user_from:
                            confirmation_text += f"👤 <b>From user:</b> {user_from}\n"
                        if thread_id:
                            confirmation_text += f"🧵 <b>Thread ID:</b> {thread_id}\n"
                        confirmation_text += f"\n🔐 <b>Password required for {group_title}</b>\n\n"
                        confirmation_text += f"Please enter the password:"
                        
                        await message.answer(confirmation_text, parse_mode="HTML")
                        
                        logger.info(f"✅ Auto-added group confirmation sent to user {user_id} for group {group_id}")
                        return True
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to auto-add group {group_id}: {e}")
                        await message.answer(
                            f"❌ <b>Group not found</b>\n\n"
                            f"The group you came from is no longer available or I don't have access to it.\n\n"
                            f"<i>Error: {str(e)}</i>",
                            parse_mode="HTML"
                        )
                        return True
            else:
                # Regular group deep link: group_{group_id}
                group_id_str = payload.replace("group_", "")
                group_id = -int(group_id_str)  # Convert back to negative
                
                logger.info(f"🔗 User {user_id} came from group {group_id}")
                
                # Get group info
                from luka_bot.services.group_service import get_group_service
                group_service = await get_group_service()
                kb_index = await group_service.get_group_kb_index(group_id)
                
                if kb_index:
                    await message.answer(
                        f"👋 <b>Welcome!</b>\n\n"
                        f"I see you came from a group!\n\n"
                        f"✅ You can now:\n"
                        f"• 🔍 Search the group's history using /search\n"
                        f"• 💬 Ask me questions here in DM\n"
                        f"• 🤖 Mention me in the group for help\n\n"
                        f"<i>Try /search to explore group messages!</i>",
                        parse_mode="HTML"
                    )
                else:
                    await message.answer(
                        f"👋 <b>Welcome!</b>\n\n"
                        f"I see you came from a group. Once the group is fully set up, "
                        f"you'll be able to search its history!",
                        parse_mode="HTML"
                    )
                return True
            
        elif payload.startswith("admin_"):
            # Admin user came from a group
            group_id_str = payload.replace("admin_", "")
            group_id = -int(group_id_str)
            
            logger.info(f"🔗 Admin user {user_id} came from group {group_id}")
            
            # Get group info
            from luka_bot.services.thread_service import get_thread_service
            from luka_bot.keyboards.group_admin import create_group_admin_menu
            
            # Get group title from Thread
            thread_service = get_thread_service()
            group_thread = await thread_service.get_group_thread(group_id)
            group_title = group_thread.name if group_thread else None
            
            # Fallback: try to get from chat
            if not group_title:
                try:
                    chat = await message.bot.get_chat(group_id)
                    group_title = chat.title
                except Exception:
                    group_title = f"Group {group_id}"
            
            # Show admin controls with dynamic state
            from luka_bot.services.moderation_service import get_moderation_service
            
            moderation_service = await get_moderation_service()
            group_service = await get_group_service()
            
            settings = await moderation_service.get_group_settings(group_id)
            moderation_enabled = settings.moderation_enabled if settings else True
            stoplist_count = len(settings.stoplist_words) if settings else 0
            current_language = await group_service.get_group_language(group_id)
            
            admin_menu = create_group_admin_menu(
                group_id, 
                group_title,
                moderation_enabled,
                stoplist_count,
                current_language,
                silent_mode=settings.silent_mode if settings else False,
                ai_assistant_enabled=settings.ai_assistant_enabled if settings else True,
                kb_indexation_enabled=settings.kb_indexation_enabled if settings else True,
                moderate_admins_enabled=settings.moderate_admins_enabled if settings else False
            )
            await message.answer(
                f"🛡️ <b>Group Moderation & Filters</b>\n\n"
                f"Group: <b>{group_title}</b>\n\n"
                f"<i>Configure moderation and content filters below:</i>",
                reply_markup=admin_menu,
                parse_mode="HTML"
            )
            return True
            
        elif payload.startswith("topic_"):
            # User came from a topic
            parts = payload.replace("topic_", "").split("_")
            if len(parts) >= 2:
                group_id = -int(parts[0])
                topic_id = int(parts[1])
                
                logger.info(f"🔗 User {user_id} came from topic {topic_id} in group {group_id}")
                
                await message.answer(
                    f"👋 <b>Welcome!</b>\n\n"
                    f"I see you came from a topic in a group!\n\n"
                    f"You can search the group's messages using /search.",
                    parse_mode="HTML"
                )
                return True
        
        elif payload == "help":
            # User came from help link
            await message.answer(
                f"👋 <b>Help & Documentation</b>\n\n"
                f"Coming soon: Comprehensive help and guides!\n\n"
                f"For now, try these commands:\n"
                f"• /start - Main menu\n"
                f"• /chat - Manage threads\n"
                f"• /search - Search knowledge bases\n"
                f"• /profile - Your profile",
                parse_mode="HTML"
            )
            return True
            
    except Exception as e:
        logger.error(f"Failed to handle deep link payload '{payload}': {e}")
    
    return False


async def show_onboarding_welcome(message: Message, profile, payload: str = None) -> None:
    """
    Show onboarding Step 1 with detected language and optional language change.
    
    Args:
        message: Telegram message
        profile: UserProfile instance
        payload: Optional deep link payload (e.g., "group_123" if came from group)
    """
    user_id = profile.user_id
    
    # Detect user's Telegram language_code
    telegram_lang = message.from_user.language_code if message.from_user else "en"
    
    # Map to supported languages (en/ru)
    if telegram_lang and telegram_lang.startswith("ru"):
        detected_lang = "ru"
    else:
        detected_lang = "en"
    
    # Set detected language in profile
    profile_service = get_user_profile_service()
    await profile_service.update_language(user_id, detected_lang)
    await profile_service.mark_onboarding_complete(user_id)
    
    # Phase 5: Set KB index for user
    kb_index_name = f"{settings.ELASTICSEARCH_USER_KB_PREFIX}{user_id}"
    await profile_service.set_kb_index(user_id, kb_index_name)
    logger.info(f"📚 Set KB index for user {user_id}: {kb_index_name}")
    
    logger.info(f"🌍 Detected language '{detected_lang}' for user {user_id} from Telegram locale '{telegram_lang}'")
    
    # Add context if user came from a group
    context_text = ""
    if payload and payload.startswith("group_"):
        context_text = "\n\n<i>💡 I see you came from a group! After setup, you'll be able to search that group's history.</i>\n"
    elif payload and payload.startswith("admin_"):
        context_text = "\n\n<i>⭐ I see you're a group admin! After setup, you'll get access to admin controls.</i>\n"
    
    # Show Step 1 with detected language
    bot_name = settings.LUKA_NAME
    step1_text = f"""{_('onboarding.step1_hook', detected_lang, bot_name=bot_name)}
{context_text}
{_('onboarding.step1_capabilities_header', detected_lang)}
{_('onboarding.step1_cap_threads', detected_lang)}
{_('onboarding.step1_cap_tasks', detected_lang)}
{_('onboarding.step1_cap_summarize', detected_lang)}
{_('onboarding.step1_cap_kb', detected_lang)}

{_('onboarding.step1_try_now', detected_lang)}
{_('onboarding.step1_example_1', detected_lang)}
{_('onboarding.step1_example_2', detected_lang)}
{_('onboarding.step1_example_3', detected_lang)}"""
    
    # Optional language change button
    language_name = "English" if detected_lang == "en" else "Русский"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"🌍 Change Language ({language_name})",
                callback_data="onboarding_change_lang"
            )
        ]
    ])
    
    await message.answer(step1_text, reply_markup=keyboard, parse_mode="HTML")
    logger.info(f"📋 Showed onboarding Step 1 to user {user_id} in {detected_lang}")
    
    # Add quick prompt keyboard for new users
    try:
        # Check if chatbot_start process exists before trying to start it
        from luka_bot.services.process_definition_cache import get_process_definition_cache

        process_cache = get_process_definition_cache()
        has_chatbot_start = process_cache.has_process("chatbot_start")

        if has_chatbot_start:
            # Start chatbot_start BPMN in background
            asyncio.create_task(ensure_chatbot_start_running(
                user_id=str(user_id),
                telegram_user_id=user_id,
                chat_id=message.chat.id
            ))
        else:
            logger.debug(f"chatbot_start process not deployed - skipping process start for new user {user_id}")

        # Get user's groups for prompt personalization
        from luka_bot.services.group_service import get_group_service
        group_service = await get_group_service()
        group_links = await group_service.list_user_groups(user_id, active_only=True)
        
        # Get group names from metadata
        group_names = []
        for link in group_links:
            try:
                metadata = await group_service.get_cached_group_metadata(link.group_id)
                if metadata and metadata.group_title:
                    group_names.append(metadata.group_title)
            except Exception as e:
                logger.debug(f"Could not get metadata for group {link.group_id}: {e}")
                # Fallback to group ID if metadata unavailable
                group_names.append(f"Group {link.group_id}")
        
        # Get quick prompts
        prompt_service = get_prompt_pool_service()
        prompt_options = await prompt_service.get_quick_prompts(
            locale=detected_lang, 
            group_names=group_names, 
            count=3
        )
        
        # Store prompts in FSM state for callback handling
        if prompt_options:
            # We need to get the FSM context for this user
            from luka_bot.core.loader import dp
            fsm_context = dp.fsm.get_context(message.bot, user_id, user_id)
            await fsm_context.update_data(quick_prompts=[option.text for option in prompt_options])
        else:
            # Still need to set empty list to avoid errors
            from luka_bot.core.loader import dp
            fsm_context = dp.fsm.get_context(message.bot, user_id, user_id)
            await fsm_context.update_data(quick_prompts=[])
        
        # Set up KB scope for new user
        scope_service = get_user_kb_scope_service()
        available_group_ids = [str(link.group_id) for link in group_links if link.group_id]
        scope = await scope_service.refresh_scope_from_groups(user_id, available_group_ids)
        
        # Store KB scope in FSM state as well
        from luka_bot.core.loader import dp
        fsm_context = dp.fsm.get_context(message.bot, user_id, user_id)
        await fsm_context.update_data(kb_scope=scope.to_dict())
        
        # Build and send start reply keyboard (prompts + emoji scope controls)
        from luka_bot.keyboards.start_menu import build_start_reply_keyboard
        
        start_keyboard = await build_start_reply_keyboard(
            prompt_options or [],
            include_scope_controls=bool(group_links),
            language=detected_lang
        )
        
        # Fetch Camunda tasks first (before sending welcome message)
        tasks_inline = None
        if has_chatbot_start:
            try:
                from luka_bot.keyboards.camunda_tasks_inline import build_camunda_tasks_inline_keyboard
                from luka_bot.services.camunda_service import CamundaService

                camunda_service = CamundaService.get_instance()
                # Filter tasks to only show chatbot_start tasks
                user_tasks = await camunda_service.get_user_tasks(
                    user_id,
                    process_definition_key="chatbot_start"
                )

                tasks_inline = await build_camunda_tasks_inline_keyboard(
                    user_tasks,
                    language=detected_lang
                )

                logger.info(f"📋 Built inline keyboard with {len(user_tasks)} chatbot_start tasks for new user {user_id}")
            except Exception as camunda_error:
                logger.warning(f"Failed to fetch Camunda tasks for new user {user_id}: {camunda_error}")
                tasks_inline = None
        
        # Send welcome with tasks inline keyboard (if available) or reply keyboard
        prompt_intro = _("onboarding_quick_questions_intro", detected_lang)
        if tasks_inline:
            # Send welcome message with tasks inline keyboard attached
            welcome_msg = await message.answer(
                prompt_intro,
                reply_markup=tasks_inline,
                parse_mode="HTML"
            )
            logger.info(f"📋 Sent onboarding welcome with tasks inline keyboard to new user {user_id}")
            
            # Set reply keyboard separately
            kb_msg = await message.answer(
                " ",
                reply_markup=start_keyboard
            )
            asyncio.create_task(_delete_keyboard_setup_message(kb_msg))
        else:
            # No tasks - send welcome with reply keyboard only
            welcome_msg = await message.answer(
                prompt_intro,
                reply_markup=start_keyboard,
                parse_mode="HTML"
            )
            logger.info(f"📝 Sent onboarding welcome with start reply keyboard to new user {user_id}")
    
    except Exception as e:
        logger.warning(f"Failed to add quick prompts for new user {user_id}: {e}")


@router.callback_query(lambda c: c.data == "onboarding_change_lang")
async def handle_change_language_request(callback_query: Message, state: FSMContext) -> None:
    """Handle 'Change Language' button click during onboarding."""
    user_id = callback_query.from_user.id if callback_query.from_user else None
    
    if not user_id:
        await callback_query.answer("Error: User ID not found")
        return
    
    try:
        # Show language selection inline keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="onboarding_lang:en"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="onboarding_lang:ru"),
            ]
        ])
        
        await callback_query.message.edit_text(
            "🌍 <b>Choose your language:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback_query.answer()
        
        logger.info(f"🌍 User {user_id} requested language change")
        
    except Exception as e:
        logger.error(f"❌ Error showing language selector: {e}")
        await callback_query.answer("Error", show_alert=True)


@router.callback_query(lambda c: c.data and c.data.startswith("onboarding_lang:"))
async def handle_language_selection(callback_query: Message, state: FSMContext) -> None:
    """Handle explicit language selection during onboarding."""
    user_id = callback_query.from_user.id if callback_query.from_user else None
    
    if not user_id:
        await callback_query.answer("Error: User ID not found")
        return
    
    try:
        # Parse language
        lang = callback_query.data.split(":", 1)[1]  # "en" or "ru"
        
        # Update profile
        profile_service = get_user_profile_service()
        await profile_service.update_language(user_id, lang)
        
        # Edit the language selection message to confirm choice
        language_name = "English" if lang == "en" else "Русский"
        await callback_query.message.edit_text(
            f"✅ Language set to {language_name}",
            parse_mode="HTML"
        )
        await callback_query.answer()
        
        # Show Step 1: Hook + Capabilities + Examples (single message)
        step1_text = f"""{_('onboarding.step1_hook', lang)}

{_('onboarding.step1_capabilities_header', lang)}
{_('onboarding.step1_cap_threads', lang)}
{_('onboarding.step1_cap_tasks', lang)}
{_('onboarding.step1_cap_summarize', lang)}
{_('onboarding.step1_cap_kb', lang)}

{_('onboarding.step1_try_now', lang)}
{_('onboarding.step1_example_1', lang)}
{_('onboarding.step1_example_2', lang)}
{_('onboarding.step1_example_3', lang)}"""
        
        await callback_query.message.answer(step1_text, parse_mode="HTML")
        
        # Set FSM state to waiting for first message (no keyboard yet)
        await state.set_state(ThreadCreationStates.waiting_for_first_message)
        
        logger.info(f"✅ Language changed to {lang} for user {user_id}, Step 1 shown")
        
    except Exception as e:
        logger.error(f"❌ Error in language selection: {e}")
        await callback_query.answer("Error setting language", show_alert=True)


# ============================================================================
# Phase 4: Action Menu Callbacks
# ============================================================================

# Disabled - /chat command not enabled (configure via LUKA_COMMANDS_ENABLED)
# @router.callback_query(lambda c: c.data == "action_chat")
# async def handle_action_chat(callback_query: Message) -> None:
#     """Redirect to /chat command."""
#     await callback_query.message.delete()
#     await callback_query.answer()
#     # Simulate /chat command
#     await handle_chat_redirect(callback_query.message)


# Disabled - /tasks command not enabled (configure via LUKA_COMMANDS_ENABLED)
# @router.callback_query(lambda c: c.data == "action_tasks")
# async def handle_action_tasks(callback_query: Message) -> None:
#     """Redirect to /tasks command."""
#     await callback_query.message.delete()
#     await callback_query.answer("Opening Tasks...")
#     await callback_query.message.answer(
#         "📋 <b>Tasks (Coming Soon)</b>\n\nTask management with GTD organization will be available soon!",
#         parse_mode="HTML"
#     )


@router.callback_query(lambda c: c.data == "action_groups")
async def handle_action_groups(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Redirect to /groups command."""
    await callback_query.message.delete()
    await callback_query.answer("Opening Groups...")
    
    # Import and call the groups handler
    from luka_bot.handlers.groups_enhanced import handle_groups_enhanced
    await handle_groups_enhanced(callback_query.message, state)


@router.callback_query(lambda c: c.data == "action_add_group")
async def handle_action_add_group(callback_query: CallbackQuery) -> None:
    """Show instructions for adding bot to a group."""
    await callback_query.message.delete()
    await callback_query.answer("Loading instructions...")
    
    user_id = callback_query.from_user.id if callback_query.from_user else None
    if not user_id:
        return
    
    # Get user language
    from luka_bot.utils.i18n_helper import get_user_language
    lang = await get_user_language(user_id)
    
    # Get bot username
    bot_info = await callback_query.bot.get_me()
    bot_username = bot_info.username
    
    instructions = _('start.add_group_instructions', lang, bot_username=bot_username)
    
    # Add a "Done" button to close
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Done", callback_data="action_close")]
    ])
    
    await callback_query.message.answer(
        instructions,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data == "action_help")
async def handle_action_help(callback_query: CallbackQuery) -> None:
    """Show help and documentation."""
    await callback_query.message.delete()
    await callback_query.answer("Loading help...")
    
    user_id = callback_query.from_user.id if callback_query.from_user else None
    if not user_id:
        return
    
    # Get user language
    from luka_bot.utils.i18n_helper import get_user_language
    lang = await get_user_language(user_id)
    
    # Get bot info first
    bot_info = await callback_query.bot.get_me()
    bot_name = settings.LUKA_NAME
    
    help_text = f"""📚 <b>{bot_name} - Help & Guide</b>

<b>🎯 Core Commands:</b>
• /start - Main menu and quick actions
• /groups - Manage your Telegram groups
• /profile - Your settings and preferences

<b>🏘 Group Management:</b>
• Add me as admin to your group
• I'll automatically index messages to KB
• Configure AI assistance per group
• Set up smart moderation and filters
• View detailed group statistics

<b>🤖 In Groups:</b>
• Mention me (@{bot_info.username}) to ask questions
• I'll search the group's KB and help members
• Auto-moderate based on your settings
• Track member reputation and activity

<b>💡 Tips:</b>
• Each group gets its own knowledge base
• Use /groups to configure multiple groups
• Check group stats to see engagement
• Customize moderation per group

<i>Need more help? Contact support or visit our docs.</i>"""
    
    # Add a "Done" button to close
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Done", callback_data="action_close")]
    ])
    
    await callback_query.message.answer(
        help_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data == "action_profile")
async def handle_action_profile(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Redirect to /profile command."""
    await callback_query.message.delete()
    await callback_query.answer("Opening Profile...")
    
    # Import and call the profile handler
    from luka_bot.handlers.profile import handle_profile
    await handle_profile(callback_query.message, state)


@router.callback_query(lambda c: c.data and c.data.startswith("action_"))
async def handle_action_coming_soon(callback_query: CallbackQuery) -> None:
    """Handle coming soon actions."""
    data = callback_query.data or ""
    if data == "action_close":
        # Close the inline menu
        await callback_query.message.delete()
        await callback_query.answer()
        return
    await callback_query.answer("🚧 Coming Soon!\n\nThis feature is under development.", show_alert=True)


# Disabled - /chat command not enabled (configure via LUKA_COMMANDS_ENABLED)
# async def handle_chat_redirect(message: Message) -> None:
#     """Helper to redirect to chat functionality."""
#     from luka_bot.services.thread_service import get_thread_service
#     from luka_bot.utils.i18n_helper import get_user_language
#     
#     user_id = message.from_user.id if message.from_user else None
#     first_name = message.from_user.first_name if message.from_user else ""
#     
#     if not user_id:
#         return
#     
#     # Get user language
#     lang = await get_user_language(user_id)
#     
#     thread_service = get_thread_service()
#     threads = await thread_service.list_threads(user_id)
#     
#     if threads:
#         welcome_text = f"""{_('chat.title', lang)}
# 
# {_('chat.threads_count', lang, count=len(threads))}
# 
# {_('chat.threads_instruction', lang)}"""
#         
#         await message.answer(welcome_text, parse_mode="HTML")
#         
#         current_thread = await thread_service.get_active_thread(user_id)
#         keyboard = await get_threads_keyboard(threads, current_thread, lang)
#         
#         await message.answer(
#             _('chat.your_threads', lang),
#             reply_markup=keyboard,
#             parse_mode="HTML"
#         )
#     else:
#         from aiogram.fsm.context import FSMContext
#         from luka_bot.core.loader import dp
#         
#         state = dp.fsm.get_context(message.bot, user_id, user_id)
#         welcome_text = get_welcome_message(first_name, language=lang)
#         await message.answer(welcome_text, parse_mode="HTML")
#         await state.set_state(ThreadCreationStates.waiting_for_first_message)
#         keyboard = await get_empty_state_keyboard(lang)
#         await message.answer(
#             _('chat.tip_start', lang),
#             reply_markup=keyboard,
#             parse_mode="HTML"
#         )


# ============================================================================
# Quick Prompt Callback Handlers
# ============================================================================

@router.callback_query(lambda c: c.data and c.data.startswith("qp:"))
async def handle_quick_prompt_selected(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Handle quick prompt selections from the onboarding keyboard."""
    state_data = await state.get_data()
    stored_prompts: list[str] = state_data.get("quick_prompts", [])

    try:
        idx = int(callback_query.data.split(":", maxsplit=1)[1])
    except (IndexError, ValueError):
        await callback_query.answer(_("quick_prompt_missing"), show_alert=True)
        return

    if idx < 0 or idx >= len(stored_prompts):
        # Try to regenerate prompts if they're missing
        logger.warning(f"Quick prompt index {idx} out of range for user {callback_query.from_user.id}, stored_prompts: {stored_prompts}")
        
        # Get user language for fallback prompts
        from luka_bot.utils.i18n_helper import get_user_language
        lang = await get_user_language(callback_query.from_user.id)
        
        # Try to get fresh prompts
        try:
            from luka_bot.services.prompt_pool_service import get_prompt_pool_service
            from luka_bot.services.group_service import get_group_service
            
            prompt_service = get_prompt_pool_service()
            group_service = await get_group_service()
            group_links = await group_service.list_user_groups(callback_query.from_user.id, active_only=True)
            
            # Get group names for prompt personalization
            group_names = []
            for link in group_links:
                try:
                    metadata = await group_service.get_cached_group_metadata(link.group_id)
                    if metadata and metadata.group_title:
                        group_names.append(metadata.group_title)
                except Exception as e:
                    logger.debug(f"Could not get metadata for group {link.group_id}: {e}")
                    group_names.append(f"Group {link.group_id}")
            
            prompt_options = await prompt_service.get_quick_prompts(
                locale=lang, 
                group_names=group_names, 
                count=3
            )
            
            if prompt_options and idx < len(prompt_options):
                # Update state with fresh prompts
                await state.update_data(quick_prompts=[option.text for option in prompt_options])
                prompt_text = prompt_options[idx].text
                logger.info(f"Regenerated quick prompts for user {callback_query.from_user.id}")
            else:
                await callback_query.answer(_("quick_prompt_missing"), show_alert=True)
                return
                
        except Exception as e:
            logger.error(f"Failed to regenerate prompts for user {callback_query.from_user.id}: {e}")
            await callback_query.answer(_("quick_prompt_missing"), show_alert=True)
            return
    else:
        prompt_text = stored_prompts[idx]

    await callback_query.answer(_("quick_prompt_ack"))

    # Create a pseudo message to route through existing streaming handler
    pseudo_message = callback_query.message.model_copy(update={
        "text": prompt_text,
        "from_user": callback_query.from_user,
    })

    # Route to existing streaming handler
    from luka_bot.handlers.streaming_dm import handle_streaming_message
    await handle_streaming_message(pseudo_message, state)


# ============================================================================
# KB Scope Callback Handlers
# ============================================================================

@router.callback_query(lambda c: c.data == "sc:all")
async def handle_scope_all_sources(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Switch to all knowledge base sources."""
    scope_service = get_user_kb_scope_service()
    scope = await scope_service.set_custom_scope(callback_query.from_user.id, [])
    await state.update_data(kb_scope=scope.to_dict())
    await callback_query.answer(_("kb_scope_saved_all_toast"))
    await callback_query.message.answer(_("kb_scope_saved_all_message"))


@router.callback_query(lambda c: c.data == "sc:auto")
async def handle_scope_auto_groups(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Switch to auto groups scope."""
    from luka_bot.services.group_service import get_group_service
    
    group_service = await get_group_service()
    group_links = await group_service.list_user_groups(callback_query.from_user.id, active_only=True)
    group_ids = [str(link.group_id) for link in group_links if link.group_id]
    
    scope_service = get_user_kb_scope_service()
    scope = await scope_service.refresh_scope_from_groups(callback_query.from_user.id, group_ids, force=True)
    await state.update_data(kb_scope=scope.to_dict())

    if not scope.group_ids:
        await callback_query.answer(_("kb_scope_saved_all_toast"))
        await callback_query.message.answer(_("kb_scope_saved_all_message"))
        return

    # Create summary of selected groups
    group_names = []
    for link in group_links:
        if str(link.group_id) in scope.group_ids:
            try:
                metadata = await group_service.get_cached_group_metadata(link.group_id)
                if metadata and metadata.group_title:
                    group_names.append(metadata.group_title)
                else:
                    group_names.append(f"Group {link.group_id}")
            except Exception:
                group_names.append(f"Group {link.group_id}")
    group_summary = ", ".join(group_names[:3])
    if len(group_names) > 3:
        group_summary += f" and {len(group_names) - 3} more"

    await callback_query.answer(_("kb_scope_saved_auto_toast"))
    await callback_query.message.answer(_("kb_scope_saved_auto_message").format(group_summary=group_summary))


@router.callback_query(lambda c: c.data == "sc:edit")
async def handle_scope_edit_groups(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Open group selection menu for KB scope."""
    from luka_bot.services.group_service import get_group_service
    
    group_service = await get_group_service()
    group_links = await group_service.list_user_groups(callback_query.from_user.id, active_only=True)

    if not group_links:
        await callback_query.answer(_("kb_scope_selection_empty"), show_alert=True)
        return

    # Get current scope
    state_data = await state.get_data()
    current_scope = state_data.get("kb_scope", {})
    selected = list(current_scope.get("group_ids") or [])
    if not selected:
        selected = [str(link.group_id) for link in group_links if link.group_id]

    # Create selection keyboard
    keyboard_buttons = []
    for link in group_links:
        if not link.group_id:
            continue
        group_id_str = str(link.group_id)
        is_selected = group_id_str in selected
        checkbox = "✅" if is_selected else "⬜"
        
        # Get group title from metadata
        group_title = f"Group {link.group_id}"  # fallback
        try:
            metadata = await group_service.get_group_metadata(link.group_id)
            if metadata and metadata.group_title:
                group_title = metadata.group_title
        except Exception:
            pass  # use fallback
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{checkbox} {group_title}",
                callback_data=f"kb_toggle_{group_id_str}"
            )
        ])

    # Add confirm/cancel buttons
    keyboard_buttons.append([
        InlineKeyboardButton(text="✅ Confirm", callback_data="kb_confirm_selection"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="kb_cancel_selection")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    selection_message = await callback_query.message.answer(
        _("kb_scope_selection_prompt"),
        reply_markup=keyboard,
    )

    await state.update_data(
        kb_scope_edit={
            "selected": selected,
            "message_id": selection_message.message_id,
        }
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("kb_toggle_"))
async def handle_scope_toggle(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Toggle group selection in KB scope edit."""
    group_id = callback_query.data.removeprefix("kb_toggle_")
    data = await state.get_data()
    edit_state = data.get("kb_scope_edit")
    if not edit_state:
        await callback_query.answer(_("kb_scope_selection_expired"), show_alert=True)
        return

    selected = list(edit_state.get("selected", []))
    if group_id in selected:
        selected.remove(group_id)
    else:
        if len(selected) >= 10:
            await callback_query.answer(_("kb_scope_selection_limit"), show_alert=True)
            return
        selected.append(group_id)

    # Update the keyboard
    from luka_bot.services.group_service import get_group_service
    group_service = await get_group_service()
    group_links = await group_service.list_user_groups(callback_query.from_user.id, active_only=True)

    keyboard_buttons = []
    for link in group_links:
        if not link.group_id:
            continue
        group_id_str = str(link.group_id)
        is_selected = group_id_str in selected
        checkbox = "✅" if is_selected else "⬜"
        
        # Get group title from metadata
        group_title = f"Group {link.group_id}"  # fallback
        try:
            metadata = await group_service.get_group_metadata(link.group_id)
            if metadata and metadata.group_title:
                group_title = metadata.group_title
        except Exception:
            pass  # use fallback
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{checkbox} {group_title}",
                callback_data=f"kb_toggle_{group_id_str}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="✅ Confirm", callback_data="kb_confirm_selection"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="kb_cancel_selection")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await state.update_data(kb_scope_edit={**edit_state, "selected": selected})
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "kb_confirm_selection")
async def handle_scope_confirm(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Confirm KB scope selection."""
    data = await state.get_data()
    edit_state = data.get("kb_scope_edit")

    if not edit_state:
        await callback_query.answer(_("kb_scope_selection_expired"), show_alert=True)
        return

    selected = list(edit_state.get("selected", []))
    scope_service = get_user_kb_scope_service()
    scope = await scope_service.set_custom_scope(callback_query.from_user.id, selected)
    await state.update_data(kb_scope=scope.to_dict(), kb_scope_edit=None)

    if scope.source == "all":
        await callback_query.answer(_("kb_scope_saved_all_toast"))
        await callback_query.message.delete()
        await callback_query.message.answer(_("kb_scope_saved_all_message"))
        return

    # Create summary of selected groups
    from luka_bot.services.group_service import get_group_service
    group_service = await get_group_service()
    group_links = await group_service.list_user_groups(callback_query.from_user.id, active_only=True)
    
    group_names = []
    for link in group_links:
        if str(link.group_id) in scope.group_ids:
            try:
                metadata = await group_service.get_cached_group_metadata(link.group_id)
                if metadata and metadata.group_title:
                    group_names.append(metadata.group_title)
                else:
                    group_names.append(f"Group {link.group_id}")
            except Exception:
                group_names.append(f"Group {link.group_id}")
    group_summary = ", ".join(group_names[:3])
    if len(group_names) > 3:
        group_summary += f" and {len(group_names) - 3} more"

    await callback_query.answer(_("kb_scope_saved_custom_toast"))
    await callback_query.message.delete()
    await callback_query.message.answer(_("kb_scope_saved_custom_message").format(group_summary=group_summary))


@router.callback_query(lambda c: c.data == "kb_cancel_selection")
async def handle_scope_cancel(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Cancel KB scope selection."""
    await state.update_data(kb_scope_edit=None)
    try:
        await callback_query.message.delete()
    except Exception:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.answer(_("kb_scope_selection_cancelled"))


# ============================================================================
# Reply Keyboard Handlers (Start Menu)
# ============================================================================

@router.message(lambda m: m.text and m.text not in ["⚙️", "🌐", "🎯"] and len(m.text) > 10)
async def handle_quick_prompt_reply(message: Message, state: FSMContext) -> None:
    """
    Handle quick prompt from reply keyboard.
    Matches any text button that's not a scope control emoji.
    """
    prompt_text = message.text.strip()
    
    # Create pseudo message to route through streaming handler
    pseudo_message = message.model_copy(update={
        "text": prompt_text,
        "from_user": message.from_user,
    })
    
    # Route to existing streaming handler
    from luka_bot.handlers.streaming_dm import handle_streaming_message
    await handle_streaming_message(pseudo_message, state)


@router.message(lambda m: m.text == "⚙️")
async def handle_scope_edit_reply(message: Message, state: FSMContext) -> None:
    """Handle ⚙️ Edit Groups button from reply keyboard."""
    from luka_bot.services.group_service import get_group_service
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    group_service = await get_group_service()
    group_links = await group_service.list_user_groups(message.from_user.id, active_only=True)

    if not group_links:
        await message.answer("❌ No groups available for selection.")
        return

    # Get current scope
    state_data = await state.get_data()
    current_scope = state_data.get("kb_scope", {})
    selected = list(current_scope.get("group_ids") or [])
    if not selected:
        selected = [str(link.group_id) for link in group_links if link.group_id]

    # Create selection keyboard
    keyboard_buttons = []
    for link in group_links:
        if not link.group_id:
            continue
        group_id_str = str(link.group_id)
        is_selected = group_id_str in selected
        checkbox = "✅" if is_selected else "⬜"
        
        # Get group title from metadata
        group_title = f"Group {link.group_id}"  # fallback
        try:
            metadata = await group_service.get_group_metadata(link.group_id)
            if metadata and metadata.group_title:
                group_title = metadata.group_title
        except Exception:
            pass  # use fallback
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{checkbox} {group_title}",
                callback_data=f"kb_toggle_{group_id_str}"
            )
        ])

    # Add confirm/cancel buttons
    keyboard_buttons.append([
        InlineKeyboardButton(text="✅ Confirm", callback_data="kb_confirm_selection"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="kb_cancel_selection")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    selection_message = await message.answer(
        "🔧 <b>Select Groups for Knowledge Base</b>\n\n"
        "Choose which groups to include in your knowledge base search:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.update_data(
        kb_scope_edit={
            "selected": selected,
            "message_id": selection_message.message_id,
        }
    )


@router.message(lambda m: m.text == "🌐")
async def handle_scope_all_reply(message: Message, state: FSMContext) -> None:
    """Handle 🌐 All Sources button from reply keyboard."""
    user_id = message.from_user.id
    
    # Set KB scope to all sources (empty group_ids = all sources)
    from luka_bot.services.user_kb_scope_service import get_user_kb_scope_service
    scope_service = get_user_kb_scope_service()
    scope = await scope_service.set_custom_scope(user_id, [])
    await state.update_data(kb_scope=scope.to_dict())
    
    await message.answer("✅ Knowledge base scope set to <b>All Sources</b>", parse_mode="HTML")


@router.message(lambda m: m.text == "🎯")
async def handle_scope_auto_reply(message: Message, state: FSMContext) -> None:
    """Handle 🎯 My Groups button from reply keyboard."""
    user_id = message.from_user.id
    
    # Get user's groups and set scope to auto groups
    from luka_bot.services.group_service import get_group_service
    from luka_bot.services.user_kb_scope_service import get_user_kb_scope_service
    
    group_service = await get_group_service()
    group_links = await group_service.list_user_groups(user_id, active_only=True)
    
    scope_service = get_user_kb_scope_service()
    available_group_ids = [str(link.group_id) for link in group_links if link.group_id]
    scope = await scope_service.refresh_scope_from_groups(user_id, available_group_ids, force=True)
    await state.update_data(kb_scope=scope.to_dict())
    
    await message.answer("✅ Knowledge base scope set to <b>My Groups</b>", parse_mode="HTML")


# ============================================================================
# Camunda Tasks Inline Keyboard Handlers
# ============================================================================

@router.callback_query(lambda c: c.data and c.data.startswith("task:"))
async def handle_task_launch(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Handle task launch from inline keyboard."""
    try:
        task_id = callback_query.data.split(":", 1)[1]
        user_id = callback_query.from_user.id
        
        # Render the task using existing task service
        from luka_bot.services.task_service import TaskService
        task_service = TaskService.get_instance()
        
        success = await task_service.render_task(
            task_id=task_id,
            message=callback_query.message,
            user_id=user_id,
            state=state
        )
        
        if success:
            # Delete the menu message (with inline keyboard) when task is successfully rendered
            try:
                await callback_query.message.delete()
                logger.debug(f"🗑️ Deleted task menu message for user {user_id}")
            except Exception as e:
                logger.debug(f"Could not delete menu message: {e}")
            
            await callback_query.answer("✅ Task loaded")
        else:
            logger.warning(f"Failed to load task {task_id} for user {user_id}")
            await callback_query.answer()
            
    except Exception as e:
        logger.error(f"Error launching task {task_id}: {e}")
        
        # Check if it's a Camunda expression error
        if "Unknown property used in expression" in str(e) or "Cannot resolve identifier" in str(e):
            await callback_query.answer(
                "❌ Task has configuration issues. Please contact support.",
                show_alert=True
            )
        else:
            await callback_query.answer("❌ Error loading task", show_alert=True)


@router.callback_query(lambda c: c.data == "no_tasks")
async def handle_no_tasks(callback_query: CallbackQuery) -> None:
    """Handle no tasks info button."""
    from luka_bot.utils.i18n_helper import get_user_language
    
    try:
        user_id = callback_query.from_user.id
        lang = await get_user_language(user_id)
        await callback_query.answer(
            _("start.no_tasks_info", lang),
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error handling no_tasks callback: {e}")
        await callback_query.answer("✅ No pending tasks", show_alert=True)


# ============================================================================
# Guest User Handler
# ============================================================================

async def handle_guest_start(message: Message, state: FSMContext) -> None:
    """
    Handle /start command for guest users (user_id = 0).
    
    Provides a simplified experience without user profile requirements.
    """
    logger.info("👋 Guest user accessed /start command")
    
    try:
        bot_name = settings.LUKA_NAME
        
        # Simple welcome message for guests
        welcome_text = f"""👋 <b>Welcome to {bot_name}!</b>

🔓 <b>Guest Mode</b>
You're browsing as a guest with limited features.

✅ <b>What you can do:</b>
• 📚 Browse knowledge base catalog
• 💬 Try basic chat functionality
• 🔍 Test search capabilities

🔑 <b>Sign in for full access to:</b>
• 📋 Task management
• 👥 Group integration
• 🎯 Personalized knowledge scope
• 💾 Conversation history

<i>Try the commands below to explore!</i>"""

        # Simple reply keyboard for guests
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        
        guest_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📚 Browse Catalog"),
                    KeyboardButton(text="💬 Test Chat")
                ],
                [
                    KeyboardButton(text="🔍 Search Demo"),
                    KeyboardButton(text="❓ Help")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Try a command or ask a question..."
        )
        
        await message.answer(welcome_text, reply_markup=guest_keyboard, parse_mode="HTML")
        logger.info("📝 Sent guest welcome message with keyboard")
        
        # Show demo tasks for guests (mocked Camunda tasks)
        demo_tasks_text = """📋 <b>Demo Tasks</b>

Here's what task management looks like for authenticated users:

🔹 <b>Welcome Survey</b>
   <i>Complete your profile setup</i>
   
🔹 <b>Group Integration</b>
   <i>Connect your Telegram groups</i>
   
🔹 <b>Knowledge Base Setup</b>
   <i>Configure your search preferences</i>

<i>✨ Sign in to access real tasks and workflows!</i>"""

        # Simple inline keyboard for demo
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        demo_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔑 Sign In", callback_data="guest_signin"),
                InlineKeyboardButton(text="📖 Learn More", callback_data="guest_learn")
            ]
        ])
        
        await message.answer(demo_tasks_text, reply_markup=demo_keyboard, parse_mode="HTML")
        logger.info("📋 Sent demo tasks to guest user")
        
    except Exception as e:
        logger.error(f"❌ Error in guest /start handler: {e}")
        await message.answer(
            "👋 Welcome to the bot!\n\n"
            "You're in guest mode. Some features are limited.\n\n"
            "Try /catalog to browse the knowledge base."
        )


@router.callback_query(lambda c: c.data == "guest_signin")
async def handle_guest_signin(callback_query: CallbackQuery) -> None:
    """Handle guest sign in button."""
    await callback_query.answer("🔑 Sign In")
    
    signin_text = """🔑 <b>Sign In Options</b>

Choose how you'd like to authenticate:

📱 <b>Telegram Mini App</b>
Connect using your Telegram account for seamless integration

🔐 <b>Bot Password</b>
Enter the bot password if you have one

💡 <i>Signing in unlocks all features including task management, group integration, and personalized experiences.</i>"""

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    signin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Use Telegram", callback_data="auth_telegram"),
            InlineKeyboardButton(text="🔐 Enter Password", callback_data="auth_password")
        ],
        [
            InlineKeyboardButton(text="❌ Cancel", callback_data="auth_cancel")
        ]
    ])
    
    await callback_query.message.answer(signin_text, reply_markup=signin_keyboard, parse_mode="HTML")


@router.callback_query(lambda c: c.data == "guest_learn")
async def handle_guest_learn(callback_query: CallbackQuery) -> None:
    """Handle guest learn more button."""
    await callback_query.answer("📖 Learn More")
    
    learn_text = """📖 <b>About Luka Bot</b>

🤖 <b>AI-Powered Assistant</b>
Advanced conversational AI with knowledge base integration

📋 <b>Task Management</b>
Camunda BPMN workflows for structured processes and automation

👥 <b>Group Integration</b>
Connect your Telegram groups for knowledge indexing and moderation

🔍 <b>Smart Search</b>
Search across multiple knowledge bases and group histories

🎯 <b>Personalization</b>
Customizable scope and preferences for tailored experiences

🔐 <b>Enterprise Ready</b>
Secure authentication and role-based access control

<i>Ready to get started? Sign in to unlock all features!</i>"""

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    learn_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 Sign In", callback_data="guest_signin"),
            InlineKeyboardButton(text="✅ Continue as Guest", callback_data="auth_cancel")
        ]
    ])
    
    await callback_query.message.answer(learn_text, reply_markup=learn_keyboard, parse_mode="HTML")


@router.callback_query(lambda c: c.data == "auth_cancel")
async def handle_auth_cancel(callback_query: CallbackQuery) -> None:
    """Handle authentication cancel."""
    await callback_query.answer("Continuing as guest")
    await callback_query.message.delete()


@router.callback_query(lambda c: c.data == "auth_telegram")
async def handle_auth_telegram(callback_query: CallbackQuery) -> None:
    """Handle Telegram authentication."""
    await callback_query.answer("🚧 Coming Soon")
    await callback_query.message.answer(
        "📱 <b>Telegram Mini App Authentication</b>\n\n"
        "🚧 This feature is under development.\n\n"
        "For now, you can continue as a guest or use the bot password if available.",
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data == "auth_password")
async def handle_auth_password(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Handle password authentication."""
    await callback_query.answer("🔐 Enter Password")
    await callback_query.message.answer(
        "🔐 <b>Bot Password</b>\n\n"
        "Please enter the bot password to access all features:\n\n"
        "<i>Type your password below...</i>",
        parse_mode="HTML"
    )
    
    # Set state to wait for password
    await state.set_state("waiting_for_password")
