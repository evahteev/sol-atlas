"""
Handlers for inline group settings buttons (admin-only).
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from loguru import logger

from luka_bot.core.config import settings
from luka_bot.services.group_service import get_group_service
from luka_bot.utils.permissions import is_user_admin_in_group
from luka_bot.keyboards.group_settings_inline import (
    create_group_settings_inline,
    create_language_selection_menu,
    get_welcome_message_with_settings,
)

router = Router()


@router.callback_query(F.data.startswith("group_toggle_mod:"))
async def handle_group_moderation_toggle(callback: CallbackQuery):
    """Toggle moderation on/off - works for BOTH groups AND user defaults!"""
    try:
        id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        # Admin check (only for groups, not for user defaults)
        if id < 0:  # Group
            if not await is_user_admin_in_group(callback.bot, id, user_id):
                await callback.answer("⚠️ Admin only", show_alert=True)
                return
        
        group_id = id  # Keep for compatibility below
        
        # Get services
        from luka_bot.services.moderation_service import get_moderation_service
        from luka_bot.services.thread_service import get_thread_service
        from luka_bot.handlers.groups_enhanced import get_settings_for_id
        
        moderation_service = await get_moderation_service()
        thread_service = get_thread_service()
        group_service = await get_group_service()
        
        # Get current settings (works for both groups and user defaults!)
        group_settings = await get_settings_for_id(id)
        if not group_settings:
            await callback.answer("❌ Settings not found", show_alert=True)
            return
        
        # Toggle moderation
        group_settings.moderation_enabled = not group_settings.moderation_enabled
        await moderation_service.save_group_settings(group_settings)
        
        status = "enabled" if group_settings.moderation_enabled else "disabled"
        
        # Check if user defaults or group
        if id > 0:
            logger.info(f"👤 User {user_id} {status} moderation in defaults")
        else:
            logger.info(f"👑 Admin {user_id} {status} moderation in group {group_id}")
        
        # Get updated info
        if id < 0:  # Group
            thread = await thread_service.get_group_thread(group_id)
            group_language = thread.language if thread else "en"
        else:  # User defaults
            from luka_bot.utils.i18n_helper import get_user_language
            group_language = await get_user_language(user_id)
        
        # Check if we're in DM (admin menu) or in group (inline settings)
        # DM messages will have the comprehensive group info card (📊) or be in private chat
        is_dm = callback.message.chat.type == "private"
        
        if is_dm:
            await _render_moderation_menu(callback, id, user_id)
        else:
            from luka_bot.keyboards.group_settings_inline import create_group_settings_inline
            new_keyboard = create_group_settings_inline(
                group_id,
                current_language=group_language,
                moderation_enabled=group_settings.moderation_enabled
            )
            try:
                await callback.message.edit_reply_markup(reply_markup=new_keyboard)
            except Exception:
                pass

        if group_settings.moderation_enabled:
            message = "🛡️✅ Moderation enabled" if group_language != "ru" else "🛡️✅ Модерация включена"
            await callback.answer(message, show_alert=is_dm)
        else:
            message = "🛡️❌ Moderation disabled" if group_language != "ru" else "🛡️❌ Модерация отключена"
            await callback.answer(message, show_alert=False)
        
    except Exception as e:
        logger.error(f"Failed to toggle moderation: {e}", exc_info=True)
        await callback.answer("❌ Error toggling moderation", show_alert=True)





@router.callback_query(F.data.startswith("group_lang_menu:"))
async def handle_group_language_menu(callback: CallbackQuery):
    """Show language selection submenu - works for BOTH groups AND user defaults!"""
    try:
        id = int(callback.data.split(":")[1])
        
        # Check if user is admin (only for groups, not user defaults)
        if id < 0:  # Group
            is_admin = await is_user_admin_in_group(callback.bot, id, callback.from_user.id)
            if not is_admin:
                await callback.answer("🔒 Admin only", show_alert=True)
                return
        
        group_id = id  # Keep for compatibility
        
        # Get current language
        group_service = await get_group_service()
        if id > 0:  # User defaults
            from luka_bot.utils.i18n_helper import get_user_language
            current_language = await get_user_language(callback.from_user.id)
        else:  # Group
            current_language = await group_service.get_group_language(group_id)
        
        # Show language selection menu
        lang_menu = create_language_selection_menu(group_id, current_language)
        
        await callback.message.edit_reply_markup(reply_markup=lang_menu)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Failed to show language menu: {e}", exc_info=True)
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("group_lang_back:"))
async def handle_group_language_back(callback: CallbackQuery):
    """Return to main settings from language menu - works for BOTH groups AND user defaults!"""
    try:
        id = int(callback.data.split(":")[1])
        
        # Route based on context
        if id > 0:  # User defaults - back to defaults menu
            from luka_bot.handlers.group_admin import refresh_admin_menu_simple
            await refresh_admin_menu_simple(callback, id)
        else:  # Group - back to in-group settings
            group_id = id
            
            # Get current language
            group_service = await get_group_service()
            current_language = await group_service.get_group_language(group_id)
            
            # Restore main settings keyboard
            # Get moderation status
            from luka_bot.services.moderation_service import get_moderation_service
            moderation_service = await get_moderation_service()
            group_settings = await moderation_service.get_group_settings(group_id)
            moderation_enabled = group_settings.moderation_enabled if group_settings else False
            
            main_keyboard = create_group_settings_inline(group_id, current_language, moderation_enabled)
            
            await callback.message.edit_reply_markup(reply_markup=main_keyboard)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Failed to go back: {e}", exc_info=True)
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("group_set_lang:"))
async def handle_group_language_change(callback: CallbackQuery):
    """Handle language change - works for BOTH groups AND user defaults!"""
    try:
        # Parse callback data
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        
        id = int(parts[1])
        new_language = parts[2]  # en or ru
        
        # Check if user is admin (only for groups, not user defaults)
        if id < 0:  # Group
            is_admin = await is_user_admin_in_group(callback.bot, id, callback.from_user.id)
            if not is_admin:
                await callback.answer("🔒 Admin only", show_alert=True)
                return
        
        group_id = id  # Keep for compatibility
        
        # Get services
        from luka_bot.services.moderation_service import get_moderation_service
        moderation_service = await get_moderation_service()
        group_service = await get_group_service()
        
        # Get old language based on context
        if id > 0:  # User defaults
            from luka_bot.utils.i18n_helper import get_user_language
            old_language = await get_user_language(callback.from_user.id)
        else:  # Group
            old_language = await group_service.get_group_language(group_id)
        
        # Skip if same language
        if old_language == new_language:
            await callback.answer("✅ Already using this language")
            
            # Refresh menu based on context
            if id > 0:  # User defaults - refresh defaults menu
                from luka_bot.handlers.group_admin import refresh_admin_menu_simple
                await refresh_admin_menu_simple(callback, id)
            else:  # Group - restore main keyboard
                group_settings = await moderation_service.get_group_settings(group_id)
                moderation_enabled = group_settings.moderation_enabled if group_settings else False
                main_keyboard = create_group_settings_inline(group_id, new_language, moderation_enabled)
                await callback.message.edit_reply_markup(reply_markup=main_keyboard)
            return
        
        # Update language based on context
        if id > 0:  # User defaults
            # Update user's language preference via profile service
            from luka_bot.services.user_profile_service import get_user_profile_service
            profile_service = get_user_profile_service()
            success = await profile_service.update_language(callback.from_user.id, new_language)
            
            # Also update language in GroupSettings (user defaults template)
            if success:
                try:
                    user_defaults = await moderation_service.get_or_create_user_default_settings(callback.from_user.id)
                    user_defaults.language = new_language
                    await moderation_service.save_group_settings(user_defaults)
                    logger.info(f"🌍 Updated language in user defaults template for user {callback.from_user.id}: {new_language}")
                except Exception as e:
                    logger.error(f"❌ Error updating language in user defaults: {e}")
                    # Don't fail the whole operation if this fails
        else:  # Group
            success = await group_service.update_group_language(group_id, new_language)
            
            # Also update language in GroupSettings if it exists
            if success:
                try:
                    group_settings = await moderation_service.get_group_settings(group_id)
                    if group_settings:
                        group_settings.language = new_language
                        await moderation_service.save_group_settings(group_settings)
                        logger.info(f"🌍 Updated language in group settings for group {group_id}: {new_language}")
                except Exception as e:
                    logger.error(f"❌ Error updating language in group settings: {e}")
                    # Don't fail the whole operation if this fails
        
        if not success:
            await callback.answer("❌ Failed to update language", show_alert=True)
            return
        
        # Notify user
        lang_name = "🇬🇧 English" if new_language == "en" else "🇷🇺 Русский"
        await callback.answer(f"✅ Language changed to {lang_name}")
        
        # If user defaults, just refresh the menu and return
        if id > 0:
            from luka_bot.handlers.group_admin import refresh_admin_menu_simple
            await refresh_admin_menu_simple(callback, id)
            return
        
        # Group-specific logic continues below (only for groups)
        from luka_bot.services.thread_service import get_thread_service
        thread_service = get_thread_service()
        thread = await thread_service.get_group_thread(group_id)
        
        if not thread:
            await callback.answer("❌ Thread not found", show_alert=True)
            return
        
        kb_index = thread.knowledge_bases[0] if thread.knowledge_bases else "not-set"
        
        # Get group title
        try:
            chat = await callback.bot.get_chat(group_id)
            group_title = chat.title or f"Group {group_id}"
        except:
            group_title = f"Group {group_id}"
        
        # Instead of editing welcome message, navigate back to comprehensive admin menu
        # The admin is in DM, so we should show the admin settings card
        
        # Build comprehensive admin info card in new language
        from luka_bot.keyboards.group_admin import create_group_admin_menu
        
        # Get moderation settings
        group_settings = await moderation_service.get_group_settings(group_id)
        moderation_enabled = group_settings.moderation_enabled if group_settings else False
        stoplist_count = len(group_settings.stoplist_words) if group_settings else 0
        
        # Get user who added the bot
        added_by_name = "Unknown"
        try:
            group_link = await group_service.get_group_link(callback.from_user.id, group_id)
            if group_link and group_link.added_by_name:
                added_by_name = group_link.added_by_name
        except:
            pass
        
        # Get group type
        group_type = "Group"
        group_type_icon = "👥"
        try:
            chat_info = await callback.bot.get_chat(group_id)
            if chat_info.type == "supergroup":
                group_type = "Supergroup"
                group_type_icon = "👥📌"
        except:
            pass
        
        # Language flag
        lang_flag = "🇬🇧 English" if new_language == "en" else "🇷🇺 Русский"
        
        # Status
        status_text = "Active and indexing" if new_language == "en" else "Активен и индексирует"
        
        # Build info text in new language
        if new_language == "en":
            info_text = f"""📊 <b>{group_title}</b>

