"""
Reply keyboards for different bot modes.

Each command (mode) has its own distinct reply keyboard:
- /start: Actions hub navigation
- /chat: Thread management (existing in threads_menu.py)
- /tasks: GTD task categories
- /profile: Simple back button
- /agents: Agent management (Phase 6)
- /stats: Statistics (Phase 7)
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from luka_bot.utils.i18n_helper import _


def get_start_mode_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Reply keyboard for /start command with section header - Main navigation hub.
    
    Layout:
    [🏠 Start] [❌]
    [💬 Chat] [📋 Tasks] [👤 Profile]
    
    Args:
        lang: Language code (en/ru)
    
    Returns:
        ReplyKeyboardMarkup with section header and 3-button navigation
    """
    keyboard = [
        # FIX 43: Section header
        [
            KeyboardButton(text=_("section.start", lang)),
            KeyboardButton(text="❌")
        ],
        [
            KeyboardButton(text=_("keyboard.btn_chat", lang)),
            KeyboardButton(text=_("keyboard.btn_tasks", lang)),
            KeyboardButton(text=_("keyboard.btn_profile", lang))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=_("keyboard.placeholder_start", lang)
    )


def get_tasks_mode_keyboard(lang: str = "en", counts: dict = None) -> ReplyKeyboardMarkup:
    """
    Reply keyboard for /tasks command with section header - GTD task categories.
    
    Layout:
    [📋 Tasks] [❌]
    [➕ New Task]
    [📥 Inbox (3)] [⏭️ Next (5)]
    [⏸️ Waiting (1)] [📅 Scheduled (2)]
    [💭 Someday (0)]
    
    Args:
        lang: Language code (en/ru)
        counts: Task counts per category (dict with keys: inbox, next, waiting, scheduled, someday)
    
    Returns:
        ReplyKeyboardMarkup with section header and GTD categories
    """
    counts = counts or {"inbox": 0, "next": 0, "waiting": 0, "scheduled": 0, "someday": 0}
    
    keyboard = [
        # FIX 43: Section header
        [
            KeyboardButton(text=_("section.tasks", lang)),
            KeyboardButton(text="❌")
        ],
        [
            KeyboardButton(text=_("tasks.btn_new_task", lang))
        ],
        [
            KeyboardButton(text=_("tasks.btn_inbox", lang, count=counts.get("inbox", 0))),
            KeyboardButton(text=_("tasks.btn_next", lang, count=counts.get("next", 0)))
        ],
        [
            KeyboardButton(text=_("tasks.btn_waiting", lang, count=counts.get("waiting", 0))),
            KeyboardButton(text=_("tasks.btn_scheduled", lang, count=counts.get("scheduled", 0)))
        ],
        [
            KeyboardButton(text=_("tasks.btn_someday", lang, count=counts.get("someday", 0)))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=_("keyboard.placeholder_tasks", lang)
    )


def get_profile_mode_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Reply keyboard for /profile command with section header.
    
    Layout:
    [👤 Profile] [❌]
    [◀️ Back to Start]
    
    Args:
        lang: Language code (en/ru)
    
    Returns:
        ReplyKeyboardMarkup with section header and back button
    """
    keyboard = [
        # FIX 43: Section header
        [
            KeyboardButton(text=_("section.profile", lang)),
            KeyboardButton(text="❌")
        ],
        [KeyboardButton(text=_("keyboard.btn_back_start", lang))]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=_("keyboard.placeholder_profile", lang)
    )


def get_groups_mode_keyboard(lang: str = "en", group_count: int = 0) -> ReplyKeyboardMarkup:
    """
    Reply keyboard for /groups command with section header - Group management (Phase 6).
    
    Layout:
    [👥 Groups] [❌]
    [➕ Add Group]
    [📋 My Groups (3)] [📥 Import History (CS)]
    
    Args:
        lang: Language code (en/ru)
        group_count: Number of linked groups
    
    Returns:
        ReplyKeyboardMarkup with section header for group management
    """
    keyboard = [
        # FIX 43: Section header
        [
            KeyboardButton(text=_("section.groups", lang)),
            KeyboardButton(text="❌")
        ],
        [
            KeyboardButton(text=_("groups.btn_add_group", lang))
        ],
        [
            KeyboardButton(text=_("groups.btn_my_groups", lang, count=group_count)),
            KeyboardButton(text=_("groups.btn_import_history", lang))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=_("keyboard.placeholder_groups", lang)
    )


def get_stats_mode_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Reply keyboard for /stats command - Statistics view (Phase 7).
    
    Layout:
    [❌]
    [◀️ Back]
    
    Args:
        lang: Language code (en/ru)
    
    Returns:
        ReplyKeyboardMarkup with back button
    """
    keyboard = [
        [KeyboardButton(text="❌")],
        [KeyboardButton(text=_("keyboard.btn_back", lang))]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=_("keyboard.placeholder_stats", lang)
    )


# Export all keyboard factories
__all__ = [
    'get_start_mode_keyboard',
    'get_tasks_mode_keyboard',
    'get_profile_mode_keyboard',
    'get_agents_mode_keyboard',
    'get_stats_mode_keyboard',
]

