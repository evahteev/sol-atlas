"""
Standalone i18n utility for luka_agent.

This is a simplified version that provides passthrough translation
when running in standalone mode (without luka_bot services).

When integrated with luka_bot, that system's i18n_helper is used instead.
"""
from typing import Optional
from loguru import logger


def _(key: str, language: Optional[str] = None, **kwargs) -> str:
    """
    Passthrough translation function for standalone mode.

    In standalone mode, this just returns the key text with optional formatting.
    When integrated with luka_bot, that module's translation system is used.

    Args:
        key: Translation key or text
        language: Language code (ignored in standalone mode)
        **kwargs: Placeholder values for string formatting (filtered from language param)

    Returns:
        The key text, optionally formatted with kwargs

    Example:
        _("Started {name} sub-agent!", language="en", name="Onboarding")
        # Returns: "Started Onboarding sub-agent!"
    """
    try:
        # Filter out 'language' from kwargs if it's there
        # (it comes in as kwargs when called with language= parameter)
        format_kwargs = {k: v for k, v in kwargs.items() if k != 'language'}

        if format_kwargs:
            return key.format(**format_kwargs)
        return key
    except (KeyError, ValueError) as e:
        logger.warning(f"Error formatting i18n string '{key}': {e}")
        return key


__all__ = ["_"]
