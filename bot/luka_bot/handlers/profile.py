"""
/profile command handler - Phase 4 MVP.

Shows user profile with language selector.
Phase 4: Full i18n support.
Future: Bot preferences, running processes, agents, stats.
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.services.user_profile_service import get_user_profile_service
from luka_bot.services.elasticsearch_service import get_elasticsearch_service
from luka_bot.utils.i18n_helper import _, get_user_language
from luka_bot.keyboards.mode_reply import get_profile_mode_keyboard
from luka_bot.handlers.states import NavigationStates
from luka_bot.core.config import settings

router = Router()


async def get_kb_stats(user_id: int) -> dict:
    """
    Get knowledge base statistics for user.
    
    Returns dict with:
    - total_messages: int
    - kb_enabled: bool
    - kb_index: str or None
    """
    stats = {
        "total_messages": 0,
        "kb_enabled": settings.ELASTICSEARCH_ENABLED,
        "kb_index": None
    }
    
    if not settings.ELASTICSEARCH_ENABLED:
        return stats
    
    try:
        # Get user's KB index
        profile_service = get_user_profile_service()
        profile = await profile_service.get_profile(user_id)
        
        if not profile or not profile.kb_index:
            return stats
        
        stats["kb_index"] = profile.kb_index
        
        # Get message count from Elasticsearch
        es_service = await get_elasticsearch_service()
        
        try:
            # Use Elasticsearch count API
            result = await es_service.client.count(index=profile.kb_index)
            stats["total_messages"] = result.get("count", 0)
            logger.debug(f"📊 KB stats for user {user_id}: {stats['total_messages']} messages")
        except Exception as e:
            logger.warning(f"⚠️  Failed to get KB count for {profile.kb_index}: {e}")
            # Index might not exist yet - that's OK
            stats["total_messages"] = 0
            
    except Exception as e:
        logger.error(f"❌ Error getting KB stats for user {user_id}: {e}")
    
    return stats


@router.message(Command("profile"))
async def handle_profile(message: Message, state: FSMContext) -> None:
    """
    Handle /profile command - show user profile (MVP).
    
    Phase 4: Basic profile with language selector + i18n + PROFILE_MODE keyboard.
    Phase 5+: Bot preferences, running processes, agents, stats.
    """
    user_id = message.from_user.id if message.from_user else None
    
    if not user_id:
        return
    
    logger.info(f"👤 /profile from user {user_id}")
    
    try:
        # Set navigation state to groups_mode (since we show groups keyboard)
        await state.set_state(NavigationStates.groups_mode)
        
        # Get user profile and language
        profile_service = get_user_profile_service()
        profile = await profile_service.get_or_create_profile(user_id, message.from_user)
        lang = profile.language
        
        # Get KB stats
        kb_stats = await get_kb_stats(user_id)
        
        # Build profile text with i18n
        display_name = profile.get_display_name()
        language_display = "🇬🇧 English" if profile.language == "en" else "🇷🇺 Русский"
        onboarding_status = _('profile.onboarding_complete', lang) if profile.is_blocked else _('profile.onboarding_pending', lang)
        
        # KB stats section
        kb_section = ""
        if kb_stats["kb_enabled"]:
            kb_status = "✅ Active" if kb_stats["kb_index"] else "⏳ Pending"
            kb_section = f"""
📚 <b>Knowledge Base:</b>
• Status: {kb_status}
• Messages indexed: {kb_stats['total_messages']}
"""
        else:
            kb_section = """
📚 <b>Knowledge Base:</b>
• Status: ❌ Disabled
"""
        
        profile_text = f"""{_('profile.title', lang)}

{_('profile.user_info', lang)}
{_('profile.name', lang, name=display_name)}
{_('profile.user_id', lang, user_id=user_id)}
{_('profile.username', lang, username=profile.username or "N/A")}

{_('profile.settings', lang)}

{_('profile.language', lang, lang_name=language_display)}
{_('profile.onboarding', lang, status=onboarding_status)}

