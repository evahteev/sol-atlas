"""
Reply keyboard action handlers - Phase 3.

Handles thread selection and control buttons from reply keyboard.
NEW: Also handles groups navigation.
"""
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from luka_bot.utils.i18n_helper import _, get_user_language
from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.group_service import get_group_service
from luka_bot.services.group_thread_service import get_group_thread_service
from luka_bot.services.divider_service import send_thread_divider
from luka_bot.services.group_divider_service import send_group_divider
from luka_bot.handlers.states import NavigationStates
from luka_bot.keyboards.threads_menu import (
    get_threads_keyboard,
    get_empty_state_keyboard,
    is_thread_button,
    is_control_button,
)
from luka_bot.keyboards.groups_menu import (
    get_groups_keyboard,
    is_group_button,
)

router = Router()


# FSM States for thread editing
class ThreadEditStates(StatesGroup):
    waiting_for_name = State()


# FSM States for lazy thread creation
class ThreadCreationStates(StatesGroup):
    waiting_for_first_message = State()  # User has no active thread, waiting for first message


# FSM States for thread settings (Phase 4)
class ThreadSettingsStates(StatesGroup):
    editing_prompt = State()  # User is entering custom system prompt


# Custom filter for thread selection
class ThreadSelectionFilter(BaseFilter):
    """Filter that only passes thread selection messages (but NOT group buttons)."""
    
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        if not message.from_user or not message.text:
            return False
        
        # IMPORTANT: Skip if user is in groups_mode - groups have their own handler
        current_state = await state.get_state()
        if current_state == NavigationStates.groups_mode:
            return False
        
        user_id = message.from_user.id
        text = message.text
        
        # Skip control buttons
        if is_control_button(text):
            return False
        
        try:
            thread_service = get_thread_service()
            threads = await thread_service.list_threads(user_id)
            thread_id = is_thread_button(text, threads)
            return thread_id is not None
        except Exception:
            return False


@router.message(F.text.in_(["➕ Start New Chat", "➕ Начать новый чат"]))
async def handle_start_new_chat_button(message: Message, state: FSMContext) -> None:
    """
    Handle 'Start New Chat' button (empty state).
    
    Same as New Thread button, but for users with no threads.
    Shows welcome prompt and waits for first message.
    Supports both English and Russian button text.
    """
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    
    logger.info(f"✨ User {user_id} starting first chat via button")
    
    try:
        from luka_bot.services.welcome_prompts import get_new_thread_prompt
        from luka_bot.services.user_profile_service import get_user_profile_service
        
        # Get user's language preference
        profile_service = get_user_profile_service()
        user_lang = await profile_service.get_language(user_id) or "en"
        
        # Set FSM state to waiting for first message
        await state.set_state(ThreadCreationStates.waiting_for_first_message)
        
        # Get random prompt in user's language
        prompt = get_new_thread_prompt(language=user_lang)
        
        header = _('actions.welcome', user_lang)
        response = f"""✨ <b>{header}</b>

{prompt}"""
        
        # Keep empty keyboard with correct language
        keyboard = await get_empty_state_keyboard(language=user_lang)
        
        await message.answer(response, reply_markup=keyboard, parse_mode="HTML")
        
        logger.info(f"✅ User {user_id} ready for first message")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await message.answer("❌ Error. Please try again.")


@router.message(F.text.in_(["➕ New Thread", "➕ Новый чат"]))
async def handle_new_thread_button(message: Message, state: FSMContext) -> None:
    """
    Handle 'New Thread' button - lazy creation.
    
    Shows welcome prompt, clears active thread, sets FSM state.
    Thread created when user sends first message.
    Supports both English and Russian button text.
    """
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    
    logger.info(f"➕ User {user_id} starting new thread via reply button")
    
    try:
        from luka_bot.services.welcome_prompts import get_new_thread_prompt
        from luka_bot.services.user_profile_service import get_user_profile_service
        thread_service = get_thread_service()
        
        # Get user's language preference
        profile_service = get_user_profile_service()
        user_lang = await profile_service.get_language(user_id) or "en"
        
        # Clear active thread (user is starting fresh)
        await thread_service.clear_active_thread(user_id)
        
        # Set FSM state to waiting for first message
        await state.set_state(ThreadCreationStates.waiting_for_first_message)
        
        # Get random prompt in user's language
        prompt = get_new_thread_prompt(language=user_lang)
        
        header = _('actions.intro', user_lang)
        response = f"""💭 <b>{header}</b>

{prompt}"""
        
        # Keep existing keyboard (threads still visible) with correct language
        threads = await thread_service.list_threads(user_id)
        keyboard = await get_threads_keyboard(threads, None, language=user_lang)  # No active thread
        
        await message.answer(response, reply_markup=keyboard, parse_mode="HTML")
        
        logger.info(f"✅ User {user_id} set to waiting_for_first_message state")
        
    except Exception as e:
        logger.error(f"❌ Error starting new thread: {e}")
        await message.answer("❌ Error starting new thread. Please try again.")