<b>Setup Complete:</b>
• {group_type_icon} Type: {group_type}
• 🆔 Group ID: <code>{group_id}</code>
• 📚 KB Index: <code>{kb_index}</code>
• 👤 Added by: {added_by_name}
• 🌍 Language: {lang_flag}
• ✅ Status: {status_text}

<i>Use buttons below to manage group settings:</i>"""
        else:  # Russian
            info_text = f"""📊 <b>{group_title}</b>

<b>Настройка завершена:</b>
• {group_type_icon} Тип: {group_type}
• 🆔 ID группы: <code>{group_id}</code>
• 📚 KB Index: <code>{kb_index}</code>
• 👤 Добавил: {added_by_name}
• 🌍 Язык: {lang_flag}
• ✅ Статус: {status_text}

<i>Используйте кнопки ниже для управления настройками:</i>"""
        
        # Create admin menu keyboard
        admin_keyboard = create_group_admin_menu(
            group_id, 
            group_title,
            moderation_enabled,
            stoplist_count,
            new_language,
            silent_mode=group_settings.silent_mode if group_settings else False,
            ai_assistant_enabled=group_settings.ai_assistant_enabled if group_settings else True,
            kb_indexation_enabled=group_settings.kb_indexation_enabled if group_settings else True,
            moderate_admins_enabled=group_settings.moderate_admins_enabled if group_settings else False
        )
        
        # Edit message to show admin menu
        await callback.message.edit_text(
            info_text,
            reply_markup=admin_keyboard,
            parse_mode="HTML"
        )
        
        logger.info(f"🌍 Admin {callback.from_user.id} changed group {group_id} language: {old_language} → {new_language}")
        
        # Generate LLM confirmation message in the new language
        try:
            from luka_bot.services.llm_service import get_llm_service
            from luka_bot.agents.context import ConversationContext
            from luka_bot.agents.agent_factory import create_static_agent_with_basic_tools
            
            lang_emoji = "🇬🇧" if new_language == "en" else "🇷🇺"
            lang_full = "English" if new_language == "en" else "Russian (Русский)"
            
            # Build LLM prompt for language change confirmation
            if new_language == "en":
                llm_prompt = f"""You just changed the language setting for the Telegram group "{group_title}" to English.

