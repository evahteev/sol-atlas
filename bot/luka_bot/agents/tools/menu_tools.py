"""
Menu rendering tools for agents to show command interfaces.
"""
from typing import List, Dict, Any
from pydantic_ai import Tool
from loguru import logger

from luka_bot.keyboards.start_menu import build_start_reply_keyboard
from luka_bot.keyboards.groups_menu import get_groups_keyboard
from luka_bot.keyboards.threads_menu import get_threads_keyboard
from luka_bot.services.prompt_pool_service import get_prompt_pool_service
from luka_bot.services.group_service import get_group_service
from luka_bot.services.thread_service import get_thread_service
from luka_bot.utils.i18n_helper import get_user_language


async def show_start_menu(user_id: int) -> str:
    """Show the main start menu with quick actions."""
    try:
        # Get user language
        lang = await get_user_language(user_id)
        
        # Get prompt pool service
        prompt_service = get_prompt_pool_service()
        prompts = await prompt_service.get_prompts_for_user(user_id, limit=3)
        
        # Build start keyboard
        keyboard = await build_start_reply_keyboard(
            prompts=prompts,
            include_scope_controls=False,
            language=lang
        )
        
        return f"✅ Start menu displayed. The menu includes quick actions and {len(prompts)} prompt options."
    except Exception as e:
        logger.error(f"Error showing start menu: {e}")
        return f"❌ Error displaying start menu: {str(e)}"


async def show_groups_menu(user_id: int) -> str:
    """Show the groups management menu."""
    try:
        # Get user language
        lang = await get_user_language(user_id)
        
        # Get user's groups
        group_service = await get_group_service()
        groups = await group_service.list_user_groups(user_id, active_only=True)
        
        # Build groups keyboard
        keyboard = await get_groups_keyboard(
            groups=groups,
            current_group_id=None,
            language=lang
        )
        
        return f"✅ Groups menu displayed. You have {len(groups)} groups available."
    except Exception as e:
        logger.error(f"Error showing groups menu: {e}")
        return f"❌ Error displaying groups menu: {str(e)}"


async def show_chat_menu(user_id: int) -> str:
    """Show the chat/threads management menu."""
    try:
        # Get user language
        lang = await get_user_language(user_id)
        
        # Get user's threads
        thread_service = get_thread_service()
        threads = await thread_service.list_threads(user_id)
        
        # Build threads keyboard
        keyboard = await get_threads_keyboard(
            threads=threads,
            current_thread_id=None,
            language=lang
        )
        
        return f"✅ Chat menu displayed. You have {len(threads)} conversation threads."
    except Exception as e:
        logger.error(f"Error showing chat menu: {e}")
        return f"❌ Error displaying chat menu: {str(e)}"


async def show_profile_menu(user_id: int) -> str:
    """Show the profile and settings menu."""
    try:
        # Get user language
        lang = await get_user_language(user_id)
        
        # Profile menu is typically just a back button
        return f"✅ Profile menu displayed. Use the back button to return to the main menu."
    except Exception as e:
        logger.error(f"Error showing profile menu: {e}")
        return f"❌ Error displaying profile menu: {str(e)}"


async def show_group_settings(group_id: int, user_id: int) -> str:
    """Show settings menu for a specific group."""
    try:
        # Get user language
        lang = await get_user_language(user_id)
        
        # Get group service
        group_service = await get_group_service()
        
        # Verify user has access to this group
        user_groups = await group_service.list_user_groups(user_id, active_only=True)
        group_ids = [g.group_id for g in user_groups]
        
        if group_id not in group_ids:
            return f"❌ You don't have access to group {group_id}."
        
        # Get group info
        group_info = next((g for g in user_groups if g.group_id == group_id), None)
        if not group_info:
            return f"❌ Group {group_id} not found."
        
        # Get moderation service for settings
        from luka_bot.services.moderation_service import get_moderation_service
        moderation_service = await get_moderation_service()
        group_settings = await moderation_service.get_group_settings(group_id)
        
        settings_info = []
        if group_settings:
            settings_info.append(f"• AI Assistant: {'Enabled' if group_settings.ai_assistant_enabled else 'Disabled'}")
            settings_info.append(f"• Silent Mode: {'Enabled' if group_settings.silent_mode else 'Disabled'}")
        else:
            settings_info.append("• Using default settings")
        
        return f"""✅ Group Settings for "{group_info.title}" (ID: {group_id})

Current Settings:
{chr(10).join(settings_info)}

Use the inline buttons below to modify settings."""
        
    except Exception as e:
        logger.error(f"Error showing group settings: {e}")
        return f"❌ Error displaying group settings: {str(e)}"


async def list_user_groups(user_id: int) -> str:
    """List all groups the user has access to."""
    try:
        # Get user language
        lang = await get_user_language(user_id)
        
        # Get group service
        group_service = await get_group_service()
        groups = await group_service.list_user_groups(user_id, active_only=True)
        
        if not groups:
            return "📭 You don't have access to any groups yet. Add the bot to a group to get started!"
        
        group_list = []
        for group in groups:
            group_list.append(f"• {group.title} (ID: {group.group_id})")
        
        return f"""✅ Your Groups ({len(groups)} total):

{chr(10).join(group_list)}

Use /groups to manage your groups or ask me to show settings for a specific group."""
        
    except Exception as e:
        logger.error(f"Error listing user groups: {e}")
        return f"❌ Error listing groups: {str(e)}"


def get_menu_tools() -> List[Tool]:
    """Return all menu rendering tools."""
    return [
        Tool(show_start_menu, name="show_start_menu", description="Display the main start menu with quick actions and prompts"),
        Tool(show_groups_menu, name="show_groups_menu", description="Display the groups management menu to view and select groups"),
        Tool(show_chat_menu, name="show_chat_menu", description="Display the chat/threads menu to manage conversation threads"),
        Tool(show_profile_menu, name="show_profile_menu", description="Display the profile and settings menu"),
        Tool(show_group_settings, name="show_group_settings", description="Show settings for a specific group. Use group_id parameter."),
        Tool(list_user_groups, name="list_user_groups", description="List all groups the user has access to"),
    ]
