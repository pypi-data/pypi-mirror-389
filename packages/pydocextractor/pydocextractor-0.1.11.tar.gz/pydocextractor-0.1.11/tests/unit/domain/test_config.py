"""
Unit tests for domain configuration models.

Tests LLMConfig validation and behavior.
"""

import pytest

from pydocextractor.domain.config import LLMConfig


class TestLLMConfig:
    """Test LLMConfig domain model."""

    def test_create_valid_config(self):
        """Test creating valid LLM configuration."""
        config = LLMConfig(
            api_url="https://api.openai.com/v1/chat/completions",
            api_key="sk-test123",
            model_name="gpt-4o-mini",
        )

        assert config.api_url == "https://api.openai.com/v1/chat/completions"
        assert config.api_key == "sk-test123"
        assert config.model_name == "gpt-4o-mini"
        assert config.enabled is True
        assert config.context_lines == 100  # default
        assert config.timeout_seconds == 30  # default
        assert config.max_retries == 3  # default
        assert config.image_size == 1024  # default
        assert config.max_images_per_document == 5  # default

    def test_create_with_custom_values(self):
        """Test creating config with custom values."""
        config = LLMConfig(
            api_url="http://localhost:8000/v1/chat/completions",
            api_key="local-key",
            model_name="llava:13b",
            context_lines=200,
            enabled=True,
            timeout_seconds=60,
            max_retries=5,
            image_size=512,
            max_images_per_document=10,
        )

        assert config.api_url == "http://localhost:8000/v1/chat/completions"
        assert config.model_name == "llava:13b"
        assert config.context_lines == 200
        assert config.timeout_seconds == 60
        assert config.max_retries == 5
        assert config.image_size == 512
        assert config.max_images_per_document == 10

    def test_config_is_frozen(self):
        """Test that config is immutable."""
        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
        )

        with pytest.raises(AttributeError):
            config.api_url = "https://different.com"  # type: ignore

    def test_validation_negative_context_lines(self):
        """Test validation rejects negative context lines."""
        with pytest.raises(ValueError, match="context_lines must be non-negative"):
            LLMConfig(
                api_url="https://api.test.com",
                api_key="test-key",
                context_lines=-1,
            )

    def test_validation_zero_context_lines(self):
        """Test validation allows zero context lines."""
        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            context_lines=0,
        )
        assert config.context_lines == 0

    def test_validation_negative_timeout(self):
        """Test validation rejects negative timeout."""
        with pytest.raises(ValueError, match="timeout_seconds must be at least 1"):
            LLMConfig(
                api_url="https://api.test.com",
                api_key="test-key",
                timeout_seconds=-5,
            )

    def test_validation_negative_max_retries(self):
        """Test validation rejects negative max retries."""
        with pytest.raises(ValueError, match="max_retries must be at least 1"):
            LLMConfig(
                api_url="https://api.test.com",
                api_key="test-key",
                max_retries=-1,
            )

    def test_validation_negative_image_size(self):
        """Test validation rejects negative image size."""
        with pytest.raises(ValueError, match="image_size must be at least 128"):
            LLMConfig(
                api_url="https://api.test.com",
                api_key="test-key",
                image_size=-100,
            )

    def test_validation_negative_max_images(self):
        """Test validation rejects negative max images below -1."""
        with pytest.raises(ValueError, match="max_images_per_document must be -1 or at least 1"):
            LLMConfig(
                api_url="https://api.test.com",
                api_key="test-key",
                max_images_per_document=-2,
            )

    def test_validation_zero_max_images(self):
        """Test validation rejects zero max images."""
        with pytest.raises(ValueError, match="max_images_per_document must be -1 or at least 1"):
            LLMConfig(
                api_url="https://api.test.com",
                api_key="test-key",
                max_images_per_document=0,
            )

    def test_unlimited_max_images(self):
        """Test that -1 max images is accepted for unlimited processing."""
        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            max_images_per_document=-1,
        )
        assert config.max_images_per_document == -1

    def test_validation_empty_api_url(self):
        """Test validation rejects empty API URL."""
        with pytest.raises(ValueError, match="api_url is required when LLM is enabled"):
            LLMConfig(
                api_url="",
                api_key="test-key",
            )

    def test_validation_empty_api_key(self):
        """Test validation rejects empty API key."""
        with pytest.raises(ValueError, match="api_key is required when LLM is enabled"):
            LLMConfig(
                api_url="https://api.test.com",
                api_key="",
            )

    def test_validation_empty_model_name(self):
        """Test that empty model name is allowed (no validation)."""
        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            model_name="",
        )
        assert config.model_name == ""

    def test_disabled_config_still_validates(self):
        """Test that disabled configs still validate parameters."""
        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            enabled=False,
        )

        assert config.enabled is False
        assert config.api_url == "https://api.test.com"

    def test_zero_max_retries_not_allowed(self):
        """Test that zero max retries is rejected (minimum is 1)."""
        with pytest.raises(ValueError, match="max_retries must be at least 1"):
            LLMConfig(
                api_url="https://api.test.com",
                api_key="test-key",
                max_retries=0,
            )

    def test_config_equality(self):
        """Test config equality comparison."""
        config1 = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
        )
        config2 = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
        )

        assert config1 == config2

    def test_config_inequality(self):
        """Test config inequality comparison."""
        config1 = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
        )
        config2 = LLMConfig(
            api_url="https://api.different.com",
            api_key="test-key",
        )

        assert config1 != config2

    def test_config_hashable(self):
        """Test that config is hashable (can be used in sets/dicts)."""
        config1 = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
        )
        config2 = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
        )

        config_set = {config1, config2}
        assert len(config_set) == 1  # Same config, only one in set
