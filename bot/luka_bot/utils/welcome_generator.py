"""
Smart welcome message generator for groups.

Generates permission-aware welcome messages based on bot's actual capabilities.
"""
from luka_bot.models.group_metadata import GroupMetadata
from luka_bot.models.thread import Thread


def generate_smart_welcome_message(
    bot_name: str,
    metadata: GroupMetadata,
    thread: Thread,
    language: str = "en"
) -> str:
    """
    Generate welcome message based on actual bot permissions and group state.
    
    Adapts content based on what bot can actually do:
    - Full admin with all permissions
    - Admin with limited permissions
    - Not admin (member only)
    
    Args:
        bot_name: Bot name from settings
        metadata: GroupMetadata with bot permissions
        thread: Thread configuration
        language: Language code (en/ru)
        
    Returns:
        Formatted welcome message adapted to bot's capabilities
    """
    # Check bot status
    is_admin = metadata.bot_is_admin
    permissions = metadata.bot_admin_permissions
    
    # Full permissions check
    has_full_perms = is_admin and (
        permissions.get("can_delete_messages") and
        permissions.get("can_restrict_members")
    )
    
    if language == "en":
        return _generate_english_welcome(bot_name, metadata, has_full_perms, is_admin, permissions)
    else:  # Russian
        return _generate_russian_welcome(bot_name, metadata, has_full_perms, is_admin, permissions)


def _generate_english_welcome(
    bot_name: str,
    metadata: GroupMetadata,
    has_full_perms: bool,
    is_admin: bool,
    permissions: dict
) -> str:
    """Generate English welcome message."""
    
    # Header
    msg = f"👋 <b>Hi! I'm {bot_name}</b>\n\n"
    msg += f"I've just joined <b>{metadata.group_title}</b>"
    if metadata.group_username:
        msg += f" (@{metadata.group_username})"
    msg += "!\n\n"
    
    # Group info section
    msg += "<b>📊 Group Overview:</b>\n"
    
    # Group type
    if metadata.group_type == "supergroup":
        type_str = "Supergroup"
        if metadata.has_topics:
            type_str += " (Forum Topics)"
        msg += f"• 👥📌 Type: {type_str}\n"
    else:
        msg += f"• 👥 Type: Group\n"
    
    # Group ID
    msg += f"• 🆔 Group ID: <code>{metadata.group_id}</code>\n"
    
    # Member count
    if metadata.total_member_count > 0:
        msg += f"• 👤 Members: {metadata.total_member_count:,}\n"
    
    # Admin count with bot permission status
    if metadata.admin_count > 0:
        msg += f"• 👑 Admins: {metadata.admin_count}"
        # Show bot permissions status inline
        if is_admin:
            if has_full_perms:
                msg += " (Bot: Full permissions ✅)"
            else:
                msg += " (Bot: Limited permissions ⚠️)"
        else:
            msg += " (Bot: Not admin ❌)"
        msg += "\n"
    
    msg += "\n"
    
    # Bot permissions status - CRITICAL SECTION
    if has_full_perms:
        msg += "<b>✅ Setup Complete - Full Access</b>\n\n"
        
        msg += "<b>🛡️ Active Features:</b>\n"
        if permissions.get("can_delete_messages"):
            msg += "• ✅ Auto-delete spam/violations\n"
        if permissions.get("can_restrict_members"):
            msg += "• ✅ Restrict rule breakers\n"
        if permissions.get("can_manage_topics"):
            msg += "• ✅ Manage forum topics\n"
        if permissions.get("can_pin_messages"):
            msg += "• ✅ Pin important messages\n"
        msg += "\n"
        
    elif is_admin:
        msg += "<b>⚠️ Setup Incomplete - Limited Access</b>\n\n"
        msg += "<b>⚠️ Missing Permissions:</b>\n"
        
        if not permissions.get("can_delete_messages"):
            msg += "• ❌ Cannot delete messages (moderation limited)\n"
        if not permissions.get("can_restrict_members"):
            msg += "• ❌ Cannot restrict members\n"
        if not permissions.get("can_manage_topics") and metadata.has_topics:
            msg += "• ❌ Cannot manage topics\n"
        
        msg += "\n<i>💡 Grant full admin rights for best experience</i>\n\n"
        
    else:
        msg += "<b>❌ Limited Mode - Not an Administrator</b>\n\n"
        msg += "Without admin rights, I can only:\n"
        msg += "• Answer questions when mentioned\n"
        msg += "• Index new messages\n"
        msg += "• Search history in DMs\n\n"
        
        if metadata.admin_list:
            first_admin = metadata.admin_list[0]
            admin_name = first_admin.get("username") or first_admin.get("full_name", "admin")
            msg += f"<i>💡 Contact @{admin_name} to make me admin</i>\n\n"
    
    # Description if available
    if metadata.description:
        desc_preview = metadata.description[:150]
        if len(metadata.description) > 150:
            desc_preview += "..."
        msg += f"<b>📝 About this group:</b>\n<i>{desc_preview}</i>\n\n"
    
    # Pinned message if available
    if metadata.pinned_message_text:
        pinned_preview = metadata.pinned_message_text[:80]
        if len(metadata.pinned_message_text) > 80:
            pinned_preview += "..."
        msg += f"📌 <b>Pinned:</b> \"{pinned_preview}\"\n\n"
    
    # Usage instructions
    msg += "<b>👥 For Everyone:</b>\n"
    msg += f"• 💬 Mention me (@{bot_name.replace(' ', '')}) with questions\n"
    msg += "• 🔍 I'll help find info from discussions\n"
    msg += "• 📨 DM me to search this group's history\n\n"
    
    # Admin section
    msg += "<b>👑 For Admins:</b>\n"
    if has_full_perms or is_admin:
        msg += "• 🌐 <b>Language</b> - Change bot language\n"
        msg += "• 📚 <b>Import History</b> - Import past messages\n"
        msg += "• ⚙️ <b>Settings</b> - Full configuration:\n"
        if has_full_perms:
            msg += "  - 🛡️ Moderation (auto-filter spam, toxicity)\n"
            msg += "  - 🚫 Stoplist (block words)\n"
            msg += "  - 🗑️ System messages filter\n"
            msg += "  - 📊 Stats and analytics\n"
        else:
            msg += "  - Limited features (grant full permissions)\n"
    else:
        msg += "• Make me admin to unlock all features\n"
    
    msg += "\n<i>🔒 Admin buttons only work for group administrators</i>"
    
    # Add privacy mode warning if applicable
    from luka_bot.core.config import settings
    if settings.BOT_PRIVACY_MODE_ENABLED and not is_admin:
        msg += """\n
⚠️ <b>Privacy Mode Active</b>
Bot only sees @mentions and commands. KB will only index messages directed to bot.
Make bot admin to index all group messages."""
    
    return msg


