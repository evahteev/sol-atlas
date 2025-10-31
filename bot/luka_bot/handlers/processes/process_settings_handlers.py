"""
Process instance management handlers.

Handles:
- process_settings: Show process info and management options
- process_delete: Delete process instance
- process_suspend: Suspend/activate process instance  
- process_restart: Restart process instance
- process_back_to_task: Return to task dialog
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from loguru import logger

router = Router(name="process_settings")


async def _get_process_id_from_context(state: FSMContext, process_id_short: str) -> tuple[str | None, bool, bool]:
    """
    Helper function to get full process ID from either form_context or process_list_context.
    
    Returns:
        tuple: (process_instance_id, from_profile, is_active)
        - process_instance_id: Full process instance ID
        - from_profile: Whether called from profile (True) or task (False)
        - is_active: Whether process is active (True) or completed (False). Always True for task context.
    """
    data = await state.get_data()
    
    # Check if called from profile processes list
    process_list_context = data.get("process_list_context", {})
    from_profile = process_list_context.get("from_profile", False)
    
    if from_profile:
        # Find full process ID from stored profile context
        processes = process_list_context.get("processes", {})
        
        for pid, proc_data in processes.items():
            if pid.startswith(process_id_short):
                is_active = proc_data.get('active', True)
                return pid, True, is_active
        
        return None, True, False
    else:
        # Get full process ID from task form context
        form_context = data.get("form_context", {})
        form_data_dict = form_context.get("form_data", {})
        process_instance_id = form_data_dict.get("process_instance_id")
        
        # Tasks always belong to active processes
        return process_instance_id, False, True


@router.callback_query(F.data.startswith("show_process_id:"))
async def handle_show_process_id(callback: CallbackQuery, state: FSMContext):
    """
    Show full process instance ID in an alert for copying.
    
    Format: show_process_id:{process_id_short}
    """
    try:
        # Extract short process ID
        process_id_short = callback.data.split(":")[1]
        
        # Get full process ID from context (works for both task and profile contexts)
        process_instance_id, _, _ = await _get_process_id_from_context(state, process_id_short)
        
        if not process_instance_id:
            await callback.answer("❌ Process ID not found", show_alert=True)
            return
        
        # Show full process ID in alert (user can copy it)
        await callback.answer(
            f"Process Instance ID:\n{process_instance_id}",
            show_alert=True
        )
        
    except Exception as e:
        logger.error(f"❌ Error showing process ID: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("process_settings:"))
async def handle_process_settings(callback: CallbackQuery, state: FSMContext):
    """
    Show process instance information and management options.
    
    Format: process_settings:{process_id_short}
    """
    try:
        # Extract short process ID (first 8 chars)
        process_id_short = callback.data.split(":")[1]
        
        # Get full process ID and active status from context
        process_instance_id, from_profile, is_active = await _get_process_id_from_context(state, process_id_short)
        
        if not process_instance_id:
            await callback.answer("❌ Process ID not found", show_alert=True)
            return
        
        # Get user ID to access Camunda
        user_id = callback.from_user.id
        
        # Fetch process instance details
        from luka_bot.services.camunda_service import get_camunda_service
        camunda_service = get_camunda_service()
        client = await camunda_service._get_client(user_id)
        
        process_instance = await client.get_process_instance(
            process_instance_id
        )
        
        if not process_instance:
            # Try history if not active
            process_instance = await client.get_history_process_instance(
                process_instance_id
            )
            
            if not process_instance:
                await callback.answer("❌ Process not found", show_alert=True)
                return
        
        # Get current activity
        try:
            activities = await client.get_current_activity(
                process_instance_id
            )
        except Exception as e:
            logger.warning(f"Could not fetch activities for process {process_instance_id}: {e}")
            activities = []
        
        # Build info message
        info_message = _build_process_info_message(
            process_instance, 
            activities,
            process_instance_id,
            is_active
        )
        
        # Build management keyboard
        keyboard = _build_process_settings_keyboard(
            process_instance_id,
            getattr(process_instance, 'suspended', False),
            from_profile=from_profile,
            is_active=is_active
        )
        
        # Edit current message to show process info
        await callback.message.edit_text(
            info_message,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Error showing process settings: {e}")
        await callback.answer("❌ Error loading process info", show_alert=True)


def _build_process_info_message(
    process_instance,
    activities: list,
    process_id: str,
    is_active: bool = True
) -> str:
    """Build formatted process instance information message."""
    
    parts = [
        "<b>⚙️ Process Instance Settings</b>\n",
        f"<b>ID:</b> <code>{process_id}</code>",
        f"<b>Definition:</b> {getattr(process_instance, 'process_definition_name', 'N/A')}",
        f"<b>Key:</b> <code>{getattr(process_instance, 'process_definition_key', 'N/A')}</code>",
    ]
    
    # Business key
    business_key = getattr(process_instance, 'business_key', None)
    if business_key:
        parts.append(f"<b>Business Key:</b> <code>{business_key}</code>")
    
    # Status
    if not is_active:
        status = "✅ Completed"
    else:
        is_suspended = getattr(process_instance, 'suspended', False)
        status = "⏸️ Suspended" if is_suspended else "▶️ Active"
    parts.append(f"<b>Status:</b> {status}")
    
    # Current activities
    if activities:
        activity_names = [a.get('activityName', a.get('activityId', 'Unknown')) 
                         for a in activities[:5]]  # Show max 5
        parts.append(f"\n<b>Current Activities:</b>")
        for name in activity_names:
            parts.append(f"  • {name}")
        
        if len(activities) > 5:
            parts.append(f"  <i>...and {len(activities) - 5} more</i>")
    
    parts.append("\n" + "─" * 30)
    
    # Show warning only for active processes
    if is_active:
        parts.append("\n<i>⚠️ Warning: Deleting or suspending will affect all tasks in this process.</i>")
    else:
        parts.append("\n<i>ℹ️ This process has completed and is in view-only mode.</i>")
    
    return "\n".join(parts)


def _build_process_settings_keyboard(
    process_id: str,
    is_suspended: bool,
    from_profile: bool = False,
    is_active: bool = True
) -> InlineKeyboardMarkup:
    """Build keyboard for process management actions."""
    
    buttons = []
    
    # Only show management buttons for active processes
    if is_active:
        # Suspend/Activate toggle
        if is_suspended:
            buttons.append([InlineKeyboardButton(
                text="▶️ Activate Process",
                callback_data=f"process_activate:{process_id[:8]}"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text="⏸️ Suspend Process",
                callback_data=f"process_suspend:{process_id[:8]}"
            )])
        
        # Restart button
        buttons.append([InlineKeyboardButton(
            text="🔄 Restart Process",
            callback_data=f"process_restart_confirm:{process_id[:8]}"
        )])
        
        # Delete button (dangerous action)
        buttons.append([InlineKeyboardButton(
            text="🗑️ Delete Process",
            callback_data=f"process_delete_confirm:{process_id[:8]}"
        )])
    else:
        # Show info message for completed processes
        buttons.append([InlineKeyboardButton(
            text="ℹ️ Process Completed - View Only",
            callback_data=f"process_settings:{process_id[:8]}"
        )])
    
    # Context-aware back button
    if from_profile:
        buttons.append([InlineKeyboardButton(
            text="◀️ Back to Processes",
            callback_data="profile_processes"
        )])
    else:
        buttons.append([InlineKeyboardButton(
            text="◀️ Back to Task",
            callback_data=f"process_back_to_task:{process_id[:8]}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("process_suspend:"))
async def handle_process_suspend(callback: CallbackQuery, state: FSMContext):
    """Suspend process instance."""
    await _toggle_suspension(callback, state, suspended=True)


@router.callback_query(F.data.startswith("process_activate:"))
async def handle_process_activate(callback: CallbackQuery, state: FSMContext):
    """Activate (resume) process instance."""
    await _toggle_suspension(callback, state, suspended=False)


async def _toggle_suspension(
    callback: CallbackQuery, 
    state: FSMContext, 
    suspended: bool
):
    """Toggle process suspension state."""
    try:
        process_id_short = callback.data.split(":")[1]
        
        # Get full process ID and active status from context
        process_instance_id, _, is_active = await _get_process_id_from_context(state, process_id_short)
        
        if not process_instance_id:
            await callback.answer("❌ Process ID not found", show_alert=True)
            return
        
        if not is_active:
            await callback.answer("❌ Cannot modify completed process", show_alert=True)
            return
        
        # Update suspension state
        from luka_bot.services.camunda_service import get_camunda_service
        camunda_service = get_camunda_service()
        user_id = callback.from_user.id
        client = await camunda_service._get_client(user_id)
        
        await client.update_suspension_state_by_id(
            process_instance_id,
            suspended
        )
        
        action = "suspended" if suspended else "activated"
        await callback.answer(f"✅ Process {action}")
        
        # Refresh the settings view
        callback.data = f"process_settings:{process_id_short}"
        await handle_process_settings(callback, state)
        
    except Exception as e:
        logger.error(f"❌ Error toggling suspension: {e}")
        await callback.answer("❌ Error updating process", show_alert=True)


@router.callback_query(F.data.startswith("process_delete_confirm:"))
async def handle_process_delete_confirm(callback: CallbackQuery, state: FSMContext):
    """Show confirmation dialog before deleting process."""
    try:
        process_id_short = callback.data.split(":")[1]
        
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Yes, Delete",
                    callback_data=f"process_delete:{process_id_short}"
                ),
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data=f"process_settings:{process_id_short}"
                )
            ]
        ])
        
        await callback.message.edit_text(
            "<b>⚠️ Delete Process Instance?</b>\n\n"
            "This will permanently delete the process instance and all associated tasks.\n\n"
            "<i>This action cannot be undone.</i>",
            parse_mode="HTML",
            reply_markup=confirm_keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Error showing delete confirmation: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("process_delete:"))
async def handle_process_delete(callback: CallbackQuery, state: FSMContext):
    """Delete process instance."""
    try:
        process_id_short = callback.data.split(":")[1]
        
        # Get full process ID and active status from context
        process_instance_id, _, is_active = await _get_process_id_from_context(state, process_id_short)
        
        if not process_instance_id:
            await callback.answer("❌ Process ID not found", show_alert=True)
            return
        
        if not is_active:
            await callback.answer("❌ Cannot delete completed process", show_alert=True)
            return
        
        # Delete process
        from luka_bot.services.camunda_service import get_camunda_service
        camunda_service = get_camunda_service()
        user_id = callback.from_user.id
        client = await camunda_service._get_client(user_id)
        
        await client.delete_process(process_instance_id)
        
        await callback.message.edit_text(
            "<b>✅ Process Deleted</b>\n\n"
            "The process instance and all associated tasks have been deleted.",
            parse_mode="HTML"
        )
        
        # Clear form context
        await state.update_data({
            "form_context": None,
            "current_task_id": None
        })
        await state.clear()
        
        await callback.answer("✅ Process deleted")
        
    except Exception as e:
        logger.error(f"❌ Error deleting process: {e}")
        await callback.answer("❌ Error deleting process", show_alert=True)


@router.callback_query(F.data.startswith("process_restart_confirm:"))
async def handle_process_restart_confirm(callback: CallbackQuery, state: FSMContext):
    """Show confirmation dialog before restarting process."""
    try:
        process_id_short = callback.data.split(":")[1]
        
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Yes, Restart",
                    callback_data=f"process_restart:{process_id_short}"
                ),
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data=f"process_settings:{process_id_short}"
                )
            ]
        ])
        
        await callback.message.edit_text(
            "<b>🔄 Restart Process Instance?</b>\n\n"
            "This will:\n"
            "1. Delete the current process instance\n"
            "2. Start a new instance with the same definition\n\n"
            "<i>⚠️ All progress will be lost. The process will start from the beginning.</i>",
            parse_mode="HTML",
            reply_markup=confirm_keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Error showing restart confirmation: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("process_restart:"))
async def handle_process_restart(callback: CallbackQuery, state: FSMContext):
    """Restart process instance (delete + create new)."""
    try:
        process_id_short = callback.data.split(":")[1]
        
        # Get full process ID and active status from context
        process_instance_id, _, is_active = await _get_process_id_from_context(state, process_id_short)
        
        if not process_instance_id:
            await callback.answer("❌ Process ID not found", show_alert=True)
            return
        
        if not is_active:
            await callback.answer("❌ Cannot restart completed process", show_alert=True)
            return
        
        from luka_bot.services.camunda_service import get_camunda_service
        camunda_service = get_camunda_service()
        user_id = callback.from_user.id
        client = await camunda_service._get_client(user_id)
        
        # Get process instance details before deleting
        process_instance = await client.get_process_instance(
            process_instance_id
        )
        
        if not process_instance:
            await callback.answer("❌ Process not found", show_alert=True)
            return
        
        process_key = process_instance.process_definition_key
        business_key = process_instance.business_key
        
        # Get current variables (to restart with same state)
        try:
            variables = await client.get_variables_for_process_instance(
                process_instance_id
            )
        except Exception as e:
            logger.warning(f"Could not fetch variables for restart: {e}")
            variables = {}
        
        # Delete old process
        await client.delete_process(process_instance_id)
        
        # Start new process
        new_process = await camunda_service.start_process(
            telegram_user_id=user_id,
            process_key=process_key,
            business_key=business_key,
            variables=variables
        )
        
        await callback.message.edit_text(
            f"<b>✅ Process Restarted</b>\n\n"
            f"New Process ID: <code>{new_process.id}</code>\n\n"
            f"The process has been restarted from the beginning.",
            parse_mode="HTML"
        )
        
        # Update state with new process ID
        await state.update_data({
            "active_process": str(new_process.id),
            "form_context": None,
            "current_task_id": None
        })
        
        await callback.answer("✅ Process restarted")
        
        # Poll for new task
        from luka_bot.handlers.processes.start_process import poll_and_render_next_task
        await poll_and_render_next_task(
            callback.message,
            user_id,
            str(new_process.id),
            state
        )
        
    except Exception as e:
        logger.error(f"❌ Error restarting process: {e}")
        await callback.answer("❌ Error restarting process", show_alert=True)


@router.callback_query(F.data.startswith("process_back_to_task:"))
async def handle_process_back_to_task(callback: CallbackQuery, state: FSMContext):
    """Return to task dialog from process settings."""
    try:
        # Get form context to restore task view
        data = await state.get_data()
        form_context = data.get("form_context", {})
        
        if not form_context:
            logger.warning(f"No form context found when returning to task for user {callback.from_user.id}")
            await callback.answer()
            return
        
        # Restore intro message text with keyboard
        intro_text = form_context.get("intro_message_text", "")
        
        # Rebuild original keyboard
        from luka_bot.models.form_models import FormContext
        context = FormContext.from_dict(form_context)
        form_data = context.form_data
        
        # Rebuild keyboard (same as in render_form)
        keyboard_rows = []
        
        # Add action buttons if available
        if form_data.has_action_buttons:
            from luka_bot.keyboards.inline.task_keyboards import build_action_keyboard
            action_keyboard = build_action_keyboard(
                form_data.task_id,
                form_data.action_vars,
                show_cancel=False
            )
            keyboard_rows.extend(action_keyboard.inline_keyboard)
        
        # Add cancel/start buttons
        keyboard_rows.append([
            InlineKeyboardButton(
                text="❌",
                callback_data=f"form_close:{form_data.form_type.value}"
            ),
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"form_begin:{form_data.form_type.value}"
            )
        ])
        
        # NO process instance link button for tasks (removed per requirements)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
        
        # Restore task intro message
        await callback.message.edit_text(
            intro_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        await callback.answer("◀️ Back to task")
        
    except Exception as e:
        logger.error(f"❌ Error returning to task: {e}")
        await callback.answer("❌ Error", show_alert=True)

