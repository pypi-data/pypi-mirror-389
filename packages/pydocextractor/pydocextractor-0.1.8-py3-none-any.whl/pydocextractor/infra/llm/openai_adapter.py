"""
OpenAI-compatible multimodal LLM adapter for image description.

This adapter implements the ImageDescriber protocol using OpenAI's API
or any OpenAI-compatible endpoint (e.g., Azure OpenAI, local models).
"""

from __future__ import annotations

import base64
import logging
from io import BytesIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydocextractor.domain.config import LLMConfig

logger = logging.getLogger(__name__)


class OpenAIImageDescriber:
    """
    OpenAI-compatible multimodal LLM adapter (synchronous).

    This adapter:
    1. Resizes images to fixed dimensions (1024x1024)
    2. Encodes images as base64
    3. Calls OpenAI-compatible vision API
    4. Returns textual description

    Requires: httpx, Pillow
    """

    def __init__(self, config: LLMConfig) -> None:
        """
        Initialize OpenAI image describer.

        Args:
            config: LLM configuration

        Raises:
            ImportError: If required dependencies not installed
        """
        try:
            import httpx  # noqa: F401
            from PIL import Image  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "LLM dependencies not installed. Install with: pip install pydocextractor[llm]"
            ) from e

        self.config = config

        try:
            import httpx

            self.client = httpx.Client(timeout=config.timeout_seconds)
            logger.info("LLM client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise

    def describe_image(
        self,
        image_data: bytes,
        context_text: str,
        mime_type: str,
    ) -> str:
        """
        Describe an image using LLM with context.

        Args:
            image_data: Raw image bytes
            context_text: Previous text context (last N lines)
            mime_type: Image MIME type (e.g., "image/jpeg")

        Returns:
            Image description from LLM

        Raises:
            Exception: If LLM call fails (caller should handle)
        """
        import httpx

        # 1. Resize image to 1024x1024
        resized_image = self._resize_image(image_data)

        # 2. Base64 encode
        base64_image = base64.b64encode(resized_image).decode("utf-8")

        # 3. Build prompt
        prompt = self._build_prompt(context_text)

        # 4. Call OpenAI API
        try:
            response = self.client.post(
                self.config.api_url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                },
                            ],
                        }
                    ],
                    "max_tokens": 600,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            raise
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise

        # 5. Extract description
        result = response.json()
        description = result["choices"][0]["message"]["content"]
        return str(description)

    def _resize_image(self, image_data: bytes) -> bytes:
        """
        Resize image to 1024x1024 maintaining aspect ratio with padding.

        Args:
            image_data: Original image bytes

        Returns:
            Resized image bytes (JPEG format)

        Raises:
            Exception: If image processing fails
        """
        try:
            from PIL import Image

            # Open image
            img: Image.Image = Image.open(BytesIO(image_data))

            # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Calculate resize dimensions (maintain aspect ratio)
            target_size = self.config.image_size
            img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

            # Create new image with white background
            new_img = Image.new("RGB", (target_size, target_size), (255, 255, 255))

            # Paste resized image centered
            offset = ((target_size - img.width) // 2, (target_size - img.height) // 2)
            new_img.paste(img, offset)

            # Convert to bytes
            buffer = BytesIO()
            new_img.save(buffer, format="JPEG", quality=85)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Failed to resize image: {e}")
            raise

    def _build_prompt(self, context_text: str) -> str:
        """
        Build prompt with context.

        Args:
            context_text: Context from previous text

        Returns:
            Formatted prompt
        """
        if context_text.strip():
            return f"""You are analyzing a document. Based on the following context (previous text):

{context_text}

{self.config.prompt_template}"""
        else:
            return (
                "Please describe this image in detail. "
                "Keep the description concise (2-3 sentences)."
            )

    def close(self) -> None:
        """Close HTTP client."""
        try:
            self.client.close()
        except Exception as e:
            logger.error(f"Error closing LLM client: {e}")
