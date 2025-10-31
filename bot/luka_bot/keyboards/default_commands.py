"""
Default bot commands for luka_bot.

Sets up the command menu visible in Telegram with different scopes:
- Private chats: Full command set
- Groups: Discovery commands (/help, /stats)
- Group admins: Additional management commands (/settings, /import)
"""
from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllChatAdministrators,
)
from loguru import logger

from luka_bot.core.config import settings


# Private chat commands (full feature set for DMs)
private_commands_by_language = {
    "en": {
        "start": "Main menu with Quick Actions",
        "chat": "Manage conversation threads",
        "search": "Search knowledge bases",
        "tasks": "View and manage tasks (GTD)",
        "groups": "Manage Telegram groups",
        "profile": "Your profile and settings",
        "reset": "Clear all threads and history",
    },
    "ru": {
        "start": "Меню действий",
        "chat": "Управление чатами",
        "search": "Поиск по базам знаний",
        "tasks": "Задачи и управление (GTD)",
        "groups": "Управление группами",
        "profile": "Ваш профиль и настройки",
        "reset": "Очистить все чаты и историю",
    },
}

# Group commands (limited, discovery-focused for all members)
# Minimal command set - only /help enabled for now
group_commands_by_language = {
    "en": {
        "help": "Learn how to use me",
        # "stats": "Group statistics and usage",  # Disabled - access via DM /groups
        # "reputation": "Check your reputation",  # Disabled - coming soon
    },
    "ru": {
        "help": "Как пользоваться ботом",
        # "stats": "Статистика группы",  # Отключено - доступ через ЛС /groups
        # "reputation": "Проверить свою репутацию",  # Отключено - скоро
    },
}

# Group admin commands (includes management features)
# Admin-focused command set - management commands only
admin_commands_by_language = {
    "en": {
        "help": "Learn how to use me",
        # "stats": "Group statistics and usage",  # Disabled - access via DM /groups
        "settings": "Configure bot for this group",
        "import": "Import group history (coming soon)",
        "reset": "Reset bot data for this group",
    },
    "ru": {
        "help": "Как пользоваться ботом",
        # "stats": "Статистика группы",  # Отключено - доступ через ЛС /groups
        "settings": "Настроить бота для группы",
        "import": "Импорт истории группы (скоро)",
        "reset": "Сбросить данные бота для группы",
    },
}


async def set_default_commands(bot: Bot) -> None:
    """
    Set default bot commands for different scopes.
    
    This makes commands visible in the Telegram UI when user types "/".
    Different command sets for:
    - Private chats (all features)
    - Groups (discovery: help, stats)
    - Group admins (+ management: settings, import, reset)
    """
    try:
        # Remove old commands first (default scope)
        await bot.delete_my_commands(scope=BotCommandScopeDefault())
        logger.info("🗑️  Cleared default scope commands")
        
        for language_code in ["en", "ru"]:
            # 1. Private chat commands (full feature set) - filtered by LUKA_COMMANDS_ENABLED
            enabled_commands = settings.LUKA_COMMANDS_ENABLED
            private_command_list = [
                BotCommand(command=cmd, description=desc)
                for cmd, desc in private_commands_by_language[language_code].items()
                if cmd in enabled_commands
            ]
            await bot.set_my_commands(
                private_command_list,
                scope=BotCommandScopeAllPrivateChats(),
                language_code=language_code,
            )
            logger.info(f"✅ Private [{language_code}]: {len(private_command_list)} commands - {[cmd for cmd in private_commands_by_language[language_code].keys() if cmd in enabled_commands]}")
            
            # 2. Group commands (limited, discovery-focused)
            group_command_list = [
                BotCommand(command=cmd, description=desc)
                for cmd, desc in group_commands_by_language[language_code].items()
            ]
            await bot.set_my_commands(
                group_command_list,
                scope=BotCommandScopeAllGroupChats(),
                language_code=language_code,
            )
            logger.info(f"✅ Groups [{language_code}]: {len(group_command_list)} commands - {list(group_commands_by_language[language_code].keys())}")
            
            # 3. Group admin commands (includes management)
            admin_command_list = [
                BotCommand(command=cmd, description=desc)
                for cmd, desc in admin_commands_by_language[language_code].items()
            ]
            await bot.set_my_commands(
                admin_command_list,
                scope=BotCommandScopeAllChatAdministrators(),
                language_code=language_code,
            )
            logger.info(f"✅ Admins [{language_code}]: {len(admin_command_list)} commands - {list(admin_commands_by_language[language_code].keys())}")
        
        logger.info("✅ All command scopes configured successfully")
        logger.info("📋 Note: Telegram may take a few minutes to update command list in groups")
        
    except Exception as e:
        logger.error(f"❌ Failed to set default commands: {e}", exc_info=True)


async def remove_default_commands(bot: Bot) -> None:
    """Remove all default bot commands for all scopes and languages."""
    try:
        # Remove default scope
        await bot.delete_my_commands(scope=BotCommandScopeDefault())
        
        # Remove language-specific scopes for all command types
        for language_code in ["en", "ru"]:
            # Private chats
            await bot.delete_my_commands(
                scope=BotCommandScopeAllPrivateChats(),
                language_code=language_code,
            )
            # Groups
            await bot.delete_my_commands(
                scope=BotCommandScopeAllGroupChats(),
                language_code=language_code,
            )
            # Group admins
            await bot.delete_my_commands(
                scope=BotCommandScopeAllChatAdministrators(),
                language_code=language_code,
            )
        
        logger.info("✅ Removed commands for all scopes and languages")
    except Exception as e:
        logger.error(f"❌ Failed to remove default commands: {e}")

