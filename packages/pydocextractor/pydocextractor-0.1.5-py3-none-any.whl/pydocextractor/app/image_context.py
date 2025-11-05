"""
Image context tracking for LLM-based description.

This module provides utilities for tracking text context around images
to provide better context to LLM when describing images.
"""

from __future__ import annotations


class ImageContextTracker:
    """
    Tracks text context for image description.

    Maintains a rolling buffer of text lines to provide context
    to LLM when describing images. Typically keeps the last N lines
    of text that appear before an image.
    """

    def __init__(self, context_lines: int = 100) -> None:
        """
        Initialize context tracker.

        Args:
            context_lines: Maximum number of lines to keep in context
        """
        self.context_lines = context_lines
        self.text_buffer: list[str] = []

    def add_text(self, text: str) -> None:
        """
        Add text lines to context buffer.

        Args:
            text: Text to add (may contain multiple lines)
        """
        lines = text.split("\n")
        self.text_buffer.extend(lines)

        # Keep only last N lines
        if len(self.text_buffer) > self.context_lines:
            self.text_buffer = self.text_buffer[-self.context_lines :]

    def get_context(self) -> str:
        """
        Get current context as string.

        Returns:
            Current context text (last N lines joined)
        """
        return "\n".join(self.text_buffer)

    def clear(self) -> None:
        """Clear context buffer."""
        self.text_buffer = []

    def __len__(self) -> int:
        """Get number of lines in buffer."""
        return len(self.text_buffer)