# State storage for edit/delete context
_last_thread_context = {}  # user_id -> thread_id


async def _get_thread_from_recent_messages(user_id: int, message: Message) -> Optional[str]:
    """
    Get thread ID from recent keyboard interaction.
    
    Since edit/delete buttons are in the same row as thread name,
    we look at recent message context to figure out which thread.
    """
    thread_service = get_thread_service()
    
    # Check stored context first
    if user_id in _last_thread_context:
        return _last_thread_context[user_id]
    
    # If no context, try to get active thread
    active_thread = await thread_service.get_active_thread(user_id)
    if active_thread:
        return active_thread
    
    # Last fallback: get most recent thread
    threads = await thread_service.list_threads(user_id)
    if threads:
        # Sort by updated_at and return most recent
        threads.sort(key=lambda t: t.updated_at, reverse=True)
        return threads[0].thread_id
    
    return None


@router.message(F.text == "✏️")
async def handle_edit_button(message: Message, state: FSMContext) -> None:
    """Handle edit button - shows thread edit menu."""
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    
    # Try to get thread from context or recent activity
    thread_id = await _get_thread_from_recent_messages(user_id, message)
    if not thread_id:
        await message.answer("❌ Please select a thread first, then tap ✏️")
        return
    
    logger.info(f"✏️ User {user_id} editing thread {thread_id}")
    
    try:
        thread_service = get_thread_service()
        thread = await thread_service.get_thread(thread_id)
        
        if not thread or thread.user_id != user_id:
            await message.answer("❌ Thread not found or access denied.")
            return
        
        # Get user language
        lang = await get_user_language(user_id)
        
        # Create inline keyboard for editing
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_("thread_edit.btn_rename", lang), callback_data=f"edit_name:{thread_id}")],
            [InlineKeyboardButton(text=_("thread_edit.btn_settings", lang), callback_data=f"thread_settings:{thread_id}")],
            [InlineKeyboardButton(text=_("thread_edit.btn_add_kb", lang), callback_data=f"edit_kb:{thread_id}")],
            [InlineKeyboardButton(text=_("thread_edit.btn_delete", lang), callback_data=f"delete_confirm:{thread_id}")],
            [InlineKeyboardButton(text=_("common.cancel", lang), callback_data="edit_cancel")],
        ])
        
        edit_text = f"""{_("thread_edit.title", lang)}

{_("thread_edit.name", lang)} {thread.name}
{_("thread_edit.messages", lang)} {thread.message_count}
{_("thread_edit.created", lang)} {thread.created_at.strftime('%Y-%m-%d %H:%M')}
{_("thread_edit.last_active", lang)} {thread.updated_at.strftime('%Y-%m-%d %H:%M')}

{_("thread_edit.select_action", lang)}"""
        
        await message.answer(edit_text, reply_markup=keyboard, parse_mode="HTML")
        logger.info(f"✅ Showed edit menu for thread {thread_id}")
        
    except Exception as e:
        logger.error(f"❌ Error showing edit menu: {e}")
        await message.answer("❌ Error loading edit menu.")


@router.message(F.text == "🗑️")
async def handle_delete_button(message: Message) -> None:
    """Handle delete button - confirms and deletes thread."""
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    
    # Try to get thread from context or recent activity
    thread_id = await _get_thread_from_recent_messages(user_id, message)
    if not thread_id:
        await message.answer("❌ Please select a thread first, then tap 🗑️")
        return
    
    logger.info(f"🗑️  User {user_id} deleting thread {thread_id}")
    
    try:
        thread_service = get_thread_service()
        thread = await thread_service.get_thread(thread_id)
        
        if not thread or thread.user_id != user_id:
            await message.answer("❌ Thread not found or access denied.")
            return
        
        # Store thread info before deletion
        thread_name = thread.name
        thread_messages = thread.message_count
        
        # Get user language
        lang = await get_user_language(user_id)
        
        # Delete the thread
        success = await thread_service.delete_thread(thread_id, user_id)
        
        if success:
            # Update keyboard
            threads = await thread_service.list_threads(user_id)
            keyboard = await get_threads_keyboard(threads, None, lang)
            
            delete_msg = f"""{_("thread_delete.title", lang)}

{_("thread_delete.name", lang)} {thread_name}
{_("thread_delete.messages", lang)} {thread_messages}

{_("thread_delete.confirmation", lang)}"""
            
            await message.answer(delete_msg, reply_markup=keyboard, parse_mode="HTML")
            
            # Clear context
            _last_thread_context.pop(user_id, None)
            
            logger.info(f"✅ Deleted thread {thread_id}")
        else:
            await message.answer("❌ Failed to delete thread.")
        
    except Exception as e:
        logger.error(f"❌ Error deleting thread: {e}")
        await message.answer("❌ Error deleting thread.")


