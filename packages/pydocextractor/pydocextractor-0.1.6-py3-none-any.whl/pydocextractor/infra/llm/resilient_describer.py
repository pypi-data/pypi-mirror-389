"""
Resilient wrapper for image describers with retry logic and fallbacks.

This module provides a decorator-style wrapper that adds retry logic,
exponential backoff, and graceful fallbacks to any ImageDescriber.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydocextractor.domain.config import LLMConfig
    from pydocextractor.domain.ports import ImageDescriber

logger = logging.getLogger(__name__)


class ResilientImageDescriber:
    """
    Wrapper with retry logic and fallbacks (synchronous).

    This wrapper adds:
    - Configurable retry attempts with exponential backoff
    - Graceful fallback to placeholder text on failure
    - Comprehensive error logging
    - Timeout handling
    """

    def __init__(self, base_describer: ImageDescriber, config: LLMConfig) -> None:
        """
        Initialize resilient wrapper.

        Args:
            base_describer: Underlying image describer to wrap
            config: LLM configuration with retry settings
        """
        self.base = base_describer
        self.config = config

    def describe_image(
        self,
        image_data: bytes,
        context: str,
        mime: str,
    ) -> str:
        """
        Describe image with retries and fallback.

        Args:
            image_data: Raw image bytes
            context: Text context
            mime: Image MIME type

        Returns:
            Image description or fallback message
        """
        last_error: Exception | None = None

        for attempt in range(self.config.max_retries):
            try:
                description = self.base.describe_image(image_data, context, mime)
                if attempt > 0:
                    logger.info(f"LLM request succeeded on retry {attempt + 1}")
                return description

            except Exception as e:
                last_error = e
                attempt_num = attempt + 1

                # Import inside try block to handle optional dependency
                try:
                    import httpx

                    if isinstance(e, httpx.TimeoutException):
                        logger.warning(
                            f"LLM timeout (attempt {attempt_num}/{self.config.max_retries})"
                        )
                    elif isinstance(e, httpx.HTTPStatusError):
                        logger.error(
                            f"LLM API error: {e.response.status_code} "
                            f"(attempt {attempt_num}/{self.config.max_retries})"
                        )
                        # Don't retry on auth errors (401, 403)
                        if e.response.status_code in (401, 403):
                            logger.error("Authentication failed, not retrying")
                            break
                    else:
                        logger.warning(
                            f"LLM request failed: {e} "
                            f"(attempt {attempt_num}/{self.config.max_retries})"
                        )
                except ImportError:
                    # httpx not available, just log generic error
                    logger.warning(
                        f"LLM request failed: {e} (attempt {attempt_num}/{self.config.max_retries})"
                    )

                # Exponential backoff before retry (except on last attempt)
                if attempt < self.config.max_retries - 1:
                    backoff_seconds = 2**attempt  # 1s, 2s, 4s, ...
                    logger.debug(f"Waiting {backoff_seconds}s before retry")
                    time.sleep(backoff_seconds)

        # All retries exhausted
        logger.error(f"All {self.config.max_retries} LLM attempts failed. Last error: {last_error}")
        return self._fallback_description()

    def _fallback_description(self) -> str:
        """
        Fallback description when LLM fails.

        Returns:
            Placeholder text indicating description unavailable
        """
        return "[Image description unavailable]"
