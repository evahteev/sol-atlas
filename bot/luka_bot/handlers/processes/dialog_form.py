"""
Dialog form handler for multi-step form variables.

Note: Form input routing is now handled by FormInputMiddleware (form_input_middleware.py).
This file only contains STATE-BASED handlers that match specific FSM states.
The middleware intercepts messages when forms are active and routes them to the correct handler.
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.handlers.states import ProcessStates
from luka_bot.services.dialog_service import get_dialog_service

router = Router(name="dialog_form")

# NOTE: Removed handle_form_input_check handler - it was redundant with FormInputMiddleware
# and was breaking event propagation with non-existent SkipHandler exception.
#
# Form routing now works as follows:
# 1. FormInputMiddleware checks FSM state (waiting_for_input, dialog_active, file_upload_pending)
# 2. If in form state AND form context exists, middleware routes to form handler
# 3. Otherwise, middleware allows message to continue to streaming handler
# 4. The state-based handlers below (ProcessStates.waiting_for_input) provide additional
#    matching for specific scenarios like ForceReply responses


@router.message(F.reply_to_message, ProcessStates.waiting_for_input)
async def handle_dialog_input(message: Message, state: FSMContext):
    """
    Handle dialog form input (ForceReply responses).
    
    Supports both unified form_context and legacy task_dialog/start_form formats.
    
    Args:
        message: User's response message
        state: FSM context
    """
    data = await state.get_data()
    
    # Check which format is being used
    if "form_context" in data or "start_form" in data:
        # Use start form input handler (unified format)
        from luka_bot.handlers.processes.start_form_handlers import handle_start_form_input
        await handle_start_form_input(message, state)
    elif "task_dialog" in data:
        # Use legacy task dialog handler
        dialog_service = get_dialog_service()
        await dialog_service.handle_dialog_response(message, state)
    else:
        logger.warning(f"Dialog input received but no known context in state for user {message.from_user.id}")
        await message.answer("⚠️ Контекст диалога утерян. Пожалуйста, начните заново.")


@router.message(ProcessStates.waiting_for_input)
async def handle_dialog_fallback(message: Message, state: FSMContext):
    """
    Handle messages during dialog that aren't replies.
    Fallback for users who don't use reply mechanism.
    """
    data = await state.get_data()
    
    # Check which format is being used
    if "form_context" in data or "start_form" in data:
        # Use start form input handler (unified format)
        from luka_bot.handlers.processes.start_form_handlers import handle_start_form_input
        await handle_start_form_input(message, state)
    elif "task_dialog" in data:
        # Use legacy task dialog handler
        dialog_service = get_dialog_service()
        await dialog_service.handle_dialog_input(message, state)
    else:
        logger.warning(f"Dialog fallback received but no known context in state for user {message.from_user.id}")
        await message.answer("⚠️ Контекст диалога утерян. Пожалуйста, начните заново.")
