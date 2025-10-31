"""
Dialog management service.
Handles task dialog interactions, variable collection, and state management.
"""
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from aiogram.types import Message, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.services.camunda_service import get_camunda_service
from luka_bot.services.message_cleanup_service import get_message_cleanup_service
from luka_bot.handlers.states import ProcessStates
from luka_bot.utils.i18n_helper import _, get_user_language


class DialogService:
    """Centralized dialog management for task completion."""
    
    _instance: Optional['DialogService'] = None
    
    def __init__(self):
        self.camunda_service = get_camunda_service()
        self.cleanup_service = get_message_cleanup_service()
    
    @classmethod
    def get_instance(cls) -> 'DialogService':
        """Get singleton"""
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("✅ DialogService singleton created")
        return cls._instance
    
    async def render_start_form(
        self,
        process_definition: Dict[str, Any],
        variables: List[Dict[str, Any]],
        message: Message,
        user_id: int,
        state: FSMContext
    ) -> bool:
        """
        Render a Camunda start form in a user-friendly way.
        Now uses UnifiedFormService for consistent UI/UX with tasks.
        
        Separates variables by prefix:
        - text_*: Informational text (display only)
        - form_*: Form fields to collect (one by one dialog)
        - s3_*: File upload requests
        
        Args:
            process_definition: Process definition with name, description, etc.
            variables: List of form variables from Camunda
            message: Message to respond to
            user_id: Telegram user ID
            state: FSM context
            
        Returns:
            bool: True if rendered successfully
        """
        try:
            # Get pending process data
            data = await state.get_data()
            pending_process = data.get("pending_process", {})
            
            # Categorize variables by prefix
            text_vars = []
            form_vars = []
            s3_vars = []
            
            for var in variables:
                var_name = var.get("name", "")
                if var_name.startswith("text_"):
                    text_vars.append(var)
                elif var_name.startswith("form_"):
                    form_vars.append(var)
                elif var_name.startswith("s3_"):
                    s3_vars.append(var)
                else:
                    # Unknown prefix - treat as form variable
                    form_vars.append(var)
            
            logger.debug(
                f"📋 Start form: {len(text_vars)} text, {len(form_vars)} form, {len(s3_vars)} s3"
            )
            
            # Build FormData for unified rendering
            from luka_bot.models.form_models import FormData, FormType
            
            form_data = FormData(
                id=process_definition.get("key", "unknown"),
                name=process_definition.get("name", "Process Form"),
                description=process_definition.get("description", ""),
                form_type=FormType.START_FORM,
                process_key=process_definition.get("key"),
                business_key=pending_process.get("business_key"),
                text_vars=text_vars,
                form_vars=form_vars,
                s3_vars=s3_vars,
                action_vars=[],  # Start forms don't have action buttons
                group_id=pending_process.get("group_id"),
                telegram_user_id=user_id
            )
            
            # Also store in old format for backward compatibility with existing handlers
            # This will be removed once all handlers are migrated
            await state.update_data({
                "start_form": {
                    "process_key": process_definition.get("key"),
                    "process_definition": process_definition,
                    "text_vars": text_vars,
                    "editable_vars": form_vars + s3_vars,
                    "total_editable": len(form_vars) + len(s3_vars),
                    "current_index": 0,
                    "collected_values": {},
                    "user_id": user_id
                },
                "pending_process": pending_process
            })
            
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
            logger.error(f"❌ Error rendering start form: {e}")
            await message.answer("❌ Error displaying form")
            return False
    
    def _build_start_form_message(
        self,
        process_definition: Dict[str, Any],
        text_vars: List[Dict],
        form_vars: List[Dict],
        s3_vars: List[Dict]
    ) -> str:
        """
        Build the start form intro message.
        
        Format:
        <b>✨ {Emoji} {Process Name}</b>
        
        {Process Description}
        
        {text_ variables content with labels}
        """
        import json
        
        # Use process definition name as title
        raw_name = process_definition.get("name", "Process Form")
                
        # Build title with emoji
        title = f"✨ {raw_name}"
        
        # Parse description
        raw_description = process_definition.get("description", "")
        description = ""
        
        if raw_description:
            # Check if description is a JSON object
            if isinstance(raw_description, str) and (raw_description.startswith('{') or raw_description.startswith('[')):
                try:
                    # Try to parse as JSON
                    desc_obj = json.loads(raw_description)
                    if isinstance(desc_obj, dict):
                        # Extract description field from object
                        description = desc_obj.get("description", "")
                    else:
                        # If it's not a dict, use as-is
                        description = raw_description
                except json.JSONDecodeError:
                    # Not valid JSON, use as string
                    description = raw_description
            else:
                # Simple string, use as-is
                description = raw_description
        
        # Build message
        parts = [f"<b>{title}</b>"]
        
        if description:
            parts.append(description)
        
        # Add text variables content (using their LABELS, not names)
        for var in text_vars:
            var_name = var.get("name", "")
            # Get label from variable, fallback to formatted name
            label = var.get("label", var_name.replace("text_", "").replace("_", " ").title())
            
            # Extract the actual value (now properly converted by CamundaService)
            var_value = var.get("value", "")
            content = str(var_value) if var_value else ""
            
            # Format content for better display (fix numbered lists, etc.)
            content = self._format_text_content(content)
            
            if content:
                parts.append(f"\n<b>{label}:</b>\n{content}")
        
        # Add info about what will be collected
        total_editable = len(form_vars) + len(s3_vars)
        if total_editable > 0:
            parts.append("\n" + "─" * 30)
            
            # Count form and s3 separately
            form_count = len(form_vars)
            s3_count = len(s3_vars)
            
            collect_parts = []
            if form_count > 0:
                field_text = _("forms.field_count", count=form_count)
                collect_parts.append(f"📝 {form_count} {field_text}")
            if s3_count > 0:
                file_text = _("forms.file_count", count=s3_count)
                collect_parts.append(f"📎 {s3_count} {file_text}")
            
            if collect_parts:
                parts.append("\n".join(collect_parts))
                total_field_text = _("forms.field_count", count=total_editable)
                parts.append(f"\n<i>{_('forms.total')}: {total_editable} {total_field_text}</i>")
        
        return "\n\n".join(parts)
    
    async def _ask_next_editable_variable(
        self,
        message: Message,
        state: FSMContext
    ) -> None:
        """
        Ask for the next editable variable (form_ or s3_).
        Shows progress: Variable Label (X/Total)
        
        Supports both new (form_context) and old (start_form) state formats.
        """
        data = await state.get_data()
        
        # Check for new format first (form_context)
        if "form_context" in data:
            from luka_bot.models.form_models import FormContext
            context = FormContext.from_dict(data["form_context"])
            form_data_obj = context.form_data
            
            editable_vars = form_data_obj.editable_vars
            total_editable = form_data_obj.total_editable
            current_index = context.current_index
            
            # Use form_context for tracking
            state_key = "form_context"
            form_data = data[state_key]
        else:
            # Fall back to old format (start_form)
            form_data = data.get("start_form", {})
            
            editable_vars = form_data.get("editable_vars", [])
            total_editable = form_data.get("total_editable", 0)
            current_index = form_data.get("current_index", 0)
            
            # Use start_form for tracking
            state_key = "start_form"
        
        # Check if we've collected all variables
        if current_index >= len(editable_vars):
            # All done - complete based on form type
            if state_key == "form_context":
                # Unified form - check if it's a task or start form
                from luka_bot.models.form_models import FormContext, FormType
                context = FormContext.from_dict(form_data)
                
                if context.form_data.form_type == FormType.TASK:
                    # Task - complete with cleanup and confirmation
                    from luka_bot.services.camunda_service import get_camunda_service
                    camunda_service = get_camunda_service()
                    
                    # Re-read state to get latest collected values
                    current_data = await state.get_data()
                    current_form_data = current_data.get("form_context", {})
                    final_collected_values = current_form_data.get("collected_values", {})
                    
                    logger.info(
                        f"📋 Completing task {context.form_data.task_id} with variables: "
                        f"{list(final_collected_values.keys())} = {list(final_collected_values.values())}"
                    )
                    
                    # 🧹 CLEANUP: Delete intro + dialog messages, show clean confirmation
                    await self._complete_task_with_confirmation(
                        message=message,
                        state=state,
                        task_name=context.form_data.name,
                        task_id=context.form_data.task_id,
                        collected_values=final_collected_values,
                        form_data=current_form_data,
                        telegram_user_id=context.form_data.telegram_user_id
                    )
                    
                    # Complete task in Camunda
                    await camunda_service.complete_task(
                        telegram_user_id=context.form_data.telegram_user_id,
                        task_id=context.form_data.task_id,
                        variables=final_collected_values
                    )
                    
                    logger.info(f"✅ Completed task {context.form_data.task_id} with {len(final_collected_values)} variables")
                    
                    # Poll for next task
                    from luka_bot.handlers.processes.start_process import poll_and_render_next_task
                    process_id = (await state.get_data()).get("active_process")
                    if process_id:
                        await poll_and_render_next_task(
                            message, context.form_data.telegram_user_id, process_id, state
                        )
                    return
                else:
                    # Start form - show confirmation
                    # Retrieve intro message text from stored context
                    intro_message_text = form_data.get("intro_message_text", "")
                    await self._show_start_form_confirmation(
                        message, state,
                        intro_message_text,
                        context.collected_values
                    )
                    return
            else:
                # Legacy start_form format - show confirmation
                intro_message_text = form_data.get("intro_message", "")
                await self._show_start_form_confirmation(
                    message, state,
                    intro_message_text,
                    form_data.get("collected_values", {})
                )
                return
        
        # Get current variable
        current_var = editable_vars[current_index]
        var_name = current_var.get("name", "")
        
        # Get label from variable (use actual label, not derived from name)
        label = current_var.get("label", var_name.replace("form_", "").replace("s3_", "").replace("_", " ").title())
        
        # Build progress indicator
        progress = f"({current_index + 1}/{total_editable})"
        
        # Check if it's an s3 (file upload) variable
        is_file_upload = var_name.startswith("s3_")
        
        if is_file_upload:
            # File upload prompt
            prompt = f"📎 <b>{label}</b> {progress}\n\n<i>{_('forms.upload_file_prompt')}</i>"
            
            prompt_msg = await message.answer(
                prompt,
                parse_mode="HTML"
            )
            
            # Track this prompt message for later deletion
            data = await state.get_data()
            form_data = data.get(state_key, {})
            if "dialog_message_ids" not in form_data:
                form_data["dialog_message_ids"] = []
            form_data["dialog_message_ids"].append(prompt_msg.message_id)
            await state.update_data({state_key: form_data})
            
            # Change state to file upload pending
            await state.set_state(ProcessStates.file_upload_pending)
        else:
            # Form variable prompt
            # Check for default value (now properly converted by CamundaService)
            default_val = current_var.get("value", "")
            
            if default_val:
                prompt = (
                    f"📝 <b>{label}</b> {progress}\n\n"
                    f"{_('forms.default_value')}: <code>{default_val}</code>\n\n"
                    f"<i>{_('forms.enter_new_value_prompt')}</i>"
                )
            else:
                prompt = f"📝 <b>{label}</b> {progress}\n\n<i>{_('forms.enter_value_prompt')}</i>"
            
            prompt_msg = await message.answer(
                prompt,
                parse_mode="HTML",
                reply_markup=ForceReply(force_reply=True, selective=True)
            )
            
            # Track this prompt message for later deletion
            data = await state.get_data()
            form_data = data.get(state_key, {})
            if "dialog_message_ids" not in form_data:
                form_data["dialog_message_ids"] = []
            form_data["dialog_message_ids"].append(prompt_msg.message_id)
            await state.update_data({state_key: form_data})
            
            # Ensure state is set to waiting_for_input so handler can catch the response
            await state.set_state(ProcessStates.waiting_for_input)
    
    def _format_text_content(self, content: str) -> str:
        """
        Format text content for better display:
        - Fix numbered lists to have proper line breaks
        - Preserve HTML tags
        """
        if not content:
            return content
        
        # Fix numbered lists: "1. Item 2. Item" -> "1. Item\n2. Item"
        import re
        # Match patterns like " 2. " or " 3. " etc (space before number, dot after)
        content = re.sub(r'\s+(\d+)\.\s+', r'\n\1. ', content)
        
        # Clean up leading/trailing whitespace and multiple newlines
        content = content.strip()
        content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 consecutive newlines
        
        return content
    
    def _get_variable_label(self, var_name: str, editable_vars: List[Dict[str, Any]]) -> str:
        """Get proper label from original variable definition"""
        for var in editable_vars:
            if var.get("name") == var_name:
                return var.get("label", var_name)
        # Fallback to formatted name
        return var_name.replace("form_", "").replace("s3_", "").replace("_", " ").title()
    
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract readable filename from S3 URL or return generic success message"""
        try:
            from urllib.parse import urlparse
            path = urlparse(url).path
            filename = path.split("/")[-1] if path else ""
            # If we got a UUID-style filename, it's not very readable, just say "uploaded"
            if filename and len(filename) > 30:
                return _("forms.uploaded_successfully")
            return filename if filename else _("forms.uploaded_successfully")
        except:
            return _("forms.uploaded_successfully")
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Smart truncation that doesn't break words"""
        if not text or len(text) <= max_length:
            return text
        # Try to break at word boundary
        truncated = text[:max_length-3]
        last_space = truncated.rfind(" ")
        if last_space > max_length * 0.7:  # If space is reasonably close
            return truncated[:last_space] + "..."
        return truncated + "..."
    
    async def _show_start_form_confirmation(
        self,
        message: Message,
        state: FSMContext,
        intro_message_text: str,
        collected_values: Dict[str, Any]
    ) -> None:
        """
        Edit intro message to add collected variables and change button to "Launch".
        This keeps all the helpful context visible while showing what will be submitted.
        
        Progressive cleanup:
        1. Delete all dialog messages (prompts + user inputs)
        2. Edit intro message to add collected variables
        3. Change button from "▶️ Начать" to "🚀 Запустить"
        4. Keep intro message visible (will remove buttons on launch)
        """
        logger.debug(f"📦 Showing confirmation with collected values: {collected_values}")
        
        # Get editable vars for proper labels
        data = await state.get_data()
        
        # Support both form_context (new) and start_form (old) formats
        if "form_context" in data:
            form_data = data.get("form_context", {})
            # Extract form_data from nested structure if needed
            if isinstance(form_data, dict) and "form_data" in form_data:
                editable_vars = form_data["form_data"].get("editable_vars", [])
            else:
                editable_vars = form_data.get("editable_vars", [])
        else:
            form_data = data.get("start_form", {})
            editable_vars = form_data.get("editable_vars", [])
            # For legacy format, get intro_message from form_data if not provided
            if not intro_message_text:
                intro_message_text = form_data.get("intro_message", "")
        
        # 🧹 CLEANUP: Delete all dialog messages (prompts + user inputs)
        dialog_msg_ids = form_data.get("dialog_message_ids", [])
        logger.debug(f"📋 Found {len(dialog_msg_ids)} dialog messages to delete")
        deleted_count = 0
        for msg_id in dialog_msg_ids:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=msg_id
                )
                deleted_count += 1
            except Exception as e:
                logger.debug(f"Could not delete dialog message {msg_id}: {e}")
        
        if deleted_count > 0:
            logger.debug(f"🗑️ Deleted {deleted_count} dialog messages")
        
        # Build collected values section to append to intro message
        values_parts = []
        
        if collected_values:
            values_parts.append("\n\n" + "─" * 30)
            values_parts.append(f"<b>📋 {_('forms.launch_data')}</b>\n")
            
            for var_name, value in collected_values.items():
                # Get proper label from original variable definition
                label = self._get_variable_label(var_name, editable_vars)
                
                # Smart value formatting based on variable type
                if var_name.startswith("s3_"):
                    # For files, show filename
                    filename = self._extract_filename_from_url(str(value))
                    values_parts.append(f"  📎 <b>{label}:</b> {filename}")
                else:
                    # For text, use smart truncation
                    display_value = self._smart_truncate(str(value), 80)
                    values_parts.append(f"  ✏️ <b>{label}:</b> {display_value}")
            
            values_parts.append("\n" + "─" * 30)
        
        collected_section = "\n".join(values_parts)
        
        # Edit intro message to add collected values
        intro_msg_id = form_data.get("intro_message_id")
        if intro_msg_id:
            try:
                # Build updated message with original intro + collected values
                updated_text = intro_message_text + collected_section
                
                # Build keyboard with "Launch" button instead of "Start"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="❌", callback_data="start_form_cancel"),
                        InlineKeyboardButton(text="🚀", callback_data="start_form_confirm")
                    ]
                ])
                
                await message.bot.edit_message_text(
                    text=updated_text,
                    chat_id=message.chat.id,
                    message_id=intro_msg_id,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                
                logger.debug(f"✅ Updated intro message with collected values and Launch button")
                
                # Store intro message ID as confirmation message ID (same message now)
                form_data["confirmation_message_id"] = intro_msg_id
                
            except Exception as e:
                logger.error(f"Could not edit intro message {intro_msg_id}: {e}")
                # Fallback: send new confirmation message
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="❌", callback_data="start_form_cancel"),
                        InlineKeyboardButton(text="🚀", callback_data="start_form_confirm")
                    ]
                ])
                confirmation_msg = await message.answer(
                    collected_section,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                form_data["confirmation_message_id"] = confirmation_msg.message_id
        else:
            logger.warning(f"⚠️ No intro_message_id found (keys: {list(form_data.keys())})")
        
        # Update state in the correct format (form_context or start_form)
        if "form_context" in data:
            await state.update_data({"form_context": form_data})
        else:
            await state.update_data({"start_form": form_data})
        
        # Update state to confirmation
        await state.set_state(ProcessStates.dialog_active)
    
    async def _complete_task_with_confirmation(
        self,
        message: Message,
        state: FSMContext,
        task_name: str,
        task_id: str,
        collected_values: Dict[str, Any],
        form_data: Dict[str, Any],
        telegram_user_id: int
    ) -> None:
        """
        Complete task with cleanup and show confirmation.
        
        Progressive cleanup:
        1. Delete intro message (task description)
        2. Delete all dialog messages (prompts + user inputs)
        3. Show clean confirmation with submitted variables
        """
        logger.debug(f"📦 Task completion with {len(collected_values)} values")
        
        # 🧹 CLEANUP STEP 1: Delete intro message
        intro_msg_id = form_data.get("intro_message_id")
        if intro_msg_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=intro_msg_id
                )
                logger.debug(f"🗑️ Deleted task intro message {intro_msg_id}")
            except Exception as e:
                logger.debug(f"Could not delete task intro message: {e}")
        
        # 🧹 CLEANUP STEP 2: Delete all dialog messages
        dialog_msg_ids = form_data.get("dialog_message_ids", [])
        logger.debug(f"📋 Found {len(dialog_msg_ids)} task dialog messages to delete")
        deleted_count = 0
        for msg_id in dialog_msg_ids:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=msg_id
                )
                deleted_count += 1
            except Exception as e:
                logger.debug(f"Could not delete dialog message {msg_id}: {e}")
        
        if deleted_count > 0:
            logger.debug(f"🗑️ Deleted {deleted_count} task dialog messages")
        
        # 🧹 CLEANUP STEP 3: Delete action buttons message if exists
        menu_message_ids = form_data.get("menu_message_ids", [])
        for msg_id in menu_message_ids:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=msg_id
                )
                logger.debug(f"🗑️ Deleted action buttons message {msg_id}")
            except Exception as e:
                logger.debug(f"Could not delete action buttons message: {e}")
        
        # Get user language for i18n
        language = await get_user_language(telegram_user_id)
        
        # Build clean confirmation - simplified format
        parts = []
        
        # Title with task name
        parts.append(f"<b>✅ {task_name}</b>")
        
        # Show submitted values if any
        if collected_values:
            # Get editable vars for proper labels
            editable_vars = []
            if "form_data" in form_data:
                editable_vars = form_data["form_data"].get("editable_vars", [])
            
            for var_name, value in collected_values.items():
                # Get proper label
                label = self._get_variable_label(var_name, editable_vars)
                
                # Format value
                if var_name.startswith("s3_"):
                    filename = self._extract_filename_from_url(str(value))
                    parts.append(f"📎 <b>{label}:</b> {filename}")
                else:
                    display_value = self._smart_truncate(str(value), 80)
                    parts.append(f"✏️ <b>{label}:</b> {display_value}")
        
        summary = "\n".join(parts)
        
        # Send confirmation (no buttons needed, task is done)
        await message.answer(
            summary,
            parse_mode="HTML"
        )

        # Clear form-related context and transition back to process mode
        await state.update_data({
            "form_context": None,
            "start_form": None,
            "task_dialog": None
        })
        await state.set_state(ProcessStates.process_active)
    
    async def start_task_dialog(
        self, 
        task_id: str, 
        variables: List[Dict[str, Any]], 
        message: Message, 
        user_id: int, 
        state: FSMContext
    ) -> bool:
        """
        Start a dialog-based task completion process.
        
        Args:
            task_id: The task ID to complete
            variables: List of form variables to collect
            message: Message object to respond to
            user_id: Telegram user ID
            state: FSM context for state management
            
        Returns:
            bool: True if dialog started successfully
        """
        try:
            logger.info(f"🗨️  Starting task dialog for task {task_id} with {len(variables)} variables")
            
            # Store task dialog context in state
            await state.update_data({
                "task_dialog": {
                    "task_id": task_id,
                    "variables": variables,
                    "current_index": 0,
                    "collected_values": [],
                    "user_id": user_id
                }
            })
            
            # Set dialog state
            await state.set_state(ProcessStates.waiting_for_input)
            
            # Start with the first variable
            await self._ask_next_variable(message, state)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting task dialog for task {task_id}: {e}")
            await message.answer(_("task.dialog.error"))
            return False
    
    async def handle_dialog_response(
        self, 
        message: Message, 
        state: FSMContext
    ) -> bool:
        """
        Handle user responses during task dialog completion.
        
        Args:
            message: User's response message
            state: FSM context
            
        Returns:
            bool: True if response was handled successfully
        """
        try:
            data = await state.get_data()
            task_dialog = data.get("task_dialog", {})
            
            if not task_dialog:
                logger.warning("Dialog response received but no task_dialog in state")
                await message.answer(_("task.dialog.expired"))
                return False
            
            variables = task_dialog.get("variables", [])
            current_index = task_dialog.get("current_index", 0)
            collected_values = task_dialog.get("collected_values", [])
            
            if current_index >= len(variables):
                logger.info("All variables already collected; completing task")
                return await self._complete_task_with_variables(message, state)
            
            # Process current variable
            current_variable = variables[current_index]
            value, var_type = self._process_user_input(message.text.strip())
            
            # Add collected value
            collected_values.append({
                "name": current_variable["name"],
                "value": value,
                "type": var_type
            })
            
            # Update state
            task_dialog["collected_values"] = collected_values
            task_dialog["current_index"] = current_index + 1
            await state.update_data({"task_dialog": task_dialog})
            
            # Confirm input
            var_label = current_variable.get("label", current_variable["name"])
            await message.answer(f"✅ {var_label}: {message.text.strip()}")
            
            # Continue to next variable or complete
            if current_index + 1 >= len(variables):
                logger.info("All variables collected; completing task")
                return await self._complete_task_with_variables(message, state)
            else:
                await self._ask_next_variable(message, state)
                return True
                
        except Exception as e:
            logger.error(f"❌ Error handling dialog response: {e}")
            await message.answer(_("task.dialog.error"))
            # Clear only the dialog state
            await state.update_data(task_dialog=None)
            return False
    
    async def handle_dialog_input(
        self, 
        message: Message, 
        state: FSMContext
    ) -> bool:
        """
        Handle task dialog input even if user didn't reply to ForceReply.
        This is a fallback for when users don't use the reply mechanism.
        """
        return await self.handle_dialog_response(message, state)
    
    async def _ask_next_variable(
        self, 
        message: Message, 
        state: FSMContext
    ) -> None:
        """Ask the user for the next variable in the task dialog."""
        data = await state.get_data()
        task_dialog = data.get("task_dialog", {})
        variables = task_dialog.get("variables", [])
        current_index = task_dialog.get("current_index", 0)
        
        if current_index >= len(variables):
            await self._complete_task_with_variables(message, state)
            return
        
        current_variable = variables[current_index]
        var_label = current_variable.get("label", current_variable["name"])
        
        # Check for default value
        default_value = current_variable.get("value")
        if default_value not in (None, ""):
            prompt = f"📝 Please provide: <b>{var_label}</b>\n(Default: {default_value})"
        else:
            prompt = f"📝 Please provide: <b>{var_label}</b>"
        
        reply_message = await message.answer(
            prompt,
            reply_markup=ForceReply(force_reply=True, selective=True)
        )
        
        # Track this dialog message for cleanup
        task_id = task_dialog.get("task_id")
        if task_id:
            await self.cleanup_service.track_task_message(
                task_id, reply_message, state, "dialog_prompt"
            )
    
    async def _complete_task_with_variables(
        self, 
        message: Message, 
        state: FSMContext
    ) -> bool:
        """Complete the task with all collected variables."""
        try:
            data = await state.get_data()
            task_dialog = data.get("task_dialog", {})
            
            task_id = task_dialog.get("task_id")
            user_id = task_dialog.get("user_id")
            collected_values = task_dialog.get("collected_values", [])
            
            # Format variables for Camunda
            variables = {}
            for item in collected_values:
                variables[item["name"]] = item["value"]
            
            # Check if this is a start form
            if task_id == "start_form":
                # This is a start form - start the process with collected variables
                await self._start_process_after_form(message, state, user_id, variables)
            else:
                # Regular task completion
                await self.camunda_service.complete_task(
                    telegram_user_id=user_id,
                    task_id=task_id,
                    variables=variables
                )
                
                logger.info(f"✅ Dialog task {task_id} completed with {len(variables)} variables")
                
                # Clean up dialog messages
                await self.cleanup_service.delete_task_messages(task_id, message.bot, state)
                
                # Clear dialog state
                await state.update_data({"task_dialog": None})
                
                # Success message
                await message.answer(_("task.dialog.completed"))
                
                # Poll for next task
                process_id = data.get("active_process")
                if process_id:
                    from luka_bot.handlers.processes.start_process import poll_and_render_next_task
                    await poll_and_render_next_task(message, user_id, process_id, state)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error completing task with variables: {e}")
            await message.answer(_("task.dialog.error"))
            return False
    
    async def _start_process_after_form(
        self,
        message: Message,
        state: FSMContext,
        user_id: int,
        form_variables: dict
    ):
        """Start process after start form completion"""
        try:
            data = await state.get_data()
            pending_process = data.get("pending_process", {})
            
            # Use only form variables - no automatic merging of initial variables
            # The start form should request all needed variables from the user
            
            # Start the process
            process_instance = await self.camunda_service.start_process(
                telegram_user_id=user_id,
                process_key=pending_process["process_key"],
                business_key=pending_process["business_key"],
                variables=form_variables  # Only collected form variables
            )
            
            # Set FSM state
            from luka_bot.handlers.states import ProcessStates
            await state.set_state(ProcessStates.process_active)
            await state.update_data({
                "active_process": process_instance.id,
                "process_key": pending_process["process_key"],
                "group_id": pending_process.get("group_id"),
                "task_dialog": None,  # Clear dialog
                "pending_process": None  # Clear pending process
            })
            
            await message.answer("✅ Process started! Processing your request...")
            logger.info(f"Started process {process_instance.id} after start form completion")
            
            # Poll for first task
            from luka_bot.handlers.processes.start_process import poll_and_render_next_task
            await poll_and_render_next_task(message, user_id, process_instance.id, state)
            
        except Exception as e:
            logger.error(f"Failed to start process after form: {e}")
            await message.answer(f"❌ Failed to start process: {str(e)}")
    
    def _process_user_input(self, user_input: str) -> Tuple[Any, str]:
        """
        Process user input and determine variable type.
        
        Args:
            user_input: The raw user input string
            
        Returns:
            Tuple of (processed_value, variable_type)
        """
        user_input_lower = user_input.lower()
        
        # Check for boolean responses
        if user_input_lower in ["yes", "true", "да", "da", "1"]:
            return True, "Boolean"
        elif user_input_lower in ["no", "false", "нет", "net", "0"]:
            return False, "Boolean"
        
        # Check for numeric input
        if user_input.isdigit():
            return int(user_input), "Long"
        
        # Try to parse as float
        try:
            float_val = float(user_input)
            return float_val, "Double"
        except ValueError:
            pass
        
        # Default to string
        return user_input, "String"


def get_dialog_service() -> DialogService:
    """Get DialogService singleton"""
    return DialogService.get_instance()
