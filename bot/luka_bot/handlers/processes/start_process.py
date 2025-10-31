"""
Process start handler for initiating BPMN workflows.
"""
from typing import Optional, Dict, Any

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from luka_bot.services.camunda_service import get_camunda_service
from luka_bot.services.task_service import get_task_service
from luka_bot.services.group_service import get_group_service
from luka_bot.handlers.states import ProcessStates
from luka_bot.utils.i18n_helper import _

router = Router(name="process_start")


async def safe_callback_answer(callback: CallbackQuery, text: str, show_alert: bool = False):
    """
    Safely answer callback query, handling expired queries gracefully.
    
    Args:
        callback: Callback query to answer
        text: Text to show
        show_alert: Whether to show as alert
    """
    try:
        await callback.answer(text, show_alert=show_alert)
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "query ID is invalid" in str(e):
            logger.warning(f"⏰ Callback query expired for user {callback.from_user.id}: {text}")
            # Query expired - send as regular message instead
            try:
                await callback.message.answer(text)
            except Exception as msg_error:
                logger.error(f"Failed to send message after expired callback: {msg_error}")
        else:
            # Re-raise other Telegram errors
            raise


@router.callback_query(F.data == "start_history_import")
async def handle_start_history_import(callback: CallbackQuery, state: FSMContext):
    """
    Start history import BPMN process.
    Triggered from group admin menu.
    Checks for existing running process first, then checks for start form.
    """
    user_id = callback.from_user.id
    
    # Extract group_id from state
    data = await state.get_data()
    group_id = data.get("current_group_id")
    
    if not group_id:
        await safe_callback_answer(callback, "⚠️ No group selected", show_alert=True)
        return
    
    # Get group name for business key
    from luka_bot.services.thread_service import get_thread_service
    thread_service = get_thread_service()
    thread = await thread_service.get_group_thread(group_id)
    group_name = thread.name if thread else f"Group {group_id}"
    
    # Initialize Camunda service
    camunda_service = get_camunda_service()
    process_key = "chatbot_group_import_history"
    business_key = f"import_{group_id}_{user_id}"
    
    # Check for existing running process with this business key
    existing_process = await camunda_service.get_process_instance_by_business_key(
        telegram_user_id=user_id,
        business_key=business_key,
        active_only=True
    )
    
    if existing_process:
        # Resume existing process - poll for its tasks
        logger.info(
            f"🔄 Resuming existing process {existing_process.id} "
            f"for group {group_id}, user {user_id}"
        )
        
        await safe_callback_answer(
            callback,
            "🔄 Resuming existing import process..."
        )
        
        # Update state with process info
        await state.set_state(ProcessStates.process_active)
        await state.update_data({
            "active_process": str(existing_process.id),
            "process_key": process_key,
            "group_id": group_id
        })
        
        # Poll for tasks
        await poll_and_render_next_task(
            callback.message, user_id, str(existing_process.id), state
        )
        return
    
    try:
        # Get start form variables - returns (variables, error)
        start_form_vars, error = await camunda_service.get_start_form_variables(user_id, process_key)
        
        # If there was an error fetching start form, don't proceed
        if error:
            logger.error(f"Cannot start process {process_key}: Start form API error")
            await safe_callback_answer(
                callback,
                "❌ Process configuration error\n\n"
                "The process start form could not be loaded from Camunda. "
                "Please check the process definition or contact support.",
                show_alert=True
            )
            return
        
        # Prepare initial variables for process (injected before/with start form)
        initial_variables = {
            "group_index": str(group_id)  # For KB indexing (handles group migrations)
        }
        
        if start_form_vars:
            # Has start form - render it and collect variables
            # Format variables for dialog (convert to dict list)
            form_vars = [var.model_dump() if hasattr(var, 'model_dump') else var for var in start_form_vars]
            
            logger.debug(f"📋 Start form loaded: {len(form_vars)} variables for {process_key}")
            
            # Get process definition details (name, description)
            process_def = await camunda_service.get_process_definition(user_id, process_key)
            logger.debug(f"📋 Starting process: {process_def.get('name')}")
            
            # Store process context with initial variables
            # The start form will collect additional variables from the user
            await state.update_data({
                "pending_process": {
                    "process_key": process_key,
                    "business_key": business_key,
                    "initial_variables": initial_variables,  # Will be merged with form vars
                    "telegram_user_id": user_id
                }
            })
            
            # Render start form using enhanced start form renderer
            from luka_bot.services.dialog_service import get_dialog_service
            dialog_service = get_dialog_service()
            
            await dialog_service.render_start_form(
                process_definition=process_def,
                variables=form_vars,
                message=callback.message,
                user_id=user_id,
                state=state
            )
            
            await safe_callback_answer(callback, "📝 Пожалуйста, ознакомьтесь с формой ниже" if group_name else "📝 Please review the form below")
        else:
            # No start form - start process immediately with initial variables
            await _start_process_immediately(
                callback=callback,
                state=state,
                user_id=user_id,
                process_key=process_key,
                business_key=business_key,
                camunda_service=camunda_service,
                initial_variables=initial_variables
            )
    
    except ValueError as e:
        # Catch credential errors
        error_msg = str(e)
        if "no Camunda credentials" in error_msg:
            logger.error(f"User {user_id} missing Camunda credentials")
            await safe_callback_answer(
                callback,
                "❌ Camunda credentials not configured\n\n"
                "Your account needs to be linked with Camunda first. "
                "Please contact support or login via the flow API.",
                show_alert=True
            )
        else:
            logger.error(f"Failed to start process: {e}")
            await safe_callback_answer(callback, "❌ Failed to start process", show_alert=True)
    except Exception as e:
        logger.error(f"Failed to check/start process: {e}")
        await safe_callback_answer(callback, "❌ Failed to start process", show_alert=True)


