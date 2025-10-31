"""
File upload handler for S3 variables.
Handles Telegram file uploads and uploads to Cloudflare R2.
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.handlers.states import ProcessStates
from luka_bot.services.s3_upload_service import get_s3_upload_service
from luka_bot.services.camunda_service import get_camunda_service
from luka_bot.services.message_cleanup_service import get_message_cleanup_service
from luka_bot.handlers.processes.start_process import poll_and_render_next_task
from luka_bot.utils.i18n_helper import _

router = Router(name="file_upload")


@router.message(F.document, ProcessStates.file_upload_pending)
async def handle_file_upload(message: Message, state: FSMContext):
    """
    Handle file upload for S3 variables.
    Uploads to Cloudflare R2 and stores URL in form or completes task.
    """
    user_id = message.from_user.id
    
    # Early file size check - provide helpful feedback before attempting upload
    if message.document and message.document.file_size:
        MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB in bytes
        size_mb = message.document.file_size / (1024 * 1024)
        
        if message.document.file_size > MAX_FILE_SIZE:
            # Get user language for i18n
            from luka_bot.utils.i18n_helper import get_user_language
            lang = await get_user_language(user_id)
            
            await message.answer(
                _('file_upload.error.file_too_large', lang, size_mb=f"{size_mb:.1f}"),
                parse_mode="HTML"
            )
            logger.warning(f"File size limit exceeded for user {user_id}: {size_mb:.1f}MB")
            # Stay in file_upload_pending state to allow retry with smaller file
            return
    
    try:
        # Get context from state
        data = await state.get_data()
        
        # Check context: form_context (new) > start_form (old) > task
        form_context = data.get("form_context")
        start_form_data = data.get("start_form")
        task_id = data.get("current_task_id")
        
        if form_context:
            # New unified form context
            await handle_start_form_file_upload(message, state, form_context, use_form_context=True)
        elif start_form_data:
            # Old start form format (backward compatibility)
            await handle_start_form_file_upload(message, state, start_form_data, use_form_context=False)
        elif task_id:
            # This is a regular task file upload
            await handle_task_file_upload(message, state, task_id, data)
        else:
            await message.answer("⚠️ Контекст загрузки утерян. Пожалуйста, начните заново.")
            logger.warning(f"File upload without context for user {user_id}")
    
    except Exception as e:
        logger.error(f"File upload failed for user {user_id}: {e}")
        await message.answer(f"❌ Ошибка загрузки файла: {str(e)}")
        await state.set_state(ProcessStates.file_upload_pending)  # Allow retry


async def handle_start_form_file_upload(
    message: Message,
    state: FSMContext,
    start_form_data: dict,
    use_form_context: bool = False
):
    """
    Handle file upload during start form collection.
    Supports both new (form_context) and old (start_form) formats.
    """
    user_id = message.from_user.id
    
    try:
        # Extract data based on format
        if use_form_context:
            from luka_bot.models.form_models import FormContext
            context = FormContext.from_dict(start_form_data)
            editable_vars = context.form_data.editable_vars
            current_index = context.current_index
            collected_values = context.collected_values
            state_key = "form_context"
        else:
            editable_vars = start_form_data.get("editable_vars", [])
            current_index = start_form_data.get("current_index", 0)
            collected_values = start_form_data.get("collected_values", {})
            state_key = "start_form"
        
        if current_index >= len(editable_vars):
            await message.answer("⚠️ Неожиданная загрузка файла")
            return
        
        # Get current variable (should be s3_ type)
        current_var = editable_vars[current_index]
        var_name = current_var.get("name", "")
        
        if not var_name.startswith("s3_"):
            await message.answer("⚠️ Сейчас ожидается не файл, а текстовое значение")
            return
        
        # Show processing message
        processing_msg = await message.answer("⏳ Загрузка файла...")
        
        # Upload to S3 using the telegram file upload method
        s3_service = get_s3_upload_service()
        
        # For start forms, we use "start_form" as task_id placeholder
        file_url = await s3_service.upload_telegram_file(
            message=message,
            document=message.document,
            task_id="start_form",
            user_id=user_id,
            variable_name=var_name
        )
        
        # Delete processing message
        try:
            await processing_msg.delete()
        except:
            pass
        
        # Store the URL in collected values (this will be sent to Camunda)
        collected_values[var_name] = file_url
        
        logger.debug(
            f"📝 Stored file URL for {var_name}\n"
            f"   URL: {file_url}\n"
            f"   Total collected: {list(collected_values.keys())}"
        )
        
        # Update state
        data = await state.get_data()
        form_data = data.get(state_key, {})
        form_data["collected_values"] = collected_values
        form_data["current_index"] = current_index + 1
        await state.update_data({state_key: form_data})
        
        logger.debug(f"💾 Updated state with {len(collected_values)} values (state_key={state_key})")
        
        # Confirm with original filename and UUID info
        label = current_var.get("label", var_name.replace("s3_", "").replace("_", " ").title())
        file_name = message.document.file_name or "file"
        confirm_msg = await message.answer(
            f"✅ <b>{label}:</b> {file_name}\n"
            f"<i>Файл успешно загружен. URL сохранен для загрузки.</i>",
            parse_mode="HTML"
        )
        
        # Track confirmation message for later deletion
        if "dialog_message_ids" not in form_data:
            form_data["dialog_message_ids"] = []
        form_data["dialog_message_ids"].append(confirm_msg.message_id)
        await state.update_data({state_key: form_data})
        
        logger.info(
            f"User {user_id} uploaded file for start form var {var_name}:\n"
            f"   Original: {file_name}\n"
            f"   URL: {file_url}"
        )
        
        # Ask next variable
        from luka_bot.services.dialog_service import get_dialog_service
        dialog_service = get_dialog_service()
        
        # Switch back to waiting_for_input state
        await state.set_state(ProcessStates.waiting_for_input)
        await dialog_service._ask_next_editable_variable(message, state)
        
    except Exception as e:
        logger.error(f"Start form file upload failed: {e}")
        await message.answer(f"❌ Ошибка загрузки файла: {str(e)}")
        # Stay in file_upload_pending state to allow retry


async def handle_task_file_upload(
    message: Message,
    state: FSMContext,
    task_id: str,
    data: dict
):
    """
    Handle file upload for regular Camunda task.
    """
    user_id = message.from_user.id
    s3_variable_name = data.get("current_s3_variable")
    expected_extension = data.get("expected_file_extension")
    
    if not s3_variable_name:
        await message.answer("⚠️ Контекст переменной утерян")
        logger.warning(f"Task file upload without variable name for user {user_id}")
        return
    
    try:
        # Validate file extension if specified
        if expected_extension:
            file_name = message.document.file_name
            if not file_name.endswith(expected_extension):
                await message.answer(
                    f"⚠️ Пожалуйста, загрузите файл {expected_extension}.\n"
                    f"Получен: {file_name}"
                )
                return
        
        # Validate file size (max 20MB)
        max_size_mb = 20
        file_size_mb = message.document.file_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            await message.answer(
                f"⚠️ Файл слишком большой. Максимум: {max_size_mb}MB\n"
                f"Ваш файл: {file_size_mb:.1f}MB"
            )
            return
        
        # Show processing message
        processing_msg = await message.answer("⏳ Загрузка файла...")
        
        # Upload to S3 using the telegram file upload method
        # This generates a unique UUID filename and returns a public URL
        s3_service = get_s3_upload_service()
        file_url = await s3_service.upload_telegram_file(
            message=message,
            document=message.document,
            task_id=task_id,
            user_id=user_id,
            variable_name=s3_variable_name
        )
        
        # Delete processing message
        try:
            await processing_msg.delete()
        except:
            pass
        
        await message.answer(
            f"✅ Файл загружен\n"
            f"<i>{message.document.file_name}</i>\n"
            f"<code>URL сохранен для загрузки</code>",
            parse_mode="HTML"
        )
        
        logger.info(
            f"User {user_id} uploaded file for task {task_id}:\n"
            f"   Variable: {s3_variable_name}\n"
            f"   Original: {message.document.file_name}\n"
            f"   URL: {file_url}"
        )
        
        # Complete task with file URL (stored in Camunda variable)
        camunda_service = get_camunda_service()
        await camunda_service.complete_task(
            telegram_user_id=user_id,
            task_id=task_id,
            variables={s3_variable_name: file_url}
        )
        
        # Clean up task messages
        cleanup_service = get_message_cleanup_service()
        await cleanup_service.delete_task_messages(task_id, message.bot, state)
        
        # Clear upload context
        await state.update_data({
            "current_s3_variable": None,
            "expected_file_extension": None
        })
        
        # Poll for next task
        process_id = data.get("active_process")
        await poll_and_render_next_task(message, user_id, process_id, state)
    
    except Exception as e:
        logger.error(f"Task file upload failed: {e}")
        await message.answer(f"❌ Ошибка загрузки файла: {str(e)}")
        await state.set_state(ProcessStates.file_upload_pending)  # Allow retry


@router.message(ProcessStates.file_upload_pending)
async def handle_non_document_during_upload(message: Message, state: FSMContext):
    """Handle non-document messages during file upload state"""
    # Check if it's /cancel command
    if message.text and message.text.startswith("/cancel"):
        # Handle cancellation
        data = await state.get_data()
        if data.get("start_form"):
            await message.answer("❌ Загрузка файла отменена")
            await state.clear()
        else:
            await message.answer("❌ Загрузка файла отменена")
            await state.set_state(ProcessStates.idle)
        return
    
    await message.answer(
        "⚠️ Пожалуйста, загрузите файл используя кнопку 📎.\n"
        "Или отправьте /cancel для отмены."
    )
