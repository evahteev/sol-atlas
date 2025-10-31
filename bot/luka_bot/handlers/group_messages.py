"""
Group message handler for Luka bot.

Handles messages in Telegram groups where the bot is added,
indexing them to the group's KB for searchability.
"""
import asyncio
from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.exceptions import TelegramBadRequest
from loguru import logger
from datetime import datetime

from luka_bot.services.group_service import get_group_service
from luka_bot.services.elasticsearch_service import get_elasticsearch_service
from luka_bot.services.moderation_service import get_moderation_service
from luka_bot.utils.message_parser import extract_mentions, extract_hashtags, extract_urls
from luka_bot.utils.content_detection import (
    check_stoplist,
    match_patterns,
    contains_links,
    is_service_message
)
from luka_bot.core.config import settings

router = Router()


@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def handle_bot_added_to_group(event: ChatMemberUpdated) -> None:
    """
    Handle bot being added to a group.
    
    Creates a group link and KB index for the group.
    """
    try:
        user_id = event.from_user.id
        group_id = event.chat.id
        group_title = event.chat.title or f"Group {group_id}"
        group_username = event.chat.username
        
        logger.info(f"🎉 Bot added to group {group_id} ({group_title}) by user {user_id}")
        
        # Determine user role
        user_role = "member"
        if event.new_chat_member.status in ["administrator", "creator"]:
            user_role = "admin" if event.new_chat_member.status == "administrator" else "owner"
        
        # Get user's default language from their group settings defaults
        # This allows users to set a default language for all new groups
        from luka_bot.services.moderation_service import get_moderation_service
        moderation_service_temp = await get_moderation_service()
        user_defaults_temp = await moderation_service_temp.get_or_create_user_default_settings(user_id)
        user_language = user_defaults_temp.language
        logger.info(f"📝 Using language '{user_language}' for group {group_id} (from user {user_id} default settings)")
        
        # Create group link (which creates Thread automatically)
        group_service = await get_group_service()
        link = await group_service.create_group_link(
            user_id=user_id,
            group_id=group_id,
            group_title=group_title,
            language=user_language,  # Use user's language preference
            user_role=user_role
        )
        
        # Get thread configuration
        from luka_bot.services.thread_service import get_thread_service
        thread_service = get_thread_service()
        thread = await thread_service.get_group_thread(group_id)
        
        if not thread:
            logger.error(f"❌ Thread not found for group {group_id} after creation")
            return
        
        kb_index = thread.knowledge_bases[0] if thread.knowledge_bases else None
        logger.info(f"✅ Created group link with KB index: {kb_index}")
        
        # Create group settings from user's default template
        moderation_service = await get_moderation_service()
        
        # DEBUG: Log user's defaults first
        user_defaults = await moderation_service.get_or_create_user_default_settings(user_id)
        logger.info(f"📋 User {user_id} defaults: AI={user_defaults.ai_assistant_enabled}, Silent={user_defaults.silent_mode}, KB={user_defaults.kb_indexation_enabled}, Moderation={user_defaults.moderation_enabled}")
        
        group_settings = await moderation_service.create_group_settings_from_user_defaults(
            user_id=user_id,
            group_id=group_id
        )
        logger.info(f"✅ Created GroupSettings for group {group_id} from user {user_id} template")
        logger.info(f"📋 Group {group_id} settings: AI={group_settings.ai_assistant_enabled}, Silent={group_settings.silent_mode}, KB={group_settings.kb_indexation_enabled}, Moderation={group_settings.moderation_enabled}")
        
        # Check if silent mode is enabled in group settings
        silent_mode = group_settings.silent_mode if group_settings else False
        
        # Get bot info
        bot_info = await event.bot.get_me()
        bot_username = bot_info.username
        bot_name = thread.agent_name or settings.LUKA_NAME
        
        # Get group language from thread
        group_language = thread.language
        
        # 🌟 NEW: Collect full group metadata
        logger.info(f"🔄 Collecting group metadata for {group_id}")
        metadata = await group_service.collect_group_metadata(
            group_id=group_id,
            bot=event.bot,
            added_by_user_id=user_id,
            added_by_username=event.from_user.username if event.from_user else None,
            added_by_full_name=event.from_user.full_name if event.from_user else "Unknown"
        )
        
        # Store metadata in cache
        metadata.bot_name = bot_name
        metadata.kb_index = kb_index or ""
        metadata.thread_id = thread.thread_id
        metadata.initial_language = group_language
        await group_service.cache_group_metadata(metadata)
        logger.info(f"✅ Cached metadata for group {group_id}")
        
        # Generate smart welcome message based on bot permissions
        from luka_bot.utils.welcome_generator import generate_smart_welcome_message
        
        welcome_text = generate_smart_welcome_message(
            bot_name=bot_name,
            metadata=metadata,
            thread=thread,
            language=group_language
        )
        
        # Create inline keyboard with settings
        from luka_bot.keyboards.group_settings_inline import create_group_settings_inline
        moderation_enabled = group_settings.moderation_enabled if group_settings else False
        inline_keyboard = create_group_settings_inline(group_id, group_language, moderation_enabled)
        
        # Check silent mode setting - this only affects GROUP messages, not DMs
        if silent_mode:
            # SILENT MODE: Don't send welcome in group, send DM to admin instead
            logger.info(f"🔇 Silent mode ON - sending welcome to admin DM instead of group")
            
            # Send welcome message + controls to user's DM
            from luka_bot.utils.group_onboarding import send_group_onboarding_to_dm
            
            await send_group_onboarding_to_dm(
                bot=event.bot,
                user_id=user_id,
                group_id=group_id,
                group_title=group_title,
                welcome_text=welcome_text,
                inline_keyboard=inline_keyboard,
                metadata=metadata,
                thread=thread,
                language=group_language
            )
            logger.info(f"✅ Sent silent mode welcome to user {user_id} DM")
        else:
            # NORMAL MODE: Send welcome message in group
            await event.answer(welcome_text, reply_markup=inline_keyboard, parse_mode="HTML")
            logger.info(f"✅ Sent smart welcome message to group (bot_is_admin={metadata.bot_is_admin})")
        
        # ========================================================================
        # Note: Notification is now included in the welcome message above
        # No need for separate notification message
        # ========================================================================
        
        # Get LLM-generated personalized welcome ONLY if AI assistant is enabled AND silent mode is OFF
        if not silent_mode and group_settings.ai_assistant_enabled:
            try:
                from luka_bot.services.llm_service import get_llm_service
                llm_service = get_llm_service()
                
                # Create a prompt for the LLM using bot personality from settings
                # Include language instruction based on group settings
                language_instruction = ""
                if group_language == "ru":
                    language_instruction = "\n\nIMPORTANT: Write your response in Russian language (русский язык)."
                
                llm_prompt = f"""You are {settings.LUKA_NAME}. You've just been added to a Telegram group called "{group_title}".

Write a SHORT (2-3 sentences max), friendly welcome message that:
- Greets the group members warmly
- Shows enthusiasm about helping this specific group
- Mentions you can help with questions when they mention you
- Shows personality and warmth

Be conversational, brief, and friendly. No bullet points or technical details.{language_instruction}"""
                
                # Generate welcome from LLM (simple request, no streaming needed)
                from luka_bot.agents.context import ConversationContext
                
                # Create minimal context for welcome message
                ctx = ConversationContext(
                    user_id=user_id,
                    thread_id=thread.thread_id,
                    thread_knowledge_bases=thread.knowledge_bases
                )
                
                # Get agent and generate response
                from luka_bot.agents.agent_factory import create_static_agent_with_basic_tools
                agent = await create_static_agent_with_basic_tools(user_id)
                
                result = await agent.run(llm_prompt, deps=ctx)
                
                # Extract text from AgentRunResult properly
                if hasattr(result, 'data'):
                    llm_welcome = str(result.data)
                elif hasattr(result, 'output'):
                    llm_welcome = str(result.output)
                else:
                    llm_welcome = str(result)
                
                # Clean up the text (remove AgentRunResult wrapper if present)
                if llm_welcome.startswith("AgentRunResult("):
                    import re
                    match = re.search(r"output='([^']*(?:\\.[^']*)*)'", llm_welcome)
                    if match:
                        llm_welcome = match.group(1).replace("\\'", "'").replace("\\n", "\n")
                
                # Send LLM-generated welcome (just the message, no prefix)
                await event.answer(llm_welcome, parse_mode="HTML")
                
                logger.info(f"✅ Sent AI-generated welcome to group {group_id}")
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to generate LLM welcome: {e}")
                # Non-critical, continue without LLM welcome
        else:
            logger.info(f"ℹ️ Skipped AI welcome for group {group_id} (AI assistant disabled in settings)")
        
        # Note: Admin menu is now included in the welcome message keyboard above
        # No need for separate admin menu message
        logger.info(f"✅ Bot addition complete for group {group_id}")
        
    except Exception as e:
        logger.error(f"❌ Error handling bot added to group: {e}")


