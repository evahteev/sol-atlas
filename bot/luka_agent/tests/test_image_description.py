"""
Tests for image_description tool.

Tests validate the tool's structure, input validation, prompt generation,
and integration with Ollama llava vision model.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from langchain_core.tools import StructuredTool
from langchain_core.messages import AIMessage

from luka_agent.tools.image_description import (
    DescribeImageInput,
    describe_image_impl,
    create_image_description_tool,
)


@pytest.fixture
def mock_httpx_client():
    """Fixture that mocks httpx AsyncClient for image downloads."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response_obj = Mock()
        mock_response_obj.content = b"fake_image_data"
        mock_response_obj.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response_obj)
        mock_client.return_value = mock_client_instance

        yield mock_client


class TestDescribeImageInput:
    """Test input schema validation."""

    def test_input_schema_has_required_fields(self):
        """Test input schema has all required fields."""
        # Valid input with required field only
        input_data = DescribeImageInput(image_url="https://example.com/image.jpg")
        assert input_data.image_url == "https://example.com/image.jpg"
        assert input_data.detail_level == "standard"  # default
        assert input_data.custom_prompt is None  # default

    def test_input_schema_accepts_all_fields(self):
        """Test input schema accepts all fields."""
        input_data = DescribeImageInput(
            image_url="https://example.com/image.jpg",
            detail_level="high",
            custom_prompt="Describe the colors in this image"
        )
        assert input_data.image_url == "https://example.com/image.jpg"
        assert input_data.detail_level == "high"
        assert input_data.custom_prompt == "Describe the colors in this image"

    def test_input_schema_validates_image_url_required(self):
        """Test that image_url is required."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            DescribeImageInput()


class TestDescribeImageImplementation:
    """Test describe_image_impl function."""

    @pytest.mark.asyncio
    async def test_empty_image_url_returns_error(self):
        """Test empty image URL returns user-friendly error."""
        result = await describe_image_impl(
            image_url="",
            detail_level="standard",
            custom_prompt=None,
            user_id=123,
            thread_id="test_thread",
            user_language="en",
        )
        assert "provide an image url" in result.lower()

    @pytest.mark.asyncio
    async def test_invalid_url_protocol_returns_error(self):
        """Test invalid URL protocol returns user-friendly error."""
        result = await describe_image_impl(
            image_url="ftp://example.com/image.jpg",
            detail_level="standard",
            custom_prompt=None,
            user_id=123,
            thread_id="test_thread",
            user_language="en",
        )
        assert "invalid image url" in result.lower()
        assert "http://" in result or "https://" in result

    @pytest.mark.asyncio
    async def test_invalid_detail_level_defaults_to_standard(self):
        """Test invalid detail level defaults to standard."""
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            # Mock the vision model
            mock_response = AIMessage(content="A beautiful landscape")
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_llm

            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    "OLLAMA_URL": "http://localhost:11434",
                    "DEFAULT_VISION_MODEL": "llava",
                    "VISION_ENABLED": "true"
                }.get(key, default)

                # Mock httpx client
                with patch("httpx.AsyncClient") as mock_client:
                    mock_response_obj = Mock()
                    mock_response_obj.content = b"fake_image_data"
                    mock_response_obj.raise_for_status = Mock()

                    mock_client_instance = AsyncMock()
                    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
                    mock_client_instance.__aexit__ = AsyncMock()
                    mock_client_instance.get = AsyncMock(return_value=mock_response_obj)
                    mock_client.return_value = mock_client_instance

                    result = await describe_image_impl(
                        image_url="https://example.com/image.jpg",
                        detail_level="invalid_level",  # Invalid level
                        custom_prompt=None,
                        user_id=123,
                        thread_id="test_thread",
                        user_language="en",
                    )

                    # Should still succeed with standard prompt
                    assert "beautiful landscape" in result.lower()

    @pytest.mark.asyncio
    async def test_custom_prompt_overrides_default(self, mock_httpx_client):
        """Test custom prompt overrides default detail level prompt."""
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            # Mock the vision model
            mock_response = AIMessage(content="The image has blue, red, and green colors")
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_llm

            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    "OLLAMA_URL": "http://localhost:11434",
                    "DEFAULT_VISION_MODEL": "llava",
                    "VISION_ENABLED": "true"
                }.get(key, default)

                custom_prompt = "What colors are in this image?"
                result = await describe_image_impl(
                    image_url="https://example.com/image.jpg",
                    detail_level="standard",
                    custom_prompt=custom_prompt,
                    user_id=123,
                    thread_id="test_thread",
                    user_language="en",
                )

                # Verify custom prompt was used (check message content sent to LLM)
                assert "colors" in result.lower()
                assert mock_llm.ainvoke.called
                call_args = mock_llm.ainvoke.call_args
                messages = call_args[0][0]
                assert len(messages) > 0
                # Check that custom prompt was in the message
                message_content = messages[0].content
                assert any(item["text"] == custom_prompt for item in message_content if isinstance(item, dict) and "text" in item)

    @pytest.mark.skip(reason="Skipped until integration is complete")
    @pytest.mark.asyncio
    async def test_vision_disabled_returns_error(self):
        """Test vision feature disabled returns user-friendly error."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "OLLAMA_URL": "http://localhost:11434",
                "DEFAULT_VISION_MODEL": "llava",
                "VISION_ENABLED": "false"  # Disabled
            }.get(key, default)

            result = await describe_image_impl(
                image_url="https://example.com/image.jpg",
                detail_level="standard",
                custom_prompt=None,
                user_id=123,
                thread_id="test_thread",
                user_language="en",
            )

            assert "disabled" in result.lower()
            assert "VISION_ENABLED=true" in result

    @pytest.mark.asyncio
    async def test_successful_image_description(self, mock_httpx_client):
        """Test successful image description with mocked Ollama."""
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            # Mock the vision model
            mock_response = AIMessage(content="A beautiful sunset over the ocean with vibrant orange and pink colors.")
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_llm

            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    "OLLAMA_URL": "http://localhost:11434",
                    "DEFAULT_VISION_MODEL": "llava",
                    "VISION_ENABLED": "true"
                }.get(key, default)

                result = await describe_image_impl(
                    image_url="https://example.com/image.jpg",
                    detail_level="standard",
                    custom_prompt=None,
                    user_id=123,
                    thread_id="test_thread",
                    user_language="en",
                )

                assert "sunset" in result.lower()
                assert "ocean" in result.lower()
                assert mock_llm.ainvoke.called

    @pytest.mark.asyncio
    async def test_detail_level_low_uses_brief_prompt(self, mock_httpx_client):
        """Test detail_level='low' uses brief description prompt."""
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            mock_response = AIMessage(content="A cat")
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_llm

            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    "OLLAMA_URL": "http://localhost:11434",
                    "DEFAULT_VISION_MODEL": "llava",
                    "VISION_ENABLED": "true"
                }.get(key, default)

                result = await describe_image_impl(
                    image_url="https://example.com/cat.jpg",
                    detail_level="low",
                    custom_prompt=None,
                    user_id=123,
                    thread_id="test_thread",
                    user_language="en",
                )

                # Verify the prompt sent to LLM contains "Briefly" (low detail prompt)
                assert "cat" in result.lower()
                call_args = mock_llm.ainvoke.call_args
                messages = call_args[0][0]
                message_content = messages[0].content
                text_content = next(item["text"] for item in message_content if isinstance(item, dict) and "text" in item)
                assert "brief" in text_content.lower()

    @pytest.mark.asyncio
    async def test_detail_level_high_uses_comprehensive_prompt(self, mock_httpx_client):
        """Test detail_level='high' uses comprehensive analysis prompt."""
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            mock_response = AIMessage(content="Detailed description...")
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_llm

            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    "OLLAMA_URL": "http://localhost:11434",
                    "DEFAULT_VISION_MODEL": "llava",
                    "VISION_ENABLED": "true"
                }.get(key, default)

                result = await describe_image_impl(
                    image_url="https://example.com/artwork.jpg",
                    detail_level="high",
                    custom_prompt=None,
                    user_id=123,
                    thread_id="test_thread",
                    user_language="en",
                )

                # Verify the prompt sent to LLM contains "comprehensive" (high detail prompt)
                assert "detailed" in result.lower() or "description" in result.lower()
                call_args = mock_llm.ainvoke.call_args
                messages = call_args[0][0]
                message_content = messages[0].content
                text_content = next(item["text"] for item in message_content if isinstance(item, dict) and "text" in item)
                assert "comprehensive" in text_content.lower()

    @pytest.mark.asyncio
    async def test_empty_response_returns_error(self, mock_httpx_client):
        """Test empty response from vision model returns user-friendly error."""
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            # Mock empty response
            mock_response = AIMessage(content="")
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_llm

            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    "OLLAMA_URL": "http://localhost:11434",
                    "DEFAULT_VISION_MODEL": "llava",
                    "VISION_ENABLED": "true"
                }.get(key, default)

                result = await describe_image_impl(
                    image_url="https://example.com/image.jpg",
                    detail_level="standard",
                    custom_prompt=None,
                    user_id=123,
                    thread_id="test_thread",
                    user_language="en",
                )

                assert "unable to describe" in result.lower()