def _generate_russian_welcome(
    bot_name: str,
    metadata: GroupMetadata,
    has_full_perms: bool,
    is_admin: bool,
    permissions: dict
) -> str:
    """Generate Russian welcome message."""
    
    # Header
    msg = f"👋 <b>Привет! Я {bot_name}</b>\n\n"
    msg += f"Я только что присоединился к <b>{metadata.group_title}</b>"
    if metadata.group_username:
        msg += f" (@{metadata.group_username})"
    msg += "!\n\n"
    
    # Group info section
    msg += "<b>📊 Обзор группы:</b>\n"
    
    # Group type
    if metadata.group_type == "supergroup":
        type_str = "Супергруппа"
        if metadata.has_topics:
            type_str += " (Forum Topics)"
        msg += f"• 👥📌 Тип: {type_str}\n"
    else:
        msg += f"• 👥 Тип: Группа\n"
    
    # Group ID
    msg += f"• 🆔 ID группы: <code>{metadata.group_id}</code>\n"
    
    # Member count
    if metadata.total_member_count > 0:
        msg += f"• 👤 Участников: {metadata.total_member_count:,}\n"
    
    # Admin count with bot permission status
    if metadata.admin_count > 0:
        msg += f"• 👑 Администраторов: {metadata.admin_count}"
        # Show bot permissions status inline
        if is_admin:
            if has_full_perms:
                msg += " (Бот: Полные права ✅)"
            else:
                msg += " (Бот: Ограниченные права ⚠️)"
        else:
            msg += " (Бот: Не админ ❌)"
        msg += "\n"
    
    msg += "\n"
    
    # Bot permissions status - CRITICAL SECTION
    if has_full_perms:
        msg += "<b>✅ Настройка завершена - Полный доступ</b>\n\n"
        
        msg += "<b>🛡️ Активные функции:</b>\n"
        if permissions.get("can_delete_messages"):
            msg += "• ✅ Авто-удаление спама/нарушений\n"
        if permissions.get("can_restrict_members"):
            msg += "• ✅ Ограничение нарушителей\n"
        if permissions.get("can_manage_topics"):
            msg += "• ✅ Управление темами форума\n"
        if permissions.get("can_pin_messages"):
            msg += "• ✅ Закрепление важных сообщений\n"
        msg += "\n"
        
    elif is_admin:
        msg += "<b>⚠️ Настройка неполная - Ограниченный доступ</b>\n\n"
        msg += "<b>⚠️ Отсутствующие разрешения:</b>\n"
        
        if not permissions.get("can_delete_messages"):
            msg += "• ❌ Не могу удалять сообщения (модерация ограничена)\n"
        if not permissions.get("can_restrict_members"):
            msg += "• ❌ Не могу ограничивать участников\n"
        if not permissions.get("can_manage_topics") and metadata.has_topics:
            msg += "• ❌ Не могу управлять темами\n"
        
        msg += "\n<i>💡 Предоставьте полные права администратора для лучшей работы</i>\n\n"
        
    else:
        msg += "<b>❌ Ограниченный режим - Не администратор</b>\n\n"
        msg += "Без прав администратора я могу только:\n"
        msg += "• Отвечать на вопросы при упоминании\n"
        msg += "• Индексировать новые сообщения\n"
        msg += "• Искать по истории в ЛС\n\n"
        
        if metadata.admin_list:
            first_admin = metadata.admin_list[0]
            admin_name = first_admin.get("username") or first_admin.get("full_name", "админ")
            msg += f"<i>💡 Свяжитесь с @{admin_name}, чтобы сделать меня админом</i>\n\n"
    
    # Description if available
    if metadata.description:
        desc_preview = metadata.description[:150]
        if len(metadata.description) > 150:
            desc_preview += "..."
        msg += f"<b>📝 О группе:</b>\n<i>{desc_preview}</i>\n\n"
    
    # Pinned message if available
    if metadata.pinned_message_text:
        pinned_preview = metadata.pinned_message_text[:80]
        if len(metadata.pinned_message_text) > 80:
            pinned_preview += "..."
        msg += f"📌 <b>Закреплено:</b> \"{pinned_preview}\"\n\n"
    
    # Usage instructions
    msg += "<b>👥 Для всех:</b>\n"
    msg += f"• 💬 Упомяните меня (@{bot_name.replace(' ', '')}) с вопросами\n"
    msg += "• 🔍 Я помогу найти информацию из обсуждений\n"
    msg += "• 📨 Напишите мне в ЛС для поиска по истории группы\n\n"
    
    # Admin section
    msg += "<b>👑 Для администраторов:</b>\n"
    if has_full_perms or is_admin:
        msg += "• 🌐 <b>Язык</b> - Изменить язык бота\n"
        msg += "• 📚 <b>Импорт истории</b> - Импорт старых сообщений\n"
        msg += "• ⚙️ <b>Настройки</b> - Полная конфигурация:\n"
        if has_full_perms:
            msg += "  - 🛡️ Модерация (авто-фильтр спама, токсичности)\n"
            msg += "  - 🚫 Стоп-лист (блокировка слов)\n"
            msg += "  - 🗑️ Фильтр системных сообщений\n"
            msg += "  - 📊 Статистика и аналитика\n"
        else:
            msg += "  - Ограниченные функции (предоставьте полные разрешения)\n"
    else:
        msg += "• Сделайте меня админом, чтобы разблокировать все функции\n"
    
    msg += "\n<i>🔒 Кнопки админа работают только для администраторов группы</i>"
    
    # Add privacy mode warning if applicable
    from luka_bot.core.config import settings
    if settings.BOT_PRIVACY_MODE_ENABLED and not is_admin:
        msg += """\n
⚠️ <b>Режим приватности активен</b>
Бот видит только @упоминания и команды. БЗ индексирует только сообщения к боту.
Сделайте бота админом для индексации всех сообщений."""
    
    return msg

