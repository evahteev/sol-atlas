"""
Start form handlers for form variable collection and confirmation.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.handlers.states import ProcessStates
from luka_bot.utils.i18n_helper import _, get_user_language


router = Router(name="start_form")


@router.callback_query(F.data == "start_form_close")
async def handle_start_form_close(callback: CallbackQuery, state: FSMContext):
    """
    Handle X button - delete intro message and clear state.
    """
    try:
        # Delete the intro message
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"Could not delete intro message: {e}")
        
        # Clear state
        await state.update_data({"start_form": None, "pending_process": None})
        await state.clear()
        
        user_lang = await get_user_language(callback.from_user.id)
        await callback.answer(_('common.cancel', user_lang))
        logger.info(f"User {callback.from_user.id} closed start form")
        
    except Exception as e:
        logger.error(f"❌ Error closing start form: {e}")
        user_lang = await get_user_language(callback.from_user.id)
        await callback.answer(_('error.generic', user_lang), show_alert=True)


@router.callback_query(F.data == "start_form_begin")
async def handle_start_form_begin(callback: CallbackQuery, state: FSMContext):
    """
    Handle Start button - begin variable collection or start process immediately.
    """
    try:
        data = await state.get_data()
        form_data = data.get("start_form", {})
        
        editable_vars = form_data.get("editable_vars", [])
        total_editable = form_data.get("total_editable", 0)
        
        # Remove the inline keyboard from intro message
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            logger.warning(f"Could not remove keyboard: {e}")
        
        await callback.answer("▶️ Начинаем...")
        
        if total_editable == 0:
            # No variables to collect - start process immediately with initial variables
            logger.info(f"No variables to collect, starting process immediately")
            
            # Get process data
            pending_process = data.get("pending_process", {})
            process_key = pending_process.get("process_key")
            business_key = pending_process.get("business_key")
            telegram_user_id = pending_process.get("telegram_user_id")
            initial_variables = pending_process.get("initial_variables", {})
            
            if not process_key:
                user_lang = await get_user_language(callback.from_user.id)
                await callback.message.answer(_('error.process_not_found', user_lang))
                return
            
            # Start process with initial variables (e.g., group_index)
            from luka_bot.services.camunda_service import get_camunda_service
            camunda_service = get_camunda_service()
            
            process_instance = await camunda_service.start_process(
                telegram_user_id=telegram_user_id,
                process_key=process_key,
                business_key=business_key,
                variables=initial_variables
            )
            
            # Update state
            await state.set_state(ProcessStates.process_active)
            await state.update_data({
                "active_process": process_instance.id,
                "process_key": process_key,
                "start_form": None,
                "pending_process": None
            })
            
            await callback.message.answer(
                "✅ Процесс запущен!\n\n"
                f"ID процесса: <code>{process_instance.id}</code>",
                parse_mode="HTML"
            )
            
            logger.info(f"✅ Started process {process_instance.id} (no variables)")
            
            # Poll for first task
            from luka_bot.handlers.processes.start_process import poll_and_render_next_task
            await poll_and_render_next_task(
                callback.message, telegram_user_id, process_instance.id, state
            )
        else:
            # Has variables - start dialog collection
            logger.info(f"Starting variable collection: {total_editable} variables")
            
            from luka_bot.services.dialog_service import get_dialog_service
            dialog_service = get_dialog_service()
            
            # Switch to waiting_for_input state
            await state.set_state(ProcessStates.waiting_for_input)
            
            # Start asking for variables
            await dialog_service._ask_next_editable_variable(callback.message, state)
        
    except Exception as e:
        logger.error(f"❌ Error beginning start form: {e}")
        user_lang = await get_user_language(callback.from_user.id)
        await callback.answer(_('error.generic', user_lang), show_alert=True)


@router.message(ProcessStates.waiting_for_input, F.text)
async def handle_start_form_input(message: Message, state: FSMContext):
    """
    Handle user input for form variables (form_ prefix).
    Supports both unified form_context and legacy start_form formats.
    """
    user_id = message.from_user.id if message.from_user else None
    text = message.text or ""
    
    logger.info(f"🔍 START_FORM_INPUT: Handler called for user {user_id}, text='{text[:50]}'")
    
    data = await state.get_data()
    
    logger.debug(f"🔍 START_FORM_INPUT: State keys: {list(data.keys())}")
    
    # Check which format is being used
    if "form_context" in data:
        logger.debug(f"🔍 START_FORM_INPUT: Using form_context format")
        state_key = "form_context"
        form_data = data["form_context"]
        from luka_bot.models.form_models import FormContext
        context = FormContext.from_dict(form_data)
        editable_vars = context.form_data.editable_vars
        current_index = context.current_index
        collected_values = context.collected_values
    elif "start_form" in data:
        logger.debug(f"🔍 START_FORM_INPUT: Using start_form format")
        state_key = "start_form"
        form_data = data["start_form"]
        editable_vars = form_data.get("editable_vars", [])
        current_index = form_data.get("current_index", 0)
        collected_values = form_data.get("collected_values", {})
    else:
        logger.warning(f"🔍 START_FORM_INPUT: No form context found - ignoring")
        # Not a form input - ignore
        return
    
    try:
        logger.debug(f"🔍 START_FORM_INPUT: current_index={current_index}, editable_vars count={len(editable_vars)}")
        
        if current_index >= len(editable_vars):
            logger.warning(f"🔍 START_FORM_INPUT: current_index >= len(editable_vars) - all collected")
            return
        
        # Get current variable
        current_var = editable_vars[current_index]
        var_name = current_var.get("name", "")
        
        # Skip s3_ variables (they should be handled by file upload handler)
        if var_name.startswith("s3_"):
            return
        
        # Handle /skip command for default values
        user_input = message.text.strip()
        if user_input == "/skip":
            # Use default value
            default_value = current_var.get("value", {})
            if isinstance(default_value, dict):
                value = default_value.get("value", "")
            else:
                value = default_value
            
            if not value:
                await message.answer("⚠️ Нет значения по умолчанию. Пожалуйста, введите значение:")
                return
        else:
            value = user_input
        
        # Store collected value
        collected_values[var_name] = value
        
        logger.debug(
            f"📝 Stored value for {var_name}: {value}\n"
            f"   Total collected: {list(collected_values.keys())}"
        )
        
        # Track message IDs for deletion
        if "dialog_message_ids" not in form_data:
            form_data["dialog_message_ids"] = []
        form_data["dialog_message_ids"].append(message.message_id)
        
        # Update state
        form_data["collected_values"] = collected_values
        form_data["current_index"] = current_index + 1
        await state.update_data({state_key: form_data})
        
        logger.debug(f"💾 Updated state with {len(collected_values)} values")
        
        # Confirm
        label = current_var.get("label", var_name.replace("form_", "").replace("_", " ").title())
        confirm_msg = await message.answer(f"✅ <b>{label}:</b> {value}", parse_mode="HTML")
        
        # Track confirmation message too
        form_data["dialog_message_ids"].append(confirm_msg.message_id)
        await state.update_data({state_key: form_data})
        
        # Ask next variable
        from luka_bot.services.dialog_service import get_dialog_service
        dialog_service = get_dialog_service()
        await dialog_service._ask_next_editable_variable(message, state)
        
    except Exception as e:
        logger.error(f"❌ Error handling start form input: {e}")
        user_lang = await get_user_language(message.from_user.id)
        await message.answer(_('error.input_processing', user_lang))


@router.callback_query(F.data == "start_form_confirm")
async def handle_start_form_confirm(callback: CallbackQuery, state: FSMContext):
    """
    Handle Start button on confirmation:
    - Intro and dialog messages are already deleted (done when confirmation was shown)
    - Edit confirmation message to add process ID and status
    - Keep confirmation visible as audit trail
    """
    try:
        data = await state.get_data()
        
        logger.debug(f"📦 STATE KEYS: {list(data.keys())}")
        logger.debug(f"📦 FULL STATE: {data}")
        
        # Try new format first (form_context), fall back to old format (start_form)
        if "form_context" in data:
            from luka_bot.models.form_models import FormContext
            context = FormContext.from_dict(data["form_context"])
            collected_values = context.collected_values
            form_data = data["form_context"]
            logger.debug(f"📋 Using form_context format: {len(collected_values)} values collected")
        else:
            form_data = data.get("start_form", {})
            collected_values = form_data.get("collected_values", {})
            logger.debug(f"📋 Using start_form format: {len(collected_values)} values collected")
        
        logger.debug(f"📦 Collected values: {list(collected_values.keys())} = {list(collected_values.values())}")
        
        # Get pending process data
        pending_process = data.get("pending_process", {})
        process_key = pending_process.get("process_key")
        business_key = pending_process.get("business_key")
        telegram_user_id = pending_process.get("telegram_user_id")
        initial_variables = pending_process.get("initial_variables", {})
        
        if not process_key:
            user_lang = await get_user_language(callback.from_user.id)
            await callback.answer(_('error.process_not_found', user_lang), show_alert=True)
            return
        
        # Note: Intro + dialog messages were already deleted when confirmation was shown
        user_lang = await get_user_language(callback.from_user.id)
        await callback.answer(_('process.starting', user_lang))
        
        # Start the process with collected variables
        from luka_bot.services.camunda_service import get_camunda_service
        camunda_service = get_camunda_service()
        
        # Format variables for Camunda - start with initial variables
        variables = dict(initial_variables)  # Copy initial variables (e.g., group_index)
        
        # Merge in collected form variables (form variables take precedence)
        for var_name, value in collected_values.items():
            variables[var_name] = value
        
        logger.debug(f"🚀 Starting process with {len(variables)} variables: {list(variables.keys())}")
        
        process_instance = await camunda_service.start_process(
            telegram_user_id=telegram_user_id,
            process_key=process_key,
            business_key=business_key,
            variables=variables
        )
        
        # Update state
        await state.set_state(ProcessStates.process_active)
        await state.update_data({
            "active_process": process_instance.id,
            "process_key": process_key,
            "start_form": None,  # Clear form data
            "pending_process": None  # Clear pending process
        })
        
        # Edit confirmation message to add process started status
        # Keep the original message content and append the process ID
        current_text = callback.message.html_text or callback.message.text or ""
        updated_text = (
            f"{current_text}\n\n"
            f"─────────────────────────────\n"
            f"✅ <b>Процесс запущен!</b>\n"
            f"ID: <code>{process_instance.id}</code>"
        )
        
        try:
            await callback.message.edit_text(
                updated_text,
                parse_mode="HTML",
                reply_markup=None  # Remove buttons
            )
            logger.debug("✅ Updated confirmation message with process ID")
        except Exception as e:
            logger.warning(f"Could not edit confirmation message: {e}")
            # Fallback: send new message if edit fails
            await callback.message.answer(
                f"✅ Процесс запущен!\nID: <code>{process_instance.id}</code>",
                parse_mode="HTML"
            )
        
        logger.info(f"✅ Started process {process_instance.id} for user {telegram_user_id}")
        
        # Check if WebSocket is connected - if so, rely on WebSocket events instead of polling
        from luka_bot.core.config import settings
        if settings.WAREHOUSE_ENABLED:
            try:
                from luka_bot.services.task_websocket_manager import get_websocket_manager
                ws_manager = get_websocket_manager()
                ws_conn = ws_manager._connections.get(telegram_user_id)
                
                if ws_conn and ws_conn.is_connected:
                    logger.info(f"🔌 WebSocket active for user {telegram_user_id}, task will be delivered via WebSocket")
                    # WebSocket will handle task notification, no polling needed
                    return
            except Exception as e:
                logger.warning(f"⚠️  Error checking WebSocket status: {e}")
        
        # Fallback to polling if WebSocket is not available
        logger.info(f"🔄 WebSocket not available, using polling fallback for user {telegram_user_id}")
        from luka_bot.handlers.processes.start_process import poll_and_render_next_task
        await poll_and_render_next_task(
            callback.message, telegram_user_id, process_instance.id, state
        )
        
    except Exception as e:
        logger.error(f"❌ Error confirming start form: {e}")
        user_lang = await get_user_language(callback.from_user.id)
        await callback.answer(_('error.process_launch', user_lang), show_alert=True)


@router.callback_query(F.data == "start_form_cancel")
async def handle_start_form_cancel(callback: CallbackQuery, state: FSMContext):
    """
    Handle X button on confirmation - delete intro message.
    
    Note: The intro message IS the confirmation message (we edited it to add collected values).
          Dialog messages are already deleted.
    """
    try:
        # Delete intro/confirmation message (they're the same now)
        # Dialog messages were already deleted when showing confirmation
        try:
            await callback.message.delete()
            logger.debug(f"🗑️ Deleted intro/confirmation message")
        except Exception as e:
            logger.warning(f"Could not delete intro/confirmation message: {e}")
        
        # Clear all form-related state
        await state.update_data({
            "start_form": None,
            "pending_process": None,
            "form_context": None
        })
        await state.clear()
        
        user_lang = await get_user_language(callback.from_user.id)
        await callback.answer(_('common.cancel', user_lang))
        logger.info(f"User {callback.from_user.id} cancelled start form")
        
    except Exception as e:
        logger.error(f"❌ Error cancelling start form: {e}")
        await callback.answer("❌", show_alert=True)

