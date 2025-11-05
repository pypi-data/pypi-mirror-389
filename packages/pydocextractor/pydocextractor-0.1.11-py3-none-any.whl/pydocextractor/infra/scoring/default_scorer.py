"""
Default quality scorer implementation.

Uses domain rules for quality scoring.
"""

from __future__ import annotations

from ...domain import Document, NormalizedDoc, quality_score


class DefaultQualityScorer:
    """
    Default quality scorer using domain rules.

    Delegates to pure domain function for scoring logic.
    """

    def calculate_score(
        self,
        ndoc: NormalizedDoc,
        markdown: str,
        original: Document | None = None,
    ) -> float:
        """
        Calculate quality score for conversion.

        Args:
            ndoc: Normalized document
            markdown: Rendered markdown
            original: Original document (optional, unused in default implementation)

        Returns:
            Quality score between 0.0 and 1.0
        """
        return quality_score(ndoc, markdown)