@router.my_chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def handle_bot_removed_from_group(event: ChatMemberUpdated) -> None:
    """
    Handle bot being removed from a group.
    
    Deactivates the group link (keeps data for potential re-add).
    """
    try:
        user_id = event.from_user.id
        group_id = event.chat.id
        
        logger.info(f"👋 Bot removed from group {group_id} by user {user_id}")
        
        # Deactivate group link (don't delete - user might re-add)
        group_service = await get_group_service()
        await group_service.deactivate_group_link(user_id, group_id)
        
        logger.info(f"✅ Deactivated group link for group {group_id}")
        
    except Exception as e:
        logger.error(f"❌ Error handling bot removed from group: {e}")


@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def handle_user_left_group(event: ChatMemberUpdated) -> None:
    """
    Handle user leaving group.
    Deactivates their GroupLink to remove group from their /groups list.
    """
    try:
        user_id = event.from_user.id
        group_id = event.chat.id
        
        # Skip if bot itself is leaving (already handled)
        bot_info = await event.bot.get_me()
        if user_id == bot_info.id:
            return
        
        logger.info(f"👋 User {user_id} left group {group_id}")
        
        # Deactivate group link
        group_service = await get_group_service()
        await group_service.deactivate_group_link(user_id, group_id)
        
        logger.info(f"✅ Deactivated GroupLink for user {user_id} in group {group_id}")
        
    except Exception as e:
        logger.error(f"❌ Error handling user left group: {e}")