@router.message(ThreadSelectionFilter(), F.state != NavigationStates.groups_mode)
async def handle_thread_selection(message: Message) -> None:
    """
    Handle thread selection from reply keyboard.
    
    Checks if message text matches a thread name.
    Only processes if it's actually a thread button.
    """
    user_id = message.from_user.id if message.from_user else None
    text = message.text
    
    if not user_id or not text:
        return
    
    try:
        thread_service = get_thread_service()
        threads = await thread_service.list_threads(user_id)
        
        # Check if text matches a thread
        thread_id = is_thread_button(text, threads)
        
        if not thread_id:
            # This shouldn't happen due to filter, but just in case
            return
        
        logger.info(f"🔀 User {user_id} switching to thread via reply button: {thread_id}")
        
        # Get thread details
        thread = await thread_service.get_thread(thread_id)
        if not thread:
            await message.answer("❌ Thread not found.")
            return
        
        # Switch to thread
        await thread_service.set_active_thread(user_id, thread_id)
        
        # Store in context for edit/delete
        _last_thread_context[user_id] = thread_id
        
        # Prepare updated keyboard
        keyboard = await get_threads_keyboard(threads, thread_id)
        
        # Send divider with thread info and updated keyboard
        await send_thread_divider(
            user_id, 
            thread_id, 
            divider_type="switch", 
            bot=message.bot,
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Switched to thread {thread_id} via reply button")
        
    except Exception as e:
        logger.error(f"❌ Error handling thread selection: {e}")


# Close reply menu handler (works across modes)
@router.message(F.text == "❌")
async def handle_close_reply_menu(message: Message) -> None:
    """Remove reply keyboard when user taps Close (❌)."""
    try:
        from luka_bot.keyboards.threads_menu import remove_keyboard
        
        # Get user's language
        user_id = message.from_user.id if message.from_user else None
        language = await get_user_language(user_id) if user_id else "en"
        
        # Send translated message
        await message.answer(
            _('common.menu_closed', language),
            reply_markup=remove_keyboard()
        )
    except Exception:
        pass


# Callback handlers for inline edit menu
@router.callback_query(F.data.startswith("edit_name:"))
async def handle_edit_name_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle rename thread callback."""
    user_id = callback.from_user.id if callback.from_user else None
    if not user_id:
        await callback.answer("❌ User not found", show_alert=True)
        return
    
    thread_id = callback.data.split(":")[1]
    logger.info(f"✏️ User {user_id} renaming thread {thread_id}")
    
    # Store thread_id in state
    await state.update_data(editing_thread_id=thread_id)
    await state.set_state(ThreadEditStates.waiting_for_name)
    
    await callback.message.edit_text(
        "✏️ <b>Rename Thread</b>\n\nSend me the new name for this thread:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_kb:"))
async def handle_edit_kb_callback(callback: CallbackQuery) -> None:
    """Handle knowledge base callback (mocked)."""
    await callback.answer("📚 Knowledge Base feature coming soon!", show_alert=True)


@router.callback_query(F.data.startswith("delete_confirm:"))
async def handle_delete_confirm_callback(callback: CallbackQuery) -> None:
    """Handle delete confirmation from inline menu."""
    user_id = callback.from_user.id if callback.from_user else None
    if not user_id:
        await callback.answer("❌ User not found", show_alert=True)
        return
    
    thread_id = callback.data.split(":")[1]
    logger.info(f"🗑️  User {user_id} confirming delete of thread {thread_id}")
    
    try:
        thread_service = get_thread_service()
        thread = await thread_service.get_thread(thread_id)
        
        if not thread or thread.user_id != user_id:
            await callback.answer("❌ Thread not found", show_alert=True)
            return
        
        # Store info before deletion
        thread_name = thread.name
        thread_messages = thread.message_count
        
        # Delete the thread
        success = await thread_service.delete_thread(thread_id, user_id)
        
        if success:
            # Update keyboard
            threads = await thread_service.list_threads(user_id)
            keyboard = await get_threads_keyboard(threads, None)
            
            delete_msg = f"""🗑️ <b>Thread Deleted</b>

<b>Name:</b> {thread_name}
<b>Messages:</b> {thread_messages}

The thread and its history have been permanently deleted."""
            
            await callback.message.edit_text(delete_msg, parse_mode="HTML")
            
            # Send updated keyboard in new message
            await callback.message.answer("📋 <b>Updated Threads:</b>", reply_markup=keyboard, parse_mode="HTML")
            
            # Clear context
            _last_thread_context.pop(user_id, None)
            
            await callback.answer("✅ Thread deleted", show_alert=False)
            logger.info(f"✅ Deleted thread {thread_id}")
        else:
            await callback.answer("❌ Failed to delete thread", show_alert=True)
    
    except Exception as e:
        logger.error(f"❌ Error deleting thread: {e}")
        await callback.answer("❌ Error deleting thread", show_alert=True)


@router.callback_query(F.data == "edit_cancel")
async def handle_edit_cancel_callback(callback: CallbackQuery) -> None:
    """Handle cancel button in edit menu."""
    await callback.message.edit_text("❌ <b>Edit Cancelled</b>", parse_mode="HTML")
    await callback.answer()


# Message handler for thread rename
@router.message(ThreadEditStates.waiting_for_name)
async def handle_thread_rename_input(message: Message, state: FSMContext) -> None:
    """Handle new thread name input."""
    user_id = message.from_user.id if message.from_user else None
    new_name = message.text
    
    if not user_id or not new_name:
        return
    
    try:
        data = await state.get_data()
        thread_id = data.get("editing_thread_id")
        
        if not thread_id:
            await message.answer("❌ Session expired. Please try again.")
            await state.clear()
            return
        
        thread_service = get_thread_service()
        thread = await thread_service.get_thread(thread_id)
        
        if not thread or thread.user_id != user_id:
            await message.answer("❌ Thread not found or access denied.")
            await state.clear()
            return
        
        # Update thread name
        old_name = thread.name
        thread.name = new_name
        await thread_service.update_thread(thread)
        
        # Update keyboard
        threads = await thread_service.list_threads(user_id)
        keyboard = await get_threads_keyboard(threads, thread_id)
        
        success_msg = f"""✅ <b>Thread Renamed</b>

<b>Old name:</b> {old_name}
<b>New name:</b> {new_name}

Thread successfully updated!"""
        
        await message.answer(success_msg, reply_markup=keyboard, parse_mode="HTML")
        
        await state.clear()
        logger.info(f"✅ Renamed thread {thread_id}: {old_name} → {new_name}")
        
    except Exception as e:
        logger.error(f"❌ Error renaming thread: {e}")
        await message.answer("❌ Error renaming thread. Please try again.")
        await state.clear()


# ============================================================================
# PHASE 4: Thread Settings Handlers
# ============================================================================

@router.callback_query(F.data.startswith("thread_settings:"))
async def handle_thread_settings(callback: CallbackQuery) -> None:
    """Show thread settings menu."""
    from luka_bot.keyboards.thread_settings import get_thread_settings_menu
    
    thread_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id if callback.from_user else None
    
    if not user_id:
        await callback.answer("Error: User ID not found")
        return
    
    try:
        thread_service = get_thread_service()
        thread = await thread_service.get_thread(thread_id)
        
        if not thread or thread.user_id != user_id:
            await callback.answer("Thread not found or access denied", show_alert=True)
            return
        
        # Get current settings
        provider = thread.llm_provider or "ollama (default)"
        model = thread.model_name or "gpt-oss (default)"
        has_custom_prompt = "Yes" if thread.system_prompt else "No (using default)"
        
        settings_text = f"""⚙️ <b>Thread Settings</b>

<b>Thread:</b> {thread.name}

<b>Current Settings:</b>
• <b>Provider:</b> {provider}
• <b>Model:</b> {model}
• <b>Custom Prompt:</b> {has_custom_prompt}

Select what you'd like to change:"""
        
        keyboard = get_thread_settings_menu(thread_id)
        
        await callback.message.edit_text(
            settings_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        logger.info(f"⚙️ Showed settings menu for thread {thread_id}")
        
    except Exception as e:
        logger.error(f"❌ Error showing settings menu: {e}")
        await callback.answer("Error loading settings", show_alert=True)


@router.callback_query(F.data.startswith("settings_model:"))
async def handle_settings_model(callback: CallbackQuery) -> None:
    """Show model/provider selection."""
    from luka_bot.keyboards.thread_settings import get_provider_selection_menu
    
    thread_id = callback.data.split(":", 1)[1]
    
    selection_text = (
        "🤖 <b>" + _("Select LLM Provider") + "</b>\n\n"
        + _("Choose which LLM provider to use for this thread:") + "\n\n"
        + "• <b>Ollama:</b> " + _("Local models, fast, free") + "\n"
        + "• <b>OpenAI:</b> " + _("GPT-4 (Coming Soon)") + "\n"
        + "• <b>Anthropic:</b> " + _("Claude (Coming Soon)")
    )
    
    keyboard = get_provider_selection_menu(thread_id)
    
    await callback.message.edit_text(
        selection_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("provider_ollama:"))
async def handle_provider_ollama(callback: CallbackQuery) -> None:
    """Show Ollama model selection."""
    from luka_bot.keyboards.thread_settings import get_model_selection_menu
    
    thread_id = callback.data.split(":", 1)[1]
    
    selection_text = (
        "🦙 <b>" + _("Select Ollama Model") + "</b>\n\n"
        + _("Choose which Ollama model to use:") + "\n\n"
        + _("Available models on your local instance:")
    )
    
    keyboard = get_model_selection_menu(thread_id, "ollama")
    
    await callback.message.edit_text(
        selection_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("provider_openai:") | F.data.startswith("provider_anthropic:"))
async def handle_provider_coming_soon(callback: CallbackQuery) -> None:
    """Handle coming soon providers."""
    await callback.answer(
        _("🚧 This provider is coming soon!\n\nCurrently only Ollama is supported."),
        show_alert=True
    )


@router.callback_query(F.data.startswith("model_ollama_"))
async def handle_model_selection(callback: CallbackQuery) -> None:
    """Handle model selection."""
    from luka_bot.keyboards.thread_settings import get_thread_settings_menu
    
    # Parse: model_ollama_gpt-oss:thread_id
    parts = callback.data.split(":")
    model_info = parts[0]  # model_ollama_gpt-oss
    thread_id = parts[1]
    
    _, provider, model_name = model_info.split("_", 2)
    
    user_id = callback.from_user.id if callback.from_user else None
    if not user_id:
        await callback.answer(_("Error: User ID not found"))
        return
    
    try:
        thread_service = get_thread_service()
        thread = await thread_service.get_thread(thread_id)
        
        if not thread or thread.user_id != user_id:
            await callback.answer(_("Thread not found"), show_alert=True)
            return
        
        # Update thread settings
        thread.llm_provider = provider
        thread.model_name = model_name
        await thread_service.update_thread(thread)
        
        # Show success message
        success_text = (
            "✅ <b>" + _("Model Updated") + "</b>\n\n"
            + "<b>" + _("Provider") + ":</b> " + provider + "\n"
            + "<b>" + _("Model") + ":</b> " + model_name + "\n\n"
            + _("Settings saved! Your next messages will use this model.")
        )
        
        keyboard = get_thread_settings_menu(thread_id)
        
        await callback.message.edit_text(
            success_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer(_("Model updated successfully!"))
        logger.info(f"✅ Updated thread {thread_id} model: {provider}:{model_name}")
        
    except Exception as e:
        logger.error(f"❌ Error updating model: {e}")
        await callback.answer("Error updating model", show_alert=True)


@router.callback_query(F.data.startswith("settings_back:"))
async def handle_settings_back(callback: CallbackQuery) -> None:
    """Go back to main settings menu."""
    thread_id = callback.data.split(":", 1)[1]
    
    # Re-show settings menu (reuse handler logic)
    callback.data = f"thread_settings:{thread_id}"
    await handle_thread_settings(callback)


@router.callback_query(F.data.startswith("settings_close:"))
async def handle_settings_close(callback: CallbackQuery) -> None:
    """Close settings menu."""
    await callback.message.delete()
    await callback.answer("Settings closed")
    logger.info("⚙️ Settings menu closed")


@router.callback_query(F.data.startswith("settings_reset:"))
async def handle_settings_reset(callback: CallbackQuery) -> None:
    """Reset thread settings to defaults."""
    thread_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id if callback.from_user else None
    
    if not user_id:
        await callback.answer("Error: User ID not found")
        return
    
    try:
        thread_service = get_thread_service()
        thread = await thread_service.get_thread(thread_id)
        
        if not thread or thread.user_id != user_id:
            await callback.answer("Thread not found", show_alert=True)
            return
        
        # Reset settings
        thread.llm_provider = None
        thread.model_name = None
        thread.system_prompt = None
        await thread_service.update_thread(thread)
        
        await callback.answer("✅ Settings reset to defaults!", show_alert=True)
        
        # Re-show settings menu
        callback.data = f"thread_settings:{thread_id}"
        await handle_thread_settings(callback)
        
        logger.info(f"🔄 Reset settings for thread {thread_id}")
        
    except Exception as e:
        logger.error(f"❌ Error resetting settings: {e}")
        await callback.answer("Error resetting settings", show_alert=True)


@router.callback_query(F.data.startswith("settings_prompt:"))
async def handle_settings_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    """Start custom system prompt editing."""
    thread_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id if callback.from_user else None
    
    if not user_id:
        await callback.answer("Error: User ID not found")
        return
    
    try:
        thread_service = get_thread_service()
        thread = await thread_service.get_thread(thread_id)
        
        if not thread or thread.user_id != user_id:
            await callback.answer("Thread not found", show_alert=True)
            return
        
        # Show current prompt and instructions
        current_prompt = thread.system_prompt or "Using default Luka system prompt"
        
        prompt_text = f"""💭 <b>Custom System Prompt</b>

<b>Current Prompt:</b>
<code>{current_prompt[:500]}...</code>

Send me your custom system prompt for this thread. This will define the bot's personality and behavior in this thread only.

<b>Tips:</b>
• Be specific about the role and tone
• Include any special instructions
• Keep it concise but clear

Send your prompt now, or type /cancel to abort."""
        
        # Set FSM state and store thread_id
        await state.set_state(ThreadSettingsStates.editing_prompt)
        await state.update_data(thread_id=thread_id)
        
        await callback.message.edit_text(prompt_text, parse_mode="HTML")
        await callback.answer()
        logger.info(f"💭 Started prompt editing for thread {thread_id}")
        
    except Exception as e:
        logger.error(f"❌ Error starting prompt edit: {e}")
        await callback.answer("Error starting prompt editor", show_alert=True)


@router.message(ThreadSettingsStates.editing_prompt)
async def handle_prompt_input(message: Message, state: FSMContext) -> None:
    """Handle custom system prompt input."""
    user_id = message.from_user.id if message.from_user else None
    text = message.text
    
    if not user_id or not text:
        return
    
    # Check for cancel
    if text.strip().lower() in ['/cancel', 'cancel']:
        await state.clear()
        await message.answer("❌ Prompt editing cancelled.")
        logger.info(f"❌ Prompt editing cancelled by user {user_id}")
        return
    
    try:
        # Get thread_id from FSM data
        data = await state.get_data()
        thread_id = data.get('thread_id')
        
        if not thread_id:
            await message.answer("❌ Error: Thread ID not found. Please try again.")
            await state.clear()
            return
        
        thread_service = get_thread_service()
        thread = await thread_service.get_thread(thread_id)
        
        if not thread or thread.user_id != user_id:
            await message.answer("❌ Thread not found or access denied.")
            await state.clear()
            return
        
        # Update thread with new system prompt
        thread.system_prompt = text
        await thread_service.update_thread(thread)
        
        # Show confirmation with preview
        from luka_bot.keyboards.thread_settings import get_prompt_confirmation_menu
        
        preview = text[:300] + "..." if len(text) > 300 else text
        
        confirmation_text = f"""✅ <b>System Prompt Set</b>

<b>Your Custom Prompt:</b>
<code>{preview}</code>

This prompt will be used for all future messages in this thread.

What would you like to do?"""
        
        keyboard = get_prompt_confirmation_menu(thread_id)
        
        await message.answer(
            confirmation_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await state.clear()
        logger.info(f"✅ Set custom prompt for thread {thread_id}: {len(text)} chars")
        
    except Exception as e:
        logger.error(f"❌ Error setting custom prompt: {e}")
        await message.answer("❌ Error setting prompt. Please try again.")
        await state.clear()


@router.callback_query(F.data.startswith("prompt_confirm:"))
async def handle_prompt_confirm(callback: CallbackQuery) -> None:
    """Confirm and close prompt editing."""
    await callback.message.delete()
    await callback.answer("✅ Custom prompt saved!")
    logger.info("✅ Custom prompt confirmed and saved")


@router.callback_query(F.data.startswith("prompt_reset:"))
async def handle_prompt_reset(callback: CallbackQuery) -> None:
    """Reset prompt to default."""
    thread_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id if callback.from_user else None
    
    if not user_id:
        await callback.answer("Error: User ID not found")
        return
    
    try:
        thread_service = get_thread_service()
        thread = await thread_service.get_thread(thread_id)
        
        if not thread or thread.user_id != user_id:
            await callback.answer("Thread not found", show_alert=True)
            return
        
        # Reset prompt
        thread.system_prompt = None
        await thread_service.update_thread(thread)
        
        await callback.message.delete()
        await callback.answer("✅ Reverted to default system prompt!")
        logger.info(f"🔄 Reset prompt for thread {thread_id}")
        
    except Exception as e:
        logger.error(f"❌ Error resetting prompt: {e}")
        await callback.answer("Error resetting prompt", show_alert=True)


# ============================================================================
# FIX 42: Search Thread Management Handlers
# ============================================================================

@router.message(F.text == "🔄")
async def handle_reset_search_button(message: Message) -> None:
    """
    Handle reset button for search thread.
    
    Clears the chatbot_search thread's message history and restarts it.
    """
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    
    logger.info(f"🔄 User {user_id} resetting search thread")
    
    try:
        thread_service = get_thread_service()
        
        # Get the search thread
        threads = await thread_service.list_threads(user_id)
        search_thread = None
        for thread in threads:
            if thread.name == "chatbot_search":
                search_thread = thread
                break
        
        if not search_thread:
            await message.answer("❌ Search thread not found. Use /search to create one.")
            return
        
        # Clear history for search thread
        from luka_bot.services.llm_service import LLMService
        llm_service = LLMService()
        await llm_service._clear_history(user_id, search_thread.thread_id)
        
        # Reset message count
        search_thread.message_count = 0
        await thread_service.update_thread(search_thread)
        
        # Get user language
        lang = await get_user_language(user_id)
        
        await message.answer(
            _("search.thread_reset", language=lang),
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Reset search thread for user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error resetting search thread: {e}")
        await message.answer("❌ Error resetting search thread. Please try again.")


# ============================================================================
# GROUPS NAVIGATION HANDLERS
# ============================================================================

# Custom filter for group selection
class GroupSelectionFilter(BaseFilter):
    """Filter that only passes group selection messages."""
    
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        if not message.from_user or not message.text:
            return False
        
        # Check if user is in groups mode
        current_state = await state.get_state()
        if current_state != NavigationStates.groups_mode:
            return False
        
        user_id = message.from_user.id
        text = message.text
        
        # Skip control buttons (Settings, Delete)
        from luka_bot.keyboards.groups_menu import is_control_button
        if is_control_button(text):
            return False
        
        # Skip section header (has its own handler)
        if text in ["🏘 Groups", "🏘 Группы"]:
            return False
        
        # Skip other control buttons (have their own handlers)
        if text in ["➕ New Group", "➕ Новая группа", "⚙️ Default Settings", "⚙️ Настройки по умолчанию"]:
            return False
        
        try:
            group_service = await get_group_service()
            groups = await group_service.list_user_groups(user_id, active_only=True)
            from luka_bot.keyboards.groups_menu import is_group_button
            group_id = await is_group_button(text, groups)
            return group_id is not None
        except Exception as e:
            logger.debug(f"GroupSelectionFilter exception: {e}")
            return False


@router.message(GroupSelectionFilter())
async def handle_group_selection(message: Message, state: FSMContext) -> None:
    """
    Handle group selection from reply keyboard.
    
    Switches to selected group's context:
    - Creates/gets user-group thread
    - Shows group divider with inline buttons
    - User can chat with group-aware AI agent
    - STAYS in groups_mode (doesn't switch to threads view)
    """
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    
    text = message.text
    logger.info(f"🔀 User {user_id} selecting group: {text}")
    
    try:
        # Get user's groups
        group_service = await get_group_service()
        groups = await group_service.list_user_groups(user_id, active_only=True)
        
        # Find which group was selected
        from luka_bot.keyboards.groups_menu import is_group_button
        selected_group_id = await is_group_button(text, groups)
        
        if not selected_group_id:
            logger.warning(f"⚠️ Could not match button text to group: {text}")
            return
        
        # Get user language
        lang = await get_user_language(user_id)
        
        # Ensure group thread exists (recreate if missing after /reset)
        thread_service = get_thread_service()
        group_thread = await thread_service.get_group_thread(selected_group_id)
        
        if not group_thread:
            # Thread missing (e.g., after /reset), recreate it
            from luka_bot.services.group_service import get_group_service
            group_service = await get_group_service()
            
            # Get group metadata for title
            metadata = await group_service.get_cached_group_metadata(selected_group_id)
            group_title = metadata.group_title if metadata else f"Group {selected_group_id}"
            
            # Recreate group thread with KB
            group_thread = await thread_service.create_group_thread(
                group_id=selected_group_id,
                group_title=group_title,
                owner_id=user_id,
                language=lang
            )
            logger.info(f"✅ Recreated group thread {group_thread.thread_id} after /reset")
        
        # Create or get user's thread for this group
        group_thread_service = await get_group_thread_service()
        user_group_thread = await group_thread_service.get_or_create_user_group_thread(
            user_id=user_id,
            group_id=selected_group_id
        )
        
        # Set as active thread
        thread_service = get_thread_service()
        await thread_service.set_active_thread(user_id, user_group_thread.thread_id)
        
        # IMPORTANT: Ensure we stay in groups_mode
        await state.set_state(NavigationStates.groups_mode)
        
        # Update state with current group
        await state.update_data(current_group_id=selected_group_id)
        
        # Rebuild keyboard with new selection (GROUPS keyboard, not threads!)
        keyboard = await get_groups_keyboard(
            groups=groups,
            current_group_id=selected_group_id,
            language=lang
        )
        
        intro_text = _('groups.intro', lang, count=len(groups))
        await message.answer(intro_text, parse_mode="HTML", reply_markup=keyboard)

        # Send GROUP divider with updated inline controls
        await send_group_divider(
            user_id=user_id,
            group_id=selected_group_id,
            divider_type="switch",
            bot=message.bot
        )
        
        logger.info(f"✅ Switched to group {selected_group_id} for user {user_id} (staying in groups_mode)")
        
    except Exception as e:
        logger.error(f"❌ Error switching group: {e}", exc_info=True)
        await message.answer("❌ Error switching group. Please try again.")


@router.message(F.text.in_(["➕ New Group", "➕ Новая группа"]))
async def handle_new_group_button(message: Message, state: FSMContext) -> None:
    """
    Handle '+ New Group' button.
    
    Shows instructions for adding bot to a new group.
    """
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    
    logger.info(f"➕ User {user_id} clicked New Group button")
    
    try:
        lang = await get_user_language(user_id)
        
        # Get bot username
        bot_info = await message.bot.get_me()
        bot_username = bot_info.username
        
        # Instructions for adding bot to group
        instructions = _('groups.add_instructions', lang, bot_username=bot_username)
        
        await message.answer(instructions, parse_mode="HTML")
        
        logger.info(f"✅ Showed add group instructions to user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error showing add group instructions: {e}")
        await message.answer("❌ Error. Please try again.")


@router.message(F.text.in_(["⚙️ Default Settings", "⚙️ Настройки по умолчанию"]))
async def handle_default_settings_button(message: Message, state: FSMContext) -> None:
    """
    Handle 'Default Settings' button.
    
    Shows user's default group settings (applied to new groups).
    """
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    
    logger.info(f"⚙️ User {user_id} clicked Default Settings button")
    
    try:
        lang = await get_user_language(user_id)
        
        from luka_bot.services.moderation_service import get_moderation_service
        moderation_service = await get_moderation_service()
        
        # Get or create user default settings
        user_defaults = await moderation_service.get_or_create_user_default_settings(user_id)
        
        # Header text
        text = f"""<b>{_('user_group_defaults.title', lang)}</b>

<i>{_('user_group_defaults.intro', lang)}</i>"""
        
        # Reuse existing group admin menu
        from luka_bot.keyboards.group_admin import create_group_admin_menu
        
        keyboard = create_group_admin_menu(
            group_id=user_id,  # Use user_id as "group_id"
            group_title=None,
            moderation_enabled=user_defaults.moderation_enabled,
            kb_indexation_enabled=user_defaults.kb_indexation_enabled,
            moderate_admins_enabled=user_defaults.moderate_admins_enabled,
            stoplist_count=len(user_defaults.stoplist_words),
            current_language=lang,
            silent_mode=user_defaults.silent_mode,
            ai_assistant_enabled=user_defaults.ai_assistant_enabled,
            is_user_defaults=True
        )
        
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Showed default settings to user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error showing default settings: {e}", exc_info=True)
        await message.answer("❌ Error loading settings. Please try again.")
