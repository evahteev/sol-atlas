"""
/reset command handler - Phase 3.

Clears all user data: threads, history, FSM state.
Similar to bot_server reset but simplified for luka_bot.
Phase 4: i18n support.
"""
import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from loguru import logger

from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.user_profile_service import get_user_profile_service
from luka_bot.services.welcome_prompts import get_welcome_message
from luka_bot.core.loader import redis_client
from luka_bot.middlewares.password_middleware import PasswordMiddleware
from luka_bot.keyboards.threads_menu import get_empty_state_keyboard
from luka_bot.handlers.keyboard_actions import ThreadCreationStates
from luka_bot.handlers.states import NavigationStates
from luka_bot.utils.i18n_helper import _, get_user_language

router = Router()


@router.message(Command("reset"))
async def handle_reset_command(message: Message, state: FSMContext) -> None:
    """
    Handle /reset command to show reset options.
    """
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    
    logger.info(f"🔄 Reset command from user {user_id}")
    
    # Get user language
    lang = await get_user_language(user_id)
    
    # Show reset options
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_('reset.option_basic', lang),
                callback_data="reset_basic"
            ),
            InlineKeyboardButton(
                text=_('reset.option_full', lang),
                callback_data="reset_full"
            )
        ],
        [
            InlineKeyboardButton(
                text=_('reset.option_auth', lang),
                callback_data="reset_auth"
            ),
            InlineKeyboardButton(
                text=_('reset.option_cancel', lang),
                callback_data="reset_cancel"
            )
        ]
    ])
    
    reset_options_msg = f"""{_('reset.options_title', lang)}

{_('reset.options_basic', lang)}
{_('reset.options_full', lang)}
{_('reset.options_auth', lang)}

{_('reset.options_choose', lang)}"""
    
    await message.answer(reset_options_msg, reply_markup=keyboard, parse_mode="HTML")


async def perform_reset(user_id: int, reset_type: str, state: FSMContext) -> str:
    """
    Perform the actual reset based on type.
    
    Args:
        user_id: User ID
        reset_type: 'basic', 'full', or 'auth'
        state: FSM context
        
    Returns:
        Status message
    """
    try:
        thread_service = get_thread_service()
        
        if reset_type in ['basic', 'full']:
            # 1. Get all threads to delete their history
            threads = await thread_service.list_threads(user_id)
            thread_count = len(threads)
            
            # 2. Delete all threads (this also deletes their history)
            for thread in threads:
                try:
                    await thread_service.delete_thread(thread.thread_id, user_id)
                except Exception as e:
                    logger.warning(f"⚠️  Failed to delete thread {thread.thread_id}: {e}")
        else:
            thread_count = 0
        
        if reset_type in ['basic', 'full']:
            # 3. Clear FSM state
            await state.clear()
            logger.info(f"✅ Cleared FSM state for user {user_id}")

            # 4. Clear any remaining user-scoped history (Phase 2 compat)
            try:
                await redis_client.delete(f"llm_history:{user_id}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to clear user history: {e}")

            # 5. Clear active thread pointer
            try:
                await redis_client.delete(f"user_active_thread:{user_id}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to clear active thread: {e}")

            # 6. Reset user profile to trigger onboarding again
            try:
                profile_service = get_user_profile_service()
                await profile_service.reset_onboarding(user_id)
                logger.info(f"✅ Reset onboarding status for user {user_id}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to reset onboarding: {e}")
        
        if reset_type in ['auth', 'full']:
            # Clear password authentication (both global and group-specific)
            try:
                # Clear global auth
                await redis_client.delete(f"{PasswordMiddleware.REDIS_KEY_PREFIX}user:{user_id}")
                
                # Clear all group auths for this user
                pattern = f"{PasswordMiddleware.REDIS_KEY_PREFIX}group:{user_id}:*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
                    logger.info(f"✅ Cleared {len(keys)} group auth keys for user {user_id}")
                
                logger.info(f"✅ Cleared password authentication for user {user_id}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to clear password auth: {e}")
        
        # Small delay for Redis operations to complete
        await asyncio.sleep(0.2)
        
        # Build status message
        if reset_type == 'basic':
            return f"✅ Basic reset complete: {thread_count} threads deleted, FSM state cleared"
        elif reset_type == 'full':
            return f"✅ Full reset complete: {thread_count} threads deleted, FSM state cleared, password auth cleared"
        elif reset_type == 'auth':
            return f"✅ Authentication reset complete: Password authentication cleared"
        
    except Exception as e:
        logger.error(f"❌ Error during {reset_type} reset for user {user_id}: {e}")
        return f"❌ Error during reset: {str(e)}"


@router.callback_query(lambda c: c.data and c.data.startswith("reset_"))
async def handle_reset_callback(callback_query, state: FSMContext) -> None:
    """Handle reset option selection."""
    user_id = callback_query.from_user.id if callback_query.from_user else None
    if not user_id:
        await callback_query.answer("Error: User ID not found")
        return
    
    reset_type = callback_query.data.replace("reset_", "")
    
    if reset_type == "cancel":
        await callback_query.message.delete()
        await callback_query.answer("Reset cancelled")
        return
    
    # Show processing message
    await callback_query.message.edit_text("🔄 Processing reset...")
    
    # Perform the reset
    status_msg = await perform_reset(user_id, reset_type, state)
    
    # Get user language
    lang = await get_user_language(user_id)
    
    if reset_type in ['basic', 'full']:
        # Clear navigation state after reset
        await state.clear()
        
        first_name = callback_query.from_user.first_name if callback_query.from_user else ""
        
        # Build reset message with i18n
        reset_msg = f"""{_('reset.title', lang)}

{status_msg}

{_('reset.welcome', lang, first_name=first_name)}

{_('reset.invite', lang)}"""
        
        # Hide the groups keyboard after reset
        await callback_query.message.delete()
        await callback_query.message.answer(reset_msg, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    else:
        # Auth-only reset
        await callback_query.message.edit_text(f"✅ {status_msg}")
    
    await callback_query.answer()
    logger.info(f"✅ {reset_type.title()} reset completed for user {user_id}")
