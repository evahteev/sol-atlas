"""
Thread management reply keyboard - Phase 3.

Always-visible keyboard showing thread list and controls.
Phase 4: i18n support for button labels.
"""
from typing import List, Optional
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from loguru import logger

from luka_bot.models.thread import Thread
from luka_bot.utils.i18n_helper import _

# Active thread indicator emoji options:
# "▶️" - Play button
# "✅" - Check mark
# "🔵" - Blue circle
# "⭐" - Star
# "💬" - Speech bubble (current)
# "📌" - Pin
ACTIVE_THREAD_INDICATOR = "💬"


async def get_threads_keyboard(
    threads: List[Thread],
    current_thread_id: Optional[str] = None,
    language: str = "en",
    section: str = "chat",  # FIX 43: Section identifier for header
    max_threads: int = 10
) -> ReplyKeyboardMarkup:
    """
    Create reply keyboard with thread list and section header.
    
    Shows section header, threads with edit/delete buttons in each row.
    
    Args:
        threads: List of user threads
        current_thread_id: ID of active thread (highlighted)
        language: User's language preference (en/ru)
        section: Section identifier (e.g., "chat") for header
        max_threads: Maximum threads to show
        
    Returns:
        Reply keyboard markup
    """
    buttons = []
    
    # FIX 43: Row 0 - Section header + Close
    section_header = _(f"section.{section}", language=language)
    buttons.append([
        KeyboardButton(text=section_header),
        KeyboardButton(text="❌")
    ])
    
    # Row 1 - New Thread button
    buttons.append([KeyboardButton(text=_('keyboard.btn_new_thread', language))])
    
    # Show up to max_threads most recent
    display_threads = threads[:max_threads]
    
    for thread in display_threads:
        # Check if this is the active thread
        is_active = thread.thread_id == current_thread_id
        
        # Build button text
        name = thread.name[:18]  # Shorter to fit edit/delete buttons
        
        # Add indicator if current thread - more prominent!
        if is_active:
            name = f"{ACTIVE_THREAD_INDICATOR} {name}"
        
        # Add message count
        if thread.message_count > 0:
            name = f"{name} ({thread.message_count})"
        
        # Row with thread name + edit + delete buttons
        thread_row = [
            KeyboardButton(text=name),
            KeyboardButton(text="✏️"),
            KeyboardButton(text="🗑️"),
        ]
        buttons.append(thread_row)
        
        logger.debug(f"Thread {thread.name}: is_active={is_active}, thread_id={thread.thread_id}, current={current_thread_id}")
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Type a message or tap thread..."
    )
    
    logger.info(f"📋 Created reply keyboard with {len(display_threads)} threads")
    return keyboard


async def get_empty_state_keyboard(language: str = "en", section: str = "chat") -> ReplyKeyboardMarkup:
    """
    Keyboard when user has no threads yet (empty state).
    
    Shows section header and "Start New Chat" button to encourage first message.
    Used for lazy thread creation flow.
    
    Args:
        language: User's language preference (en/ru)
        section: Section identifier for header
    
    Returns:
        Minimal reply keyboard for empty state
    """
    buttons = [
        # FIX 43: Section header
        [KeyboardButton(text=_(f"section.{section}", language=language)), KeyboardButton(text="❌")],
        [KeyboardButton(text=_('keyboard.btn_start_new_chat', language))],
    ]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Type your message to start..."
    )
    
    logger.info("📋 Created empty state keyboard")
    return keyboard


async def get_default_keyboard() -> ReplyKeyboardMarkup:
    """
    Create default keyboard when no threads exist (legacy).
    
    Deprecated: Use get_empty_state_keyboard() instead.
    
    Returns:
        Basic reply keyboard
    """
    return await get_empty_state_keyboard()


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove reply keyboard."""
    return ReplyKeyboardRemove()


def is_thread_button(text: str, threads: List[Thread]) -> Optional[str]:
    """
    Check if button text matches a thread.
    
    Args:
        text: Button text
        threads: List of threads to match against
        
    Returns:
        Thread ID if matched, None otherwise
    """
    # Clean the text - remove active indicator
    clean_text = text.replace(f"{ACTIVE_THREAD_INDICATOR} ", "").strip()
    
    # Also handle other indicators for backwards compatibility
    for emoji in ["▶️", "✅", "🔵", "⭐", "💬", "📌"]:
        clean_text = clean_text.replace(f"{emoji} ", "").strip()
    
    # Remove message count
    if "(" in clean_text:
        clean_text = clean_text.split("(")[0].strip()
    
    # Try to match thread by name
    for thread in threads:
        if thread.name.startswith(clean_text) or clean_text.startswith(thread.name[:18]):
            return thread.thread_id
    
    return None


def is_control_button(text: str) -> bool:
    """Check if text is a control button."""
    control_buttons = [
        "➕ New Thread",
        "✏️",
        "🗑️",
    ]
    return text in control_buttons

