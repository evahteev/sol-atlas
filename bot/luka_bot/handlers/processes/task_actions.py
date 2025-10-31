"""
Task action handler for button callbacks.
"""
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.keyboards.inline.task_keyboards import TaskActionCallback
from luka_bot.services.task_service import get_task_service
from luka_bot.services.message_cleanup_service import get_message_cleanup_service
from luka_bot.handlers.processes.start_process import poll_and_render_next_task

router = Router(name="task_actions")


@router.callback_query(TaskActionCallback.filter())
async def handle_task_action(
    callback: CallbackQuery,
    callback_data: TaskActionCallback,
    state: FSMContext
):
    """
    Handle task action button clicks.
    
    Args:
        callback: Callback query from button press
        callback_data: Parsed callback data
        state: FSM context
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    task_service = get_task_service()
    
    # Get full task ID from state
    data = await state.get_data()
    current_task_id = data.get("current_task_id")
    
    if not current_task_id:
        logger.warning(f"Task action called but no current_task_id in state for user {user_id}")
        await callback.answer()
        return
    
    # Handle different actions
    if callback_data.action == "cancel" or callback_data.action == "cancel_upload":
        await handle_task_cancel(callback, current_task_id, state)
    else:
        # Complete task with action
        logger.info(f"Completing task {current_task_id} with action {callback_data.action}")
        
        success = await task_service.complete_task_with_action(
            task_id=current_task_id,
            action_name=callback_data.action,
            user_id=user_id,
            state=state
        )
        
        if success:
            # Edit message to show completion
            action_display = callback_data.action.replace('action_', '').replace('_', ' ').title()
            await callback.message.edit_text(
                f"✅ Action completed: {action_display}",
                reply_markup=None
            )
            
            # Clean up messages
            cleanup_service = get_message_cleanup_service()
            await cleanup_service.delete_task_messages(current_task_id, callback.bot, state)
            
            # Poll for next task
            process_id = data.get("active_process")
            if process_id:
                await poll_and_render_next_task(callback.message, user_id, process_id, state)
            else:
                await callback.message.answer("✅ Task completed successfully!")
        else:
            await callback.answer("❌ Failed to complete task", show_alert=True)


async def handle_task_cancel(callback: CallbackQuery, task_id: str, state: FSMContext):
    """
    Handle task/process cancellation.
    
    Args:
        callback: Callback query
        task_id: Task ID to cancel
        state: FSM context
    """
    # Delete messages
    cleanup_service = get_message_cleanup_service()
    await cleanup_service.delete_task_messages(task_id, callback.bot, state)
    
    # Clear process state
    await state.set_state(None)
    await state.update_data({
        "active_process": None,
        "current_task_id": None,
        "current_s3_variable": None,
        "expected_file_extension": None
    })
    
    await callback.message.answer("❌ Process cancelled")
    logger.info(f"User {callback.from_user.id} cancelled task {task_id}")