Write a SHORT (2-3 sentences max), cheerful confirmation message that:
- Confirms the language was changed to English
- Shows excitement about communicating in English
- Encourages them to try asking you something

Be warm, natural, and conversational. You are {bot_name}."""
            else:  # Russian
                llm_prompt = f"""Вы только что изменили настройки языка для Telegram группы "{group_title}" на Русский.

Напишите КОРОТКОЕ (максимум 2-3 предложения), жизнерадостное подтверждающее сообщение, которое:
- Подтверждает, что язык был изменен на Русский
- Показывает энтузиазм по поводу общения на Русском
- Призывает их попробовать задать вам вопрос

Будьте тепл(ой/ым), естественн(ой/ым) и разговорчив(ой/ым). Вы - {bot_name}.

ВАЖНО: Отвечайте ТОЛЬКО на русском языке."""
            
            # Create context
            ctx = ConversationContext(
                user_id=callback.from_user.id,
                thread_id=None,
                thread_knowledge_bases=[kb_index] if kb_index else []
            )
            
            # Generate LLM response
            agent = await create_static_agent_with_basic_tools(callback.from_user.id)
            result = await agent.run(llm_prompt, deps=ctx)
            
            # Extract text from AgentRunResult
            if hasattr(result, 'data'):
                llm_message = str(result.data)
            elif hasattr(result, 'output'):
                llm_message = str(result.output)
            else:
                llm_message = str(result)
            
            # Clean up text
            if llm_message.startswith("AgentRunResult("):
                import re
                match = re.search(r"output='([^']*(?:\\.[^']*)*)'", llm_message)
                if match:
                    llm_message = match.group(1).replace("\\'", "'").replace("\\n", "\n")
            
            # Send LLM confirmation message to the group
            await callback.bot.send_message(
                chat_id=group_id,
                text=f"{lang_emoji} {llm_message}",
                parse_mode="HTML"
            )
            
            logger.info(f"✅ Sent LLM language confirmation for group {group_id}")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to generate LLM confirmation: {e}")
            # Non-critical, language change was successful anyway
        
    except Exception as e:
        logger.error(f"Failed to handle language change: {e}", exc_info=True)
        await callback.answer("❌ Error updating language", show_alert=True)


@router.callback_query(F.data.startswith("group_settings_menu:"))
async def handle_group_settings_menu(callback: CallbackQuery):
    """Handle settings menu button - shows same comprehensive view as /groups -> group name."""
    try:
        group_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        # Check if admin
        is_admin = await is_user_admin_in_group(callback.bot, group_id, user_id)
        if not is_admin:
            await callback.answer("🔒 Admin only", show_alert=True)
            return
        
        # Get services
        from luka_bot.keyboards.group_admin import create_group_admin_menu
        from luka_bot.services.thread_service import get_thread_service
        from luka_bot.services.moderation_service import get_moderation_service
        
        group_service = await get_group_service()
        thread_service = get_thread_service()
        moderation_service = await get_moderation_service()
        
        # Get thread info
        thread = await thread_service.get_group_thread(group_id)
        
        if not thread:
            await callback.answer("❌ Group info not found", show_alert=True)
            return
        
        # Get moderation settings
        group_settings = await moderation_service.get_group_settings(group_id)
        moderation_enabled = group_settings.moderation_enabled if group_settings else False
        stoplist_count = len(group_settings.stoplist_words) if group_settings else 0
        
        # Build info card
        group_title = thread.name or f"Group {group_id}"
        kb_index = thread.knowledge_bases[0] if thread.knowledge_bases else "Not set"
        language = thread.language
        
        # Get user who added the bot
        added_by_name = "Unknown"
        try:
            group_link = await group_service.get_group_link(user_id, group_id)
            if group_link and group_link.added_by_name:
                added_by_name = group_link.added_by_name
        except:
            pass
        
        # Get group type
        group_type = "Group"
        group_type_icon = "👥"
        try:
            chat_info = await callback.bot.get_chat(group_id)
            if chat_info.type == "supergroup":
                group_type = "Supergroup"
                group_type_icon = "👥📌"
        except:
            pass
        
        # Language flag
        lang_flag = "🇬🇧 English" if language == "en" else "🇷🇺 Русский"
        
        # Status
        status_text = "Active and indexing" if language == "en" else "Активен и индексирует"
        
        # Build info text
        if language == "en":
            info_text = f"""📊 <b>{group_title}</b>

