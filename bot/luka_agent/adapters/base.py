"""
Base platform adapter interface.

Defines the contract that all platform adapters must implement.
"""

from abc import ABC, abstractmethod
from typing import Any


class BasePlatformAdapter(ABC):
    """Base class for platform adapters.

    Platform adapters transform luka_agent output (platform-agnostic)
    into platform-specific formats (Telegram keyboards, Web buttons, etc.).

    Responsibilities:
    - Render suggestions as platform-specific UI (keyboard buttons, chips, etc.)
    - Format messages for platform (markdown variations, limits, etc.)
    - Handle platform-specific constraints (message length, button limits, etc.)

    Does NOT:
    - Contain business logic (that's in luka_agent)
    - Make decisions about what tools to use (that's the LLM)
    - Manage state (that's the graph)
    """

    @abstractmethod
    def render_suggestions(self, suggestions: list[str]) -> Any:
        """Render suggestions as platform-specific UI.

        Args:
            suggestions: List of suggestion strings from luka_agent

        Returns:
            Platform-specific UI object (keyboard, buttons, chips, etc.)

        Examples:
            Telegram: ReplyKeyboardMarkup with buttons
            Web: List of quick prompt objects
        """
        pass

    @abstractmethod
    def format_message(self, text: str) -> str:
        """Format message text for platform constraints.

        Args:
            text: Raw message text from luka_agent

        Returns:
            Formatted text respecting platform limits

        Examples:
            Telegram: Max 4096 chars, Telegram markdown
            Web: Max ~unlimited, standard markdown
        """
        pass

    @abstractmethod
    def chunk_long_message(self, text: str) -> list[str]:
        """Split long messages into platform-appropriate chunks.

        Args:
            text: Long message that exceeds platform limits

        Returns:
            List of message chunks, each within platform limits

        Examples:
            Telegram: Split at 4096 chars, preserve markdown
            Web: May not need chunking (unlimited length)
        """
        pass

    @abstractmethod
    def escape_markdown(self, text: str) -> str:
        """Escape markdown for platform-specific rendering.

        Args:
            text: Text potentially containing markdown

        Returns:
            Text with properly escaped markdown for platform

        Examples:
            Telegram: Escape MarkdownV2 special chars
            Web: Standard markdown escaping
        """
        pass

    def get_platform_name(self) -> str:
        """Get platform identifier.

        Returns:
            Platform name ("telegram" or "web")
        """
        return self.__class__.__name__.replace("Adapter", "").lower()