{_('profile.statistics', lang)}
{_('profile.joined', lang, date=profile.created_at.strftime('%Y-%m-%d'))}
{kb_section}
{_('profile.coming_soon', lang)}
{_('profile.bot_preferences', lang)}
{_('profile.running_processes', lang)}
{_('profile.agents', lang)}
{_('profile.stats', lang)}"""
        
        # Profile actions keyboard (inline)
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_('profile.btn_change_language', lang), callback_data="profile_language")],
            [InlineKeyboardButton(text=_('profile.btn_preferences', lang), callback_data="profile_preferences")],
            [InlineKeyboardButton(text=_('profile.btn_processes', lang), callback_data="profile_processes")],
            [InlineKeyboardButton(text=_('common.close', lang), callback_data="profile_close")],
        ])
        
        # Get persistent groups keyboard instead of profile-specific keyboard
        from luka_bot.services.group_service import get_group_service
        from luka_bot.keyboards.groups_menu import get_groups_keyboard, get_empty_groups_keyboard
        
        group_service = await get_group_service()
        group_links = await group_service.list_user_groups(user_id, active_only=True)
        
        if group_links:
            reply_keyboard = await get_groups_keyboard(
                group_links,
                current_group_id=None,
                language=lang
            )
        else:
            reply_keyboard = await get_empty_groups_keyboard(language=lang)
        
        # Send profile with persistent groups keyboard
        await message.answer(profile_text, reply_markup=reply_keyboard, parse_mode="HTML")
        
        # Send inline menu as separate message
        await message.answer(
            _('profile.actions_prompt', lang),
            reply_markup=inline_keyboard,
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Showed PROFILE_MODE keyboard and profile to user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in /profile handler: {e}")
        lang = await get_user_language(user_id)
        from luka_bot.utils.i18n_helper import get_error_message
        await message.answer(get_error_message("generic", lang))


@router.callback_query(lambda c: c.data == "profile_language")
async def handle_profile_language(callback: CallbackQuery) -> None:
    """Show language selection menu."""
    user_id = callback.from_user.id if callback.from_user else None
    
    if not user_id:
        await callback.answer("Error: User ID not found")
        return
    
    # Get current language
    profile_service = get_user_profile_service()
    profile = await profile_service.get_profile(user_id)
    lang = profile.language if profile else "en"
    
    language_display = "English" if lang == "en" else "Русский"
    language_text = f"""{_('profile.language_selection', lang)}

{_('profile.current_language', lang, lang_name=language_display)}

{_('profile.select_language', lang)}"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{'✅ ' if lang == 'en' else ''}🇬🇧 English",
                callback_data="lang_en"
            ),
            InlineKeyboardButton(
                text=f"{'✅ ' if lang == 'ru' else ''}🇷🇺 Русский",
                callback_data="lang_ru"
            ),
        ],
        [InlineKeyboardButton(text=_('common.back', lang), callback_data="profile_back")],
    ])
    
    await callback.message.edit_text(language_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("lang_"))
