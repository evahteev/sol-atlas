from typing import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_server.core.config import settings


def task_keyboard(tasks: Sequence[dict]) -> InlineKeyboardMarkup:
    """Use in main menu."""

    buttons = []
    for task in tasks:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=task["name"],
                    url=settings.TELEGRAM_APP_LINK + f"?startapp",
                )
            ]
        )

    keyboard = InlineKeyboardBuilder(markup=buttons)

    return keyboard.as_markup()
