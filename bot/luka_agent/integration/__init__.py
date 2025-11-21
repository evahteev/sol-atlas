"""
Integration helpers for connecting luka_agent to platforms.

This module provides integration adapters that make it easy to use
luka_agent with Telegram (aiogram) and Web (FastAPI/CopilotKit).
"""

from luka_agent.integration.telegram import (
    stream_telegram_response,
    invoke_telegram_response,
    create_telegram_keyboard_from_suggestions,
)
from luka_agent.integration.web import (
    stream_web_response,
    invoke_web_response,
)

__all__ = [
    # Telegram
    "stream_telegram_response",
    "invoke_telegram_response",
    "create_telegram_keyboard_from_suggestions",
    # Web
    "stream_web_response",
    "invoke_web_response",
]
