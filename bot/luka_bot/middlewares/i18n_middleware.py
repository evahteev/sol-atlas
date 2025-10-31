"""
I18n Middleware - Phase 4.

Custom i18n middleware that reads language preference from UserProfile.
"""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from loguru import logger

from luka_bot.services.user_profile_service import get_user_profile_service


class UserProfileI18nMiddleware(BaseMiddleware):
    """
    Middleware that sets language based on UserProfile.
    
    Priority:
    1. UserProfile.language (if profile exists)
    2. Telegram user language_code
    3. Default "en"
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process event and set language."""
        
        # Get user from event
        user: User = data.get("event_from_user")
        
        if user:
            user_id = user.id
            
            # Try to get language from UserProfile
            profile_service = get_user_profile_service()
            language = await profile_service.get_language(user_id)
            
            # Fallback to Telegram user language if profile returns default
            if language == "en" and user.language_code in ["ru", "uk"]:
                language = "ru"
            
            # Set language in data for i18n
            data["locale"] = language
        
        # Call next handler
        return await handler(event, data)

