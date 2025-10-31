"""
/tasks command handler - Phase 4 MVP skeleton.

Shows GTD-organized task list (Coming Soon).
Phase 4: Full i18n support.
Future: Camunda task integration with auto-switching to source threads.
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.utils.i18n_helper import _, get_user_language
from luka_bot.keyboards.mode_reply import get_tasks_mode_keyboard
from luka_bot.handlers.states import NavigationStates

router = Router()


@router.message(Command("tasks"))
async def handle_tasks(message: Message, state: FSMContext) -> None:
    """
    Handle /tasks command - show task management (MVP: Coming Soon).
    
    Phase 4: i18n support + TASKS_MODE keyboard.
    Phase 5+: Full GTD integration with Camunda.
    """
    user_id = message.from_user.id if message.from_user else None
    
    if not user_id:
        return
    
    logger.info(f"📋 /tasks from user {user_id}")
    
    # Set navigation state to tasks_mode
    await state.set_state(NavigationStates.tasks_mode)
    
    # Get user language
    lang = await get_user_language(user_id)
    
    # Build tasks text with i18n
    tasks_text = f"""{_('tasks.title', lang)}

{_('tasks.gtd_header', lang)}
{_('tasks.inbox', lang)}
{_('tasks.next', lang)}
{_('tasks.waiting', lang)}
{_('tasks.scheduled', lang)}
{_('tasks.someday', lang)}

{_('tasks.future_header', lang)}
{_('tasks.feature_claim', lang)}
{_('tasks.feature_switch', lang)}
{_('tasks.feature_llm', lang)}

{_('tasks.under_development', lang)}"""
    
    # Mock task counts (Phase 5: real data from Camunda)
    counts = {"inbox": 0, "next": 0, "waiting": 0, "scheduled": 0, "someday": 0}
    
    # Get TASKS_MODE reply keyboard
    reply_keyboard = get_tasks_mode_keyboard(lang, counts)
    
    # Send with TASKS_MODE reply keyboard only (no inline menu - it duplicates the reply keyboard)
    await message.answer(tasks_text, reply_markup=reply_keyboard, parse_mode="HTML")
    
    logger.info(f"✅ Showed TASKS_MODE keyboard to user {user_id}")


@router.callback_query(lambda c: c.data and c.data.startswith("tasks_"))
async def handle_tasks_actions(callback_query: CallbackQuery) -> None:
    """Handle task menu actions."""
    user_id = callback_query.from_user.id if callback_query.from_user else None
    action = callback_query.data.split("_", 1)[1]
    
    # Get user language
    lang = await get_user_language(user_id) if user_id else "en"
    
    if action == "close":
        await callback_query.message.delete()
        await callback_query.answer(_('tasks.menu_closed', lang))
    else:
        # Capitalize action for display
        action_display = action.capitalize()
        await callback_query.answer(
            _('tasks.coming_soon', lang, action=action_display),
            show_alert=True
        )
