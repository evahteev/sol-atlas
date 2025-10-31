"""
Group admin keyboards and controls.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from luka_bot.utils.i18n_helper import _


def _format_toggle_text(
    label_key: str,
    enabled: bool,
    language: str,
    icon_enabled: str,
    icon_disabled: str,
    show_status: bool = True
) -> str:
    """
    Build a consistently formatted toggle label with icon + status badge.
    """
    label = _(label_key, language)
    # Strip any leading icon already present in translation for consistent formatting
    parts = label.split(" ", 1)
    if len(parts) == 2 and parts[0] and not parts[0][0].isalnum():
        base_label = parts[1]
    else:
        base_label = label
    icon = icon_enabled if enabled else icon_disabled
    status = "✅" if enabled else "❌"
    if show_status:
        return f"{status} {icon} {base_label}"
    return f"{icon} {base_label}"


def create_group_admin_menu(
    group_id: int, 
    group_title: str = None,
    moderation_enabled: bool = True,
    stoplist_count: int = 0,
    current_language: str = "en",
    silent_mode: bool = False,
    ai_assistant_enabled: bool = True,
    kb_indexation_enabled: bool = True,
    moderate_admins_enabled: bool = False,
    is_user_defaults: bool = False
) -> InlineKeyboardMarkup:
    """
    Create hierarchical admin menu - main settings level.
    Used for BOTH group settings AND user defaults (same menu, different data source).
    
    New structure:
    - Row 1: Silent Mode toggle | AI Assistant submenu →
    - Row 2: Moderation submenu → | Import History (groups) / Moderation (user defaults)
    - Row 3: Language selection (both groups and user defaults)
    - Row 4: Link All Members (groups only)
    - Row 5: Delete Group (groups only)
    - Row 6: Back | Reset to Defaults
    
    Args:
        group_id: Group chat ID (or user_id for defaults)
        group_title: Optional group title for display
        moderation_enabled: Current moderation status
        stoplist_count: Number of words in stoplist
        current_language: Current group language (en/ru)
        silent_mode: Whether silent mode is enabled
        ai_assistant_enabled: Whether AI assistant is enabled
        kb_indexation_enabled: Whether KB indexation is enabled
        moderate_admins_enabled: Whether to moderate admins
        is_user_defaults: If True, hides group-specific items (import, delete, refresh)
        
    Returns:
        InlineKeyboardMarkup with hierarchical navigation
    """
    # Build button rows dynamically
    buttons = []
    
    # Row 1: Silent Mode toggle | AI Assistant submenu
    buttons.append([
        InlineKeyboardButton(
            text=_format_toggle_text(
                "group_settings.silent_mode",
                silent_mode,
                current_language,
                icon_enabled="🔕",
                icon_disabled="🔔",
                show_status=False
            ),
            callback_data=f"group_toggle_silent:{group_id}"
        ),
        InlineKeyboardButton(
            text=_('group.btn.ai_assistant', current_language),
            callback_data=f"ai_assistant_menu:{group_id}"
        )
    ])
    
    # Row 2: Moderation submenu | Import History
    if not is_user_defaults:
        # Groups: Show Import History
        buttons.append([
            InlineKeyboardButton(
                text=_('group.btn.moderation_submenu', current_language),
                callback_data=f"moderation_menu:{group_id}"
            ),
            InlineKeyboardButton(
                text=_('group.btn.import_history', current_language),
                callback_data=f"group_import:{group_id}"
            )
        ])
    else:
        # User defaults: Just Moderation submenu, full width
        buttons.append([
            InlineKeyboardButton(
                text=_('group.btn.moderation_submenu', current_language),
                callback_data=f"moderation_menu:{group_id}"
            )
        ])
    
    # Row 3: Language selection (for both groups and user defaults)
    lang_display = "🇬🇧 English" if current_language == "en" else "🇷🇺 Русский"
    lang_button_text = f"🌐 {_('group.btn.language', current_language)}: {lang_display}"
    buttons.append([
        InlineKeyboardButton(
            text=lang_button_text,
            callback_data=f"group_lang_menu:{group_id}"
        )
    ])
    
    # Group-specific buttons (hidden for user defaults)
    if not is_user_defaults:
        # Row 4: Link All Members (Backfill)
        backfill_text = "🔗 Link All Members" if current_language == "en" else "🔗 Связать участников"
        buttons.append([
            InlineKeyboardButton(
                text=backfill_text,
                callback_data=f"group_backfill:{group_id}"
            )
        ])
        
        # Row 5: Delete Group
        buttons.append([
            InlineKeyboardButton(
                text=_('group_settings.delete_group', current_language),
                callback_data=f"group_delete_confirm:{group_id}"
            )
        ])
    
    # Row 6: Back | Reset to Defaults
    back_reset_row = [
        InlineKeyboardButton(
            text=_('common.back', current_language),
            callback_data=f"close_menu:{group_id}"
        )
    ]
    
    # Add Reset button
    if is_user_defaults:
        # User defaults: Reset to factory/app defaults
        back_reset_row.append(
            InlineKeyboardButton(
                text=_('user_group_defaults.reset_button', current_language),
                callback_data=f"user_defaults_reset_confirm:{group_id}"
            )
        )
    else:
        # Groups: Reset to user's default settings
        back_reset_row.append(
            InlineKeyboardButton(
                text=_('group.btn.reset_to_defaults', current_language),
                callback_data=f"group_reset_to_user_defaults:{group_id}"
            )
        )
    
    buttons.append(back_reset_row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_system_messages_menu(group_id: int, enabled_types: list[str], language: str = "en") -> InlineKeyboardMarkup:
    """
    Create system messages filter menu with checkmarks in button names.
    
    Args:
        group_id: Group chat ID
        enabled_types: List of enabled message type groups
        language: Language code for translations
        
    Returns:
        InlineKeyboardMarkup with toggle buttons
    """
    # Map internal types to i18n keys
    type_groups = {
        "joined": {
            "i18n_key": "group.sys_msg.user_joined_left",
            "types": ["new_chat_members", "left_chat_member"]
        },
        "title": {
            "i18n_key": "group.sys_msg.name_title_changes",
            "types": ["new_chat_title"]
        },
        "pinned": {
            "i18n_key": "group.sys_msg.pinned_messages",
            "types": ["pinned_message"]
        },
        "voice": {
            "i18n_key": "group.sys_msg.voice_chat_events",
            "types": ["voice_chat_started", "voice_chat_ended", "voice_chat_scheduled"]
        },
        "photo": {
            "i18n_key": "group.sys_msg.group_photo_changed",
            "types": ["new_chat_photo", "delete_chat_photo"]
        }
    }
    
    buttons = []
    for key, config in type_groups.items():
        # enabled_types contains types we hide; invert for UX (✅ show, ❌ hide)
        is_filtered = any(t in enabled_types for t in config["types"])
        icon = "❌" if is_filtered else "✅"
        
        label = _(config['i18n_key'], language)
        
        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {label}",
                callback_data=f"sys_msg_toggle:{key}:{group_id}"
            )
        ])
    
    # Add back button - return to Moderation menu
    buttons.append([
        InlineKeyboardButton(
            text=_('common.back', language),
            callback_data=f"moderation_menu:{group_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_content_types_menu(group_id: int, settings, language: str = "en") -> InlineKeyboardMarkup:
    """
    Create content types filter menu with checkmarks.
    
    Args:
        group_id: Group chat ID (or user_id for defaults)
        settings: GroupSettings object with delete_* flags
        language: Language code for translations
        
    Returns:
        InlineKeyboardMarkup with toggle buttons
    """
    # Content type configurations
    content_types = [
        {
            "key": "delete_links",
            "i18n_key": "user_group_defaults.content_links",
            "attr": "delete_links"
        },
        {
            "key": "delete_images",
            "i18n_key": "user_group_defaults.content_images",
            "attr": "delete_images"
        },
        {
            "key": "delete_videos",
            "i18n_key": "user_group_defaults.content_videos",
            "attr": "delete_videos"
        },
        {
            "key": "delete_stickers",
            "i18n_key": "user_group_defaults.content_stickers",
            "attr": "delete_stickers"
        },
        {
            "key": "delete_forwarded",
            "i18n_key": "user_group_defaults.content_forwarded",
            "attr": "delete_forwarded"
        }
    ]
    
    buttons = []
    for content_type in content_types:
        is_filtered = getattr(settings, content_type["attr"], False)
        checkmark = "❌" if is_filtered else "✅"
        
        label = _(content_type['i18n_key'], language)
        
        buttons.append([
            InlineKeyboardButton(
                text=f"{checkmark} {label}",
                callback_data=f"content_type_toggle:{content_type['key']}:{group_id}"
            )
        ])
    
    # Add back button - return to Moderation menu
    buttons.append([
        InlineKeyboardButton(
            text=_('common.back', language),
            callback_data=f"moderation_menu:{group_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_group_settings_menu(group_id: int, language: str = "en") -> InlineKeyboardMarkup:
    """
    Create group settings menu.
    
    Args:
        group_id: Group chat ID
        language: Language code for translations
        
    Returns:
        InlineKeyboardMarkup with settings options
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_('group.settings.notification_settings', language),
                callback_data=f"group_notif:{group_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=_('group.settings.kb_indexing_rules', language),
                callback_data=f"group_kb_rules:{group_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=_('group.settings.member_access', language),
                callback_data=f"group_access:{group_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=_('common.back', language),
                callback_data=f"group_admin_menu:{group_id}"
            )
        ]
    ])