<b>Setup Complete:</b>
• {group_type_icon} Type: {group_type}
• 🆔 Group ID: <code>{group_id}</code>
• 📚 KB Index: <code>{kb_index}</code>
• 👤 Added by: {added_by_name}
• 🌍 Language: {lang_flag}
• ✅ Status: {status_text}

<i>Use buttons below to manage group settings:</i>"""
        else:  # Russian
            info_text = f"""📊 <b>{group_title}</b>

<b>Настройка завершена:</b>
• {group_type_icon} Тип: {group_type}
• 🆔 ID группы: <code>{group_id}</code>
• 📚 KB Index: <code>{kb_index}</code>
• 👤 Добавил: {added_by_name}
• 🌍 Язык: {lang_flag}
• ✅ Статус: {status_text}

<i>Используйте кнопки ниже для управления настройками:</i>"""
        
        # Create admin menu keyboard
        admin_keyboard = create_group_admin_menu(
            group_id, 
            group_title,
            moderation_enabled,
            stoplist_count,
            language,
            silent_mode=group_settings.silent_mode if group_settings else False,
            ai_assistant_enabled=group_settings.ai_assistant_enabled if group_settings else True,
            kb_indexation_enabled=group_settings.kb_indexation_enabled if group_settings else True,
            moderate_admins_enabled=group_settings.moderate_admins_enabled if group_settings else False
        )
        
        # Send to DM
        await callback.bot.send_message(
            user_id,
            info_text,
            reply_markup=admin_keyboard,
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Sent to DM")
        
    except Exception as e:
        logger.error(f"Failed to show settings menu: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("group_stats_inline:"))
async def handle_group_stats_inline(callback: CallbackQuery):
    """Handle stats button."""
    try:
        group_id = int(callback.data.split(":")[1])
        
        # Get group info
        group_service = await get_group_service()
        kb_index = await group_service.get_group_kb_index(group_id)
        language = await group_service.get_group_language(group_id)
        
        if language == "en":
            stats_text = f"""📊 <b>Group Statistics</b>

