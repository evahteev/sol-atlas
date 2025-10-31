"""
luka_bot handlers - Phase 3 with Thread Management + Reply Keyboard.

Phase 3 includes:
- /start: Welcome message
- /reset: Clear all data
- Reply keyboard: Always-visible thread menu (replaces /chats command)
- Streaming DM: Thread-scoped LLM conversations

Future phases will add:
- Phase 4: Camunda workflows & /tasks command
- Phase 5: Tools and KB
- Phase 6: Voice and attachments
"""
from aiogram import Router
from loguru import logger

from luka_bot.core.config import settings

# Phase 3-4: Thread management and navigation handlers
from luka_bot.handlers.start import router as start_router
from luka_bot.handlers.search import router as search_router  # KB search (enabled for DM and groups)
from luka_bot.handlers.groups_enhanced import router as groups_router  # Enhanced /groups with KB/agent info
from luka_bot.handlers.group_messages import router as group_messages_router
from luka_bot.handlers.group_commands import router as group_commands_router
from luka_bot.handlers.group_admin import router as group_admin_router
from luka_bot.handlers.group_settings_inline import router as group_settings_inline_router
from luka_bot.handlers.reputation_viewer import router as reputation_viewer_router
from luka_bot.handlers.kb_gathering import router as kb_gathering_router
from luka_bot.handlers.profile import router as profile_router
from luka_bot.handlers.reset import router as reset_router
from luka_bot.handlers.keyboard_actions import router as keyboard_router
from luka_bot.handlers.forwarded_messages import router as forwarded_router
from luka_bot.handlers.streaming_dm import router as streaming_router
from luka_bot.handlers.processes import router as processes_router

# Optional commands (configured via LUKA_COMMANDS_ENABLED in config.py)
chat_router = None
tasks_router = None

if "chat" in settings.LUKA_COMMANDS_ENABLED:
    try:
        from luka_bot.handlers.chat import router as chat_router
    except ImportError:
        logger.warning("⚠️  /chat command enabled in config but handler not found")

if "tasks" in settings.LUKA_COMMANDS_ENABLED:
    try:
        from luka_bot.handlers.tasks import router as tasks_router
    except ImportError:
        logger.warning("⚠️  /tasks command enabled in config but handler not found")


def get_llm_bot_router() -> Router:
    """
    Get the main luka_bot router with Phase 3 handlers.
    
    Returns:
        Router with all registered handlers
    """
    router = Router(name="luka_bot")
    
    # Build list of enabled handlers
    enabled_handlers = ["start"]
    disabled_handlers = []
    
    # Phase 3-4 routers (order matters: specific before general)
    router.include_router(start_router)
    
    # Optional command routers (configured via LUKA_COMMANDS_ENABLED in config.py)
    if chat_router is not None:
        router.include_router(chat_router)
        enabled_handlers.append("chat")
    else:
        disabled_handlers.append("chat")
    
    if tasks_router is not None:
        router.include_router(tasks_router)
        enabled_handlers.append("tasks")
    else:
        disabled_handlers.append("tasks")
    
    # Core routers (always enabled)
    router.include_router(groups_router)
    enabled_handlers.append("groups")
    
    router.include_router(group_commands_router)  # Group commands (/help, /stats, /settings, /search, /import, /moderation)
    router.include_router(search_router)  # KB search (DM multi-KB search, fallback for non-group chats)
    enabled_handlers.append("search")
    
    router.include_router(group_admin_router)  # Group admin controls (callbacks)
    router.include_router(group_settings_inline_router)  # Inline group settings (callbacks)
    router.include_router(reputation_viewer_router)  # Reputation viewer (callbacks + /reputation)
    router.include_router(kb_gathering_router)  # KB gathering system (callbacks)
    router.include_router(group_messages_router)  # Group KB indexing (must be after commands)
    router.include_router(profile_router)
    enabled_handlers.append("profile")
    
    router.include_router(reset_router)
    enabled_handlers.append("reset")
    
    router.include_router(processes_router)  # Camunda BPMN process handlers
    router.include_router(keyboard_router)  # Reply keyboard actions (before streaming)
    router.include_router(forwarded_router)  # Forwarded messages (before general streaming)
    router.include_router(streaming_router)  # Must be last (catches all messages)
    
    # Log registration summary
    enabled_str = ", ".join([f"/{cmd}" for cmd in enabled_handlers])
    logger.info(f"📦 Phase 4 handlers registered: {enabled_str}, group commands, group admin, group settings, group messages, processes, reply keyboard, forwarded messages, streaming DM")
    
    if disabled_handlers:
        disabled_str = ", ".join([f"/{cmd}" for cmd in disabled_handlers])
        logger.info(f"⏸️  Disabled commands: {disabled_str} (configure via LUKA_COMMANDS_ENABLED in config.py)")
    
    return router
