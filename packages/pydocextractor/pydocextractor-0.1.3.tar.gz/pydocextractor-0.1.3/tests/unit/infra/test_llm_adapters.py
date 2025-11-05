"""
Unit tests for LLM adapters.

Tests OpenAI adapter and resilient wrapper with mocked HTTP calls.
"""

import io
from unittest.mock import Mock, patch

import pytest

from pydocextractor.domain.config import LLMConfig

# Skip if LLM dependencies not installed
pytest.importorskip("httpx")
pytest.importorskip("PIL")

from pydocextractor.infra.llm.openai_adapter import OpenAIImageDescriber
from pydocextractor.infra.llm.resilient_describer import ResilientImageDescriber


@pytest.fixture
def llm_config():
    """Create test LLM configuration."""
    return LLMConfig(
        api_url="https://api.test.com/v1/chat/completions",
        api_key="test-key-123",
        model_name="gpt-4o-mini",
        context_lines=100,
        timeout_seconds=30,
        max_retries=3,
        image_size=1024,
    )


@pytest.fixture
def sample_image_bytes():
    """Create sample image bytes for testing."""
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


class TestOpenAIImageDescriber:
    """Test OpenAI image describer adapter."""

    def test_init(self, llm_config):
        """Test initializing OpenAI describer."""
        describer = OpenAIImageDescriber(llm_config)

        assert describer.config == llm_config
        assert describer.client is not None

    @patch("httpx.Client.post")
    def test_describe_image_success(self, mock_post, llm_config, sample_image_bytes):
        """Test successful image description."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "A red square image"}}]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        describer = OpenAIImageDescriber(llm_config)
        description = describer.describe_image(
            image_data=sample_image_bytes,
            context_text="Some context",
            mime_type="image/png",
        )

        assert description == "A red square image"
        assert mock_post.called

    @patch("httpx.Client.post")
    def test_describe_image_with_context(self, mock_post, llm_config, sample_image_bytes):
        """Test image description includes context."""
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Description"}}]}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        describer = OpenAIImageDescriber(llm_config)
        context = "This is important context\nWith multiple lines"

        describer.describe_image(
            image_data=sample_image_bytes,
            context_text=context,
            mime_type="image/png",
        )

        # Verify context was included in request
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        assert "messages" in request_data
        # Context should be in the prompt
        prompt = str(request_data["messages"])
        assert "important context" in prompt.lower()

    @patch("httpx.Client.post")
    def test_describe_image_api_error(self, mock_post, llm_config, sample_image_bytes):
        """Test handling API errors."""
        mock_post.side_effect = Exception("API Error")

        describer = OpenAIImageDescriber(llm_config)

        with pytest.raises(Exception, match="API Error"):
            describer.describe_image(
                image_data=sample_image_bytes,
                context_text="",
                mime_type="image/png",
            )

    def test_resize_image(self, llm_config, sample_image_bytes):
        """Test image resizing logic."""
        describer = OpenAIImageDescriber(llm_config)

        resized = describer._resize_image(sample_image_bytes)

        # Verify resized image
        from PIL import Image

        img = Image.open(io.BytesIO(resized))
        assert img.size == (1024, 1024)
        assert img.mode == "RGB"

    def test_resize_large_image(self, llm_config):
        """Test resizing larger image."""
        from PIL import Image

        # Create 2000x1000 image
        img = Image.new("RGB", (2000, 1000), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")

        describer = OpenAIImageDescriber(llm_config)
        resized = describer._resize_image(img_bytes.getvalue())

        # Should be resized to 1024x1024 with padding
        result_img = Image.open(io.BytesIO(resized))
        assert result_img.size == (1024, 1024)

    def test_resize_small_image(self, llm_config):
        """Test resizing smaller image."""
        from PIL import Image

        # Create 50x50 image
        img = Image.new("RGB", (50, 50), color="green")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")

        describer = OpenAIImageDescriber(llm_config)
        resized = describer._resize_image(img_bytes.getvalue())

        # Should be padded to 1024x1024
        result_img = Image.open(io.BytesIO(resized))
        assert result_img.size == (1024, 1024)

    def test_resize_preserves_aspect_ratio(self, llm_config):
        """Test that resize preserves aspect ratio."""
        from PIL import Image

        # Create 800x400 image (2:1 ratio)
        img = Image.new("RGB", (800, 400), color="yellow")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")

        describer = OpenAIImageDescriber(llm_config)
        resized = describer._resize_image(img_bytes.getvalue())

        result_img = Image.open(io.BytesIO(resized))
        # Final image should be 1024x1024 with white padding
        assert result_img.size == (1024, 1024)

    def test_convert_non_rgb_image(self, llm_config):
        """Test converting non-RGB image."""
        from PIL import Image

        # Create RGBA image
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")

        describer = OpenAIImageDescriber(llm_config)
        resized = describer._resize_image(img_bytes.getvalue())

        # Should be converted to RGB
        result_img = Image.open(io.BytesIO(resized))
        assert result_img.mode == "RGB"


class TestResilientImageDescriber:
    """Test resilient image describer wrapper."""

    def test_init(self, llm_config):
        """Test initializing resilient wrapper."""
        base_describer = Mock()
        resilient = ResilientImageDescriber(base_describer, llm_config)

        assert resilient.base == base_describer
        assert resilient.config == llm_config

    def test_describe_success_first_try(self, llm_config, sample_image_bytes):
        """Test successful description on first try."""
        base_describer = Mock()
        base_describer.describe_image.return_value = "Success description"

        resilient = ResilientImageDescriber(base_describer, llm_config)
        description = resilient.describe_image(
            sample_image_bytes,
            "Context",
            "image/png",
        )

        assert description == "Success description"
        assert base_describer.describe_image.call_count == 1

    def test_describe_retry_on_failure(self, llm_config, sample_image_bytes):
        """Test retry logic on failure."""
        base_describer = Mock()
        # Fail twice, succeed on third attempt
        base_describer.describe_image.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            "Success after retries",
        ]

        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            max_retries=3,
        )

        resilient = ResilientImageDescriber(base_describer, config)
        description = resilient.describe_image(
            sample_image_bytes,
            "Context",
            "image/png",
        )

        assert description == "Success after retries"
        assert base_describer.describe_image.call_count == 3

    def test_describe_all_retries_fail(self, llm_config, sample_image_bytes):
        """Test when all retries fail."""
        base_describer = Mock()
        base_describer.describe_image.side_effect = Exception("Persistent error")

        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            max_retries=2,
        )

        resilient = ResilientImageDescriber(base_describer, config)
        description = resilient.describe_image(
            sample_image_bytes,
            "Context",
            "image/png",
        )

        # Should return fallback message
        assert description == "[Image description unavailable]"
        assert base_describer.describe_image.call_count == 2  # max_retries attempts

    def test_describe_no_retries(self, llm_config, sample_image_bytes):
        """Test with max_retries=1 (minimum allowed)."""
        base_describer = Mock()
        base_describer.describe_image.side_effect = Exception("Error")

        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            max_retries=1,
        )

        resilient = ResilientImageDescriber(base_describer, config)
        description = resilient.describe_image(
            sample_image_bytes,
            "Context",
            "image/png",
        )

        # Should return fallback after single attempt
        assert description == "[Image description unavailable]"
        assert base_describer.describe_image.call_count == 1

    @patch("time.sleep")
    def test_exponential_backoff(self, mock_sleep, llm_config, sample_image_bytes):
        """Test exponential backoff between retries."""
        base_describer = Mock()
        base_describer.describe_image.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            "Success",
        ]

        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            max_retries=3,
        )

        resilient = ResilientImageDescriber(base_describer, config)
        resilient.describe_image(
            sample_image_bytes,
            "Context",
            "image/png",
        )

        # Verify exponential backoff: 1s, 2s
        assert mock_sleep.call_count == 2
        call_args = [call[0][0] for call in mock_sleep.call_args_list]
        assert call_args[0] == 1  # First retry: 1 second
        assert call_args[1] == 2  # Second retry: 2 seconds

    def test_http_status_error_retry(self, llm_config, sample_image_bytes):
        """Test retry on HTTP status errors."""
        from httpx import HTTPStatusError, Request, Response

        base_describer = Mock()

        # Create mock HTTP error
        mock_request = Mock(spec=Request)
        mock_response = Mock(spec=Response)
        mock_response.status_code = 500

        base_describer.describe_image.side_effect = [
            HTTPStatusError("Server error", request=mock_request, response=mock_response),
            "Success after retry",
        ]

        resilient = ResilientImageDescriber(base_describer, llm_config)
        description = resilient.describe_image(
            sample_image_bytes,
            "Context",
            "image/png",
        )

        assert description == "Success after retry"
        assert base_describer.describe_image.call_count == 2