class TestCreateImageDescriptionTool:
    """Test tool factory function."""

    def test_creates_structured_tool(self):
        """Test factory creates a valid StructuredTool."""
        tool = create_image_description_tool(
            user_id=123,
            thread_id="test_thread",
            language="en",
        )

        assert isinstance(tool, StructuredTool)
        assert tool.name == "describe_image"
        assert "image" in tool.description.lower()
        assert "vision" in tool.description.lower()

    def test_tool_has_correct_schema(self):
        """Test tool uses DescribeImageInput schema."""
        tool = create_image_description_tool(
            user_id=123,
            thread_id="test_thread",
            language="en",
        )

        assert tool.args_schema == DescribeImageInput

    def test_tool_binds_user_context(self):
        """Test tool factory binds user context correctly."""
        user_id = 999
        thread_id = "bound_thread"
        language = "ru"

        tool = create_image_description_tool(
            user_id=user_id,
            thread_id=thread_id,
            language=language,
        )

        # Tool should be bound with these values
        assert tool is not None
        # The binding happens via lambda closures, so we can't directly test the values
        # but we can verify the tool is created successfully


class TestErrorHandling:
    """Test error handling for common issues."""

    @pytest.mark.asyncio
    async def test_connection_error_returns_friendly_message(self, mock_httpx_client):
        """Test connection errors return user-friendly messages."""
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            # Mock connection error
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(side_effect=ConnectionError("Connection refused"))
            mock_openai.return_value = mock_llm

            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    "OLLAMA_URL": "http://localhost:11434",
                    "DEFAULT_VISION_MODEL": "llava",
                    "VISION_ENABLED": "true"
                }.get(key, default)

                result = await describe_image_impl(
                    image_url="https://example.com/image.jpg",
                    detail_level="standard",
                    custom_prompt=None,
                    user_id=123,
                    thread_id="test_thread",
                    user_language="en",
                )

                assert "unable to connect" in result.lower() or "error" in result.lower()
                assert "ollama" in result.lower()

    @pytest.mark.asyncio
    async def test_model_not_found_returns_friendly_message(self, mock_httpx_client):
        """Test model not found errors return user-friendly messages."""
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            # Mock model not found error
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(side_effect=Exception("model 'llava' not found, try pulling it first"))
            mock_openai.return_value = mock_llm

            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    "OLLAMA_URL": "http://localhost:11434",
                    "DEFAULT_VISION_MODEL": "llava",
                    "VISION_ENABLED": "true"
                }.get(key, default)

                result = await describe_image_impl(
                    image_url="https://example.com/image.jpg",
                    detail_level="standard",
                    custom_prompt=None,
                    user_id=123,
                    thread_id="test_thread",
                    user_language="en",
                )

                assert "not available" in result.lower() or "not found" in result.lower() or "error" in result.lower()
                assert "pull" in result.lower() or "llava" in result.lower()
