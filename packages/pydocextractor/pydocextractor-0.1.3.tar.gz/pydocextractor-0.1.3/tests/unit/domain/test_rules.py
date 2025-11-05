"""
Unit tests for domain rules (pure functions).

Tests business logic functions with no side effects.
"""

from __future__ import annotations

from pydocextractor.domain.models import Block, BlockType, Document, NormalizedDoc
from pydocextractor.domain.rules import calculate_document_hash, hint_has_tables, quality_score


class TestQualityScore:
    """Test quality_score pure function."""

    def test_empty_document_score(self):
        """Test quality score for minimal document."""
        # NormalizedDoc requires at least one block
        ndoc = NormalizedDoc(
            blocks=(Block(type=BlockType.TEXT, content=""),), source_mime="application/pdf"
        )
        markdown = ""
        score = quality_score(ndoc, markdown)
        assert score == 0.0

    def test_simple_text_score(self):
        """Test quality score for simple text."""
        blocks = (Block(type=BlockType.TEXT, content="Hello world" * 50),)
        ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf")
        markdown = "Hello world" * 50
        score = quality_score(ndoc, markdown)
        assert 0.0 < score <= 1.0

    def test_structured_document_score(self):
        """Test quality score for well-structured document."""
        blocks = (
            Block(type=BlockType.HEADER, content="# Main Title"),
            Block(type=BlockType.HEADER, content="## Section 1"),
            Block(type=BlockType.TEXT, content="Paragraph content here." * 20),
            Block(type=BlockType.LIST, content="- Item 1\n- Item 2\n- Item 3"),
            Block(
                type=BlockType.TABLE,
                content="| Col1 | Col2 |\n|------|------|\n| A    | B    |",
            ),
        )
        ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf", has_tables=True)

        markdown = (
            """
# Main Title

## Section 1

Paragraph content here. """
            + "More content. " * 20
            + """

- Item 1
- Item 2
- Item 3

| Col1 | Col2 |
|------|------|
| A    | B    |
        """
        )

        score = quality_score(ndoc, markdown)
        assert score >= 0.7  # Well-structured document should score high
        assert score <= 1.0

    def test_long_content_score(self):
        """Test quality score with long content."""
        long_text = "Word " * 1000  # 1000 words
        blocks = (
            Block(type=BlockType.HEADER, content="# Title"),
            Block(type=BlockType.TEXT, content=long_text),
        )
        ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf")
        markdown = f"# Title\n\n{long_text}"

        score = quality_score(ndoc, markdown)
        assert 0.5 < score <= 1.0  # Long documents with structure score well

    def test_table_content_score(self):
        """Test quality score with tables."""
        blocks = (
            Block(
                type=BlockType.TABLE,
                content="| H1 | H2 | H3 |\n|----|----|----|\n| A  | B  | C  |",
            ),
        )
        ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf", has_tables=True)
        markdown = "| H1 | H2 | H3 |\n|----|----|----|\n| A  | B  | C  |"

        score = quality_score(ndoc, markdown)
        assert score > 0.0
        assert score <= 1.0

    def test_score_capped_at_one(self):
        """Test quality score is always capped at 1.0."""
        # Create a very rich document
        blocks = tuple(
            Block(type=BlockType.TEXT, content="Perfect content " * 100) for _ in range(10)
        )
        ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf")
        markdown = "\n\n".join(["Perfect content " * 100 for _ in range(10)])

        score = quality_score(ndoc, markdown)
        assert score <= 1.0


class TestCalculateDocumentHash:
    """Test calculate_document_hash pure function."""

    def test_hash_deterministic(self):
        """Test hash is deterministic for same document."""
        doc = Document(
            bytes=b"Test content",
            mime="application/pdf",
            size_bytes=12,
        )

        hash1 = calculate_document_hash(doc)
        hash2 = calculate_document_hash(doc)

        assert hash1 == hash2

    def test_hash_format(self):
        """Test hash is SHA-256 (64 hex characters)."""
        doc = Document(
            bytes=b"Test content",
            mime="application/pdf",
            size_bytes=12,
        )

        doc_hash = calculate_document_hash(doc)
        assert len(doc_hash) == 64
        assert all(c in "0123456789abcdef" for c in doc_hash)

    def test_different_content_different_hash(self):
        """Test different content produces different hash."""
        doc1 = Document(
            bytes=b"Content A",
            mime="application/pdf",
            size_bytes=9,
        )
        doc2 = Document(
            bytes=b"Content B",
            mime="application/pdf",
            size_bytes=9,
        )

        hash1 = calculate_document_hash(doc1)
        hash2 = calculate_document_hash(doc2)

        assert hash1 != hash2

    def test_hash_with_real_document(self, policy_report_pdf, load_test_document):
        """Test hash calculation with real PDF document."""
        doc = load_test_document(policy_report_pdf)
        doc_hash = calculate_document_hash(doc)

        assert len(doc_hash) == 64
        # Hash should be consistent for same file
        doc2 = load_test_document(policy_report_pdf)
        hash2 = calculate_document_hash(doc2)
        assert doc_hash == hash2