async def handle_language_change(callback: CallbackQuery) -> None:
    """Handle language change from profile."""
    user_id = callback.from_user.id if callback.from_user else None
    
    if not user_id:
        await callback.answer("Error: User ID not found")
        return
    
    try:
        # Parse new language
        new_lang = callback.data.split("_", 1)[1]  # "en" or "ru"
        
        # Update language
        profile_service = get_user_profile_service()
        await profile_service.update_language(user_id, new_lang)
        
        # Get profile after update to ensure it exists
        profile = await profile_service.get_profile(user_id)
        
        if not profile:
            logger.error(f"❌ Profile not found after language update for user {user_id}")
            await callback.answer("Error: Profile not found", show_alert=True)
            return
        
        # Show confirmation with new language
        language_display = "English" if new_lang == "en" else "Русский"
        confirmation_text = f"""{_('profile.language_changed', new_lang)}

{_('profile.language_now', new_lang, lang_name=language_display)}

{_('profile.ui_updated', new_lang, lang_name=language_display)}"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_('common.back', new_lang), callback_data="profile_back")],
        ])
        
        await callback.message.edit_text(confirmation_text, reply_markup=keyboard, parse_mode="HTML")
        
        # Update command menu for this user in their new language
        from aiogram.types import BotCommand, BotCommandScopeChat
        from luka_bot.keyboards.default_commands import private_commands_by_language
        
        command_list = [
            BotCommand(command=cmd, description=desc)
            for cmd, desc in private_commands_by_language[new_lang].items()
        ]
        
        try:
            await callback.bot.set_my_commands(
                command_list,
                scope=BotCommandScopeChat(chat_id=user_id),
            )
            logger.info(f"✅ Updated command menu for user {user_id} to {new_lang}")
        except Exception as cmd_error:
            logger.warning(f"⚠️  Failed to update command menu: {cmd_error}")
        
        await callback.answer()
        
        logger.info(f"✅ Changed language for user {user_id} to {new_lang}")
        
    except Exception as e:
        logger.error(f"❌ Error changing language: {e}")
        await callback.answer("Error changing language", show_alert=True)


@router.callback_query(lambda c: c.data == "profile_back")
async def handle_profile_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Go back to profile main menu."""
    user_id = callback.from_user.id if callback.from_user else None
    
    if not user_id:
        return
    
    # Clear process list context when returning to profile
    await state.update_data({"process_list_context": None})
    
    # Re-show profile by simulating the command
    # Create a fake message object
    await callback.message.delete()
    await callback.answer()
    
    # Get profile and language
    profile_service = get_user_profile_service()
    profile = await profile_service.get_profile(user_id)
    lang = profile.language if profile else "en"
    
    # Get KB stats
    kb_stats = await get_kb_stats(user_id)
    
    # Build profile text
    display_name = profile.get_display_name() if profile else "User"
    language_display = "🇬🇧 English" if lang == "en" else "🇷🇺 Русский"
    onboarding_status = _('profile.onboarding_complete', lang) if (profile and profile.is_blocked) else _('profile.onboarding_pending', lang)
    
    # KB stats section
    kb_section = ""
    if kb_stats["kb_enabled"]:
        kb_status = "✅ Active" if kb_stats["kb_index"] else "⏳ Pending"
        kb_section = f"""
📚 <b>Knowledge Base:</b>
• Status: {kb_status}
• Messages indexed: {kb_stats['total_messages']}
"""
    else:
        kb_section = """
📚 <b>Knowledge Base:</b>
• Status: ❌ Disabled
"""
    
    profile_text = f"""{_('profile.title', lang)}

{_('profile.user_info', lang)}
{_('profile.name', lang, name=display_name)}
{_('profile.user_id', lang, user_id=user_id)}
{_('profile.username', lang, username=(profile.username if profile and profile.username else "N/A"))}

{_('profile.settings', lang)}
{_('profile.language', lang, lang_name=language_display)}
{_('profile.onboarding', lang, status=onboarding_status)}

{_('profile.statistics', lang)}
{_('profile.joined', lang, date=(profile.created_at.strftime('%Y-%m-%d') if profile else "N/A"))}
{kb_section}
{_('profile.coming_soon', lang)}
{_('profile.bot_preferences', lang)}
{_('profile.running_processes', lang)}
{_('profile.agents', lang)}
{_('profile.stats', lang)}"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_('profile.btn_change_language', lang), callback_data="profile_language")],
        [InlineKeyboardButton(text=_('profile.btn_preferences', lang), callback_data="profile_preferences")],
        [InlineKeyboardButton(text=_('profile.btn_processes', lang), callback_data="profile_processes")],
        [InlineKeyboardButton(text=_('common.close', lang), callback_data="profile_close")],
    ])
    
    await callback.message.answer(profile_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(lambda c: c.data == "profile_close")
async def handle_profile_close(callback: CallbackQuery) -> None:
    """Close profile menu."""
    await callback.message.delete()
    await callback.answer()


async def _fetch_and_display_processes(
    callback: CallbackQuery,
    state: FSMContext,
    page: int = 0
) -> None:
    """Helper function to fetch and display processes with pagination."""
    user_id = callback.from_user.id if callback.from_user else None
    
    if not user_id:
        await callback.answer("Error: User ID not found")
        return
    
    try:
        lang = await get_user_language(user_id)
        
        # Get user's processes
        from luka_bot.services.camunda_service import get_camunda_service
        camunda_service = get_camunda_service()
        client = await camunda_service._get_client(user_id)
        
        # Query for active processes
        from camunda_client.clients.engine.schemas import ProcessInstanceQuerySchema
        from datetime import datetime, timedelta
        from camunda_client.clients.engine.schemas.query import HistoryProcessInstanceQuerySchema
        
        active_query = ProcessInstanceQuerySchema(
            business_key_like=f"*_{user_id}",
            active=True
        )
        
        active_processes = await client.get_process_instances(active_query)
        
        # Query for recently completed processes (last 24 hours)
        # Format datetime with timezone (Camunda requirement: ISO 8601 with timezone)
        finished_after_dt = datetime.now() - timedelta(days=1)
        # Camunda expects format like: 2025-10-15T13:00:33.000+0000
        finished_after_str = finished_after_dt.strftime('%Y-%m-%dT%H:%M:%S.000+0000')
        
        history_query = HistoryProcessInstanceQuerySchema(
            business_key_like=f"*_{user_id}",
            finished=True,
            finished_after=finished_after_str
        )
        
        completed_processes = await client.get_history_process_instances(history_query)
        
        # Combine all processes
        all_processes = []
        
        # Add active processes
        for proc in active_processes:
            all_processes.append({
                'id': proc.id,
                'name': proc.process_definition_name or proc.process_definition_key or 'Unknown Process',
                'status': '⏸️' if proc.suspended else '▶️',
                'suspended': proc.suspended,
                'active': True
            })
        
        # Add recently completed
        for proc in completed_processes:
            proc_name = getattr(proc, 'process_definition_name', None) or getattr(proc, 'process_definition_key', None) or 'Unknown Process'
            all_processes.append({
                'id': proc.id,
                'name': proc_name,
                'status': '✅',
                'suspended': False,
                'active': False
            })
        
        # Sort to ensure active processes always appear first
        all_processes.sort(key=lambda p: (not p['active'], p['name']))
        
        if not all_processes:
            message_text = f"""<b>🔄 Your Processes</b>

