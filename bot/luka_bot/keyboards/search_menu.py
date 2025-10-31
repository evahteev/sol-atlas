"""
Inline keyboard for KB search menu.

Displays available knowledge bases with selection checkboxes.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from luka_bot.utils.i18n_helper import _


def get_search_kb_menu(available_kbs: list[dict], selected_indices: set[str], language: str) -> InlineKeyboardMarkup:
    """
    Build inline keyboard for KB selection.
    
    Args:
        available_kbs: List of KB dicts with {name, index, type, icon, description}
        selected_indices: Set of currently selected KB indices
        language: User's language for translations
    
    Returns:
        InlineKeyboardMarkup with KB selection buttons
    """
    buttons = []
    
    # KB selection buttons (one per row)
    for kb in available_kbs:
        is_selected = kb["index"] in selected_indices
        checkbox = "✅" if is_selected else "☐"
        button_text = f"{checkbox} {kb['icon']} {kb['name']}"
        
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"search_kb:toggle:{kb['index']}"
            )
        ])
    
    # Action buttons row
    action_buttons = []
    
    if len(available_kbs) > 1:
        # "Select All" button
        action_buttons.append(
            InlineKeyboardButton(
                text=_("search.button.select_all", language=language),
                callback_data="search_kb:search_all:"
            )
        )
    
    if selected_indices:
        # "Clear All" button
        action_buttons.append(
            InlineKeyboardButton(
                text=_("search.button.clear_all", language=language),
                callback_data="search_kb:clear_all:"
            )
        )
    
    if action_buttons:
        buttons.append(action_buttons)
    
    # "Done" button
    buttons.append([
        InlineKeyboardButton(
            text=_("search.button.done", language=language),
            callback_data="search_done"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
