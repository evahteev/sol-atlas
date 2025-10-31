"""
Task rendering and management service.
Handles task variable categorization, keyboard building, and dialog management.
"""
from typing import List, Dict, Any, Optional
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.services.camunda_service import get_camunda_service
from luka_bot.services.message_cleanup_service import get_message_cleanup_service
from luka_bot.models.process_models import TaskVariables
from luka_bot.keyboards.inline.task_keyboards import build_action_keyboard, build_file_upload_keyboard
from luka_bot.handlers.states import ProcessStates
from luka_bot.utils.i18n_helper import _


class TaskService:
    """Task rendering and management"""
    
    _instance: Optional['TaskService'] = None
    
    def __init__(self):
        self.camunda_service = get_camunda_service()
        self.cleanup_service = get_message_cleanup_service()
    
    @classmethod
    def get_instance(cls) -> 'TaskService':
        """Get singleton"""
        if cls._instance is None:
            cls._instance = cls()
            logger.info("✅ TaskService singleton created")
        return cls._instance
    
    async def render_task(
        self,
        task_id: str,
        message: Message,
        user_id: int,
        state: FSMContext
    ) -> bool:
        """
        Main task rendering entry point.
        Now uses UnifiedFormService for consistent UI/UX with start forms.
        """
        try:
            # Get task details
            task = await self.camunda_service.get_task(user_id, task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                await message.answer(_("task.error.not_found"))
                return False
            
            # Get and categorize variables
            raw_variables = await self.camunda_service.get_task_variables(user_id, task_id)
            variables = self._categorize_variables(raw_variables)
            
            logger.info(
                f"📋 Task {task_id} ({task.name}): "
                f"{len(variables.text_vars)} text, "
                f"{len(variables.action_vars)} action, "
                f"{len(variables.form_vars)} form, "
                f"{len(variables.s3_vars)} s3 vars"
            )
            
            # Check if task has no form and no action buttons - complete immediately
            if (len(variables.text_vars) == 0 and 
                len(variables.action_vars) == 0 and 
                len(variables.form_vars) == 0 and 
                len(variables.s3_vars) == 0):
                # Task with no variables at all - complete immediately
                logger.info(f"✅ Task {task_id} has no form - completing immediately")
                try:
                    await self.camunda_service.complete_task(user_id, task_id)
                    await message.answer(
                        f"<b>✅ {task.name}</b>",
                        parse_mode="HTML"
                    )
                    logger.info(f"✅ Auto-completed task {task_id} (no form)")
                    
                    # Poll for next task if there's an active process
                    from luka_bot.handlers.processes.start_process import poll_and_render_next_task
                    data = await state.get_data()
                    process_id = data.get("active_process")
                    if process_id:
                        await poll_and_render_next_task(
                            message, user_id, process_id, state
                        )
                    
                    return True
                except Exception as e:
                    logger.error(f"❌ Failed to complete task {task_id}: {e}")
                    await message.answer("❌ Ошибка завершения задачи")
                    return False
            
            # Get process definition name for the process instance
            process_definition_name = None
            try:
                client = await self.camunda_service._get_client(user_id)
                process_instance = await client.get_process_instance(
                    str(task.process_instance_id)
                )
                if process_instance:
                    process_definition_name = process_instance.process_definition_name
            except Exception as e:
                logger.debug(f"Could not fetch process definition name: {e}")
            
            # Build FormData for unified rendering
            from luka_bot.models.form_models import FormData, FormType
            
            form_data = FormData(
                id=task_id,
                name=task.name,
                description=task.description or "",
                form_type=FormType.TASK,
                task_id=task_id,
                process_instance_id=str(task.process_instance_id),
                process_definition_name=process_definition_name,
                text_vars=variables.text_vars,
                form_vars=variables.form_vars,
                s3_vars=variables.s3_vars,
                action_vars=variables.action_vars,
                telegram_user_id=user_id
            )
            
            # Delegate to unified form service
            from luka_bot.services.unified_form_service import get_unified_form_service
            unified_service = get_unified_form_service()
            
            return await unified_service.render_form(
                form_data=form_data,
                message=message,
                user_id=user_id,
                state=state
            )
        
        except Exception as e:
            logger.error(f"❌ Failed to render task {task_id}: {e}")
            return False
    
    def _categorize_variables(self, raw_variables: List) -> TaskVariables:
        """
        Categorize variables into text, action, form, and S3 types.
        
        Priority (by prefix first, then by writable flag):
        1. text_* → Text display (regardless of writable)
        2. s3_* + writable → S3 upload
        3. action_* + writable → Action button
        4. writable → Form input
        5. not writable → Text display
        """
        text_vars = []
        action_vars = []
        form_vars = []
        s3_vars = []
        
        for var in raw_variables:
            var_dict = var.model_dump() if hasattr(var, 'model_dump') else var
            var_name = var_dict.get("name", "")
            var_writable = var_dict.get("writable", False)
            
            # Text variables (HIGHEST PRIORITY - check prefix first)
            if var_name.startswith("text_"):
                text_vars.append(var_dict)
            # S3 file upload variables
            elif var_name.startswith("s3_") and var_writable:
                s3_vars.append(var_dict)
            # Action variables
            elif var_name.startswith("action_") and var_writable:
                action_vars.append(var_dict)
            # Form variables (writable, not action or s3)
            elif var_writable:
                form_vars.append(var_dict)
            # Other read-only variables → text
            else:
                text_vars.append(var_dict)
        
        return TaskVariables(
            text_vars=text_vars,
            action_vars=action_vars,
            form_vars=form_vars,
            s3_vars=s3_vars
        )
    
    async def _render_action_task(
        self,
        task,
        variables: TaskVariables,
        message: Message,
        user_id: int,
        state: FSMContext
    ) -> bool:
        """Render task with action buttons"""
        try:
            # Build message text
            text = self._build_task_text(task, variables.text_vars)
            
            # Build keyboard (convert UUID to string)
            keyboard = build_action_keyboard(str(task.id), variables.action_vars)
            
            # Send message
            sent_message = await message.answer(text, reply_markup=keyboard)
            
            # Track for cleanup (convert UUID to string)
            await self.cleanup_service.track_task_message(
                task_id=str(task.id),
                message=sent_message,
                state=state,
                message_type="action_buttons"
            )
            
            logger.info(f"✅ Rendered action task {task.id} with {len(variables.action_vars)} actions")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to render action task: {e}")
            return False
    
    async def _render_form_task(
        self,
        task,
        variables: TaskVariables,
        message: Message,
        user_id: int,
        state: FSMContext
    ) -> bool:
        """Render task with dialog form"""
        try:
            # Import here to avoid circular dependency
            from luka_bot.services.dialog_service import get_dialog_service
            dialog_service = get_dialog_service()
            
            # Start dialog (convert UUID to string)
            return await dialog_service.start_task_dialog(
                task_id=str(task.id),
                variables=variables.form_vars,
                message=message,
                user_id=user_id,
                state=state
            )
        
        except Exception as e:
            logger.error(f"❌ Failed to render form task: {e}")
            return False
    
    async def _render_s3_upload_task(
        self,
        task,
        variables: TaskVariables,
        message: Message,
        user_id: int,
        state: FSMContext
    ) -> bool:
        """Render task with S3 file upload"""
        try:
            # Get first S3 variable
            s3_var = variables.s3_vars[0]
            var_name = s3_var.get("name")
            var_label = s3_var.get("label", var_name.replace("s3_", "").title())
            
            # Determine expected file extension from variable metadata or name
            expected_ext = s3_var.get("extension", ".json")  # Default to JSON
            
            # Build message text
            text = self._build_task_text(task, variables.text_vars)
            text += f"\n\n📎 <b>Please upload file:</b> {var_label}\n"
            text += f"Expected format: <code>{expected_ext}</code>\n\n"
            text += "Use the 📎 attachment button to upload your file."
            
            # Build keyboard (convert UUID to string)
            keyboard = build_file_upload_keyboard(str(task.id))
            
            # Send message
            sent_message = await message.answer(text, reply_markup=keyboard)
            
            # Track for cleanup (convert UUID to string)
            await self.cleanup_service.track_task_message(
                task_id=str(task.id),
                message=sent_message,
                state=state,
                message_type="file_upload_prompt"
            )
            
            # Set state for file upload
            await state.set_state(ProcessStates.file_upload_pending)
            await state.update_data({
                "current_s3_variable": var_name,
                "expected_file_extension": expected_ext
            })
            
            logger.info(f"✅ Rendered S3 upload task {task.id} for variable {var_name}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to render S3 upload task: {e}")
            return False
    
    async def _render_simple_task(
        self,
        task,
        message: Message,
        user_id: int,
        state: FSMContext
    ) -> bool:
        """Render task with no variables (auto-complete)"""
        try:
            # Auto-complete immediately (convert UUID to string)
            await self.camunda_service.complete_task(user_id, str(task.id))
            await message.answer(
                _("task.completed", name=task.name)
            )
            logger.info(f"✅ Auto-completed simple task {task.id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to auto-complete simple task: {e}")
            return False
    
    def _build_task_text(self, task, text_vars: List[Dict]) -> str:
        """Build task description text"""
        text = f"<b>📋 {task.name}</b>\n\n"
        
        if task.description:
            text += f"{task.description}\n\n"
        
        # Add text variables
        if text_vars:
            for var in text_vars:
                label = var.get("label", var.get("name"))
                value = var.get("value", "")
                text += f"• <b>{label}:</b> {value}\n"
            text += "\n"
        
        return text
    
    async def complete_task_with_action(
        self,
        task_id: str,
        action_name: str,
        user_id: int,
        state: FSMContext
    ) -> bool:
        """Complete task with action variable"""
        try:
            # Complete task
            variables = {action_name: True}
            await self.camunda_service.complete_task(user_id, task_id, variables)
            
            logger.info(f"✅ Completed task {task_id} with action {action_name}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to complete task {task_id}: {e}")
            return False
    
    # WebSocket Event Handlers
    
    async def handle_task_created_event(self, event: Dict[str, Any], user_id: int):
        """
        Handle task_created event from WebSocket.
        Render task immediately to user.
        
        Args:
            event: Task event data from WebSocket
            user_id: Telegram user ID (from WebSocket connection)
        """
        task_id = event.get('taskId')
        task_name = event.get('taskName', 'Unknown Task')
        process_id = event.get('processInstanceId')
        
        logger.info(f"📬 Handling task_created for user {user_id}: {task_name} ({task_id})")
        
        # Get user's FSM state
        from luka_bot.core.loader import bot, dp
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.storage.base import StorageKey
        
        storage_key = StorageKey(
            bot_id=bot.id,
            chat_id=user_id,
            user_id=user_id
        )
        
        state = FSMContext(storage=dp.storage, key=storage_key)
        
        # Get user info from session cache
        from luka_bot.services.user_session_cache import get_user_session_cache
        cache = get_user_session_cache()
        session = await cache.get_session(user_id)
        
        if not session:
            logger.warning(f"⚠️  No session cached for user {user_id}, cannot render task")
            return
        
        user_info = session.get("user_info", {})
        
        if not user_info.get("camunda_user_id"):
            logger.warning(f"⚠️  No Camunda credentials for user {user_id}")
            return
        
        try:
            # Render the task directly (no notification message needed)
            # Create a placeholder message for rendering
            placeholder_msg = await bot.send_message(
                chat_id=user_id,
                text="⏳"
            )
            
            await self.render_task(
                task_id=task_id,
                message=placeholder_msg,
                user_id=user_id,
                state=state
            )
            
            logger.info(f"✅ Task {task_id} rendered successfully for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error rendering task {task_id} for user {user_id}: {e}")
    
    async def handle_task_completed_event(self, event: Dict[str, Any], user_id: int):
        """
        Handle task_completed event from WebSocket.
        Clean up task UI if needed.
        
        Args:
            event: Task event data from WebSocket
            user_id: Telegram user ID (from WebSocket connection)
        """
        task_id = event.get('taskId')
        
        logger.info(f"✅ Task completed (WebSocket): {task_id} for user {user_id}")
        
        # Task completion cleanup is already handled by the completion logic
        # This event is mainly for informational purposes
    
    async def handle_task_updated_event(self, event: Dict[str, Any], user_id: int):
        """
        Handle task_updated event from WebSocket.
        
        Args:
            event: Task event data from WebSocket
            user_id: Telegram user ID (from WebSocket connection)
        """
        task_id = event.get('taskId')
        
        logger.debug(f"🔄 Task updated (WebSocket): {task_id} for user {user_id}")
        
        # Future: Could refresh task display if needed
    
    async def handle_task_deleted_event(self, event: Dict[str, Any], user_id: int):
        """
        Handle task_deleted event from WebSocket.
        
        Args:
            event: Task event data from WebSocket
            user_id: Telegram user ID (from WebSocket connection)
        """
        task_id = event.get('taskId')
        
        logger.info(f"🗑️  Task deleted (WebSocket): {task_id} for user {user_id}")
        
        # Future: Could clean up UI if needed


def get_task_service() -> TaskService:
    """Get TaskService singleton"""
    return TaskService.get_instance()

