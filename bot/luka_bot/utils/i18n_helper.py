"""
i18n Helper

Provides translation utilities for Luka bot using Aiogram's i18n and .po files.
Migrated from Python dictionaries to .po/.mo files for professional workflow.
"""
from typing import Optional
from loguru import logger
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as aiogram_gettext

from luka_bot.core.config import settings, LOCALES_DIR, I18N_DOMAIN


# Initialize I18n with .po/.mo files
i18n = I18n(
    path=LOCALES_DIR,
    default_locale=settings.DEFAULT_LOCALE,
    domain=I18N_DOMAIN
)


async def get_user_language(user_id: int) -> str:
    """
    Get user's language preference from UserProfile.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Language code ("en" or "ru"), defaults to configured DEFAULT_LOCALE
    """
    try:
        from luka_bot.services.user_profile_service import get_user_profile_service
        
        profile_service = get_user_profile_service()
        language = await profile_service.get_language(user_id)
        
        return language 
        
    except Exception as e:
        logger.error(f"❌ Error getting user language: {e}")
        return settings.DEFAULT_LOCALE  # Fallback to configured default locale


def _(key: str, language: str = None, **kwargs) -> str:
    """
    Main translation function with backward compatibility.
    
    This maintains the same API as before (key, language, **kwargs) but now
    uses .po/.mo files instead of Python dictionaries.
    
    Args:
        key: Translation key (e.g., "onboarding.welcome_title")
        language: Language code ("en" or "ru"), defaults to configured DEFAULT_LOCALE
        **kwargs: Placeholder values for string formatting
        
    Returns:
        Translated and formatted string
        
    Example:
        _("onboarding.welcome_title", "en", bot_name="Luka")
        # Returns: "Welcome to Luka!"
    """
    # Use default locale if not specified
    if language is None:
        language = settings.DEFAULT_LOCALE
    
    try:
        # Set locale context for this translation
        with i18n.context(), i18n.use_locale(language):
            translation = aiogram_gettext(key)
            
            # Fallback to default locale if key is missing in current locale
            if translation == key and language != settings.DEFAULT_LOCALE:
                with i18n.use_locale(settings.DEFAULT_LOCALE):
                    translation = aiogram_gettext(key)
            
            # Format with kwargs if provided
            if kwargs:
                try:
                    return translation.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logger.warning(f"⚠️  Error formatting translation key '{key}': {e}")
                    return translation
            return translation
            
    except Exception as e:
        logger.error(f"❌ Error translating '{key}' for language '{language}': {e}")
        # Fallback: return the key itself
        return key


def get_i18n_text(key: str, language: str, **kwargs) -> str:
    """
    Direct translation lookup (alias for _()).
    
    Args:
        key: Translation key
        language: Language code
        **kwargs: Placeholder values
        
    Returns:
        Translated string
    """
    return _(key, language, **kwargs)


def get_error_message(key: str, language: str, **kwargs) -> str:
    """
    Get localized error message.
    
    Args:
        key: Error key (e.g., "generic", "user_not_found")
        language: Language code
        **kwargs: Placeholder values
        
    Returns:
        Localized error message
    """
    # Prefix with error. namespace if not already present
    full_key = f"error.{key}" if not key.startswith("error.") else key
    return _(full_key, language, **kwargs)


def get_notification(key: str, language: str, **kwargs) -> str:
    """
    Get localized notification message.
    
    Args:
        key: Notification key (e.g., "thread_created", "settings_updated")
        language: Language code
        **kwargs: Placeholder values
        
    Returns:
        Localized notification message
    """
    # Prefix with notification. namespace if not already present
    full_key = f"notification.{key}" if not key.startswith("notification.") else key
    return _(full_key, language, **kwargs)


# Export for use in other modules
__all__ = ['i18n', '_', 'get_user_language', 'get_i18n_text', 'get_error_message', 'get_notification']