class TestHintHasTables:
    """Test hint_has_tables heuristic function."""

    def test_small_pdf_no_hint(self):
        """Test small PDF returns no table hint."""
        doc = Document(
            bytes=b"Small PDF" * 10,
            mime="application/pdf",
            size_bytes=90,
        )
        has_tables = hint_has_tables(doc)
        assert has_tables is False

    def test_excel_file_has_tables(self):
        """Test Excel file is hinted as having tables."""
        doc = Document(
            bytes=b"Excel content",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            size_bytes=13,
        )
        has_tables = hint_has_tables(doc)
        assert has_tables is True

    def test_xls_file_has_tables(self):
        """Test XLS file is hinted as having tables."""
        doc = Document(
            bytes=b"XLS content",
            mime="application/vnd.ms-excel",
            size_bytes=11,
        )
        has_tables = hint_has_tables(doc)
        assert has_tables is True

    def test_large_pdf_might_have_tables(self):
        """Test large PDF (>0.5MB) with metadata hint."""
        doc = Document(
            bytes=b"x" * (11 * 1024 * 1024),  # 11 MB
            mime="application/pdf",
            size_bytes=11 * 1024 * 1024,
            metadata={"has_tables": True},  # Metadata hint
        )
        has_tables = hint_has_tables(doc)
        assert has_tables is True

    def test_docx_no_hint(self):
        """Test DOCX file has no automatic table hint."""
        doc = Document(
            bytes=b"DOCX content",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=12,
        )
        has_tables = hint_has_tables(doc)
        assert has_tables is False

    def test_hint_with_real_excel(self, sales_xlsx, load_test_document):
        """Test table hint with real Excel file."""
        doc = load_test_document(sales_xlsx)
        has_tables = hint_has_tables(doc)
        assert has_tables is True  # Excel files should always hint tables

    def test_hint_with_real_pdf(self, policy_report_pdf, load_test_document):
        """Test table hint with real PDF."""
        doc = load_test_document(policy_report_pdf)
        has_tables = hint_has_tables(doc)
        # Result depends on file size, just verify it returns a bool
        assert isinstance(has_tables, bool)


class TestNormalizeBlocks:
    """Test normalize_blocks pure function."""

    def test_normalize_empty_blocks(self):
        """Test normalizing empty block list."""
        from pydocextractor.domain.rules import normalize_blocks

        result = normalize_blocks([])
        assert result == ()

    def test_normalize_filters_empty_content(self):
        """Test that blocks with empty content are filtered out."""
        from pydocextractor.domain.rules import normalize_blocks

        blocks = [
            Block(type=BlockType.TEXT, content="Valid content"),
            Block(type=BlockType.TEXT, content="   "),  # Only whitespace
            Block(type=BlockType.TEXT, content=""),  # Empty
            Block(type=BlockType.TEXT, content="Another valid"),
        ]

        result = normalize_blocks(blocks)
        assert len(result) == 2
        assert result[0].content == "Valid content"
        assert result[1].content == "Another valid"

    def test_normalize_filters_zero_confidence(self):
        """Test that blocks with zero confidence are filtered."""
        from pydocextractor.domain.rules import normalize_blocks

        blocks = [
            Block(type=BlockType.TEXT, content="High confidence", confidence=0.9),
            Block(type=BlockType.TEXT, content="Zero confidence", confidence=0.0),
            Block(type=BlockType.TEXT, content="Another good", confidence=0.8),
        ]

        result = normalize_blocks(blocks)
        assert len(result) == 2
        assert result[0].content == "High confidence"
        assert result[1].content == "Another good"

    def test_normalize_sorts_by_page_and_type(self):
        """Test that blocks are sorted by page number and type."""
        from pydocextractor.domain.rules import normalize_blocks

        blocks = [
            Block(type=BlockType.TEXT, content="Page 2", page_number=2),
            Block(type=BlockType.HEADER, content="Page 1 Header", page_number=1),
            Block(type=BlockType.TEXT, content="Page 1 Text", page_number=1),
        ]

        result = normalize_blocks(blocks)
        assert len(result) == 3
        # Should be sorted by page, then by type
        assert result[0].page_number == 1
        assert result[1].page_number == 1
        assert result[2].page_number == 2