You have no active or recent processes.

<i>Processes will appear here when you start workflows in groups.</i>"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=_('common.back', lang), callback_data="profile_back")]
            ])
            
            await callback.message.edit_text(
                message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        # Pagination settings
        PAGE_SIZE = 10
        total_count = len(all_processes)
        total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE  # Ceiling division
        
        # Validate page number
        page = max(0, min(page, total_pages - 1))
        
        # Get processes for current page
        start_idx = page * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        page_processes = all_processes[start_idx:end_idx]
        
        # Build process list message
        process_text = f"""<b>🔄 Your Processes</b>

<i>Active and recently completed (last 24h)</i>

"""
        
        # Build inline keyboard with process buttons
        keyboard_rows = []
        
        for proc in page_processes:
            # Truncate long names
            display_name = proc['name'][:35] + '...' if len(proc['name']) > 35 else proc['name']
            
            button_text = f"{proc['status']} {display_name}"
            
            # Use existing process_settings callback
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"process_settings:{proc['id'][:8]}"
                )
            ])
        
        # Add pagination controls if needed
        if total_pages > 1:
            pagination_row = []
            
            # Previous button
            if page > 0:
                pagination_row.append(
                    InlineKeyboardButton(
                        text="◀️ Previous",
                        callback_data=f"process_page:{page - 1}"
                    )
                )
            
            # Page indicator (non-clickable, just shows info)
            pagination_row.append(
                InlineKeyboardButton(
                    text=f"📄 {page + 1}/{total_pages}",
                    callback_data=f"process_page_info:{page}"
                )
            )
            
            # Next button
            if page < total_pages - 1:
                pagination_row.append(
                    InlineKeyboardButton(
                        text="Next ▶️",
                        callback_data=f"process_page:{page + 1}"
                    )
                )
            
            keyboard_rows.append(pagination_row)
            
            # Add count info
            process_text += f"\n<i>Showing {start_idx + 1}-{min(end_idx, total_count)} of {total_count} processes</i>\n"
        
        # Add back button
        keyboard_rows.append([
            InlineKeyboardButton(
                text=_('common.back', lang),
                callback_data="profile_back"
            )
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
        
        # Store ALL process IDs in state for process_settings handler
        await state.update_data({
            "process_list_context": {
                "processes": {p['id']: p for p in all_processes},
                "from_profile": True,
                "current_page": page,
                "total_pages": total_pages
            }
        })
        
        await callback.message.edit_text(
            process_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await callback.answer()
        
        logger.info(f"✅ Showed page {page + 1}/{total_pages} ({len(page_processes)} processes) for user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error showing processes for user {user_id}: {e}")
        await callback.answer(
            "Error loading processes. Please try again.",
            show_alert=True
        )


@router.callback_query(lambda c: c.data == "profile_processes")
async def handle_profile_processes(callback: CallbackQuery, state: FSMContext) -> None:
    """Show list of user's running and recent processes (page 0)."""
    await _fetch_and_display_processes(callback, state, page=0)


@router.callback_query(lambda c: c.data and c.data.startswith("process_page:"))
async def handle_process_page(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle pagination for process list."""
    try:
        # Extract page number from callback data
        page = int(callback.data.split(":")[1])
        await _fetch_and_display_processes(callback, state, page=page)
    except (ValueError, IndexError) as e:
        logger.error(f"❌ Invalid page callback data: {callback.data}, error: {e}")
        await callback.answer("Invalid page number", show_alert=True)


@router.callback_query(lambda c: c.data and c.data.startswith("process_page_info:"))
async def handle_process_page_info(callback: CallbackQuery) -> None:
    """Handle click on page info button (just show current page)."""
    try:
        page = int(callback.data.split(":")[1])
        await callback.answer(f"Currently on page {page + 1}")
    except (ValueError, IndexError):
        await callback.answer()


@router.callback_query(lambda c: c.data == "profile_preferences")
async def handle_profile_preferences(callback: CallbackQuery) -> None:
    """Handle preferences - coming soon."""
    await callback.answer(
        "🚧 Coming Soon!\n\nBot preferences feature is under development.",
        show_alert=True
    )
