"""
Web platform adapter.

Handles Web-specific rendering: quick prompts, standard markdown, AG-UI protocol.
"""

import re
from typing import Any, Optional

from luka_agent.adapters.base import BasePlatformAdapter


class WebAdapter(BasePlatformAdapter):
    """Adapter for Web platform (AG-UI protocol / CopilotKit).

    Web constraints:
    - No practical message length limit (browsers handle long content)
    - Quick prompts (suggestion chips) - recommended 3-5 for UX
    - Standard markdown (not platform-specific escaping)
    - AG-UI protocol format for suggestions
    """

    # Recommended number of quick prompts for clean UX
    RECOMMENDED_SUGGESTIONS = 5

    def render_suggestions(self, suggestions: list[str]) -> list[dict[str, str]]:
        """Render suggestions as AG-UI quick prompts.

        Args:
            suggestions: List of suggestion strings

        Returns:
            List of quick prompt objects for AG-UI protocol

        Format:
            [
                {"title": "Suggestion 1", "message": "Suggestion 1"},
                {"title": "Suggestion 2", "message": "Suggestion 2"},
            ]

        Note:
            - Limits to first 5 suggestions (recommended for UX)
            - Parses links from suggestions
            - Returns AG-UI compatible format
        """
        if not suggestions:
            return []

        # Limit to recommended number for clean UX
        limited_suggestions = suggestions[: self.RECOMMENDED_SUGGESTIONS]

        quick_prompts = []
        for suggestion in limited_suggestions:
            # Parse if contains link
            text, url = self.parse_suggestion_with_link(suggestion)

            # For AG-UI: title = display text, message = what to send
            quick_prompt = {
                "title": text,
                "message": text,  # User "sends" this when clicking
            }

            # If has URL, could include as metadata (platform may use it)
            if url:
                quick_prompt["metadata"] = {"url": url}

            quick_prompts.append(quick_prompt)

        return quick_prompts

    def format_message(self, text: str) -> str:
        """Format message for Web display.

        Args:
            text: Raw message text

        Returns:
            Formatted text (minimal formatting for web)

        Note:
            Web browsers handle long content well, so no truncation.
            Standard markdown is supported.
        """
        # Web doesn't need special formatting - return as-is
        # Browser will handle rendering and scrolling
        return text

    def chunk_long_message(self, text: str) -> list[str]:
        """Split long message (rarely needed for web).

        Args:
            text: Message text

        Returns:
            Single-item list (web handles long content)

        Note:
            Web browsers can handle very long messages, so chunking
            is rarely needed. Return as single chunk.
        """
        # Web can handle long messages - return as single chunk
        return [text]

    def escape_markdown(self, text: str) -> str:
        """Escape markdown for web (minimal escaping needed).

        Args:
            text: Text with potential markdown

        Returns:
            Text with markdown preserved (web uses standard markdown)

        Note:
            Web chat interfaces typically use standard markdown,
            which requires minimal escaping compared to Telegram.
        """
        # Web uses standard markdown - no special escaping needed
        # Return as-is, markdown renderer handles it
        return text

    def format_code_block(self, code: str, language: str = "") -> str:
        """Format code block for web.

        Args:
            code: Code content
            language: Programming language for syntax highlighting

        Returns:
            Formatted code block

        Example:
            format_code_block("print('hello')", "python")
            → "```python\nprint('hello')\n```"
        """
        if language:
            return f"```{language}\n{code}\n```"
        return f"```\n{code}\n```"

    def format_link(self, text: str, url: str) -> str:
        """Format link in standard markdown.

        Args:
            text: Link text
            url: Link URL

        Returns:
            Standard markdown link

        Example:
            format_link("Click here", "https://example.com")
            → "[Click here](https://example.com)"
        """
        return f"[{text}]({url})"

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

    def format_ag_ui_response(
        self,
        message: str,
        suggestions: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Format complete AG-UI protocol response.

        Args:
            message: Agent message text
            suggestions: Optional list of suggestions
            metadata: Optional metadata (workflow hints, etc.)

        Returns:
            Dict formatted for AG-UI protocol

        Format:
            {
                "message": "Agent response text",
                "suggestions": [
                    {"title": "...", "message": "..."},
                ],
                "metadata": {...}
            }
        """
        response = {"message": self.format_message(message)}

        if suggestions:
            response["suggestions"] = self.render_suggestions(suggestions)

        if metadata:
            response["metadata"] = metadata

        return response

    def format_tool_notification(self, tool_name: str, status: str = "started") -> str:
        """Format tool execution notification.

        Args:
            tool_name: Name of tool being executed
            status: Tool status ("started", "completed", "failed")

        Returns:
            Formatted notification text

        Examples:
            format_tool_notification("knowledge_base", "started")
            → "🔍 Searching knowledge base..."

            format_tool_notification("youtube", "completed")
            → "✅ Retrieved YouTube transcript"
        """
        tool_emoji_map = {
            "knowledge_base": "🔍",
            "youtube": "📺",
            "sub_agent": "🤖",
            "search": "🔎",
            "web": "🌐",
            "code": "💻",
        }

        status_text_map = {
            "started": "...",
            "completed": "",
            "failed": "(error)",
        }

        emoji = tool_emoji_map.get(tool_name, "🔧")
        status_suffix = status_text_map.get(status, "")

        # Convert snake_case to Title Case
        tool_display = " ".join(word.capitalize() for word in tool_name.split("_"))

        if status == "started":
            return f"{emoji} Using {tool_display}{status_suffix}"
        elif status == "completed":
            return f"✅ {tool_display} complete{status_suffix}"
        elif status == "failed":
            return f"❌ {tool_display} failed{status_suffix}"

        return f"{emoji} {tool_display}"

    def format_streaming_chunk(self, chunk: str) -> dict:
        """Format streaming text chunk for AG-UI protocol.

        Args:
            chunk: Text chunk from LLM streaming

        Returns:
            Dict formatted for AG-UI streaming

        Format:
            {
                "type": "textStreamDelta",
                "delta": "text chunk"
            }
        """
        return {"type": "textStreamDelta", "delta": chunk}
