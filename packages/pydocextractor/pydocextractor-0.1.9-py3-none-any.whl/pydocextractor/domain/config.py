"""
Configuration models for pyDocExtractor.

Pure domain configuration without external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass

# Constants for configuration validation
MIN_IMAGE_SIZE = 128
MIN_IMAGES_PER_DOCUMENT = 1
MIN_CONTEXT_LINES = 0
MIN_TIMEOUT_SECONDS = 1


@dataclass(frozen=True, slots=True)
class LLMConfig:
    """
    LLM configuration for image description.

    This configuration enables optional integration with OpenAI-compatible
    multimodal LLMs to automatically describe images found in documents.
    """

    api_url: str
    api_key: str
    model_name: str = "gpt-4-vision-preview"
    context_lines: int = 100
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    image_size: int = 1024
    max_images_per_document: int = 5
    prompt_template: str = (
        "Please describe the image in detail, considering the context provided. "
        "Focus on how the image relates to the surrounding content. "
        "Keep the description concise (2-3 sentences)."
    )

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.enabled:
            if not self.api_url:
                raise ValueError("api_url is required when LLM is enabled")
            if not self.api_key:
                raise ValueError("api_key is required when LLM is enabled")
        if self.max_images_per_document < -1 or self.max_images_per_document == 0:
            raise ValueError("max_images_per_document must be -1 or at least 1")
        if self.image_size < MIN_IMAGE_SIZE:
            raise ValueError("image_size must be at least 128")
        if self.context_lines < MIN_CONTEXT_LINES:
            raise ValueError("context_lines must be non-negative")
        if self.timeout_seconds < MIN_TIMEOUT_SECONDS:
            raise ValueError("timeout_seconds must be at least 1")
        if self.max_retries < 1:
            raise ValueError("max_retries must be at least 1")
