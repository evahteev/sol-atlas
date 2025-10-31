"""
Search thread reply keyboard - FIX 42/43.

Reply keyboard for the chatbot_search thread with section header and thread management controls.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loguru import logger

from luka_bot.utils.i18n_helper import _


async def get_search_reply_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    """
    Create reply keyboard for search thread with section header.
    
    Provides controls for:
    - Section header (🔍 Search) + ❌
    - ✏️ (edit thread - rename the search thread)
    - 🔄 (reset - clear search history and restart)
    
    Returns:
        Reply keyboard markup
    """
    buttons = []
    
    # FIX 43: Row 0 - Section header + Close
    section_header = _("section.search", language=language)
    buttons.append([
        KeyboardButton(text=section_header),
        KeyboardButton(text="❌")
    ])
    
    # Row 1: Edit | Reset
    buttons.append([
        KeyboardButton(text="✏️"),
        KeyboardButton(text="🔄")
    ])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    logger.debug(f"📋 Created search reply keyboard with emoji-only buttons")
    return keyboard

