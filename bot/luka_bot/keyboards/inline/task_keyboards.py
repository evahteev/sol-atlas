"""
Inline keyboards for Camunda task actions.
"""
from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from loguru import logger


class TaskActionCallback(CallbackData, prefix="act"):
    """Callback data for task actions (compact format for 64-byte limit)"""
    task_id: str  # First 8 chars of task ID
    action: str  # Action variable name


def build_action_keyboard(
    task_id: str,
    action_vars: List[Dict[str, Any]],
    show_cancel: bool = True
) -> InlineKeyboardMarkup:
    """
    Build inline keyboard for action variables.
    
    Args:
        task_id: Full task ID (will be truncated to 8 chars)
        action_vars: List of action variable dicts
        show_cancel: Whether to show cancel button
        
    Returns:
        InlineKeyboardMarkup with action buttons
    """
    buttons = []
    row = []
    
    for var in action_vars:
        var_name = var.get("name")
        
        # Skip action_back (rendered separately if needed)
        if var_name == "action_back":
            continue
        
        # Get label (remove action_ prefix and title case)
        var_label = var.get("label", var_name.replace("action_", "").replace("_", " ").title())
        
        # Create callback (use only first 8 chars of task ID to stay under 64 bytes)
        callback = TaskActionCallback(
            task_id=task_id[:8],
            action=var_name
        )
        
        row.append(InlineKeyboardButton(
            text=var_label,
            callback_data=callback.pack()
        ))
        
        # Max 2 buttons per row
        if len(row) >= 2:
            buttons.append(row)
            row = []
    
    # Add remaining buttons
    if row:
        buttons.append(row)
    
    # Add cancel button
    if show_cancel:
        buttons.append([InlineKeyboardButton(
            text="❌ Cancel",
            callback_data=TaskActionCallback(task_id=task_id[:8], action="cancel").pack()
        )])
    
    logger.debug(f"Built action keyboard with {len(buttons)} rows for task {task_id[:8]}")
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_file_upload_keyboard(task_id: str) -> InlineKeyboardMarkup:
    """
    Build keyboard for file upload prompt.
    
    Args:
        task_id: Full task ID
        
    Returns:
        InlineKeyboardMarkup with cancel button
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="❌ Cancel Upload",
            callback_data=TaskActionCallback(task_id=task_id[:8], action="cancel_upload").pack()
        )]
    ])


def build_process_confirmation_keyboard(process_id: str) -> InlineKeyboardMarkup:
    """
    Build keyboard for process confirmation.
    
    Args:
        process_id: Process instance ID
        
    Returns:
        InlineKeyboardMarkup with start/cancel buttons
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Start", callback_data=f"process_start:{process_id[:8]}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"process_cancel:{process_id[:8]}")
        ]
    ])

