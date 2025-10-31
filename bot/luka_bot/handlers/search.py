"""
/search command handler.

Provides KB search functionality with a dedicated chatbot_search thread.
Users can select which KB to search from an inline menu.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from loguru import logger
from datetime import datetime
import uuid

from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.user_profile_service import get_user_profile_service
from luka_bot.services.elasticsearch_service import get_elasticsearch_service
from luka_bot.keyboards.search_menu import get_search_kb_menu
from luka_bot.utils.i18n_helper import _
from luka_bot.utils.formatting import escape_html
from luka_bot.core.config import settings

router = Router(name="search")

# Special thread name for KB search
SEARCH_THREAD_NAME = "chatbot_search"


async def get_or_create_search_thread(user_id: int):
    """
    Get or create the special chatbot_search thread for KB search.
    This thread is persistent and dedicated to KB search functionality.
    """
    thread_service = get_thread_service()
    
    # Try to find existing search thread
    threads = await thread_service.list_threads(user_id)
    for thread in threads:
        if thread.name == SEARCH_THREAD_NAME:
            logger.info(f"Found existing search thread: {thread.thread_id}")
            return thread
    
    # Create new search thread using service API
    new_thread = await thread_service.create_thread(user_id, name=SEARCH_THREAD_NAME)
    
    # Apply search-specific settings
    new_thread.system_prompt = (
        "You are a helpful knowledge base search assistant. Your primary function is to search "
        "through available knowledge bases and provide accurate, relevant information to users."
    )
    new_thread.knowledge_bases = []
    await thread_service.update_thread(new_thread)
    
    logger.info(f"Created new search thread: {new_thread.thread_id}")
    
    return new_thread


async def get_available_kbs(user_id: int) -> list[dict]:
    """
    Get available knowledge bases for the user.
    
    Returns only:
    - User's personal KB
    - KBs for groups the user participates in (with real group names)
    
    Returns list of dicts with: {name, index, type, icon, description}
    """
    kbs = []
    profile_service = get_user_profile_service()
    user_lang = await profile_service.get_language(user_id)
    es_service = await get_elasticsearch_service()
    
    # 1. User's personal KB (exact match)
    user_kb_pattern = f"{settings.ELASTICSEARCH_USER_KB_PREFIX}{user_id}"
    user_indices = await es_service.list_indices(user_kb_pattern)
    
    for idx_info in user_indices:
        kbs.append({
            "name": _("search.kb.personal", language=user_lang),
            "index": idx_info["name"],
            "type": "user",
            "icon": "👤",
            "description": _("search.kb.personal_desc", language=user_lang, count=idx_info["doc_count"])
        })
    
    # 2. Group KBs - only for groups user participates in
    from luka_bot.services.group_service import get_group_service
    from luka_bot.services.thread_service import get_thread_service
    
    group_service = await get_group_service()
    thread_service = get_thread_service()
    
    # Get user's groups
    user_groups = await group_service.list_user_groups(user_id, active_only=True)
    
    for group_link in user_groups:
        # Build expected KB index name for this group
        group_id_str = str(group_link.group_id)
        # Handle negative group IDs: -1001234567890 -> 1001234567890 in index name
        if group_id_str.startswith('-'):
            group_id_str = group_id_str[1:]  # Remove leading dash
        
        kb_index = f"{settings.ELASTICSEARCH_GROUP_KB_PREFIX}{group_id_str}"
        
        # Check if this KB index exists in ES
        try:
            indices = await es_service.list_indices(kb_index)
            if not indices:
                continue  # No KB for this group yet
            
            idx_info = indices[0]  # Should be only one match
            
            # Get group name from thread
            thread = await thread_service.get_group_thread(group_link.group_id)
            group_name = thread.name if (thread and thread.name) else f"Group {group_link.group_id}"
            
            kbs.append({
                "name": group_name,
                "index": idx_info["name"],
                "type": "group",
                "icon": "👥",
                "description": _("search.kb.group_desc", language=user_lang, count=idx_info["doc_count"])
            })
            
        except Exception as e:
            logger.debug(f"Could not get KB for group {group_link.group_id}: {e}")
            continue
    
    logger.info(f"📚 Discovered {len(kbs)} KBs for user {user_id}: {len(user_indices)} user, {len(kbs) - len(user_indices)} group")
    return kbs


async def execute_direct_search(message: Message, user_id: int, keyword: str, state: FSMContext):
    """
    Execute a direct search with the provided keyword.
    Searches all available KBs and displays results with new card-based format.
    """
    try:
        # Get or create search thread
        search_thread = await get_or_create_search_thread(user_id)
        
        # Set as active thread
        await state.update_data(active_thread_id=search_thread.thread_id)
        thread_service = get_thread_service()
        await thread_service.set_active_thread(user_id, search_thread.thread_id)
        
        # Get user language
        user_lang = await get_user_profile_service().get_language(user_id)
        
        # Send searching indicator
        search_msg = f"🔍 Searching for: <b>{escape_html(keyword)}</b>"
        status_message = await message.answer(search_msg, parse_mode="HTML")
        
        # Get available KBs
        available_kbs = await get_available_kbs(user_id)
        
        if not available_kbs:
            await status_message.edit_text(
                _("search.no_kbs", language=user_lang),
                parse_mode="HTML"
            )
            return
        
        # Get currently selected KBs from thread, or use all if none selected
        current_thread = await thread_service.get_thread(search_thread.thread_id)
        # Use selected KBs if any are set, otherwise default to all available
        if current_thread and current_thread.knowledge_bases:
            selected_kb_indices = list(current_thread.knowledge_bases)
            logger.info(f"Using selected KBs from thread: {selected_kb_indices}")
        else:
            selected_kb_indices = [kb["index"] for kb in available_kbs]
            logger.info(f"No KBs selected, defaulting to all {len(selected_kb_indices)} available KBs")
        
        # Search across all selected KBs
        es_service = await get_elasticsearch_service()
        all_results = []
        
        for kb_index in selected_kb_indices:
            try:
                results = await es_service.search_messages_text(
                    index_name=kb_index,
                    query_text=keyword,
                    max_results=10
                )
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Failed to search KB {kb_index}: {e}")
                continue
        
        # Format results
        if not all_results:
            no_results_msg = f"❌ No messages found for '<b>{escape_html(keyword)}</b>'. Try different keywords."
            await status_message.edit_text(no_results_msg, parse_mode="HTML")
            return
        
        # Sort by score and limit
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        all_results = all_results[:5]  # Show top 5 results
        
        # Build response with new card format
        intro_text = f"I've found relevant messages for '<b>{escape_html(keyword)}</b>'. Let me know if you need something more specific!\n"
        if user_lang == "ru":
            intro_text = f"Нашёл сообщения по запросу '<b>{escape_html(keyword)}</b>'. Дайте знать, если нужно что-то конкретное!\n"
        
        # Header
        message_word = "message" if len(all_results) == 1 else "messages"
        if user_lang == "ru":
            message_word = "сообщение" if len(all_results) == 1 else "сообщения" if len(all_results) < 5 else "сообщений"
        
        response_parts = [
            intro_text,
            "━━━━━━━━━━━━━━━━━━━━",
            f"📚 Found {len(all_results)} {message_word}\n"
        ]
        
        # Build message cards
        for i, result in enumerate(all_results, 1):
            doc = result.get('doc', result)
            
            sender = doc.get('sender_name', 'Unknown')
            text = doc.get('message_text', '')
            date = doc.get('message_date', '')
            message_id = doc.get('message_id', '')
            group_id = doc.get('group_id', None)
            
            # Format date
            if date:
                try:
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = date[:16]
            else:
                date_str = "Unknown date"
            
            # Clean text: replace newlines with spaces and truncate
            text = text.replace('\n', ' ').replace('\r', ' ')
            max_text_length = 150
            if len(text) > max_text_length:
                text = text[:max_text_length] + "..."
            
            # Build deeplink
            deeplink_url = None
            if group_id and message_id:
                try:
                    parts = message_id.split('_')
                    telegram_msg_id = parts[-1] if parts else None
                    
                    if telegram_msg_id and telegram_msg_id.isdigit():
                        group_id_str = str(group_id)
                        if group_id_str.startswith('-100'):
                            chat_id_for_link = group_id_str[4:]
                            if chat_id_for_link and telegram_msg_id:
                                deeplink_url = f"https://t.me/c/{chat_id_for_link}/{telegram_msg_id}"
                except Exception as e:
                    logger.debug(f"Failed to generate deeplink: {e}")
            
            # Build card with simple box decoration
            # ┌─ at first line, └───── as divider
            # Make date clickable if deeplink is available
            if deeplink_url:
                date_display = f"<a href=\"{deeplink_url}\">{date_str}</a>"
            else:
                date_display = date_str
            
            card_lines = [
                # f"┌─ 👤 <b>{sender}</b> • {date_str}",
                f"┌─ 👤 <b>{sender}</b> • {date_display}",
                f"\"{escape_html(text)}\""
            ]
            
            # # Add raw URL link if available (no HTML anchor tags)
            # if deeplink_url:
            #     card_lines.append(f"🔗 {deeplink_url}")
            
            # Add divider after each message
            card_lines.append("└─────")
            
            response_parts.append("\n".join(card_lines) + "\n")
        
        response_parts.append("━━━━━━━━━━━━━━━━━━━━")
        
        # Send results
        final_response = "\n".join(response_parts)
        await status_message.edit_text(final_response, parse_mode="HTML")
        
        logger.info(f"✅ Direct search for '{keyword}' returned {len(all_results)} results")
        
    except Exception as e:
        logger.error(f"Error in direct search: {e}", exc_info=True)
        try:
            error_msg = _("search.error", language=await get_user_profile_service().get_language(user_id))
            await message.answer(error_msg, parse_mode="HTML")
        except:
            await message.answer("❌ Search error. Please try again.")


@router.message(Command("search"))
async def handle_search_command(message: Message, state: FSMContext, command: CommandObject = None):
    """
    Handle /search command.
    
    - /search → Shows KB selector UI (existing behavior)
    - /search <keyword> → Direct search with keyword (new behavior)
    """
    user_id = message.from_user.id
    logger.info(f"🔍 /search command from user {user_id}")
    
    # Check if keyword provided for direct search
    if command and command.args:
        keyword = command.args.strip()
        logger.info(f"🔍 Direct search requested: '{keyword}'")
        await execute_direct_search(message, user_id, keyword, state)
        return
    
    # Otherwise, show KB selector UI (existing behavior)
    try:
        # Get or create search thread
        search_thread = await get_or_create_search_thread(user_id)
        
        # Set as active thread in FSM and in ThreadService
        await state.update_data(active_thread_id=search_thread.thread_id)
        thread_service = get_thread_service()
        await thread_service.set_active_thread(user_id, search_thread.thread_id)
        
        # Get available KBs
        available_kbs = await get_available_kbs(user_id)
        
        if not available_kbs:
            await message.answer(
                _("search.no_kbs", language=await get_user_profile_service().get_language(user_id)),
                parse_mode="HTML"
            )
            return
        
        # Get currently selected KBs from thread
        thread_service = get_thread_service()
        current_thread = await thread_service.get_thread(search_thread.thread_id)
        selected_kb_indices = set(current_thread.knowledge_bases) if current_thread else set()
        
        # Build message
        user_lang = await get_user_profile_service().get_language(user_id)
        message_text = _("search.header", language=user_lang) + "\n\n"
        
        if selected_kb_indices:
            selected_names = [kb["name"] for kb in available_kbs if kb["index"] in selected_kb_indices]
            message_text += _("search.currently_selected", language=user_lang, kbs=", ".join(selected_names)) + "\n\n"
        else:
            message_text += _("search.none_selected", language=user_lang) + "\n\n"
        
        message_text += _("search.instruction", language=user_lang)
        
        # FIX 42/43: Show reply keyboard with section header
        from luka_bot.keyboards.search_reply import get_search_reply_keyboard
        reply_keyboard = await get_search_reply_keyboard(language=user_lang)
        
        # Send message with inline keyboard and reply keyboard
        await message.answer(
            message_text,
            reply_markup=get_search_kb_menu(available_kbs, selected_kb_indices, user_lang),
            parse_mode="HTML"
        )
        
        # Send reply keyboard separately to avoid conflict
        await message.answer(
            "🔍",  # Search emoji as indicator
            reply_markup=reply_keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in /search command: {e}", exc_info=True)
        await message.answer(
            _("search.error", language=await get_user_profile_service().get_language(user_id)),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("search_kb:"))
async def handle_kb_selection(callback: CallbackQuery, state: FSMContext):
    """
    Handle KB selection/deselection from inline menu.
    
    Callback data format: search_kb:{action}:{kb_index}
    Actions: toggle, clear_all, search_all
    """
    user_id = callback.from_user.id
    data_parts = callback.data.split(":", 2)
    
    if len(data_parts) < 2:
        await callback.answer("Invalid callback data")
        return
    
    action = data_parts[1]
    kb_index = data_parts[2] if len(data_parts) > 2 else None
    
    logger.info(f"🔍 KB selection: user={user_id}, action={action}, kb_index={kb_index}")
    
    try:
        # Get search thread
        search_thread = await get_or_create_search_thread(user_id)
        thread_service = get_thread_service()
        current_thread = await thread_service.get_thread(search_thread.thread_id)
        
        if not current_thread:
            await callback.answer(_("search.error_thread_not_found", language=await get_user_profile_service().get_language(user_id)))
            return
        
        # Get current selection
        selected_kb_indices = set(current_thread.knowledge_bases)
        
        # Handle actions
        if action == "toggle" and kb_index:
            if kb_index in selected_kb_indices:
                selected_kb_indices.remove(kb_index)
                feedback = _("search.kb_deselected", language=await get_user_profile_service().get_language(user_id))
            else:
                selected_kb_indices.add(kb_index)
                feedback = _("search.kb_selected", language=await get_user_profile_service().get_language(user_id))
        
        elif action == "clear_all":
            selected_kb_indices.clear()
            feedback = _("search.all_cleared", language=await get_user_profile_service().get_language(user_id))
        
        elif action == "search_all":
            available_kbs = await get_available_kbs(user_id)
            selected_kb_indices = {kb["index"] for kb in available_kbs}
            feedback = _("search.all_selected", language=await get_user_profile_service().get_language(user_id))
        
        else:
            await callback.answer("Unknown action")
            return
        
        # Update thread with new selection
        current_thread.knowledge_bases = list(selected_kb_indices)
        await thread_service.update_thread(current_thread)
        logger.info(f"✅ Updated search thread KBs: {list(selected_kb_indices)}")
        
        # Update inline keyboard
        available_kbs = await get_available_kbs(user_id)
        user_lang = await get_user_profile_service().get_language(user_id)
        
        # Rebuild message
        message_text = _("search.header", language=user_lang) + "\n\n"
        
        if selected_kb_indices:
            selected_names = [kb["name"] for kb in available_kbs if kb["index"] in selected_kb_indices]
            message_text += _("search.currently_selected", language=user_lang, kbs=", ".join(selected_names)) + "\n\n"
        else:
            message_text += _("search.none_selected", language=user_lang) + "\n\n"
        
        message_text += _("search.instruction", language=user_lang)
        
        # Edit message
        await callback.message.edit_text(
            message_text,
            reply_markup=get_search_kb_menu(available_kbs, selected_kb_indices, user_lang),
            parse_mode="HTML"
        )
        
        # Answer callback
        await callback.answer(feedback)
        
    except Exception as e:
        logger.error(f"Error handling KB selection: {e}", exc_info=True)
        await callback.answer(_("search.error", language=await get_user_profile_service().get_language(user_id)))


@router.callback_query(F.data == "search_done")
async def handle_search_done(callback: CallbackQuery, state: FSMContext):
    """
    Handle "Done" button - user is ready to start searching.
    """
    user_id = callback.from_user.id
    user_lang = await get_user_profile_service().get_language(user_id)
    
    try:
        # Get search thread
        search_thread = await get_or_create_search_thread(user_id)
        thread_service = get_thread_service()
        current_thread = await thread_service.get_thread(search_thread.thread_id)
        
        if not current_thread or not current_thread.knowledge_bases:
            await callback.answer(_("search.select_at_least_one", language=user_lang), show_alert=True)
            return
        
        # Confirm selection
        available_kbs = await get_available_kbs(user_id)
        selected_names = [kb["name"] for kb in available_kbs if kb["index"] in current_thread.knowledge_bases]
        
        # Make search thread active now
        await thread_service.set_active_thread(user_id, current_thread.thread_id)

        await callback.message.edit_text(
            _("search.ready", language=user_lang, kbs=", ".join(selected_names)),
            parse_mode="HTML"
        )
        
        await callback.answer(_("search.start_asking", language=user_lang))
        
    except Exception as e:
        logger.error(f"Error in search_done: {e}", exc_info=True)
        await callback.answer(_("search.error", language=user_lang))
