"""
/groups command handler - Phase 6 MVP skeleton.

Shows how to add bot to groups and group management options (Coming Soon).
Phase 6: Full group-thread mapping, invitations, history import.
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.utils.i18n_helper import _, get_user_language
from luka_bot.keyboards.mode_reply import get_groups_mode_keyboard
from luka_bot.handlers.states import NavigationStates
from luka_bot.services.group_service import get_group_service

router = Router()


@router.message(Command("groups"))
async def handle_groups(message: Message, state: FSMContext) -> None:
    """
    Handle /groups command - show group management (MVP: Coming Soon).
    
    Phase 6: i18n support + GROUPS_MODE keyboard.
    Phase 6+: Full group-thread mapping, invitations, history import.
    """
    user_id = message.from_user.id if message.from_user else None
    
    if not user_id:
        return
    
    logger.info(f"👥 /groups from user {user_id}")
    
    # Set navigation state to groups_mode
    await state.set_state(NavigationStates.groups_mode)
    
    # Get user language
    lang = await get_user_language(user_id)
    
    # Build groups text with i18n
    groups_text = f"""{_('groups.title', lang)}

{_('groups.intro', lang)}

{_('groups.how_to_add_header', lang)}
{_('groups.step1', lang)}
{_('groups.step2', lang)}
{_('groups.step3', lang)}

{_('groups.features_header', lang)}
{_('groups.feature_mapping', lang)}
{_('groups.feature_owner', lang)}
{_('groups.feature_history', lang)}
{_('groups.feature_thread_switch', lang)}

{_('groups.under_development', lang)}"""
    
    # Get real group count from GroupService
    group_service = await get_group_service()
    user_groups = await group_service.list_user_groups(user_id, active_only=True)
    group_count = len(user_groups)
    
    # Get GROUPS_MODE reply keyboard
    reply_keyboard = get_groups_mode_keyboard(lang, group_count)
    
    # Send with GROUPS_MODE reply keyboard
    await message.answer(groups_text, reply_markup=reply_keyboard, parse_mode="HTML")
    
    logger.info(f"✅ Showed GROUPS_MODE keyboard to user {user_id}")


@router.callback_query(lambda c: c.data and c.data.startswith("groups_"))
async def handle_groups_actions(callback_query: CallbackQuery) -> None:
    """Handle group menu actions (all Coming Soon for Phase 6)."""
    user_id = callback_query.from_user.id if callback_query.from_user else None
    action = callback_query.data.split("_", 1)[1]
    
    # Get user language
    lang = await get_user_language(user_id) if user_id else "en"
    
    if action == "close":
        await callback_query.message.delete()
        await callback_query.answer(_('groups.menu_closed', lang))
    else:
        # All actions are Coming Soon
        await callback_query.answer(
            _('groups.coming_soon', lang, action=action),
            show_alert=True
        )
        logger.info(f"🚧 User {user_id} tried {action} (coming soon)")