class TestMergeTextBlocks:
    """Test merge_text_blocks pure function."""

    def test_merge_empty_blocks(self):
        """Test merging empty block list."""
        from pydocextractor.domain.rules import merge_text_blocks

        result = merge_text_blocks([])
        assert result == ()

    def test_merge_consecutive_text_same_page(self):
        """Test merging consecutive text blocks on same page."""
        from pydocextractor.domain.rules import merge_text_blocks

        blocks = [
            Block(type=BlockType.TEXT, content="First paragraph", page_number=1),
            Block(type=BlockType.TEXT, content="Second paragraph", page_number=1),
            Block(type=BlockType.TEXT, content="Third paragraph", page_number=1),
        ]

        result = merge_text_blocks(blocks)
        assert len(result) == 1
        assert "First paragraph\n\nSecond paragraph\n\nThird paragraph" in result[0].content

    def test_merge_preserves_non_text_blocks(self):
        """Test that non-text blocks are preserved."""
        from pydocextractor.domain.rules import merge_text_blocks

        blocks = [
            Block(type=BlockType.TEXT, content="Text 1", page_number=1),
            Block(type=BlockType.TABLE, content="Table content", page_number=1),
            Block(type=BlockType.TEXT, content="Text 2", page_number=1),
        ]

        result = merge_text_blocks(blocks)
        assert len(result) == 3
        assert result[0].type == BlockType.TEXT
        assert result[1].type == BlockType.TABLE
        assert result[2].type == BlockType.TEXT

    def test_merge_respects_page_boundaries(self):
        """Test that text blocks on different pages are not merged."""
        from pydocextractor.domain.rules import merge_text_blocks

        blocks = [
            Block(type=BlockType.TEXT, content="Page 1 text", page_number=1),
            Block(type=BlockType.TEXT, content="Page 2 text", page_number=2),
        ]

        result = merge_text_blocks(blocks)
        assert len(result) == 2
        assert result[0].content == "Page 1 text"
        assert result[1].content == "Page 2 text"


class TestValidatePrecisionLevel:
    """Test validate_precision_level pure function."""

    def test_validate_level_in_available(self):
        """Test validation when level is available."""
        from pydocextractor.domain.rules import validate_precision_level

        assert validate_precision_level(2, [1, 2, 3, 4]) is True

    def test_validate_level_not_available(self):
        """Test validation when level is not available."""
        from pydocextractor.domain.rules import validate_precision_level

        assert validate_precision_level(5, [1, 2, 3, 4]) is False

    def test_validate_empty_available_levels(self):
        """Test validation with empty available levels."""
        from pydocextractor.domain.rules import validate_precision_level

        assert validate_precision_level(1, []) is False


class TestEstimateProcessingTime:
    """Test estimate_processing_time pure function."""

    def test_estimate_small_doc_level_1(self):
        """Test estimation for small document at level 1."""
        from pydocextractor.domain.rules import estimate_processing_time

        doc = Document(
            bytes=b"x" * 1024,  # 1 KB
            mime="application/pdf",
            size_bytes=1024,
        )

        time = estimate_processing_time(doc, 1)
        assert 0.1 <= time <= 1.0  # Should be very fast

    def test_estimate_large_doc_level_4(self):
        """Test estimation for large document at level 4."""
        from pydocextractor.domain.rules import estimate_processing_time

        doc = Document(
            bytes=b"x" * (10 * 1024 * 1024),  # 10 MB
            mime="application/pdf",
            size_bytes=10 * 1024 * 1024,
        )

        time = estimate_processing_time(doc, 4)
        assert time > 60.0  # Should take significant time

    def test_estimate_unknown_level(self):
        """Test estimation with unknown precision level."""
        from pydocextractor.domain.rules import estimate_processing_time

        doc = Document(
            bytes=b"test",
            mime="application/pdf",
            size_bytes=4,
        )

        time = estimate_processing_time(doc, 99)  # Unknown level
        assert time > 0  # Should still return a valid time


class TestBuildTemplateContext:
    """Test build_template_context pure function."""

    def test_build_context_from_normalized_doc(self):
        """Test building template context."""
        from pydocextractor.domain.rules import build_template_context

        blocks = (Block(type=BlockType.TEXT, content="Test content"),)
        ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf")

        ctx = build_template_context(ndoc)

        assert ctx.has_tables is False
        assert ctx.has_images is False
        assert len(ctx.blocks) == 1
        assert ctx.quality_score is not None
        assert 0.0 <= ctx.quality_score <= 1.0

    def test_build_context_with_original_document(self):
        """Test building context with original document."""
        from pydocextractor.domain.rules import build_template_context

        blocks = (Block(type=BlockType.TEXT, content="Test content"),)
        ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf")
        original = Document(
            bytes=b"test",
            mime="application/pdf",
            size_bytes=4,
            filename="test.pdf",
        )

        ctx = build_template_context(ndoc, original)

        assert ctx.metadata.get("filename") == "test.pdf"