def create_ai_assistant_menu(
    group_id: int,
    ai_assistant_enabled: bool = True,
    kb_indexation_enabled: bool = True,
    language: str = "en"
) -> InlineKeyboardMarkup:
    """
    Create AI Assistant submenu with toggle buttons.
    
    Args:
        group_id: Group chat ID
        ai_assistant_enabled: Current AI assistant status
        kb_indexation_enabled: Current KB indexation status
        language: Language code for translations
        
    Returns:
        InlineKeyboardMarkup with AI Assistant controls
    """
    buttons = []
    
    # Row 1: AI Assistant toggle
    buttons.append([
        InlineKeyboardButton(
            text=_format_toggle_text(
                "group_settings.ai_assistant",
                ai_assistant_enabled,
                language,
                icon_enabled="🤖",
                icon_disabled="🤖"
            ),
            callback_data=f"group_toggle_ai:{group_id}"
        )
    ])
    
    # Row 2: Knowledge Base toggle
    buttons.append([
        InlineKeyboardButton(
            text=_format_toggle_text(
                "group_settings.kb_indexation",
                kb_indexation_enabled,
                language,
                icon_enabled="📚",
                icon_disabled="📚"
            ),
            callback_data=f"group_toggle_kb:{group_id}"
        )
    ])
    
    # Row 3: Bot Instructions
    buttons.append([
        InlineKeyboardButton(
            text=_('group.btn.bot_instructions', language),
            callback_data=f"moderation_prompt_menu:{group_id}"
        )
    ])
    
    # Row 4: Back
    buttons.append([
        InlineKeyboardButton(
            text=_('common.back', language),
            callback_data=f"group_admin_menu:{group_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_moderation_menu(
    group_id: int,
    moderation_enabled: bool = True,
    moderate_admins_enabled: bool = False,
    language: str = "en"
) -> InlineKeyboardMarkup:
    """
    Create Moderation submenu with toggle buttons and links to other submenus.
    
    Args:
        group_id: Group chat ID
        moderation_enabled: Current moderation status
        moderate_admins_enabled: Current moderate admins status
        language: Language code for translations
        
    Returns:
        InlineKeyboardMarkup with Moderation controls
    """
    buttons = []
    
    # Row 1: Moderation toggle
    buttons.append([
        InlineKeyboardButton(
            text=_format_toggle_text(
                "group.btn.moderation",
                moderation_enabled,
                language,
                icon_enabled="🛡️",
                icon_disabled="🚫"
            ),
            callback_data=f"group_toggle_mod:{group_id}"
        )
    ])
    
    # Row 2: Moderate Admins toggle
    buttons.append([
        InlineKeyboardButton(
            text=_format_toggle_text(
                "group_settings.moderate_admins",
                moderate_admins_enabled,
                language,
                icon_enabled="👑",
                icon_disabled="👤"
            ),
            callback_data=f"group_toggle_mod_admins:{group_id}"
        )
    ])
    
    # Row 3: System Messages submenu
    buttons.append([
        InlineKeyboardButton(
            text=_('group.btn.system_messages', language),
            callback_data=f"sys_msg_menu:{group_id}"
        )
    ])
    
    # Row 4: Content Type Filters submenu
    buttons.append([
        InlineKeyboardButton(
            text=_('user_group_defaults.content_types', language),
            callback_data=f"content_types_menu:{group_id}"
        )
    ])
    
    # Row 5: Stoplist submenu
    buttons.append([
        InlineKeyboardButton(
            text=_('group.btn.stoplist', language),
            callback_data=f"group_stoplist_config:{group_id}"
        )
    ])
    
    # Row 6: Back
    buttons.append([
        InlineKeyboardButton(
            text=_('common.back', language),
            callback_data=f"group_admin_menu:{group_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
