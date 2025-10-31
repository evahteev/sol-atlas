"""
Camunda tasks inline keyboard - Shows tasks from chatbot_start process.

Replaces the groups inline menu with task management interface.
"""
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger

from luka_bot.utils.i18n_helper import _


async def build_camunda_tasks_inline_keyboard(
    tasks: List,  # List of TaskSchema from camunda_client
    language: str = "en"
) -> InlineKeyboardMarkup:
    """
    Build inline keyboard with Camunda tasks from chatbot_start process.
    
    Layout:
    - Each task = one button (task.name)
    - callback_data = "task:{task_id}"
    - Max 10 tasks for clean UI
    
    Args:
        tasks: List of TaskSchema from chatbot_start process
        language: User language (for "no tasks" message)
        
    Returns:
        Inline keyboard markup
    """
    buttons = []
    
    if not tasks:
        # No tasks available - show info button
        buttons.append([
            InlineKeyboardButton(
                text=_("start.no_tasks_available", language),
                callback_data="no_tasks"
            )
        ])
    else:
        # Show up to 12 most recent tasks (4 rows of 3)
        display_tasks = tasks[:12]
        
        # Build task buttons (3 per row)
        for i in range(0, len(display_tasks), 3):
            row = []
            for j in range(3):
                if i + j < len(display_tasks):
                    task = display_tasks[i + j]
                    # Task name from BPMN definition (truncate for inline)
                    task_name = task.name or f"Task {task.id[:8]}"
                    # Truncate task name to fit 3 per row
                    if len(task_name) > 15:
                        task_name = task_name[:12] + "..."
                    
                    row.append(InlineKeyboardButton(
                        text=f"📋 {task_name}",
                        callback_data=f"task:{task.id}"
                    ))
            if row:
                buttons.append(row)
    
    logger.info(f"📋 Created Camunda tasks inline keyboard with {len(display_tasks) if tasks else 0} tasks (3 per row)")
    return InlineKeyboardMarkup(inline_keyboard=buttons)