async def ensure_user_group_link(
    user_id: int,
    group_id: int,
    message: Message
) -> None:
    """
    Ensure GroupLink exists for user in this group.
    Creates link if missing, updates activity timestamp if exists.
    Also creates minimal UserProfile for users seen in groups.
    """
    group_service = await get_group_service()
    
    # 1. Ensure user profile exists (minimal profile for group participants)
    from luka_bot.services.user_profile_service import UserProfileService
    profile_service = UserProfileService()
    await profile_service.get_or_create_minimal_profile(user_id, message.from_user)
    
    # 2. Check if link exists
    existing_link = await group_service.get_group_link(user_id, group_id)
    
    if existing_link:
        # Update activity timestamp (throttle to once per 24 hours)
        from datetime import timedelta
        time_since_update = datetime.utcnow() - existing_link.updated_at
        if time_since_update > timedelta(hours=24):
            existing_link.updated_at = datetime.utcnow()
            await group_service._save_group_link(existing_link)
            logger.debug(f"✅ Updated GroupLink activity: user={user_id}, group={group_id}")
        return
    
    # 3. Get group thread (should exist since bot is in group)
    from luka_bot.services.thread_service import get_thread_service
    thread_service = get_thread_service()
    group_thread = await thread_service.get_group_thread(group_id)
    
    if not group_thread:
        logger.warning(f"⚠️ No group thread for {group_id}, skipping GroupLink creation")
        return
    
    # 4. Determine user role
    user_role = "member"  # Default
    try:
        member = await message.bot.get_chat_member(group_id, user_id)
        if member.status in ["administrator", "creator"]:
            user_role = "admin" if member.status == "administrator" else "owner"
    except Exception as e:
        logger.debug(f"Could not get member status for user {user_id}: {e}")
    
    # 5. Create link
    group_title = message.chat.title or f"Group {group_id}"
    link = await group_service.create_group_link(
        user_id=user_id,
        group_id=group_id,
        group_title=group_title,
        language=group_thread.language or "en",
        user_role=user_role
    )
    
    logger.info(f"✨ Auto-created GroupLink for user {user_id} in group {group_id} ({group_title})")


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message) -> None:
    """
    Handle messages in groups.

    Indexes message to group KB for searchability.
    Also welcomes the bot when first message is sent in a topic.
    """
    try:
        group_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None
        message_text = message.text or message.caption or ""

        # DEBUG: Log that this handler was called
        logger.warning(f"✅ handle_group_message CALLED: group_id={group_id}, chat_type={message.chat.type}, text='{message_text[:50] if message_text else '(no text)'}'")

        if not user_id:
            logger.warning(f"⚠️ Group message skipped (no user_id): group_id={group_id}")
            return  # Skip messages without user
        
        # ========================================================================
        # AUTO-LINK: Ensure user has GroupLink for this group
        # ========================================================================
        await ensure_user_group_link(user_id, group_id, message)
        
        # ========================================================================
        # STEP 1: PRE-PROCESSING FILTERS (Fast, rule-based)
        # ========================================================================
        
        # Get moderation service
        moderation_service = await get_moderation_service()
        
        # Get GroupSettings (or skip moderation if not configured yet)
        group_settings = await moderation_service.get_group_settings(group_id)

        if group_settings:
            # Enforce image restrictions even when no text is present
            if group_settings.delete_images:
                is_photo = bool(getattr(message, "photo", None))
                is_image_document = (
                    getattr(message, "document", None)
                    and message.document.mime_type
                    and message.document.mime_type.startswith("image/")
                )
                if is_photo or is_image_document:
                    try:
                        await message.delete()
                        logger.info(f"🚫 Deleted image message from user {user_id} (image restriction enabled)")
                    except TelegramBadRequest as e:
                        logger.warning(f"⚠️ Cannot delete image message in group {group_id}: {e}")
                    except Exception as e:
                        logger.error(f"❌ Unexpected error deleting image message: {e}")
                    return

            # Check service messages
            if group_settings.delete_service_messages:
                content_type = message.content_type
                if is_service_message(content_type, group_settings.service_message_types):
                    logger.info(f"🗑️ Deleting service message: {content_type}")
                    try:
                        await message.delete()
                    except Exception as e:
                        logger.warning(f"Failed to delete service message: {e}")
                    return  # Stop processing

        if not message_text:
            return  # No further processing needed for empty-text messages
            
        # Check stoplist words
        if group_settings and group_settings.stoplist_enabled:
            matched_word = check_stoplist(
                message_text,
                group_settings.stoplist_words,
                group_settings.stoplist_case_sensitive
            )
            if matched_word:
                logger.info(f"🚫 Stoplist violation: '{matched_word}' by user {user_id}")
                try:
                    await message.delete()
                    # Send notification to user
                    try:
                        await message.bot.send_message(
                            user_id,
                            f"⚠️ Your message in {message.chat.title} was removed (forbidden word: {matched_word})"
                        )
                    except:
                        pass  # User may have blocked bot
                except TelegramBadRequest as e:
                    if "message can't be deleted" in str(e):
                        logger.warning(f"⚠️ Cannot delete stoplist violation in group {group_id}: Bot needs admin permissions")
                        
                        # Notify group admins about missing permissions
                        try:
                            group_service = await get_group_service()
                            
                            # Get group metadata to find admins
                            metadata = await group_service.get_cached_group_metadata(group_id)
                            
                            if metadata and metadata.admin_list:
                                # Send notification to all human admins (not bots)
                                bot_info = await message.bot.get_me()
                                notified_count = 0
                                
                                for admin_data in metadata.admin_list[:3]:  # Notify top 3 admins
                                    admin_id = admin_data.get("user_id")
                                    is_bot = admin_data.get("is_bot", False)
                                    
                                    if not admin_id or is_bot:
                                        continue
                                    
                                    try:
                                        from luka_bot.utils.i18n_helper import get_user_language
                                        lang = await get_user_language(admin_id)
                                        
                                        if lang == "ru":
                                            notification = (
                                                f"⚠️ <b>Нарушение правил обнаружено</b>\n\n"
                                                f"📌 Группа: {message.chat.title}\n"
                                                f"🚫 Запрещённое слово: '{matched_word}'\n"
                                                f"👤 Пользователь: {user_id}\n\n"
                                                f"💡 <b>Совет:</b> Назначьте меня администратором группы для автоматического удаления нарушений.\n\n"
                                                f"Для этого:\n"
                                                f"1. Откройте настройки группы\n"
                                                f"2. Администраторы → Добавить администратора\n"
                                                f"3. Выберите @{bot_info.username}\n"
                                                f"4. Включите права \"Удаление сообщений\""
                                            )
                                        else:
                                            notification = (
                                                f"⚠️ <b>Rule Violation Detected</b>\n\n"
                                                f"📌 Group: {message.chat.title}\n"
                                                f"🚫 Forbidden word: '{matched_word}'\n"
                                                f"👤 User: {user_id}\n\n"
                                                f"💡 <b>Tip:</b> Make me an admin in the group to enable automatic deletion of violations.\n\n"
                                                f"To do this:\n"
                                                f"1. Open group settings\n"
                                                f"2. Administrators → Add Administrator\n"
                                                f"3. Select @{bot_info.username}\n"
                                                f"4. Enable \"Delete messages\" permission"
                                            )
                                        
                                        await message.bot.send_message(
                                            admin_id,
                                            notification,
                                            parse_mode="HTML"
                                        )
                                        notified_count += 1
                                        logger.info(f"📤 Sent admin permission notification to user {admin_id}")
                                    except Exception as send_error:
                                        logger.debug(f"Could not notify admin {admin_id}: {send_error}")
                                
                                if notified_count == 0:
                                    logger.warning(f"⚠️ No admins could be notified for group {group_id}")
                            else:
                                logger.warning(f"⚠️ No admin metadata available for group {group_id}")
                                
                        except Exception as notify_error:
                            logger.error(f"❌ Failed to notify admins: {notify_error}", exc_info=True)
                    else:
                        logger.error(f"❌ Unexpected error deleting message: {e}")
                except Exception as e:
                    logger.warning(f"Failed to delete stoplist message: {e}")
                return  # Stop processing
            
            # Check content type filters
            if group_settings.delete_links and contains_links(message_text):
                logger.info(f"🚫 Link violation by user {user_id}")
                try:
                    await message.delete()
                except:
                    pass
                return
            
            if group_settings.delete_forwarded and message.forward_origin:
                logger.info(f"🚫 Forwarded message deleted by user {user_id}")
                try:
                    await message.delete()
                except:
                    pass
                return
            
            # Check media types
            content_type = message.content_type
            if (group_settings.delete_images and content_type == "photo") or \
               (group_settings.delete_videos and content_type == "video") or \
               (group_settings.delete_stickers and content_type == "sticker"):
                logger.info(f"🚫 Media type violation: {content_type} by user {user_id}")
                try:
                    await message.delete()
                except:
                    pass
                return
            
            # Check regex patterns
            matched_pattern = match_patterns(message_text, group_settings.pattern_filters)
            if matched_pattern:
                action = matched_pattern.get("action", "warn")
                if action == "delete":
                    logger.info(f"🚫 Pattern violation by user {user_id}: {matched_pattern.get('description')}")
                    try:
                        await message.delete()
                    except:
                        pass
                    return
        
        # ========================================================================
        # KNOWLEDGE BASE GATHERING SYSTEM (Phase 1)
        # Analyze content for potential KB inclusion before other processing
        # ========================================================================

        # Only process KB gathering if KB indexation is enabled
        if group_settings and group_settings.kb_indexation_enabled and message_text:
            try:
                from luka_bot.handlers.kb_gathering import process_kb_gathering
                from luka_bot.services.thread_service import get_thread_service

                # Get group thread for language
                thread_service = get_thread_service()
                group_thread = await thread_service.get_group_thread(group_id)
                group_language = group_thread.language if group_thread else "en"

                # Process KB gathering (non-blocking, best-effort)
                await process_kb_gathering(
                    message=message,
                    group_id=group_id,
                    user_id=user_id,
                    language=group_language
                )
            except Exception as e:
                # Non-critical - log and continue
                logger.warning(f"⚠️ KB gathering failed: {e}")

        # ========================================================================
        # Continue with existing logic (auto-initialization, etc.)
        # ========================================================================

        # Check if this message is in a topic (supergroup thread)
        thread_id = getattr(message, 'message_thread_id', None)
        
        # Get group KB index
        group_service = await get_group_service()
        kb_index = await group_service.get_group_kb_index(group_id)
        
        # If no KB index exists, create group link on the fly (auto-initialization)
        if not kb_index:
            logger.info(f"📝 No KB index for group {group_id}, creating on the fly...")
            
            try:
                group_title = message.chat.title or f"Group {group_id}"
                group_username = message.chat.username
                
                # Determine user role (default to member since we can't check status here)
                user_role = "member"
                
                # Create group link (creates Thread automatically)
                link = await group_service.create_group_link(
                    user_id=user_id,
                    group_id=group_id,
                    group_title=group_title,
                    language="en",  # Default language
                    user_role=user_role
                )
                
                # Get thread configuration
                from luka_bot.services.thread_service import get_thread_service
                thread_service = get_thread_service()
                thread = await thread_service.get_group_thread(group_id)
                
                if not thread:
                    logger.error(f"❌ Thread not found for group {group_id} after auto-creation")
                    return
                
                kb_index = thread.knowledge_bases[0] if thread.knowledge_bases else None
                logger.info(f"✅ Auto-created group link with KB index: {kb_index}")
                
                # Create default GroupSettings if not exists
                if not group_settings:
                    group_settings = await moderation_service.create_default_group_settings(
                        group_id=group_id,
                        created_by=user_id
                    )
                    logger.info(f"✅ Created default GroupSettings for group {group_id}")
                
                # Get bot info and group language from thread
                bot_info = await message.bot.get_me()
                bot_username = bot_info.username
                bot_name = thread.agent_name or settings.LUKA_NAME
                group_language = thread.language
                
                # 🌟 Collect full group metadata
                logger.info(f"🔄 Collecting group metadata for {group_id} (auto-init)")
                metadata = await group_service.collect_group_metadata(
                    group_id=group_id,
                    bot=message.bot,
                    added_by_user_id=user_id,
                    added_by_username=message.from_user.username if message.from_user else None,
                    added_by_full_name=message.from_user.full_name if message.from_user else "Unknown"
                )
                
                # Store metadata in cache
                metadata.bot_name = bot_name
                metadata.kb_index = kb_index or ""
                metadata.thread_id = thread.thread_id
                metadata.initial_language = group_language
                await group_service.cache_group_metadata(metadata)
                logger.info(f"✅ Cached metadata for group {group_id} (auto-init)")
                
                # Generate smart welcome message based on bot permissions
                from luka_bot.utils.welcome_generator import generate_smart_welcome_message
                
                welcome_text = generate_smart_welcome_message(
                    bot_name=bot_name,
                    metadata=metadata,
                    thread=thread,
                    language=group_language
                )
                
                # Check silent mode before sending welcome messages
                silent_mode = group_settings.silent_mode if group_settings else False
                
                if not silent_mode:
                    # Create inline keyboard with settings
                    from luka_bot.keyboards.group_settings_inline import create_group_settings_inline
                    moderation_enabled = group_settings.moderation_enabled if group_settings else False
                    inline_keyboard = create_group_settings_inline(group_id, group_language, moderation_enabled)
                    
                    await message.answer(welcome_text, reply_markup=inline_keyboard, parse_mode="HTML", disable_web_page_preview=True)
                    logger.info(f"✅ Sent smart welcome message (auto-init, bot_is_admin={metadata.bot_is_admin})")
                else:
                    logger.info(f"🔇 Silent mode ON - skipping welcome message for auto-init group {group_id}")
                
                # Try to get LLM welcome (non-blocking, only if silent mode is OFF)
                if not silent_mode:
                    try:
                        from luka_bot.services.llm_service import get_llm_service
                        from luka_bot.agents.context import ConversationContext
                        from luka_bot.agents.agent_factory import create_static_agent_with_basic_tools
                        
                        # Include language instruction based on group settings
                        language_instruction = ""
                        if group_language == "ru":
                            language_instruction = "\n\nIMPORTANT: Write your response in Russian language (русский язык)."
                        
                        llm_prompt = f"""You are {settings.LUKA_NAME}. You've just been initialized in a Telegram group called "{group_title}".

Write a SHORT (2-3 sentences max), friendly welcome message that:
- Greets the group members warmly
- Shows enthusiasm about helping this group
- Mentions you can help when they mention you (@{bot_username})
- Shows personality and warmth

Be conversational, brief, and friendly. No bullet points or technical details.{language_instruction}"""
                        
                        ctx = ConversationContext(
                            user_id=user_id,
                            thread_id=None,
                            thread_knowledge_bases=[kb_index]
                        )
                        
                        agent = await create_static_agent_with_basic_tools(user_id)
                        result = await agent.run(llm_prompt, deps=ctx)
                        
                        # Extract text from AgentRunResult properly
                        if hasattr(result, 'data'):
                            llm_welcome = str(result.data)
                        elif hasattr(result, 'output'):
                            llm_welcome = str(result.output)
                        else:
                            llm_welcome = str(result)
                        
                        # Clean up the text (remove AgentRunResult wrapper if present)
                        if llm_welcome.startswith("AgentRunResult("):
                            # Extract just the output text
                            import re
                            match = re.search(r"output='([^']*(?:\\.[^']*)*)'", llm_welcome)
                            if match:
                                llm_welcome = match.group(1).replace("\\'", "'").replace("\\n", "\n")
                        
                        # Send LLM welcome directly without prefix
                        await message.answer(llm_welcome, parse_mode="HTML")
                        logger.info(f"✅ Sent AI welcome for auto-initialized group {group_id}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to generate LLM welcome: {e}")
                
                # Note: Admin controls are available via /groups command
                logger.info(f"✅ Auto-initialization complete for group {group_id}")
                
            except Exception as e:
                logger.error(f"❌ Failed to auto-create group link: {e}")
                return  # Skip indexing if we can't create the link
        
        # ========================================================================
        # STEP 2: BACKGROUND MODERATION V2 (Fire-and-forget, truly parallel)
        
        # ========================================================================
        
        # Get GroupSettings (reload if needed for auto-initialized groups)
        if not group_settings:
            group_settings = await moderation_service.get_group_settings(group_id)
        
        # Fire moderation task in background (non-blocking)
        # Moderation evaluates ALL messages if enabled, but doesn't block main flow
        if group_settings and group_settings.moderation_enabled:
            logger.debug(f"🛡️ [V2] Firing background moderation for message from user {user_id}")
            try:
                from luka_bot.handlers.moderation_background import fire_moderation_task
                
                # Fire and forget - no await, no blocking!
                fire_moderation_task(
                    message_id=message.message_id,
                    chat_id=message.chat.id,
                    user_id=user_id,
                    message_text=message_text,
                    group_settings=group_settings
                )
                logger.debug(f"🔥 [V2] Moderation task fired, continuing immediately...")
            except Exception as e:
                logger.error(f"❌ Failed to fire moderation task: {e}")
        
        # Main flow continues immediately (no blocking!)
        # Note: Moderation happens in parallel:
        #   - Evaluates message quality/violations
        #   - Updates user reputation
        #   - Checks achievements
        #   - Can delete user message AND bot reply retroactively if violation found
        
        # ========================================================================
        # Continue with existing logic (topic greeting, mentions, indexing)
        # ========================================================================
        
        # Check if this is the first message in a topic (bot hasn't greeted this topic yet)
        if thread_id:
            # Check if we've already greeted this topic
            from luka_bot.core.loader import redis_client
            topic_key = f"topic_greeted:{group_id}:{thread_id}"
            already_greeted = await redis_client.get(topic_key)
            
            if not already_greeted and message.is_topic_message:
                # This is a new topic - mark as greeted but check silent mode before sending greeting
                try:
                    # Mark as greeted (expires in 7 days in case topic is deleted and recreated)
                    await redis_client.setex(topic_key, 7 * 24 * 60 * 60, "1")
                    
                    # Check silent mode - skip system messages if enabled
                    silent_mode = group_settings.silent_mode if group_settings else False
                    
                    if not silent_mode:
                        # Send topic greeting only if silent mode is OFF
                        group_title = message.chat.title or f"Group {group_id}"
                        
                        # Try to get topic name from reply_to_message if available
                        topic_name = None
                        if hasattr(message, 'reply_to_message') and message.reply_to_message:
                            if hasattr(message.reply_to_message, 'forum_topic_created'):
                                topic_name = message.reply_to_message.forum_topic_created.name
                        
                        # Fallback: check current message
                        if not topic_name and hasattr(message, 'forum_topic_created') and message.forum_topic_created:
                            topic_name = message.forum_topic_created.name
                        
                        # Build and send topic greeting
                        topic_greeting = f"""👋 <b>Hello in this topic!</b>

🧵 <b>Topic Information:</b>
• 📝 <b>Topic ID:</b> <code>{thread_id}</code>"""
                        
                        if topic_name:
                            topic_greeting += f"\n• 📌 <b>Topic Name:</b> {topic_name}"
                        
                        topic_greeting += f"""
• 👥 <b>Group:</b> {group_title}
• 🆔 <b>Group ID:</b> <code>{group_id}</code>
• 📚 <b>KB Index:</b> <code>{kb_index}</code> (shared with group)

🎯 <b>Current topic behavior:</b>
• 💬 Messages indexed with group (not separately yet)
• 🔍 Searchable within the group's KB
• 🤖 Mention me to get AI assistance
• 🧵 Topic ID is tracked in metadata

<i>💡 Coming soon: Separate KB per topic for topic-specific search!</i>"""
                        
                        await message.answer(topic_greeting, parse_mode="HTML")
                    else:
                        logger.info(f"🔇 Silent mode ON - skipping topic greeting for topic {thread_id} in group {group_id}")
                    
                    # Get LLM welcome for this topic (only if silent mode is OFF)
                    if not silent_mode:
                        try:
                            from luka_bot.services.llm_service import get_llm_service
                            from luka_bot.agents.context import ConversationContext
                            from luka_bot.agents.agent_factory import create_static_agent_with_basic_tools
                            
                            llm_prompt = f"""You've just encountered a new topic/thread in a Telegram group.

Group: "{group_title}"
Topic/Thread ID: {thread_id}

Write a brief, contextual welcome (1-2 sentences) that:
1. Acknowledges this is a dedicated space for focused discussion
2. Mentions you'll track and help with this topic's conversations

Keep it brief and professional."""
                            
                            ctx = ConversationContext(
                                user_id=user_id,
                                thread_id=f"topic_{group_id}_{thread_id}",
                                thread_knowledge_bases=[kb_index]
                            )
                            
                            agent = await create_static_agent_with_basic_tools(user_id)
                            result = await agent.run(llm_prompt, deps=ctx)
                            
                            # Extract text from AgentRunResult properly
                            if hasattr(result, 'data'):
                                llm_welcome = str(result.data)
                            elif hasattr(result, 'output'):
                                llm_welcome = str(result.output)
                            else:
                                llm_welcome = str(result)
                            
                            # Clean up the text (remove AgentRunResult wrapper if present)
                            if llm_welcome.startswith("AgentRunResult("):
                                import re
                                match = re.search(r"output='([^']*(?:\\.[^']*)*)'", llm_welcome)
                                if match:
                                    llm_welcome = match.group(1).replace("\\'", "'").replace("\\n", "\n")
                            
                            # Send LLM welcome directly without prefix
                            await message.answer(llm_welcome, parse_mode="HTML")
                            
                            logger.info(f"✅ Sent topic welcome for thread {thread_id} in group {group_id}")
                            
                        except Exception as e:
                            logger.warning(f"⚠️  Failed to generate topic LLM welcome: {e}")
                        
                except Exception as e:
                    logger.warning(f"⚠️  Failed to send topic greeting: {e}")
        
        # Check if bot is mentioned or if user is replying to bot
        bot_info = await message.bot.get_me()
        bot_username = bot_info.username

        # Safety check: Don't respond if we can't get bot username
        if not bot_username:
            logger.error(f"❌ Bot username is None or empty! Bot ID: {bot_info.id}")
            logger.warning(f"⚠️ Skipping group message processing for user {user_id} - bot username unavailable")
            return  # Skip all processing if we can't get bot username
        
        # Debug logging for bot info
        logger.debug(f"🔍 Bot info: ID={bot_info.id}, username=@{bot_username}, first_name={bot_info.first_name}")
        logger.info(f"🔍 GROUP_MESSAGES handler processing: chat_id={message.chat.id}, chat_type={message.chat.type}, text='{message_text[:50]}...'")

        is_mentioned = False
        is_reply_to_bot = False
        bot_original_message = None
        
        # Check if this is a reply to bot's message
        if message.reply_to_message:
            replied_message = message.reply_to_message
            # Check if the replied message is from the bot
            if replied_message.from_user and replied_message.from_user.id == message.bot.id:
                is_reply_to_bot = True
                bot_original_message = replied_message.text or replied_message.caption or ""
                logger.info(f"✅ Reply to bot detected from user {user_id} in group {group_id}")
            else:
                logger.debug(f"🔍 Reply to non-bot message from user {replied_message.from_user.id if replied_message.from_user else 'unknown'}")
        
        # Check for @username mentions in entities
        if message.entities:
            for entity in message.entities:
                if entity.type == "mention":
                    mention_text = message_text[entity.offset:entity.offset + entity.length]
                    logger.debug(f"🔍 Found mention entity: '{mention_text}' (bot username: @{bot_username})")
                    
                    # Check for exact match (case-sensitive)
                    if f"@{bot_username}" == mention_text:
                        is_mentioned = True
                        logger.info(f"✅ Bot mention detected via entity: {mention_text}")
                        break
                    # Also check case-insensitive match as fallback
                    elif f"@{bot_username}".lower() == mention_text.lower():
                        is_mentioned = True
                        logger.info(f"✅ Bot mention detected via entity (case-insensitive): {mention_text}")
                        break
                    else:
                        logger.debug(f"🔍 Mention '{mention_text}' does not match bot username '@{bot_username}'")
        
        # Also check plain text for mentions (fallback) - case-insensitive
        if not is_mentioned and bot_username:
            # Check both case-sensitive and case-insensitive
            if f"@{bot_username}" in message_text or f"@{bot_username.lower()}" in message_text.lower():
                is_mentioned = True
                logger.info(f"✅ Bot mention detected via text search: @{bot_username}")
        elif not is_mentioned:
            # Check if there are any mentions at all (for debugging)
            if "@" in message_text:
                logger.debug(f"🔍 Message contains @ but no bot mention found. Bot username: @{bot_username}")
        
        # Enhanced debug logging for mention detection
        logger.info(f"🔍 Group {group_id} message analysis:")
        logger.info(f"  - Message: '{message_text[:50]}...'")
        logger.info(f"  - Bot username: @{bot_username}")
        logger.info(f"  - Is mentioned: {is_mentioned}")
        logger.info(f"  - Is reply to bot: {is_reply_to_bot}")
        logger.info(f"  - Entities: {[e.type for e in (message.entities or [])]}")
        
        # Additional safety check: Only respond if we have a valid bot username
        if (is_mentioned or is_reply_to_bot) and not bot_username:
            logger.warning(f"⚠️ Skipping response - bot username is None but mention/reply detected")
            return
        
        # ========================================================================
        # ENSURE GROUP SETTINGS EXIST (create from user defaults if needed)
        # This must happen before indexing so we can properly check kb_indexation_enabled
        # ========================================================================
        
        # Reload settings if needed (in case auto-init just created the group)
        current_group_settings = await moderation_service.get_group_settings(group_id)
        
        # If still no settings exist, create them from user's default template
        if not current_group_settings:
            logger.info(f"📝 Creating group settings from user defaults for group {group_id}, user {user_id}")
            try:
                current_group_settings = await moderation_service.create_group_settings_from_user_defaults(
                    user_id=user_id,
                    group_id=group_id
                )
                logger.info(f"✅ Created group settings from user {user_id} defaults for group {group_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create group settings from user defaults: {e}")
                # Continue without settings (fail-safe mode)
        
        # Update the group_settings variable for use below
        if current_group_settings:
            group_settings = current_group_settings
        
        # ========================================================================
        # MESSAGE INDEXING (respects group settings)
        # ========================================================================
        
        # Check if Elasticsearch is enabled
        if settings.ELASTICSEARCH_ENABLED and message_text:
            try:
                # Get KB index
                group_service = await get_group_service()
                kb_index = await group_service.get_group_kb_index(group_id)
                
                if kb_index:
                    # Check if KB indexation is enabled in group settings
                    # If settings exist and indexing is enabled, we index
                    # If settings don't exist (shouldn't happen now), don't index
                    should_index = False
                    if current_group_settings:
                        should_index = current_group_settings.kb_indexation_enabled
                        logger.debug(f"📋 Group settings: KB indexation = {should_index}")
                    else:
                        # This shouldn't happen anymore since we create settings above
                        logger.debug(f"⚠️ No group settings available, skipping indexing")
                        should_index = False
                    
                    if should_index:
                        logger.debug(f"📝 Indexing group message to {kb_index}")
                        
                        # Import utilities for double-write
                        from luka_bot.utils.document_id_generator import DocumentIDGenerator
                        from luka_bot.services.camunda_service import get_camunda_service
                        from luka_bot.services.thread_service import get_thread_service
                        
                        # Get thread context
                        thread_service = get_thread_service()
                        thread = await thread_service.get_group_thread(group_id)
                        
                        # Use Telegram's message_thread_id for supergroup topics if available
                        thread_id_value = str(message.message_thread_id) if getattr(message, "message_thread_id", None) else ""
                        
                        # Generate document ID upfront
                        kb_doc_id = DocumentIDGenerator.generate_group_message_id(
                            user_id=user_id,
                            group_id=group_id,
                            telegram_message_id=message.message_id,
                            thread_id=thread_id_value if thread_id_value else None
                        )
                        
                        # Prepare message data with document ID
                        sender_name = message.from_user.full_name if message.from_user else "Unknown"
                        group_name = message.chat.title or f"Group {group_id}"

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
                            "group_id": str(group_id),
                            "user_id": str(user_id),
                            "group_name": group_name,  # Group title for config_chatHumanName
                            "role": "user",  # Group messages are always from users
                            "thread_id": thread_id_value,  # Telegram's message_thread_id (for topics)
                            "telegram_topic_id": thread_id_value,  # Telegram's native topic ID (for supergroups)
                            "message_text": message_text,
                            "message_date": message.date.isoformat() if message.date else datetime.utcnow().isoformat(),
                            "sender_name": sender_name,
                            "reply_to_message_id": f"{group_id}_{message.reply_to_message.message_id}" if message.reply_to_message else "",
                            "parent_message_text": parent_message_text,
                            "parent_message_id": parent_message_id,
                            "parent_message_user_id": parent_message_user_id,
                            "mentions": extract_mentions(message_text),
                            "hashtags": extract_hashtags(message_text),
                            "urls": extract_urls(message_text),
                            "media_type": message.content_type or "text",
                        }
                        
                        # Enhance message data with thread context if available
                        if thread:
                            camunda_service = get_camunda_service()
                            enhanced_message_data = await camunda_service._build_enhanced_message_data(message_data, thread)
                        else:
                            enhanced_message_data = message_data
                        
                        # Double-write: Call both services asynchronously
                        es_task = None
                        camunda_task = None
                        
                        try:
                            # Start both operations asynchronously
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
                                        message_type="GROUP_MESSAGE",
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
                                logger.debug(f"✅ Group message indexed: {kb_doc_id}")
                            elif es_success:
                                logger.debug(f"⚠️ Group message ES indexed but Camunda failed: {kb_doc_id}")
                            elif camunda_success:
                                logger.warning(f"⚠️ Group message Camunda succeeded but ES failed: {kb_doc_id}")
                            else:
                                logger.error(f"❌ Group message indexing failed: {kb_doc_id}")
                                
                        except Exception as e:
                            logger.error(f"❌ Error in group message double-write: {e}")
                            # Cancel any pending tasks
                            if es_task and not es_task.done():
                                es_task.cancel()
                            if camunda_task and not camunda_task.done():
                                camunda_task.cancel()
                    else:
                        logger.debug(f"⏭️  KB indexation disabled for group {group_id}, skipping message indexing")
                else:
                    logger.debug(f"⏭️  No KB index for group {group_id}, skipping message indexing")
            except Exception as e:
                logger.error(f"❌ Error indexing group message: {e}")
        
        # ========================================================================
        # AI ASSISTANT LOGIC (only responds to mentions/replies)
        # ========================================================================
        
        # Settings should already be loaded above, but reload to be safe
        if not group_settings:
            group_settings = await moderation_service.get_group_settings(group_id)
        
        # FAIL-SAFE: If settings unavailable, default to AI DISABLED (conservative)
        if not group_settings:
            logger.warning(f"⚠️ No group settings for {group_id} - defaulting to AI disabled (fail-safe)")
            return
        
        logger.info(f"🔍 Group {group_id} AI decision:")
        logger.info(f"  - Settings loaded: {group_settings is not None}")
        logger.info(f"  - AI enabled: {group_settings.ai_assistant_enabled if group_settings else 'N/A'}")
        logger.info(f"  - Silent mode: {group_settings.silent_mode if group_settings else 'N/A'}")
        logger.info(f"  - Should respond: {(is_mentioned or is_reply_to_bot) and group_settings.ai_assistant_enabled if group_settings else False}")
        
        # NEW BEHAVIOR:
        # - AI Enabled: Only respond to mentions and replies
        # - AI Disabled: Respond to nothing (completely disabled)
        
        if not group_settings.ai_assistant_enabled:
            # AI is disabled - completely ignore all messages
            logger.info(f"🔇 AI assistant disabled for group {group_id}, ignoring message")
            return
        
        # AI is enabled - ONLY respond to mentions and replies
        if not (is_mentioned or is_reply_to_bot):
            logger.debug(f"📭 No mention/reply detected in group {group_id}, skipping AI response")
            return
        
        # Bot should respond - log the interaction type
        interaction_type = "reply" if is_reply_to_bot else "mention"
        logger.info(f"🔔 Bot {interaction_type} in group {group_id} by user {user_id}")
        
        try:
            from aiogram.enums import ChatAction
            from luka_bot.services.llm_service import get_llm_service
            from luka_bot.utils.formatting import escape_html
            
            # Show typing indicator
            try:
                await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            except Exception as e:
                logger.debug(f"Skipped typing action: {e}")
            
            # Get LLM service
            llm_service = get_llm_service()
            
            # Get group thread
            from luka_bot.services.thread_service import get_thread_service
            thread_service = get_thread_service()
            group_thread = await thread_service.get_group_thread(group_id)
            
            if not group_thread:
                logger.warning(f"⚠️ No thread found for group {group_id}, cannot process mention")
                await message.reply("⚠️ Group not initialized. Please use /help to set up.")
                return
            
            # Get group language from thread
            group_language = group_thread.language
            
            # Build context for LLM
            sender_name = message.from_user.full_name or message.from_user.username or f"User {user_id}"
            
            # If this is a reply to bot, include the original bot message for context
            if is_reply_to_bot and bot_original_message:
                context_parts = [
                    f"[GROUP REPLY from {sender_name}]"
                ]
                if thread_id:
                    context_parts.append(f"[In topic/thread ID: {thread_id}]")
                # Include the original bot message that user is replying to
                truncated_original = bot_original_message[:200] + '...' if len(bot_original_message) > 200 else bot_original_message
                context_parts.append(f"[User is replying to your previous message: \"{truncated_original}\"]")
                context_parts.append(f"User's reply: {message_text}")
            else:
                context_parts = [f"[GROUP MESSAGE from {sender_name}]"]
                if thread_id:
                    context_parts.append(f"[In topic/thread ID: {thread_id}]")
                context_parts.append(message_text)
            
            # 🆕 ADD GROUP KB CONTEXT TO INFORM LLM
            if group_thread and group_thread.knowledge_bases:
                kb_index = group_thread.knowledge_bases[0]
                
                # Try to get message count from Elasticsearch
                try:
                    es_service = await get_elasticsearch_service()
                    # Get index stats using count API
                    try:
                        index_stats = await es_service.es.count(index=kb_index)
                        message_count = index_stats.get('count', 0)
                    except:
                        message_count = 0
                    
                    if message_count > 0:
                        context_parts.insert(0, 
                            f"[GROUP KB: This group has {message_count} searchable messages. "
                            f"Use search_knowledge_base tool if this question relates to previous group discussions.]"
                        )
                    else:
                        context_parts.insert(0,
                            "[GROUP KB: Use search_knowledge_base tool to search group message history if relevant.]"
                        )
                except Exception as e:
                    logger.debug(f"Could not get KB stats: {e}")
                    # Fallback: just mention KB is available
                    context_parts.insert(0,
                        "[GROUP KB: Use search_knowledge_base tool to search previous group messages if relevant.]"
                    )
            
            llm_input = "\n".join(context_parts)
            
            # Add language instruction if needed
            if group_language == "ru":
                llm_input += "\n\n[Respond in Russian (русский язык)]"
            
            # Stream response using group thread
            full_response = ""
            bot_message = None
            
            async for chunk in llm_service.stream_response(
                llm_input, 
                user_id=user_id, 
                thread_id=group_thread.thread_id,
                thread=group_thread  # Pass group thread for configuration
            ):
                # Handle tool notifications
                if isinstance(chunk, dict) and chunk.get("type") == "tool_notification":
                    tool_emoji = chunk.get("text", "🔧")
                    if bot_message:
                        try:
                            await message.bot.edit_message_text(
                                text=tool_emoji,
                                chat_id=message.chat.id,
                                message_id=bot_message.message_id
                            )
                        except Exception as e:
                            if "message is not modified" not in str(e).lower():
                                logger.debug(f"Failed to edit message: {e}")
                    else:
                        # message.reply() automatically preserves message_thread_id
                        logger.info(f"📤 GROUP_MESSAGES sending tool notification to chat_id={message.chat.id}")
                        bot_message = await message.reply(tool_emoji)
                    continue
                
                # Handle text chunks - ACCUMULATE, don't replace!
                if isinstance(chunk, str):
                    full_response += chunk
                    
                    # Update message periodically (every ~500 chars or at end)
                    if bot_message and len(full_response) % 500 < 50:
                        try:
                            await message.bot.edit_message_text(
                                text=escape_html(full_response),
                                chat_id=message.chat.id,
                                message_id=bot_message.message_id,
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            if "message is not modified" not in str(e).lower():
                                logger.debug(f"Failed to update message: {e}")
                    elif not bot_message and len(chunk) > 100:
                        # Send initial message once we have enough content
                        # message.reply() automatically preserves message_thread_id
                        logger.info(f"📤 GROUP_MESSAGES sending initial response to chat_id={message.chat.id}, length={len(chunk)}")
                        bot_message = await message.reply(
                            escape_html(chunk),
                            parse_mode="HTML"
                        )
            
            # Send or update final response
            if full_response:
                # Don't escape HTML if response contains KB snippets (they have proper HTML formatting)
                has_kb_snippets = '━━━━━━━━━━━━━━━━━━━━' in full_response
                if has_kb_snippets:
                    # KB snippets already have proper HTML formatting with <a href> tags
                    formatted_response = full_response
                else:
                    # Regular response - escape HTML for safety
                    formatted_response = escape_html(full_response)
                
                if bot_message:
                    try:
                        await message.bot.edit_message_text(
                            text=formatted_response,
                            chat_id=message.chat.id,
                            message_id=bot_message.message_id,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        if "message is not modified" not in str(e).lower():
                            logger.warning(f"⚠️  Failed final update: {e}")
                else:
                    # message.reply() automatically preserves message_thread_id
                    logger.info(f"📤 GROUP_MESSAGES sending final response to chat_id={message.chat.id}, length={len(formatted_response)}")
                    bot_message = await message.reply(
                        formatted_response,
                        parse_mode="HTML"
                    )
                
                logger.info(f"✅ Sent LLM response to group {group_id}: {len(full_response)} chars")
                
                # Track bot's reply for retroactive moderation (V2)
                if bot_message:
                    try:
                        from luka_bot.services.reply_tracker_service import get_reply_tracker_service
                        reply_tracker = get_reply_tracker_service()
                        await reply_tracker.track_reply(
                            chat_id=message.chat.id,
                            user_message_id=message.message_id,
                            bot_reply_id=bot_message.message_id
                        )
                    except Exception as e:
                        logger.warning(f"⚠️  [V2] Failed to track reply: {e}")
                
                # Index bot's response as well
                if settings.ELASTICSEARCH_ENABLED and bot_message:
                    bot_message_id = f"{group_id}_{bot_message.message_id}"
                    bot_message_data = {
                        "message_id": bot_message_id,
                        "group_id": str(group_id),
                        "user_id": str(bot_info.id),
                        "role": "assistant",
                        "thread_id": str(thread_id) if thread_id else "",
                        "message_text": full_response,
                        "message_date": datetime.utcnow().isoformat(),
                        "sender_name": bot_info.full_name,
                        "reply_to_message_id": f"{group_id}_{message.message_id}",
                        "mentions": [],
                        "hashtags": [],
                        "urls": [],
                        "media_type": "text",
                    }
                    
                    es_service = await get_elasticsearch_service()
                    await es_service.index_message_immediate(
                        index_name=kb_index,
                        document_id=bot_message_id,
                        message_data=bot_message_data
                    )
                
        except Exception as e:
            logger.error(f"❌ Error generating LLM response for group mention: {e}", exc_info=True)
            # message.reply() automatically preserves message_thread_id
            await message.reply(
                "❌ Sorry, I encountered an error while processing your message. Please try again."
            )
        
    except Exception as e:
        logger.error(f"❌ Error handling group message: {e}")
        # Don't raise - we don't want to break group functionality


async def _send_group_password_request_to_dm(message: Message, user_id: int, group_id: int):
    """Send password request to user's DM and notify group."""
    try:
        # Get group info
        group_title = message.chat.title or f"Group {group_id}"
        
        # Send password request to user's DM
        await message.bot.send_message(
            chat_id=user_id,
            text=f"🔐 <b>Password Required for Group Access</b>\n\n"
                 f"<b>Group:</b> {group_title}\n"
                 f"<b>Group ID:</b> <code>{group_id}</code>\n\n"
                 f"This bot is password-protected.\n"
                 f"Please enter the password to continue:",
            parse_mode="HTML"
        )
        
        # Send notification to group
        await message.reply(
            f"🔐 Password request sent to @{message.from_user.username or message.from_user.first_name}'s DMs.\n"
            f"Please check your private messages to continue.",
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Password request sent to DM for user {user_id} in group {group_id}")
        
    except Exception as e:
        logger.error(f"Failed to send password request to DM: {e}")
        # Fallback: send to group if DM fails
        await message.reply(
            "🔐 <b>Password Required</b>\n\n"
            "This bot is password-protected.\n"
            "Please enter the password to continue:",
            parse_mode="HTML"
        )
