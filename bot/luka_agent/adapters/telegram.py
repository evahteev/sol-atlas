"""
Telegram platform adapter.

Handles Telegram-specific rendering: keyboard buttons, MarkdownV2, message limits.
"""

import re
from typing import Any, Optional

from luka_agent.adapters.base import BasePlatformAdapter


class TelegramAdapter(BasePlatformAdapter):
    """Adapter for Telegram platform.

    Telegram constraints:
    - Max message length: 4096 characters
    - Max keyboard buttons per row: Recommended 3-4 for mobile
    - Max keyboard rows: No hard limit but UX degrades after ~10
    - Markdown: MarkdownV2 with specific escaping rules
    """

    # Telegram message length limit
    MAX_MESSAGE_LENGTH = 4096

    # Recommended buttons per row for mobile UX
    BUTTONS_PER_ROW = 3

    # MarkdownV2 characters that need escaping
    MARKDOWN_ESCAPE_CHARS = r"_*[]()~`>#+-=|{}.!"

    def render_suggestions(self, suggestions: list[str]) -> Any:
        """Render suggestions as Telegram ReplyKeyboardMarkup.

        Args:
            suggestions: List of suggestion strings

        Returns:
            Dict compatible with aiogram's ReplyKeyboardMarkup

        Note:
            - Limits to first 12 suggestions (4 rows x 3 buttons)
            - Splits into rows of 3 buttons each
            - Returns dict structure that can be converted to ReplyKeyboardMarkup
        """
        if not suggestions:
            return None

        # Limit to 12 suggestions (4 rows of 3)
        limited_suggestions = suggestions[:12]

        # Split into rows of 3 buttons each
        keyboard = []
        for i in range(0, len(limited_suggestions), self.BUTTONS_PER_ROW):
            row = limited_suggestions[i : i + self.BUTTONS_PER_ROW]
            keyboard.append([{"text": text} for text in row])

        return {
            "keyboard": keyboard,
            "resize_keyboard": True,  # Fit keyboard to screen
            "one_time_keyboard": True,  # Hide after selection
            "input_field_placeholder": "Choose an option or type your own...",
        }

    def format_message(self, text: str) -> str:
        """Format message for Telegram constraints.

        Args:
            text: Raw message text

        Returns:
            Formatted text within Telegram limits

        Note:
            - Truncates to MAX_MESSAGE_LENGTH if too long
            - Preserves markdown
            - Adds truncation indicator if cut
        """
        if len(text) <= self.MAX_MESSAGE_LENGTH:
            return text

        # Find safe cut point (end of sentence, paragraph, or word)
        # Indicator is 53 chars: "\n\n... (message truncated, continue conversation for more)"
        truncate_at = self.MAX_MESSAGE_LENGTH - 60  # Leave room for indicator + margin

        # Try to cut at paragraph
        last_paragraph = text.rfind("\n\n", 0, truncate_at)
        if last_paragraph > truncate_at - 500:  # Within 500 chars of limit
            cut_point = last_paragraph
        else:
            # Try to cut at sentence
            last_sentence = max(
                text.rfind(". ", 0, truncate_at),
                text.rfind("! ", 0, truncate_at),
                text.rfind("? ", 0, truncate_at),
            )
            if last_sentence > truncate_at - 200:  # Within 200 chars
                cut_point = last_sentence + 1  # Include punctuation
            else:
                # Cut at word boundary
                last_space = text.rfind(" ", 0, truncate_at)
                cut_point = last_space if last_space > 0 else truncate_at

        truncated = text[:cut_point].rstrip()
        return f"{truncated}\n\n... (message truncated, continue conversation for more)"

    def chunk_long_message(self, text: str) -> list[str]:
        """Split long message into Telegram-compatible chunks.

        Args:
            text: Long message exceeding Telegram limits

        Returns:
            List of message chunks, each ≤ MAX_MESSAGE_LENGTH

        Note:
            - Preserves paragraphs when possible
            - Preserves markdown formatting
            - Adds continuation indicators
        """
        if len(text) <= self.MAX_MESSAGE_LENGTH:
            return [text]

        chunks = []
        remaining = text
        chunk_num = 1

        while remaining:
            if len(remaining) <= self.MAX_MESSAGE_LENGTH:
                # Last chunk
                if chunk_num > 1:
                    chunks.append(f"(continued {chunk_num})\n\n{remaining}")
                else:
                    chunks.append(remaining)
                break

            # Find safe cut point
            cut_point = self._find_chunk_cut_point(
                remaining, self.MAX_MESSAGE_LENGTH - 100
            )

            # Extract chunk
            chunk = remaining[:cut_point].rstrip()

            # Add indicators
            if chunk_num == 1:
                chunk = f"{chunk}\n\n(continued...)"
            else:
                chunk = f"(continued {chunk_num})\n\n{chunk}\n\n(continued...)"

            chunks.append(chunk)
            remaining = remaining[cut_point:].lstrip()
            chunk_num += 1

        return chunks

    def _find_chunk_cut_point(self, text: str, max_length: int) -> int:
        """Find safe point to cut message chunk.

        Args:
            text: Text to cut
            max_length: Maximum length for chunk

        Returns:
            Index to cut at (preserving paragraphs/sentences/words)
        """
        # Try paragraph boundary
        last_paragraph = text.rfind("\n\n", 0, max_length)
        if last_paragraph > max_length - 500:
            return last_paragraph + 2  # After \n\n

        # Try sentence boundary
        last_sentence = max(
            text.rfind(". ", 0, max_length),
            text.rfind("! ", 0, max_length),
            text.rfind("? ", 0, max_length),
        )
        if last_sentence > max_length - 200:
            return last_sentence + 2  # After punctuation and space

        # Try word boundary
        last_space = text.rfind(" ", 0, max_length)
        if last_space > 0:
            return last_space + 1  # After space

        # Fallback: hard cut
        return max_length

    def escape_markdown(self, text: str) -> str:
        """Escape special characters for Telegram MarkdownV2.

        Args:
            text: Text with potential special characters

        Returns:
            Text with MarkdownV2 special characters escaped

        Note:
            Telegram MarkdownV2 requires escaping: _ * [ ] ( ) ~ ` > # + - = | { } . !
            But NOT inside code blocks or inline code.
        """
        # Simple escaping - prepend backslash to special chars
        # More sophisticated version would handle code blocks separately
        escaped = ""
        in_code = False
        in_code_block = False

        i = 0
        while i < len(text):
            # Check for code block start/end (```)
            if text[i : i + 3] == "```":
                in_code_block = not in_code_block
                escaped += "```"
                i += 3
                continue

            # Check for inline code start/end (`)
            if text[i] == "`" and not in_code_block:
                in_code = not in_code
                escaped += "`"
                i += 1
                continue

            # Escape special chars if not in code
            if (
                text[i] in self.MARKDOWN_ESCAPE_CHARS
                and not in_code
                and not in_code_block
            ):
                escaped += "\\" + text[i]
            else:
                escaped += text[i]

            i += 1

        return escaped

    def format_link(self, text: str, url: str) -> str:
        """Format link in Telegram MarkdownV2.

        Args:
            text: Link text
            url: Link URL

        Returns:
            Formatted markdown link

        Example:
            format_link("Click here", "https://example.com")
            → "[Click here](https://example.com)"
        """
        # Escape special chars in link text
        escaped_text = self.escape_markdown(text)
        return f"[{escaped_text}]({url})"

    def remove_keyboard(self) -> dict:
        """Get dict to remove keyboard.

        Returns:
            Dict compatible with aiogram's ReplyKeyboardRemove
        """
        return {"remove_keyboard": True}

    def parse_suggestion_with_link(self, suggestion: str) -> tuple[str, Optional[str]]:
        """Parse suggestion that may contain a link.

        Args:
            suggestion: Suggestion string, possibly with " - URL" format

        Returns:
            Tuple of (display_text, url_or_none)

        Examples:
            "🚀 Launch Bot - https://example.com" → ("🚀 Launch Bot", "https://example.com")
            "Simple option" → ("Simple option", None)
        """
        # Check for " - URL" pattern
        match = re.search(r"^(.+?)\s+-\s+(https?://\S+)$", suggestion.strip())
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return suggestion, None

    def format_tool_notification(self, tool_name: str, status: str) -> str:
        """Format tool execution notification for Telegram.

        Args:
            tool_name: Name of the tool being executed
            status: Tool status ('started', 'completed', 'error')

        Returns:
            Formatted notification string

        Examples:
            format_tool_notification("knowledge_base", "started")
            → "🔍 Searching knowledge base..."

            format_tool_notification("knowledge_base", "completed")
            → "✅ Knowledge base search complete"

            format_tool_notification("knowledge_base", "error")
            → "❌ Searching knowledge base failed"
        """
        # Map tool names to friendly names and icons
        tool_display_names = {
            "knowledge_base": ("🔍", "Searching knowledge base"),
            "youtube": ("📺", "Fetching YouTube content"),
            "sub_agent": ("🤖", "Starting sub-agent"),
            "describe_image": ("🖼️", "Analyzing image"),
        }

        icon, friendly_name = tool_display_names.get(
            tool_name, ("🔧", f"Using {tool_name}")
        )

        if status == "started":
            return f"{icon} {friendly_name}..."
        elif status == "completed":
            return f"✅ {friendly_name} complete"
        elif status == "error":
            return f"❌ {friendly_name} failed"
        else:
            return f"{icon} {friendly_name}"
