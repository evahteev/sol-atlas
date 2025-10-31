"""
Privacy Mode Warning Messages.

Generates warnings when bot's Privacy Mode limits functionality.
"""
from luka_bot.core.config import settings
from luka_bot.models.group_metadata import GroupMetadata
from typing import Optional


async def get_privacy_mode_warning(
    language: str = "en",
    include_kb_note: bool = True
) -> Optional[str]:
    """
    Get privacy mode warning if enabled.
    
    Args:
        language: Language code ("en" or "ru")
        include_kb_note: Include KB indexing note
    
    Returns:
        Warning text if privacy mode is ON, None if OFF
    """
    if not settings.BOT_PRIVACY_MODE_ENABLED:
        return None  # Privacy OFF, no warning needed
    
    # Privacy Mode is ON - generate warning
    if language == "ru":
        warning = """⚠️ <b>Режим приватности включён</b>

Бот видит только:
• Сообщения с @упоминанием
• Ответы на сообщения бота
• Команды (/команда)

❌ Бот НЕ видит обычные сообщения группы."""
        
        if include_kb_note:
            warning += """

📚 База знаний:
• Индексируются только сообщения с @упоминанием
• Обычные сообщения НЕ индексируются

💡 Чтобы индексировать все сообщения:
Сделайте бота администратором группы"""
    else:
        warning = """⚠️ <b>Privacy Mode is Enabled</b>

Bot can only see:
• Messages with @mentions
• Replies to bot's messages
• Commands (/command)

❌ Bot CANNOT see regular group messages."""
        
        if include_kb_note:
            warning += """

📚 Knowledge Base Impact:
• Only @mention messages are indexed
• Regular messages are NOT indexed

💡 To index all messages:
Make bot a group administrator"""
    
    return warning


async def should_show_privacy_warning(
    metadata: Optional[GroupMetadata]
) -> bool:
    """
    Check if privacy warning should be shown.
    
    Shows warning if:
    - Privacy mode is ON
    - Bot is NOT admin (admin overrides privacy mode)
    
    Args:
        metadata: Group metadata with bot admin status
    
    Returns:
        True if warning should be shown
    """
    if not settings.BOT_PRIVACY_MODE_ENABLED:
        return False  # Privacy OFF, no warning
    
    # If bot is admin, privacy mode doesn't limit functionality
    if metadata and metadata.bot_is_admin:
        return False  # Admin overrides privacy mode
    
    return True  # Privacy ON + Bot not admin = Show warning


async def get_privacy_mode_note(
    language: str = "en",
    context: str = "general"
) -> Optional[str]:
    """
    Get short privacy mode note for specific contexts.
    
    Args:
        language: Language code
        context: Context where note is shown ("kb", "stats", "moderation")
    
    Returns:
        Short note text if privacy mode is ON, None if OFF
    """
    if not settings.BOT_PRIVACY_MODE_ENABLED:
        return None
    
    notes = {
        "kb": {
            "en": "⚠️ <b>Note:</b> Privacy Mode ON - only @mention messages are indexed.",
            "ru": "⚠️ <b>Примечание:</b> Режим приватности включён - индексируются только @упоминания."
        },
        "stats": {
            "en": "⚠️ <b>Note:</b> Privacy Mode ON - stats reflect only @mention messages.",
            "ru": "⚠️ <b>Примечание:</b> Режим приватности включён - статистика учитывает только @упоминания."
        },
        "moderation": {
            "en": "⚠️ <b>Note:</b> Privacy Mode ON - bot can only moderate @mention messages.",
            "ru": "⚠️ <b>Примечание:</b> Режим приватности включён - бот модерирует только @упоминания."
        },
        "general": {
            "en": "⚠️ Privacy Mode ON - limited message visibility",
            "ru": "⚠️ Режим приватности включён - ограниченная видимость"
        }
    }
    
    return notes.get(context, notes["general"]).get(language, notes[context]["en"])

