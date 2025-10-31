"""
Unified Form Service for rendering and handling both start forms and tasks.

Provides identical UI/UX for:
1. Camunda process start forms
2. Camunda task forms

Flow:
1. Show intro with X/Start buttons
2. Collect variables via dialog
3. Show confirmation
4. Complete action (start process or complete task)
"""
from typing import Dict, Any, Optional
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.models.form_models import FormData, FormContext, FormType
from luka_bot.handlers.states import ProcessStates
from luka_bot.utils.i18n_helper import _, get_user_language


class UnifiedFormService:
    """
    Unified service for rendering and handling start forms and tasks.
    
    Provides identical UI/UX for both types with:
    - Consistent intro screen layout
    - Variable collection via dialog
    - Confirmation before completion
    - Clean message cleanup
    """
    
    def __init__(self):
        from luka_bot.services.camunda_service import get_camunda_service
        from luka_bot.services.message_cleanup_service import get_message_cleanup_service
        
        self.camunda_service = get_camunda_service()
        self.cleanup_service = get_message_cleanup_service()
    
    async def render_form(
        self,
        form_data: FormData,
        message: Message,
        user_id: int,
        state: FSMContext
    ) -> bool:
        """
        Main entry point for form rendering.
        
        Task rendering logic:
        1. Task with form_ variables: Start dialog immediately, only X button
        2. Task with text_/action_ variables (no form_): Show X and Start buttons (no link button)
        3. Task with no forms: Complete immediately (handled in task_service.py)
        
        Args:
            form_data: Unified form data (start form or task)
            message: Telegram message to respond to
            user_id: Telegram user ID
            state: FSM context
            
        Returns:
            bool: True if rendered successfully
        """
        try:
            # Get user language for i18n
            language = await get_user_language(user_id)
            
            # Special handling for tasks based on variable types
            if form_data.form_type == FormType.TASK:
                has_form_vars = len(form_data.form_vars) > 0
                has_text_or_action = len(form_data.text_vars) > 0 or len(form_data.action_vars) > 0
                
                # Case 1: Task has form_ variables - start dialog immediately
                if has_form_vars:
                    logger.info(f"📋 Task {form_data.name} has form variables - starting dialog immediately")
                    
                    # Build intro message
                    intro_message = self._build_intro_message(form_data, language=language)
                    
                    # Show only X button (no Start button, no link button)
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text="❌",
                            callback_data=f"form_close:{form_data.form_type.value}"
                        )
                    ]])
                    
                    intro_msg = await message.answer(
                        intro_message,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                    
                    # Store context for dialog cancellation
                    context = FormContext(
                        form_data=form_data,
                        intro_message_id=intro_msg.message_id,
                        intro_message_text=intro_message
                    )
                    
                    context_dict = context.to_dict()
                    context_dict["menu_message_ids"] = []
                    
                    await state.update_data({
                        "form_context": context_dict
                    })
                    await state.set_state(ProcessStates.dialog_active)
                    
                    # Start dialog collection immediately
                    await self._start_variable_collection(intro_msg, state)
                    
                    logger.info(f"✅ Started dialog immediately for task {form_data.name}")
                    return True
                
                # Case 2: Task has text_/action_ variables but no form_ variables
                elif has_text_or_action:
                    logger.info(f"📋 Task {form_data.name} has text/action variables (no form) - showing intro with X/Start buttons")
                    
                    # Build intro message
                    intro_message = self._build_intro_message(form_data, language=language)
                    
                    # Build keyboard - combine cancel/start buttons with action buttons
                    keyboard_rows = []
                    
                    # Add action buttons first (if available)
                    if form_data.has_action_buttons:
                        from luka_bot.keyboards.inline.task_keyboards import build_action_keyboard
                        action_keyboard = build_action_keyboard(
                            form_data.task_id,
                            form_data.action_vars,
                            show_cancel=False
                        )
                        keyboard_rows.extend(action_keyboard.inline_keyboard)
                    
                    # Add cancel/start buttons at the bottom (NO link button)
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
                    
                    # NO process instance ID link button added for tasks
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
                    
                    # Send intro with buttons
                    intro_msg = await message.answer(
                        intro_message,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                    
                    # Store context in FSM
                    context = FormContext(
                        form_data=form_data,
                        intro_message_id=intro_msg.message_id,
                        intro_message_text=intro_message
                    )
                    
                    context_dict = context.to_dict()
                    context_dict["menu_message_ids"] = []
                    
                    await state.update_data({
                        "form_context": context_dict
                    })
                    await state.set_state(ProcessStates.dialog_active)
                    
                    logger.info(
                        f"✅ Rendered {form_data.form_type.value} form: {form_data.name} "
                        f"(0 editable, {len(form_data.action_vars)} actions)"
                    )
                    return True
            
            # Default behavior for start forms and other cases
            # Build intro message
            intro_message = self._build_intro_message(form_data, language=language)
            
            # Build keyboard - combine cancel/start buttons with action buttons
            keyboard_rows = []
            
            # Add action buttons first (if available)
            if form_data.has_action_buttons:
                from luka_bot.keyboards.inline.task_keyboards import build_action_keyboard
                action_keyboard = build_action_keyboard(
                    form_data.task_id,
                    form_data.action_vars,
                    show_cancel=False
                )
                # Add action button rows
                keyboard_rows.extend(action_keyboard.inline_keyboard)
            
            # Add cancel/start buttons at the bottom
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
            
            # Process instance link button only for start forms (not tasks)
            # Tasks handle this separately above
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
            
            # Send intro with all buttons attached directly to the message
            intro_msg = await message.answer(
                intro_message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            # Check if this is a display-only task (no input needed)
            if form_data.total_editable == 0 and len(form_data.action_vars) == 0:
                # Display-only task - don't store form_context to avoid blocking LLM
                logger.info(
                    f"✅ Rendered display-only {form_data.form_type.value}: {form_data.name} "
                    f"(0 editable, 0 actions)"
                )
                
                # Clear any existing form context to unblock LLM
                data = await state.get_data()
                if "form_context" in data:
                    logger.debug(f"🧹 Clearing stale form_context for display-only task")
                    data_copy = dict(data)
                    del data_copy["form_context"]
                    await state.set_data(data_copy)
                
                await state.set_state(None)  # Clear FSM state
                return True
            
            # Store context in FSM (only for tasks that need input)
            context = FormContext(
                form_data=form_data,
                intro_message_id=intro_msg.message_id,
                intro_message_text=intro_message  # Store text for editing later
            )
            
            # No separate action message needed - all buttons are inline now
            menu_message_ids = []
            
            context_dict = context.to_dict()
            context_dict["menu_message_ids"] = menu_message_ids
            
            await state.update_data({
                "form_context": context_dict
            })
            await state.set_state(ProcessStates.dialog_active)
            
            logger.info(
                f"✅ Rendered {form_data.form_type.value} form: {form_data.name} "
                f"({form_data.total_editable} editable, {len(form_data.action_vars)} actions)"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to render form: {e}")
            await message.answer("❌ Ошибка отображения формы")
            return False
    
    def _build_intro_message(self, form_data: FormData, language: str = "en") -> str:
        """
        Build unified intro message for start forms and tasks.
        
        Format:
        <b>{emoji} {name}</b>
        
        {description}
        
        {text_vars with labels}
        
        ────────────────────
        📝 2 fields
        📎 1 file
        ⚡ 1 action (tasks only)
        
        Args:
            form_data: Form data to render
            language: User language code ("en" or "ru")
            
        Returns:
            str: Formatted HTML message
        """
        import json
        
        # Select emoji based on form type
        emoji = self._get_form_emoji(form_data)
        
        # Build title
        title = f"{emoji} {form_data.name}"
        
        # Start building message parts
        parts = [f"<b>{title}</b>"]
        
        # Add description (parse if JSON)
        if form_data.description:
            description = form_data.description
            
            # Check if description is JSON object
            if isinstance(description, str) and (description.startswith('{') or description.startswith('[')):
                try:
                    desc_obj = json.loads(description)
                    if isinstance(desc_obj, dict):
                        description = desc_obj.get("description", description)
                except json.JSONDecodeError:
                    pass  # Use as-is
            
            if description:
                parts.append(description)
        
        # Add text variables (read-only display)
        for var in form_data.text_vars:
            label = var.get("label", var.get("name", "").replace("text_", "").replace("_", " ").title())
            value = var.get("value", "")
            
            if value:
                # Format content for better display
                content = self._format_text_content(str(value))
                parts.append(f"<b>{label}:</b>\n{content}")
        
        # Add summary of editable variables (form and s3 only)
        # Note: Action buttons are NOT shown in summary - they appear after clicking "Начать"
        total_editable = form_data.total_editable
        
        if total_editable > 0:
            summary_items = []
            
            # Count form variables
            form_count = len(form_data.form_vars)
            if form_count > 0:
                # Use i18n for field text
                field_text = _("forms.field_count", language)
                summary_items.append(f"📝 {form_count} {field_text}")
            
            # Count s3 variables
            s3_count = len(form_data.s3_vars)
            if s3_count > 0:
                # Use i18n for file text
                file_text = _("forms.file_count", language)
                summary_items.append(f"📎 {s3_count} {file_text}")
            
            if summary_items:
                parts.append("\n".join(summary_items))
        
        return "\n".join(parts)
    
    def _get_form_emoji(self, form_data: FormData) -> str:
        """
        Get emoji based on form type.
        
        For start forms: uses process-specific emoji (import, export, etc.)
        For tasks: uses generic task emoji 📋
        
        Args:
            form_data: Form data
            
        Returns:
            str: Emoji string
        """
        if form_data.form_type == FormType.START_FORM:
            return self._get_process_emoji(form_data.process_key or "")
        else:
            # Task emoji - can be customized based on task name
            return "📋"
    
    def _get_process_emoji(self, process_key: str) -> str:
        """
        Get contextual emoji for process based on keywords in process key.
        
        Args:
            process_key: Camunda process definition key
            
        Returns:
            str: Emoji string with ✨ prefix
        """
        keywords = {
            "import": "📥",
            "export": "📤",
            "analyze": "🔍",
            "analysis": "🔍",
            "report": "📊",
            "audit": "🔎",
            "review": "👁️",
            "approve": "✅",
            "reject": "❌",
            "create": "➕",
            "delete": "🗑️",
            "update": "🔄",
            "sync": "🔄",
        }
        
        process_key_lower = process_key.lower()
        for keyword, emoji in keywords.items():
            if keyword in process_key_lower:
                return f"✨ {emoji}"
        
        # Default emoji
        return "✨ 📋"
    
    def _format_text_content(self, content: str) -> str:
        """
        Format text content for better display.
        
        Fixes:
        - Numbered lists to have proper line breaks
        - Remove excessive whitespace
        
        Args:
            content: Raw text content
            
        Returns:
            str: Formatted content
        """
        import re
        
        # Fix numbered lists: "1. Item 2. Item" → "1. Item\n2. Item"
        # Look for pattern: digit + dot + space + text + digit + dot
        content = re.sub(r'(\d+\.\s+[^\d]+?)(\d+\.)', r'\1\n\2', content)
        
        # Also handle case where there's no space before next number
        content = re.sub(r'([a-zA-Zа-яА-Я\)\]\}])(\d+\.)', r'\1\n\2', content)
        
        return content.strip()
    
    async def handle_form_close(
        self,
        callback: CallbackQuery,
        form_type: FormType,
        state: FSMContext
    ):
        """
        Handle X button click - close form and clean up.
        
        Args:
            callback: Callback query from X button
            form_type: Type of form (start_form or task)
            state: FSM context
        """
        try:
            data = await state.get_data()
            context_data = data.get("form_context", {})
            
            # Delete the intro message (which now has the keyboard)
            try:
                await callback.message.delete()
            except Exception as e:
                logger.warning(f"Could not delete intro message: {e}")
            
            # Delete fast actions message if it exists
            menu_message_ids = context_data.get("menu_message_ids", [])
            for msg_id in menu_message_ids:
                try:
                    await callback.bot.delete_message(
                        chat_id=callback.message.chat.id,
                        message_id=msg_id
                    )
                except Exception as e:
                    logger.debug(f"Could not delete action message {msg_id}: {e}")
            
            # Delete dialog messages (prompts and ForceReply messages)
            dialog_message_ids = context_data.get("dialog_message_ids", [])
            if dialog_message_ids:
                logger.debug(f"📋 Found {len(dialog_message_ids)} dialog messages to delete")
                deleted_count = 0
                for msg_id in dialog_message_ids:
                    try:
                        await callback.bot.delete_message(
                            chat_id=callback.message.chat.id,
                            message_id=msg_id
                        )
                        deleted_count += 1
                    except Exception as e:
                        logger.debug(f"Could not delete dialog message {msg_id}: {e}")
                
                if deleted_count > 0:
                    logger.debug(f"🗑️ Deleted {deleted_count} dialog messages")
            
            # Delete confirmation message if exists
            confirmation_message_id = context_data.get("confirmation_message_id")
            if confirmation_message_id:
                try:
                    await callback.bot.delete_message(
                        chat_id=callback.message.chat.id,
                        message_id=confirmation_message_id
                    )
                    logger.debug(f"🗑️ Deleted confirmation message {confirmation_message_id}")
                except Exception as e:
                    logger.debug(f"Could not delete confirmation message: {e}")
            
            # Also check legacy formats for backward compatibility
            legacy_form_data = data.get("start_form") or data.get("task_dialog", {})
            if legacy_form_data and isinstance(legacy_form_data, dict):
                legacy_dialog_ids = legacy_form_data.get("dialog_message_ids", [])
                if legacy_dialog_ids:
                    for msg_id in legacy_dialog_ids:
                        try:
                            await callback.bot.delete_message(
                                chat_id=callback.message.chat.id,
                                message_id=msg_id
                            )
                        except Exception as e:
                            logger.debug(f"Could not delete legacy dialog message {msg_id}: {e}")
            
            # Clear state
            await state.update_data({
                "form_context": None,
                "start_form": None,  # For backward compatibility
                "task_dialog": None,  # For backward compatibility
                "pending_process": None
            })
            await state.clear()
            
            await callback.answer("❌ Отменено")
            logger.info(f"User {callback.from_user.id} closed {form_type.value} form")
            
        except Exception as e:
            logger.error(f"❌ Error closing form: {e}")
            await callback.answer("❌ Ошибка", show_alert=True)
    
    async def handle_form_begin(
        self,
        callback: CallbackQuery,
        form_type: FormType,
        state: FSMContext
    ):
        """
        Handle Start button click.
        
        Determines next step based on form variables:
        1. If has action buttons → Show action buttons
        2. If no editable vars → Complete immediately
        3. If has editable vars → Start dialog collection
        
        Args:
            callback: Callback query from Start button
            form_type: Type of form
            state: FSM context
        """
        try:
            data = await state.get_data()
            context_data = data.get("form_context", {})
            context = FormContext.from_dict(context_data)
            form_data = context.form_data
            
            # Remove keyboard from intro message (where X/Start buttons are attached)
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except Exception as e:
                logger.debug(f"Could not remove keyboard from intro message: {e}")
            
            # Delete fast actions message if it exists
            menu_message_ids = context_data.get("menu_message_ids", [])
            for msg_id in menu_message_ids:
                try:
                    await callback.bot.delete_message(
                        chat_id=callback.message.chat.id,
                        message_id=msg_id
                    )
                except Exception as e:
                    logger.debug(f"Could not delete action message {msg_id}: {e}")
            
            await callback.answer("▶️ Начинаем...")
            
            # Determine next step based on form/s3 variables only
            # (Action buttons are shown immediately in intro and handle their own submission)
            if form_data.total_editable == 0:
                # No form/s3 variables - complete immediately (or just wait for action button click)
                if form_data.has_action_buttons:
                    # Has action buttons but no form vars - just wait for user to click action button
                    language = await get_user_language(form_data.telegram_user_id)
                    prompt_text = _("forms.actions_prompt", language)
                    if prompt_text == "forms.actions_prompt":
                        prompt_text = (
                            "👇 Выберите действие ниже или нажмите ❌ для отмены."
                            if language == "ru"
                            else "👇 Use the buttons below or tap ❌ to cancel."
                        )
                    await callback.message.answer(prompt_text, parse_mode="HTML")
                else:
                    # No variables at all - complete immediately
                    await self._complete_immediately(callback.message, form_data, state)
            
            else:
                # Has form/s3 variables - start dialog collection
                await self._start_variable_collection(callback.message, state)
            
        except Exception as e:
            logger.error(f"❌ Error handling form begin: {e}")
            await callback.answer("❌ Ошибка", show_alert=True)
    
    # Note: _show_action_buttons_inline and _show_action_buttons methods removed
    # Action buttons are now integrated directly into the main form keyboard in render_form()
    # No separate "⚡ Быстрые действия:" message is sent anymore
    
    async def _complete_immediately(
        self,
        message: Message,
        form_data: FormData,
        state: FSMContext
    ):
        """Complete form immediately (no variables to collect)"""
        try:
            if form_data.form_type == FormType.START_FORM:
                # Start process
                await self._start_process(form_data, {}, state)
                await message.answer("✅ Процесс запущен!")
                
                # Poll for first task
                from luka_bot.handlers.processes.start_process import poll_and_render_next_task
                process_id = (await state.get_data()).get("active_process")
                if process_id:
                    await poll_and_render_next_task(
                        message, form_data.telegram_user_id, process_id, state
                    )
            else:
                # Complete task with cleanup
                # Delete intro message (task description)
                data = await state.get_data()
                form_context = data.get("form_context", {})
                intro_msg_id = form_context.get("intro_message_id")
                
                if intro_msg_id:
                    try:
                        await message.bot.delete_message(
                            chat_id=message.chat.id,
                            message_id=intro_msg_id
                        )
                        logger.debug(f"🗑️ Deleted task intro (no variables)")
                    except Exception as e:
                        logger.debug(f"Could not delete intro: {e}")
                
                # Delete action buttons if any
                menu_msg_ids = form_context.get("menu_message_ids", [])
                for msg_id in menu_msg_ids:
                    try:
                        await message.bot.delete_message(
                            chat_id=message.chat.id,
                            message_id=msg_id
                        )
                    except:
                        pass
                
                # Complete task
                await self._complete_task(form_data, {}, state)
                
                # Show clean confirmation - simplified format
                await message.answer(
                    f"<b>✅ {form_data.name}</b>",
                    parse_mode="HTML"
                )
                
                # Poll for next task
                from luka_bot.handlers.processes.start_process import poll_and_render_next_task
                process_id = (await state.get_data()).get("active_process")
                if process_id:
                    await poll_and_render_next_task(
                        message, form_data.telegram_user_id, process_id, state
                    )
            
            logger.info(f"✅ Completed {form_data.form_type.value} {form_data.id} immediately (no variables)")
            
        except Exception as e:
            logger.error(f"❌ Error completing immediately: {e}")
            await message.answer("❌ Ошибка завершения")
    
    async def _start_variable_collection(
        self,
        message: Message,
        state: FSMContext
    ):
        """Start collecting variables via dialog"""
        from luka_bot.services.dialog_service import get_dialog_service
        
        dialog_service = get_dialog_service()
        
        await state.set_state(ProcessStates.waiting_for_input)
        await dialog_service._ask_next_editable_variable(message, state)
    
    async def _start_process(
        self,
        form_data: FormData,
        variables: Dict[str, Any],
        state: FSMContext
    ):
        """Start Camunda process with collected variables"""
        process_instance = await self.camunda_service.start_process(
            telegram_user_id=form_data.telegram_user_id,
            process_key=form_data.process_key,
            business_key=form_data.business_key,
            variables=variables
        )
        
        await state.update_data({
            "active_process": str(process_instance.id),
            "process_key": form_data.process_key,
            "group_id": form_data.group_id,
            "form_context": None
        })
        await state.set_state(ProcessStates.process_active)
        
        logger.info(f"✅ Started process {process_instance.id} from {form_data.form_type.value}")
    
    async def _complete_task(
        self,
        form_data: FormData,
        variables: Dict[str, Any],
        state: FSMContext
    ):
        """Complete Camunda task with collected variables"""
        await self.camunda_service.complete_task(
            telegram_user_id=form_data.telegram_user_id,
            task_id=form_data.task_id,
            variables=variables
        )
        
        # Clear task context
        await state.update_data({
            "current_task_id": None,
            "form_context": None,
            "start_form": None,
            "task_dialog": None
        })

        await state.set_state(ProcessStates.process_active)
        
        logger.info(f"✅ Completed task {form_data.task_id}")


# Singleton instance
_instance: Optional[UnifiedFormService] = None


def get_unified_form_service() -> UnifiedFormService:
    """Get or create singleton instance of UnifiedFormService"""
    global _instance
    if _instance is None:
        _instance = UnifiedFormService()
        logger.debug("✅ UnifiedFormService singleton created")
    return _instance
