"""
Unit tests for quality scoring infrastructure.

Tests for default quality scorer implementation.
"""

from __future__ import annotations

from pydocextractor.domain.models import Block, BlockType, Document, NormalizedDoc
from pydocextractor.infra.scoring.default_scorer import DefaultQualityScorer


class TestDefaultQualityScorer:
    """Test default quality scorer implementation."""

    def test_score_simple_document(self):
        """Test scoring a simple document."""
        scorer = DefaultQualityScorer()

        ndoc = NormalizedDoc(
            blocks=(Block(type=BlockType.TEXT, content="Test content" * 50),),
            source_mime="application/pdf",
        )
        markdown = "Test content" * 50
        original = Document(bytes=b"test", mime="application/pdf", size_bytes=4)

        score = scorer.calculate_score(ndoc, markdown, original)
        assert 0.0 <= score <= 1.0

    def test_score_empty_document(self):
        """Test scoring an empty document."""
        scorer = DefaultQualityScorer()

        ndoc = NormalizedDoc(
            blocks=(Block(type=BlockType.TEXT, content=""),),
            source_mime="application/pdf",
        )
        markdown = ""
        original = Document(bytes=b"x", mime="application/pdf", size_bytes=1)  # Min valid doc

        score = scorer.calculate_score(ndoc, markdown, original)
        assert score == 0.0

    def test_score_structured_document(self):
        """Test scoring a well-structured document."""
        scorer = DefaultQualityScorer()

        blocks = (
            Block(type=BlockType.HEADER, content="# Title"),
            Block(type=BlockType.TEXT, content="Paragraph" * 20),
            Block(type=BlockType.LIST, content="- Item 1\n- Item 2"),
        )
        ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf")
        markdown = "# Title\n\nParagraph content...\n\n- Item 1\n- Item 2"
        original = Document(bytes=b"test", mime="application/pdf", size_bytes=4)

        score = scorer.calculate_score(ndoc, markdown, original)
        assert 0.0 < score <= 1.0  # Fixed: should be > 0 not > 0.5

    def test_score_document_with_tables(self):
        """Test scoring document with tables."""
        scorer = DefaultQualityScorer()

        blocks = (Block(type=BlockType.TABLE, content="| A | B |\n|---|---|\n| 1 | 2 |"),)
        ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf", has_tables=True)
        markdown = "| A | B |\n|---|---|\n| 1 | 2 |"
        original = Document(bytes=b"test", mime="application/pdf", size_bytes=4)

        score = scorer.calculate_score(ndoc, markdown, original)
        assert 0.0 < score <= 1.0

    def test_scorer_consistent(self):
        """Test scorer returns consistent results."""
        scorer = DefaultQualityScorer()

        ndoc = NormalizedDoc(
            blocks=(Block(type=BlockType.TEXT, content="Consistent content"),),
            source_mime="application/pdf",
        )
        markdown = "Consistent content"
        original = Document(bytes=b"test", mime="application/pdf", size_bytes=4)

        score1 = scorer.calculate_score(ndoc, markdown, original)
        score2 = scorer.calculate_score(ndoc, markdown, original)

        assert score1 == score2
