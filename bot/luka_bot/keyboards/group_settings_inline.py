"""
Emoji-based inline keyboards for group settings (admin-only).

All buttons use emojis to avoid i18n complexity.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_group_settings_inline(group_id: int, current_language: str = "en", moderation_enabled: bool = False) -> InlineKeyboardMarkup:
    """
    Create emoji-based inline settings keyboard for group welcome message.
    
    Args:
        group_id: Group chat ID
        current_language: Current group language (en/ru)
        moderation_enabled: Whether moderation is currently enabled
        
    Returns:
        InlineKeyboardMarkup with admin settings
    """
    # Translate button texts
    if current_language == "en":
        lang_text = "🌐 Language"
        settings_text = "⚙️ Settings"
        import_text = "📚 Import History"
        backfill_text = "🔗 Link All Members"
        close_text = "❌ Close"
    else:  # Russian
        lang_text = "🌐 Язык"
        settings_text = "⚙️ Настройки"
        import_text = "📚 Импорт истории"
        backfill_text = "🔗 Связать участников"
        close_text = "❌ Закрыть"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        # Row 1: Language and Import
        [
            InlineKeyboardButton(
                text=lang_text,
                callback_data=f"group_lang_menu:{group_id}"
            ),
            InlineKeyboardButton(
                text=import_text,
                callback_data=f"group_import_kb:{group_id}"
            ),
        ],
        # Row 2: Backfill Links
        [
            InlineKeyboardButton(
                text=backfill_text,
                callback_data=f"group_backfill:{group_id}"
            ),
        ],
        # Row 3: Settings and Close
        [
            InlineKeyboardButton(
                text=settings_text,
                callback_data=f"group_settings_menu:{group_id}"
            ),
            InlineKeyboardButton(
                text=close_text,
                callback_data=f"group_welcome_close:{group_id}"
            ),
        ],
    ])


def create_language_selection_menu(group_id: int, current_language: str) -> InlineKeyboardMarkup:
    """
    Create language selection submenu.
    
    Args:
        group_id: Group chat ID
        current_language: Current group language (en/ru)
        
    Returns:
        InlineKeyboardMarkup with language options
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"🇬🇧 English {'✅' if current_language == 'en' else ''}",
                callback_data=f"group_set_lang:{group_id}:en"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"🇷🇺 Русский {'✅' if current_language == 'ru' else ''}",
                callback_data=f"group_set_lang:{group_id}:ru"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=f"group_lang_back:{group_id}"
            ),
        ],
    ])


def create_language_help_text(language: str) -> str:
    """
    Create help text for language buttons.
    
    Args:
        language: Current language (en/ru)
        
    Returns:
        Help text string
    """
    if language == "en":
        return """🌍 <b>Language Settings</b>

Current: 🇬🇧 English

Language affects:
• LLM responses in this group
• Welcome messages
• Bot interactions

<i>🔒 Admin-only setting</i>"""
    else:
        return """🌍 <b>Настройки языка</b>

Текущий: 🇷🇺 Русский

Язык влияет на:
• Ответы LLM в этой группе
• Приветственные сообщения
• Взаимодействие с ботом

<i>🔒 Настройка только для администраторов</i>"""


def create_button_legend(language: str) -> str:
    """
    Create legend explaining what each emoji button does.
    
    Args:
        language: Current language (en/ru)
        
    Returns:
        Legend text
    """
    if language == "en":
        return """

🔽 <b>Button Guide (Admin Controls):</b>
🌐 Language - Change group language
🛡️ Moderation - Toggle content moderation
⚙️ Settings - Advanced configuration (opens in DM)

<i>🔒 These controls are admin-only. Non-admins will see "Admin only" when clicking.</i>"""
    else:
        return """

🔽 <b>Описание кнопок (только для админов):</b>
🌐 Language - Изменить язык группы
🛡️ Moderation - Модерация контента
⚙️ Settings - Дополнительные настройки (открывается в ЛС)

<i>🔒 Эти кнопки только для администраторов. Остальные увидят "Admin only" при нажатии.</i>"""


def get_welcome_message_with_settings(
    bot_name: str,
    group_title: str,
    group_id: int,
    kb_index: str,
    added_by: str,
    language: str = "en",
    thread_id: int = None
) -> str:
    """
    Generate simplified, user-focused welcome message.
    
    Args:
        bot_name: Bot name from settings
        group_title: Group title
        group_id: Group ID
        kb_index: KB index
        added_by: User who added bot
        language: Current language
        thread_id: Optional thread/topic ID
        
    Returns:
        Formatted welcome message
    """
    if language == "en":
        msg = f"""👋 <b>Hi! I'm {bot_name}</b>

I've just joined <b>{group_title}</b> and I'm ready to help!

<b>👥 For Everyone:</b>
• 💬 Mention me (@{bot_name.replace(' ', '')}) with your questions
• 🔍 I'll help find information from past discussions
• 📨 DM me to search this group's history

<b>👑 For Admins:</b>
• 🌐 <b>Language</b> - Change bot language
• 📚 <b>Import History</b> - Import past messages (coming soon)
• ⚙️ <b>Settings</b> - Full configuration (opens in DM)
  - 🛡️ Moderation (auto-filter spam, toxicity, violations)
  - 🚫 Stoplist (block specific words)
  - 🗑️ System messages (hide joins/leaves/pins)
  - 📊 Stats and analytics

<i>🔒 Admin buttons only work for group administrators</i>"""
        
    else:  # Russian
        msg = f"""👋 <b>Привет! Я {bot_name}</b>

Я только что присоединился к <b>{group_title}</b> и готов помочь!

<b>👥 Для всех:</b>
• 💬 Упомяните меня (@{bot_name.replace(' ', '')}) с вопросами
• 🔍 Я помогу найти информацию из прошлых обсуждений
• 📨 Напишите мне в ЛС для поиска по истории группы

<b>👑 Для администраторов:</b>
• 🌐 <b>Язык</b> - Изменить язык бота
• 📚 <b>Импорт истории</b> - Импорт старых сообщений (скоро)
• ⚙️ <b>Настройки</b> - Полная конфигурация (открывается в ЛС)
  - 🛡️ Модерация (авто-фильтр спама, токсичности, нарушений)
  - 🚫 Стоп-лист (блокировка определённых слов)
  - 🗑️ Системные сообщения (скрыть входы/выходы/закрепы)
  - 📊 Статистика и аналитика

<i>🔒 Кнопки админа работают только для администраторов группы</i>"""
    
    return msg