async def _start_process_immediately(
    callback: CallbackQuery,
    state: FSMContext,
    user_id: int,
    process_key: str,
    business_key: str,
    camunda_service,
    initial_variables: dict = None
):
    """
    Start process without start form - WebSocket will notify when task is ready.
    
    Args:
        callback: Callback query from button press
        state: FSM context for state management
        user_id: Telegram user ID
        process_key: Camunda process definition key
        business_key: Business key for process identification
        camunda_service: Camunda service instance
        initial_variables: Optional dict of initial process variables to inject
    """
    try:
        # Start process with initial variables (if any)
        process_instance = await camunda_service.start_process(
            telegram_user_id=user_id,
            process_key=process_key,
            business_key=business_key,
            variables=initial_variables or {}
        )
        
        # Set FSM state
        await state.set_state(ProcessStates.process_active)
        await state.update_data({
            "active_process": process_instance.id,
            "process_key": process_key,
        })
        
        # Check if WebSocket is connected
        from luka_bot.services.task_websocket_manager import get_websocket_manager
        from luka_bot.core.config import settings
        
        ws_manager = get_websocket_manager()
        ws_conn = ws_manager.get_connection(user_id) if settings.WAREHOUSE_ENABLED else None
        
        if ws_conn and ws_conn.is_connected:
            # WebSocket mode - user will be notified automatically when task is created
            await safe_callback_answer(callback, "✅ Starting process...")
            await callback.message.answer(
                "⏳ Processing your request...\n"
                "You'll be notified when the task is ready."
            )
            logger.info(f"🔌 Process {process_instance.id} started with WebSocket notification for user {user_id}")
        else:
            # Fallback to polling (WebSocket not available)
            logger.warning(f"⚠️  WebSocket not available for user {user_id}, falling back to polling")
            await safe_callback_answer(callback, "✅ Starting process...")
            await poll_and_render_next_task(callback.message, user_id, process_instance.id, state)
    
    except Exception as e:
        logger.error(f"Failed to start process: {e}")
        raise


async def poll_and_render_next_task(
    message: Message,
    user_id: int,
    process_id: str,
    state: FSMContext
):
    """
    Poll for next task in process and render it.
    
    USAGE: Only as fallback when WebSocket is not available,
    or when user manually refreshes (clicks process button again).
    
    Args:
        message: Message to respond to
        user_id: Telegram user ID
        process_id: Camunda process instance ID
        state: FSM context
    """
    logger.info(f"🔄 Polling for tasks (fallback mode) - process {process_id}, user {user_id}")
    camunda_service = get_camunda_service()
    task_service = get_task_service()
    
    try:
        # Get user's tasks
        tasks = await camunda_service.get_user_tasks(user_id)
        
        # Filter by process (convert UUID to string for comparison)
        process_tasks = [t for t in tasks if str(t.process_instance_id) == str(process_id)]
        
        if not process_tasks:
            # No tasks yet - either processing or complete
            logger.info(
                f"No tasks found for process {process_id}, might be complete or waiting. "
                f"Total user tasks: {len(tasks)}"
            )
            
            # Show waiting message
            await message.answer("⏳ Processing your request...")
            return
        
        # Render first task
        task = process_tasks[0]
        logger.info(f"✅ Found task {task.id} ({task.name}) for process {process_id}")
        
        # Convert UUID to string for JSON serialization
        await state.update_data({"current_task_id": str(task.id)})
        await task_service.render_task(str(task.id), message, user_id, state)
    
    except Exception as e:
        logger.error(f"Failed to poll/render task for process {process_id}: {e}")
        await message.answer(f"❌ Error rendering task: {str(e)}")

