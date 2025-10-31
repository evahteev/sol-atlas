"""
Start menu reply keyboard - Quick prompts + emoji-only KB scope controls.

Replaces the inline keyboard with a persistent reply keyboard for better UX.
"""
from typing import List
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loguru import logger

from luka_bot.services.prompt_pool_service import PromptOption
from luka_bot.utils.i18n_helper import _


async def build_start_reply_keyboard(
    prompts: List[PromptOption],
    include_scope_controls: bool = False,
    language: str = "en"
) -> ReplyKeyboardMarkup:
    """
    Build reply keyboard with quick prompts and emoji-only scope controls.
    
    Layout:
    - Row 1-2: Prompts (2 per row, up to 3 prompts total)
    - Row 3: Scope controls (3 emoji-only buttons: ⚙️ 🌐 🎯)
    
    Args:
        prompts: List of localized prompts (from prompt_pools/{locale}.json)
        include_scope_controls: Whether to add scope control row
        language: User language (for placeholder only, prompts pre-localized)
        
    Returns:
        Reply keyboard markup
    """
    buttons = []
    
    # Add prompts (2 per row for readability)
    for i in range(0, len(prompts), 2):
        row = []
        for j in range(2):
            if i + j < len(prompts):
                prompt = prompts[i + j]
                # Prompts are already localized from prompt_pools
                # Truncate to fit in reply keyboard
                text = prompt.text[:40] + "..." if len(prompt.text) > 40 else prompt.text
                row.append(KeyboardButton(text=text))
        if row:
            buttons.append(row)
    
    # Add emoji-only scope controls (no translation needed!)
    if include_scope_controls:
        scope_row = [
            KeyboardButton(text="⚙️"),  # Edit Groups (custom selection)
            KeyboardButton(text="🌐"),  # All Sources (search everywhere)
            KeyboardButton(text="🎯"),  # My Groups (auto user groups)
        ]
        buttons.append(scope_row)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder=_("start.keyboard.placeholder", language)
    )
    
    logger.info(f"📋 Created start reply keyboard with {len(prompts)} prompts, scope_controls={include_scope_controls}")
    return keyboard