🆔 <b>Group ID:</b> <code>{group_id}</code>
📚 <b>KB Index:</b> <code>{kb_index or 'not-set'}</code>
🌍 <b>Language:</b> {'🇬🇧 English' if language == 'en' else '🇷🇺 Russian'}

<i>💡 More detailed stats coming soon!</i>"""
        else:
            stats_text = f"""📊 <b>Статистика группы</b>

🆔 <b>ID группы:</b> <code>{group_id}</code>
📚 <b>KB Index:</b> <code>{kb_index or 'не установлен'}</code>
🌍 <b>Язык:</b> {'🇬🇧 English' if language == 'en' else '🇷🇺 Русский'}

<i>💡 Подробная статистика скоро появится!</i>"""
        
        await callback.answer()
        await callback.message.answer(stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Failed to show stats: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("group_import_inline:"))
async def handle_group_import_inline(callback: CallbackQuery):
    """Handle import history button."""
    try:
        is_admin = await is_user_admin_in_group(
            callback.bot,
            int(callback.data.split(":")[1]),
            callback.from_user.id
        )
        if not is_admin:
            await callback.answer("🔒 Admin only", show_alert=True)
            return
        
        await callback.answer("📚 History import coming soon!", show_alert=True)
        
    except Exception as e:
        logger.error(f"Failed to handle import: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("group_threads_inline:"))
async def handle_group_threads_inline(callback: CallbackQuery):
    """Handle manage threads button."""
    try:
        is_admin = await is_user_admin_in_group(
            callback.bot,
            int(callback.data.split(":")[1]),
            callback.from_user.id
        )
        if not is_admin:
            await callback.answer("🔒 Admin only", show_alert=True)
            return
        
        await callback.answer("🔗 Thread management coming soon!", show_alert=True)
        
    except Exception as e:
        logger.error(f"Failed to handle threads: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("group_welcome_close:"))
async def handle_group_welcome_close(callback: CallbackQuery):
    """Handle close button on welcome message - deletes the message."""
    try:
        group_id = int(callback.data.split(":")[1])
        
        # Check if user is admin
        is_admin = await is_user_admin_in_group(callback.bot, group_id, callback.from_user.id)
        if not is_admin:
            await callback.answer("🔒 Admin only", show_alert=True)
            return
        
        # Delete the welcome message
        try:
            await callback.message.delete()
            logger.info(f"🗑️ Admin {callback.from_user.id} deleted welcome message in group {group_id}")
        except Exception as e:
            logger.warning(f"⚠️  Could not delete welcome message: {e}")
            await callback.answer("❌ Could not delete message", show_alert=True)
        
    except Exception as e:
        logger.error(f"Failed to handle welcome close: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("group_search_inline:"))
async def handle_group_search_inline(callback: CallbackQuery):
    """Handle search KB button."""
    try:
        group_service = await get_group_service()
        language = await group_service.get_group_language(int(callback.data.split(":")[1]))
        
        await callback.answer(_('group.search.tip', language), show_alert=True)
        
    except Exception as e:
        logger.error(f"Failed to handle search: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("group_reset_inline:"))
async def handle_group_reset_inline(callback: CallbackQuery):
    """Handle reset button - redirects to full reset flow."""
    try:
        group_id = int(callback.data.split(":")[1])
        
        # Check if admin
        is_admin = await is_user_admin_in_group(callback.bot, group_id, callback.from_user.id)
        if not is_admin:
            await callback.answer("🔒 Admin only", show_alert=True)
            return
        
        group_service = await get_group_service()
        language = await group_service.get_group_language(group_id)
        
        await callback.answer(_('group.reset.tip', language), show_alert=True)
        
    except Exception as e:
        logger.error(f"Failed to handle reset: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("group_backfill:"))
async def handle_group_backfill(callback: CallbackQuery):
    """
    Handle backfill request from group settings.
    Creates GroupLinks for all users who have posted in the group.
    """
    try:
        group_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        # Admin check
        if not await is_user_admin_in_group(callback.bot, group_id, user_id):
            await callback.answer("⚠️ Admin only", show_alert=True)
            return
        
        # Get language
        from luka_bot.services.thread_service import get_thread_service
        thread_service = get_thread_service()
        thread = await thread_service.get_group_thread(group_id)
        lang = thread.language if thread else "en"
        
        # Acknowledge immediately
        if lang == "en":
            await callback.answer("🔄 Starting backfill process...", show_alert=False)
        else:
            await callback.answer("🔄 Запуск процесса связывания...", show_alert=False)
        
        # Run backfill in background
        from luka_bot.scripts.backfill_group_links import backfill_single_group
        stats = await backfill_single_group(group_id)
        
        # Send result message
        if lang == "en":
            result_text = f"""✅ <b>Member Linking Complete</b>

Created: {stats['created']} new links
Skipped: {stats['skipped']} existing links
Errors: {stats['errors']}

Users who posted in this group can now see it in their /groups menu and search the group knowledge base."""
        else:
            result_text = f"""✅ <b>Связывание участников завершено</b>

Создано: {stats['created']} новых связей
Пропущено: {stats['skipped']} существующих
Ошибок: {stats['errors']}

Пользователи, писавшие в этой группе, теперь видят её в меню /groups и могут искать в базе знаний группы."""
        
        await callback.message.answer(result_text, parse_mode="HTML")
        
        logger.info(f"✅ Backfill completed for group {group_id} by admin {user_id}: {stats}")
        
    except Exception as e:
        logger.error(f"❌ Error handling backfill: {e}")
        await callback.answer("❌ Error running backfill", show_alert=True)

