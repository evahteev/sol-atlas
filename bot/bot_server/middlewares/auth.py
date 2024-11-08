from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from loguru import logger

from bot_server.services.users import add_user, get_user
from bot_server.utils.command import find_command_argument

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class AuthMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: dict[str, Any],
    ) -> Any:
        if isinstance(event, CallbackQuery):
            user_data = await get_user(user_id=event.from_user.id)
            if not user_data:
                return await event.answer("You are not registered, /start to register")
            data["user_data"] = user_data.dict()
            if "state" in data and isinstance(data["state"], FSMContext):
                await data["state"].update_data(user=user_data.dict())
            return await handler(event, data)
        if not isinstance(event, Message):
            return await handler(event, data)

        message: Message = event
        user = message.from_user
        if not user:
            return await handler(event, data)
        user_data = await get_user(user_id=user.id)
        if not user_data:
            logger.info(
                f"New user registration | user_id: {user.id} | message: {message.text}"
            )
            user_data = await add_user(user=user)
        referrer = find_command_argument(message.text)
        data["user_data"] = user_data.dict()
        if "state" in data and isinstance(data["state"], FSMContext):
            await data["state"].update_data(user=user_data.dict(), referrer=referrer)

        return await handler(event, data)
