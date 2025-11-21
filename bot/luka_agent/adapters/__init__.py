"""
Platform adapters for luka_agent.

Adapters handle platform-specific rendering while keeping luka_agent platform-agnostic.
"""

from luka_agent.adapters.base import BasePlatformAdapter
from luka_agent.adapters.telegram import TelegramAdapter
from luka_agent.adapters.web import WebAdapter

__all__ = [
    "BasePlatformAdapter",
    "TelegramAdapter",
    "WebAdapter",
]
