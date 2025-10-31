"""
/chat command handler - Phase 4.

Shows thread management menu (existing threads keyboard).
Phase 4: i18n support via i18n_helper.
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.user_profile_service import get_user_profile_service
from luka_bot.services.welcome_prompts import get_welcome_message
from luka_bot.keyboards.threads_menu import get_threads_keyboard, get_empty_state_keyboard
from luka_bot.handlers.keyboard_actions import ThreadCreationStates
from luka_bot.utils.i18n_helper import _, get_error_message, get_user_language

router = Router()


@router.message(Command("chat"))
async def handle_chat(message: Message, state: FSMContext) -> None:
    """
    Handle /chat command - show thread management.
    
    Phase 4: Dedicated command for thread management.
    """
    user_id = message.from_user.id if message.from_user else None
    first_name = message.from_user.first_name if message.from_user else ""
    
    if not user_id:
        return
    
    logger.info(f"💬 /chat from user {user_id}")
    
    try:
        # Get user language
        lang = await get_user_language(user_id)
        
        thread_service = get_thread_service()
        threads = await thread_service.list_threads(user_id)
        
        if threads:
            # User has existing threads - show them
            logger.info(f"📚 User {user_id} has {len(threads)} existing threads")
            
            # Show existing threads with keyboard
            current_thread = await thread_service.get_active_thread(user_id)
            keyboard = await get_threads_keyboard(threads, current_thread, lang)
            
            # Build full message with i18n
            threads_text = f"""{_('chat.title', lang)}

{_('chat.threads_count', lang, count=len(threads))}

{_('chat.threads_instruction', lang)}"""
            
            await message.answer(
                threads_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            logger.info(f"📋 Sent keyboard with {len(threads)} threads")
            
        else:
            # New user - show welcome prompt and empty state
            logger.info(f"✨ No threads for user {user_id} - showing welcome prompt")
            
            # Get random welcome message
            welcome_text = get_welcome_message(first_name, language=lang)
            
            await message.answer(welcome_text, parse_mode="HTML")
            
            # Set FSM state to waiting for first message
            await state.set_state(ThreadCreationStates.waiting_for_first_message)
            
            # Show empty state keyboard
            keyboard = await get_empty_state_keyboard(lang)
            await message.answer(
                _('chat.tip_start', lang),
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            logger.info(f"✅ Set user {user_id} to waiting_for_first_message state")
    
    except Exception as e:
        logger.error(f"❌ Error in /chat handler: {e}")
        await message.answer(get_error_message("generic", await get_user_language(user_id)))
    
    logger.info(f"✅ /chat completed for user {user_id}")

