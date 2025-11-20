"""
Image description tool for luka_agent.

Uses Ollama llava vision model to analyze and describe images from URLs.
"""

from typing import Optional

from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field


class DescribeImageInput(BaseModel):
    """Input schema for image description tool."""

    image_url: str = Field(
        ...,
        description="URL of the image to describe. Must be a publicly accessible URL (http:// or https://)."
    )
    detail_level: str = Field(
        "standard",
        description=(
            "Level of detail for the description. Options: "
            "'low' (quick, basic description), "
            "'standard' (balanced detail, recommended), "
            "'high' (comprehensive analysis). "
            "Default: 'standard'"
        )
    )
    custom_prompt: Optional[str] = Field(
        None,
        description=(
            "Optional custom prompt to guide the image description. "
            "If provided, this overrides the default prompt for the detail level. "
            "Use this to ask specific questions about the image or focus on particular aspects."
        )
    )


async def describe_image_impl(
    image_url: str,
    detail_level: str,
    custom_prompt: Optional[str],
    user_id: int,
    thread_id: str,
    user_language: str,
) -> str:
    """Describe an image using Ollama llava vision model.

    Args:
        image_url: URL of the image to describe
        detail_level: Detail level ('low', 'standard', 'high')
        custom_prompt: Optional custom prompt to override default
        user_id: User ID
        thread_id: Thread ID
        user_language: User's interface language

    Returns:
        Image description or error message
    """
    # Step 1: Validate inputs
    if not image_url:
        return "Please provide an image URL to describe."

    if not image_url.startswith(("http://", "https://")):
        return "Invalid image URL. Please provide a URL starting with http:// or https://"

    # Validate detail_level
    valid_detail_levels = ["low", "standard", "high"]
    if detail_level not in valid_detail_levels:
        logger.warning(f"Invalid detail_level '{detail_level}', defaulting to 'standard'")
        detail_level = "standard"

    # Step 2: Check configuration (dual-mode support)
    try:
        from luka_agent.core.config import settings
        ollama_url = settings.OLLAMA_URL
        vision_model = getattr(settings, "DEFAULT_VISION_MODEL", "llava")
        vision_enabled = getattr(settings, "VISION_ENABLED", True)
    except (ImportError, Exception) as settings_err:
        # Fallback to standalone mode using environment variables
        logger.debug(f"Settings import failed: {settings_err}, using environment variables")
        import os
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        vision_model = os.getenv("DEFAULT_VISION_MODEL", "llava")
        vision_enabled = os.getenv("VISION_ENABLED", "true").lower() == "true"

    # Check if vision feature is enabled
    if not vision_enabled:
        logger.warning("Vision/image description feature is disabled")
        return (
            "Image description feature is currently disabled. "
            "To enable it, set VISION_ENABLED=true in your .env file and restart."
        )

    # Step 3: Prepare prompt based on detail level or custom prompt
    if custom_prompt:
        prompt = custom_prompt
    else:
        # Default prompts for each detail level
        prompts = {
            "low": "Briefly describe what you see in this image in 1-2 sentences.",
            "standard": (
                "Describe this image in detail. Include: "
                "1) Main subject or focus, "
                "2) Important visual elements, colors, and composition, "
                "3) Context or setting, "
                "4) Any text visible in the image, "
                "5) Overall mood or style."
            ),
            "high": (
                "Provide a comprehensive analysis of this image. Include: "
                "1) Detailed description of all subjects and objects, "
                "2) Visual composition, lighting, and color palette, "
                "3) Setting, context, and background elements, "
                "4) Any text, symbols, or writing visible, "
                "5) Artistic style, technique, or photographic qualities, "
                "6) Mood, atmosphere, and emotional impact, "
                "7) Any notable details or interesting aspects."
            )
        }
        prompt = prompts.get(detail_level, prompts["standard"])

    # Step 4: Try to import and use Ollama vision model
    try:
        from langchain_ollama import ChatOllama
    except ImportError as import_err:
        logger.error(f"Unable to import ChatOllama: {import_err}")
        return (
            "Ollama integration is not available. "
            "Please ensure langchain-ollama is installed: pip install langchain-ollama"
        )

    # Step 5: Download image from URL
    try:
        import httpx
        import base64
    except ImportError as import_err:
        logger.error(f"Unable to import httpx: {import_err}")
        return (
            "Image download requires httpx package. "
            "Please ensure httpx is installed: pip install httpx"
        )

    # Download the image
    try:
        logger.info(f"Downloading image from URL: {image_url[:100]}...")
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_bytes = response.content

        # Convert to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        logger.info(f"Image downloaded successfully, size: {len(image_bytes)} bytes")

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error downloading image: {e}")
        return (
            f"Unable to download image. HTTP status: {e.response.status_code}. "
            "Please verify the URL is correct and the image is publicly accessible."
        )
    except httpx.TimeoutException:
        logger.error("Timeout downloading image")
        return (
            "Timeout while downloading the image. "
            "The image may be too large or the server is slow. Please try a different image."
        )
    except Exception as download_err:
        logger.error(f"Error downloading image: {download_err}")
        return (
            "Unable to download the image. Please verify: "
            "1) The URL is correct and publicly accessible, "
            "2) The image is not behind authentication, "
            "3) The server is responding."
        )

    # Step 6: Execute vision model with specific error handling
    try:
        # Strip /v1 suffix if present (ChatOllama doesn't need it)
        base_url = ollama_url.rstrip("/v1").rstrip("/")

        logger.info(
            f"Describing image for user {user_id}, thread {thread_id}, "
            f"model: {vision_model}, detail: {detail_level}"
        )

        # Initialize Ollama vision model
        llm = ChatOllama(
            model=vision_model,
            base_url=base_url,
            temperature=0.7,
        )

        # Create vision message with base64-encoded image
        # ChatOllama expects base64-encoded images
        from langchain_core.messages import HumanMessage

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{image_base64}",
                },
            ]
        )

        # Invoke the model
        response = await llm.ainvoke([message])

        # Extract the description from response
        description = response.content.strip()

        if not description:
            logger.warning("Vision model returned empty response")
            return "Unable to describe the image. The vision model did not return a description."

        logger.info(f"Successfully described image (length: {len(description)} chars)")
        return description

    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Error in describe_image: {e}", exc_info=True)

        # Provide user-friendly error messages for common issues
        if "connection" in error_msg or "timeout" in error_msg:
            return (
                "Unable to connect to the vision service. "
                "Please check that Ollama is running and accessible."
            )
        elif "model" in error_msg and ("not found" in error_msg or "pull" in error_msg):
            return (
                f"Vision model '{vision_model}' is not available. "
                f"Please pull the model first: ollama pull {vision_model}"
            )
        elif "image" in error_msg and ("invalid" in error_msg or "format" in error_msg):
            return (
                "Unable to process the image. Please ensure: "
                "1) The URL is correct and publicly accessible, "
                "2) The image format is supported (JPG, PNG, GIF, WebP), "
                "3) The image is not corrupted or too large."
            )
        elif "url" in error_msg or "download" in error_msg or "fetch" in error_msg:
            return (
                "Unable to access the image URL. Please verify: "
                "1) The URL is correct and publicly accessible, "
                "2) The image is not behind authentication or a paywall, "
                "3) The server hosting the image is responding."
            )
        else:
            return (
                "Unable to describe the image. "
                f"Please verify the image URL is accessible and try again. "
                f"If the problem persists, check Ollama logs for details."
            )


