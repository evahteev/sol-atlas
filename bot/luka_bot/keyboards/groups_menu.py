"""
Group management reply keyboard - Similar to threads_menu.py but for groups.

Always-visible keyboard showing group list and controls.
"""
from typing import List, Optional
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from loguru import logger

from luka_bot.models.group_link import GroupLink
from luka_bot.utils.i18n_helper import _

# Active group indicator emoji
ACTIVE_GROUP_INDICATOR = "💬"


async def _resolve_group_name(group_id: int) -> str:
    """
    Resolve group name from multiple sources with fallbacks.
    
    Priority:
    1. Thread name (if exists)
    2. Cached group metadata (GroupService.get_cached_group_metadata)
    3. Fallback to short ID format
    
    Returns name truncated to 12 chars for button display.
    """
    # 1. Try thread name first
    try:
        from luka_bot.services.thread_service import get_thread_service
        thread_service = get_thread_service()
        thread = await thread_service.get_group_thread(group_id)
        
        if thread and thread.name:
            return thread.name[:12]
    except Exception as e:
        logger.debug(f"Could not get thread for group {group_id}: {e}")
    
    # 2. Try cached group metadata
    try:
        from luka_bot.services.group_service import get_group_service
        group_service = await get_group_service()
        metadata = await group_service.get_cached_group_metadata(group_id)
        
        if metadata and metadata.group_title:
            return metadata.group_title[:12]
    except Exception as e:
        logger.debug(f"Could not get cached metadata for group {group_id}: {e}")
    
    # 3. Generic fallback - but make it more user-friendly
    return f"Group {abs(group_id) % 10000}"[:12]  # Show last 4 digits instead of full ID


async def get_groups_keyboard(
    groups: List[GroupLink],
    current_group_id: Optional[int] = None,
    language: str = "en",
    max_groups: int = 30
) -> ReplyKeyboardMarkup:
    """
    Create reply keyboard with groups list in a grid layout.
    
    Shows section header + new group button, then groups in 3-column grid.
    
    Args:
        groups: List of user's GroupLink instances
        current_group_id: ID of active group (highlighted)
        language: User's language preference (en/ru)
        max_groups: Maximum groups to show
        
    Returns:
        Reply keyboard markup
    """
    buttons = []
    
    # Row 0 - New Group button only
    new_group_text = _('groups.keyboard.btn_new_group', language)
    buttons.append([
        KeyboardButton(text=new_group_text)
    ])
    
    # Show up to max_groups most recent
    display_groups = groups[:max_groups]
    
    # Build group buttons (3 per row)
    current_row = []
    
    for group_link in display_groups:
        # Check if this is the active group
        is_active = group_link.group_id == current_group_id
        
        # Build button text with smart name resolution
        name = await _resolve_group_name(group_link.group_id)
        
        # Get message count for display
        from luka_bot.services.thread_service import get_thread_service
        thread_service = get_thread_service()
        thread = await thread_service.get_group_thread(group_link.group_id)
        message_count = thread.message_count if thread else 0
        
        # Add indicator if current group
        if is_active:
            name = f"{ACTIVE_GROUP_INDICATOR} {name}"
        
        # Optionally add message count (if space permits)
        if message_count > 0 and len(name) < 10:
            name = f"{name} ({message_count})"
        
        # Add to current row
        current_row.append(KeyboardButton(text=name))
        
        # If row is full (3 buttons), add to buttons and start new row
        if len(current_row) == 3:
            buttons.append(current_row)
            current_row = []
        
        logger.debug(f"Group {thread.name if thread else group_link.group_id}: is_active={is_active}, group_id={group_link.group_id}")
    
    # Add remaining groups if any
    if current_row:
        buttons.append(current_row)
    
    # Add "Default Settings" button at the end
    default_settings_text = _('groups.keyboard.btn_default_settings', language)
    buttons.append([KeyboardButton(text=default_settings_text)])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder=_('groups.keyboard.placeholder', language)
    )
    
    logger.info(f"📋 Created groups reply keyboard with {len(display_groups)} groups in grid layout")
    return keyboard


async def get_empty_groups_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    """
    Keyboard when user has no groups yet (empty state).
    
    Shows section header + new group button, and default settings.
    
    Args:
        language: User's language preference (en/ru)
    
    Returns:
        Minimal reply keyboard for empty state
    """
    new_group_text = _('groups.keyboard.btn_new_group', language)
    
    buttons = [
        # New Group button only
        [KeyboardButton(text=new_group_text)],
        # Default Settings button
        [KeyboardButton(text=_('groups.keyboard.btn_default_settings', language))],
    ]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder=_('groups.keyboard.empty_placeholder', language)
    )
    
    logger.info("📋 Created empty groups state keyboard")
    return keyboard


async def is_group_button(text: str, groups: List[GroupLink]) -> Optional[int]:
    """
    Check if button text matches a group.
    
    Uses the same name resolution as get_groups_keyboard() to ensure accurate matching.
    
    Args:
        text: Button text
        groups: List of groups to match against
        
    Returns:
        Group ID if matched, None otherwise
    """
    # Clean the text - remove active indicator and emojis
    clean_text = text.replace(f"{ACTIVE_GROUP_INDICATOR} ", "").strip()
    
    # Also handle other indicators for backwards compatibility
    for emoji in ["▶️", "✅", "🔵", "⭐", "💬", "📌"]:
        clean_text = clean_text.replace(f"{emoji} ", "").strip()
    
    # Remove message count
    if "(" in clean_text:
        clean_text = clean_text.split("(")[0].strip()
    
    # Match by resolving each group's display name and comparing
    for group_link in groups:
        # Use the same name resolution as keyboard display
        resolved_name = await _resolve_group_name(group_link.group_id)
        resolved_name_clean = resolved_name.strip()
        
        # Try exact match
        if clean_text == resolved_name_clean:
            return group_link.group_id
        
        # Try prefix/suffix match
        if clean_text.startswith(resolved_name_clean) or resolved_name_clean.startswith(clean_text):
            return group_link.group_id
        
        # Fallback: Match by group ID in text (last 4 digits)
        group_id_short = abs(group_link.group_id) % 10000
        if str(group_id_short) in text or str(abs(group_link.group_id)) in text:
            return group_link.group_id
    
    return None


def is_control_button(text: str) -> bool:
    """Check if text is a control button (NOT a group button)."""
    # These buttons are NOT group selection buttons
    # Note: ⚙️ and 🗑️ removed from keyboard, but kept here for backwards compatibility
    control_buttons = [
        "⚙️",
        "🗑️",
        "➕ New Group",
        "➕ Новая группа",
        "⚙️ Default Settings",
        "⚙️ Настройки по умолчанию",
    ]
    return text in control_buttons


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove reply keyboard."""
    return ReplyKeyboardRemove()

