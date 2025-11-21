"""
YouTube transcript tool for luka_agent.

Fetches YouTube video transcripts for analysis.
"""

from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field


class GetYouTubeTranscriptInput(BaseModel):
    """Input schema for YouTube transcript tool."""

    video_url: str = Field(..., description="YouTube video URL")
    language: str = Field("en", description="Preferred transcript language (e.g., 'en', 'ru')")


async def get_youtube_transcript_impl(
    video_url: str,
    language: str,
    user_id: int,
    thread_id: str,
    user_language: str,
) -> str:
    """Get transcript from YouTube video.

    Args:
        video_url: YouTube URL or video ID
        language: Preferred transcript language
        user_id: User ID
        thread_id: Thread ID
        user_language: User's interface language

    Returns:
        Video transcript or error message
    """
    # Step 1: Check if YouTube feature is enabled
    try:
        from luka_agent.core.config import settings
    except ImportError:
        logger.error("Unable to import settings - luka_agent config not available")
        return "YouTube transcript feature is not configured. Please ensure luka_agent is properly installed."

    # Note: YOUTUBE_TRANSCRIPT_ENABLED is optional - if not present, feature is enabled by default
    if hasattr(settings, "YOUTUBE_TRANSCRIPT_ENABLED") and not settings.YOUTUBE_TRANSCRIPT_ENABLED:
        logger.warning("YouTube transcript feature is disabled in settings")
        return (
            "YouTube transcript feature is currently disabled. "
            "To enable it, set YOUTUBE_TRANSCRIPT_ENABLED=true in your .env file "
            "and restart the bot."
        )

    # Step 2: Try to import YouTube service
    try:
        from luka_bot.agents.context import ConversationContext
        from luka_bot.agents.tools.youtube_tools import get_youtube_transcript
    except ImportError as import_err:
        logger.error(f"Unable to import YouTube tools: {import_err}")
        return (
            "YouTube transcript service is not available. Please ensure luka_bot YouTube tools are installed correctly."
        )

    # Step 3: Execute tool logic with specific error handling
    try:
        conv_ctx = ConversationContext(
            user_id=user_id,
            thread_id=thread_id,
            language=user_language,
            enabled_tools=["youtube"],
            platform="telegram",
        )

        result = await get_youtube_transcript(ctx=conv_ctx, video_url=video_url, language=language)

        return result

    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Error in get_youtube_transcript: {e}")

        # Provide user-friendly error messages for common issues
        if "video unavailable" in error_msg or "private" in error_msg:
            return (
                "This video is unavailable or private. "
                "Please check that the video URL is correct and the video is publicly accessible."
            )
        elif "transcript" in error_msg and ("disabled" in error_msg or "not available" in error_msg):
            return (
                "This video does not have transcripts available. "
                "Transcripts may be disabled by the uploader or not yet generated."
            )
        elif "language" in error_msg:
            return (
                f"Transcript not available in language '{language}'. "
                "Try requesting a different language or check available languages for this video."
            )
        else:
            return (
                "Unable to fetch YouTube transcript. "
                "Please verify the video URL is correct and try again. "
                "If the problem persists, the video may not have transcripts available."
            )


def create_youtube_tool(
    user_id: int,
    thread_id: str,
    language: str,
) -> StructuredTool:
    """Create YouTube transcript tool.

    Args:
        user_id: User ID
        thread_id: Thread ID
        language: User's interface language

    Returns:
        LangChain StructuredTool for YouTube transcripts
    """
    return StructuredTool.from_function(
        name="get_youtube_transcript",
        description=(
            "Get transcript from a YouTube video. Useful for summarizing videos, "
            "answering questions about video content, or extracting key points. "
            "Use this when the user provides a YouTube URL or asks about video content."
        ),
        func=lambda video_url, language="en": get_youtube_transcript_impl(
            video_url=video_url,
            language=language,
            user_id=user_id,
            thread_id=thread_id,
            user_language=language,
        ),
        args_schema=GetYouTubeTranscriptInput,
        coroutine=lambda video_url, language="en": get_youtube_transcript_impl(
            video_url=video_url,
            language=language,
            user_id=user_id,
            thread_id=thread_id,
            user_language=language,
        ),
    )


__all__ = ["create_youtube_tool"]