def create_image_description_tool(
    user_id: int,
    thread_id: str,
    language: str,
) -> StructuredTool:
    """Create image description tool.

    Args:
        user_id: User ID
        thread_id: Thread ID
        language: User's interface language

    Returns:
        LangChain StructuredTool for image description
    """
    return StructuredTool.from_function(
        name="describe_image",
        description=(
            "Describe and analyze images from URLs using AI vision. "
            "Useful for: understanding image content, extracting text from images, "
            "analyzing visual elements, identifying objects/people, or answering questions about images. "
            "Use this when the user provides an image URL or asks about image content. "
            "Supports different detail levels (low/standard/high) and custom prompts for specific analysis."
        ),
        func=lambda image_url, detail_level="standard", custom_prompt=None: describe_image_impl(
            image_url=image_url,
            detail_level=detail_level,
            custom_prompt=custom_prompt,
            user_id=user_id,
            thread_id=thread_id,
            user_language=language,
        ),
        args_schema=DescribeImageInput,
        coroutine=lambda image_url, detail_level="standard", custom_prompt=None: describe_image_impl(
            image_url=image_url,
            detail_level=detail_level,
            custom_prompt=custom_prompt,
            user_id=user_id,
            thread_id=thread_id,
            user_language=language,
        ),
    )


__all__ = ["create_image_description_tool"]
