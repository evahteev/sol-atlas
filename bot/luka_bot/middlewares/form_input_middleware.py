"""
Middleware that ensures active forms receive text input before it reaches
general-purpose handlers (e.g. streaming DM).
"""
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from luka_bot.handlers.states import ProcessStates


HandlerType = Callable[[Message, Dict[str, Any]], Awaitable[Any]]


class FormInputMiddleware(BaseMiddleware):
    """
    Short-circuit text updates when a form is active in FSM state.

    If a form context is present, the middleware routes the message to the form
    handlers directly and stops further handler processing. This avoids cases
    where the streaming DM handler consumes the message before the form handler
    sees it.
    """

    async def __call__(
        self,
        handler: HandlerType,
        event: Message,
        data: Dict[str, Any],
    ) -> Optional[Any]:
        # Only intercept plain text messages
        if not isinstance(event, Message) or not event.text:
            return await handler(event, data)

        # Allow commands (e.g. /start) to bypass the form guard
        if event.text.startswith("/"):
            return await handler(event, data)

        state: Optional[FSMContext] = data.get("state")
        if state is None:
            return await handler(event, data)

        try:
            current_state = await state.get_state()
            state_data = await state.get_data()
        except Exception:
            logger.exception("❌ FormInputMiddleware: failed to fetch FSM state")
            return await handler(event, data)

        # Allow normal processing when we're no longer in a form-related state,
        # even if stale form_context/start_form/task_dialog keys remain in storage.
        guarded_states = {
            ProcessStates.waiting_for_input.state,
            ProcessStates.dialog_active.state,
            ProcessStates.file_upload_pending.state,
        }
        if current_state not in guarded_states:
            return await handler(event, data)

        form_context = state_data.get("form_context")
        start_form = state_data.get("start_form")
        task_dialog = state_data.get("task_dialog")

        # Treat None/empty dict the same as absent (form already cleared)
        if not any(bool(val) for val in (form_context, start_form, task_dialog)):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        logger.debug(
            "🛡️ FormInputMiddleware: intercepting text for user %s (len=%d)",
            user_id,
            len(event.text),
        )

        try:
            if task_dialog:
                from luka_bot.services.dialog_service import get_dialog_service

                dialog_service = get_dialog_service()
                await dialog_service.handle_dialog_input(event, state)
            else:
                from luka_bot.handlers.processes.start_form_handlers import (
                    handle_start_form_input,
                )

                await handle_start_form_input(event, state)
        except Exception:
            logger.exception("❌ FormInputMiddleware failed to route form input")

        # Stop propagation to downstream handlers
        return None
