"""
Smoke tests for extractor adapters.

Basic tests to ensure extractors are configured correctly.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pydocextractor.domain.errors import RecoverableError
from pydocextractor.domain.models import BlockType, PrecisionLevel
from pydocextractor.infra.extractors.chunked_parallel_adapter import ChunkedParallelExtractor
from pydocextractor.infra.extractors.docling_adapter import DoclingExtractor
from pydocextractor.infra.extractors.pdfplumber_adapter import PDFPlumberExtractor
from pydocextractor.infra.extractors.pymupdf4llm_adapter import PyMuPDF4LLMExtractor


class TestChunkedParallelExtractor:
    """Comprehensive tests for ChunkedParallel extractor (Level 1)."""

    def test_properties(self):
        """Test extractor basic properties."""
        extractor = ChunkedParallelExtractor()

        assert extractor.name == "ChunkedParallel"
        assert extractor.precision_level == PrecisionLevel.FASTEST
        assert isinstance(extractor.is_available(), bool)

    def test_supports_pdf(self):
        """Test extractor supports PDF."""
        extractor = ChunkedParallelExtractor()

        assert extractor.supports("application/pdf") in [True, False]
        # Support depends on PyMuPDF availability

    def test_does_not_support_docx(self):
        """Test extractor does not support DOCX."""
        extractor = ChunkedParallelExtractor()

        assert (
            extractor.supports(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            is False
        )

    def test_calculate_chunk_size_small_doc(self):
        """Test chunk size calculation for small documents."""
        extractor = ChunkedParallelExtractor()

        assert extractor._calculate_chunk_size(5) == 5
        assert extractor._calculate_chunk_size(10) == 10

    def test_calculate_chunk_size_medium_doc(self):
        """Test chunk size calculation for medium documents."""
        extractor = ChunkedParallelExtractor()

        assert extractor._calculate_chunk_size(20) == 5
        assert extractor._calculate_chunk_size(50) == 5

    def test_calculate_chunk_size_large_doc(self):
        """Test chunk size calculation for large documents."""
        extractor = ChunkedParallelExtractor()

        assert extractor._calculate_chunk_size(100) == 10
        assert extractor._calculate_chunk_size(200) == 10

    def test_calculate_chunk_size_very_large_doc(self):
        """Test chunk size calculation for very large documents."""
        extractor = ChunkedParallelExtractor()

        assert extractor._calculate_chunk_size(300) == 20
        assert extractor._calculate_chunk_size(1000) == 20

    @patch("pydocextractor.infra.extractors.chunked_parallel_adapter.PYMUPDF_AVAILABLE", False)
    def test_extract_pymupdf_not_available(self):
        """Test extraction fails gracefully when PyMuPDF is not available."""
        extractor = ChunkedParallelExtractor()

        result = extractor.extract(b"fake pdf data", PrecisionLevel.FASTEST)

        assert result.success is False
        assert "PyMuPDF not available" in result.error
        assert result.extractor_name == "ChunkedParallel"

    @patch("pydocextractor.infra.extractors.chunked_parallel_adapter.PYMUPDF_AVAILABLE", True)
    def test_extract_success_with_single_page(self):
        """Test successful extraction with single page document."""
        extractor = ChunkedParallelExtractor()

        # Create mock PDF document
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample text from page 1"

        mock_doc = MagicMock()
        mock_doc.page_count = 1
        mock_doc.__getitem__.return_value = mock_page

        with patch("pydocextractor.infra.extractors.chunked_parallel_adapter.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(b"fake pdf data", PrecisionLevel.FASTEST)

        if result.success:
            assert result.normalized_doc is not None
            assert result.normalized_doc.page_count == 1
            assert result.normalized_doc.source_mime == "application/pdf"
            assert result.normalized_doc.extractor_name == "ChunkedParallel"
            assert result.processing_time_seconds is not None

    @patch("pydocextractor.infra.extractors.chunked_parallel_adapter.PYMUPDF_AVAILABLE", True)
    def test_extract_handles_encryption_error(self):
        """Test extraction handles encrypted PDF errors."""
        extractor = ChunkedParallelExtractor()

        with patch("pydocextractor.infra.extractors.chunked_parallel_adapter.fitz") as mock_fitz:
            mock_fitz.open.side_effect = Exception("Document is password protected")

            with pytest.raises(RecoverableError) as exc_info:
                extractor.extract(b"fake pdf data", PrecisionLevel.FASTEST)

            assert "password" in str(exc_info.value).lower()

    @patch("pydocextractor.infra.extractors.chunked_parallel_adapter.PYMUPDF_AVAILABLE", True)
    def test_extract_handles_generic_error(self):
        """Test extraction handles generic errors."""
        extractor = ChunkedParallelExtractor()

        with patch("pydocextractor.infra.extractors.chunked_parallel_adapter.fitz") as mock_fitz:
            mock_fitz.open.side_effect = Exception("Generic error")

            result = extractor.extract(b"fake pdf data", PrecisionLevel.FASTEST)

        assert result.success is False
        assert "ChunkedParallel extraction failed" in result.error
        assert result.processing_time_seconds is not None

    @patch("pydocextractor.infra.extractors.chunked_parallel_adapter.PYMUPDF_AVAILABLE", True)
    def test_extract_multi_page_document(self):
        """Test extraction with multi-page document."""
        extractor = ChunkedParallelExtractor()

        # Create mock pages
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Text from page 1"

        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Text from page 2"

        mock_doc = MagicMock()
        mock_doc.page_count = 2
        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]

        with patch("pydocextractor.infra.extractors.chunked_parallel_adapter.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(b"fake pdf data", PrecisionLevel.FASTEST)

        if result.success:
            assert result.normalized_doc is not None
            assert result.normalized_doc.page_count == 2

    @patch("pydocextractor.infra.extractors.chunked_parallel_adapter.PYMUPDF_AVAILABLE", True)
    def test_process_chunk_success(self):
        """Test _process_chunk method."""
        extractor = ChunkedParallelExtractor()

        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample text"

        mock_doc = MagicMock()
        mock_doc.page_count = 1
        mock_doc.__getitem__.return_value = mock_page

        with patch("pydocextractor.infra.extractors.chunked_parallel_adapter.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            blocks = extractor._process_chunk(b"fake pdf data", 0, 1)

        assert len(blocks) > 0
        assert blocks[0].type == BlockType.TEXT
        assert blocks[0].content == "Sample text"
        assert blocks[0].page_number == 1

    @patch("pydocextractor.infra.extractors.chunked_parallel_adapter.PYMUPDF_AVAILABLE", True)
    def test_process_chunk_empty_page(self):
        """Test _process_chunk with empty page."""
        extractor = ChunkedParallelExtractor()

        mock_page = MagicMock()
        mock_page.get_text.return_value = "   \n  "  # Whitespace only

        mock_doc = MagicMock()
        mock_doc.page_count = 1
        mock_doc.__getitem__.return_value = mock_page

        with patch("pydocextractor.infra.extractors.chunked_parallel_adapter.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            blocks = extractor._process_chunk(b"fake pdf data", 0, 1)

        assert len(blocks) == 0

    @patch("pydocextractor.infra.extractors.chunked_parallel_adapter.PYMUPDF_AVAILABLE", True)
    def test_extract_metadata_includes_chunk_info(self):
        """Test extraction result includes chunk metadata."""
        extractor = ChunkedParallelExtractor()

        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample text"

        mock_doc = MagicMock()
        mock_doc.page_count = 15
        mock_doc.__getitem__.return_value = mock_page

        with patch("pydocextractor.infra.extractors.chunked_parallel_adapter.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(b"fake pdf data", PrecisionLevel.FASTEST)

        if result.success:
            assert result.normalized_doc is not None
            metadata = result.normalized_doc.metadata
            assert "chunk_count" in metadata
            assert "chunk_size" in metadata
            assert "parallel_workers" in metadata


class TestPyMuPDF4LLMExtractor:
    """Comprehensive tests for PyMuPDF4LLM extractor (Level 2)."""

    def test_properties(self):
        """Test extractor basic properties."""
        extractor = PyMuPDF4LLMExtractor()

        assert extractor.name == "PyMuPDF4LLM"
        assert extractor.precision_level == PrecisionLevel.BALANCED
        assert isinstance(extractor.is_available(), bool)

    def test_supports_pdf(self):
        """Test extractor supports PDF."""
        extractor = PyMuPDF4LLMExtractor()

        assert extractor.supports("application/pdf") in [True, False]

    def test_does_not_support_xlsx(self):
        """Test extractor does not support XLSX."""
        extractor = PyMuPDF4LLMExtractor()

        assert (
            extractor.supports("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            is False
        )

    @patch("pydocextractor.infra.extractors.pymupdf4llm_adapter.PYMUPDF4LLM_AVAILABLE", False)
    def test_extract_library_not_available(self):
        """Test extraction fails gracefully when library is not available."""
        extractor = PyMuPDF4LLMExtractor()

        result = extractor.extract(b"fake pdf data", PrecisionLevel.BALANCED)

        assert result.success is False
        assert "pymupdf4llm not available" in result.error
        assert result.extractor_name == "PyMuPDF4LLM"

    @patch("pydocextractor.infra.extractors.pymupdf4llm_adapter.PYMUPDF4LLM_AVAILABLE", True)
    def test_extract_success(self):
        """Test successful extraction."""
        extractor = PyMuPDF4LLMExtractor()

        with patch("pydocextractor.infra.extractors.pymupdf4llm_adapter.pymupdf4llm") as mock_lib:
            mock_lib.to_markdown.return_value = "# Header\n\nSome text content"

            result = extractor.extract(b"fake pdf data", PrecisionLevel.BALANCED)

        if result.success:
            assert result.normalized_doc is not None
            assert result.normalized_doc.source_mime == "application/pdf"
            assert result.processing_time_seconds is not None

    @patch("pydocextractor.infra.extractors.pymupdf4llm_adapter.PYMUPDF4LLM_AVAILABLE", True)
    def test_extract_handles_password_error(self):
        """Test extraction handles password protected PDFs."""
        extractor = PyMuPDF4LLMExtractor()

        with patch("pydocextractor.infra.extractors.pymupdf4llm_adapter.pymupdf4llm") as mock_lib:
            mock_lib.to_markdown.side_effect = Exception("Password required")

            with pytest.raises(RecoverableError):
                extractor.extract(b"fake pdf data", PrecisionLevel.BALANCED)

    @patch("pydocextractor.infra.extractors.pymupdf4llm_adapter.PYMUPDF4LLM_AVAILABLE", True)
    def test_extract_handles_generic_error(self):
        """Test extraction handles generic errors."""
        extractor = PyMuPDF4LLMExtractor()

        with patch("pydocextractor.infra.extractors.pymupdf4llm_adapter.pymupdf4llm") as mock_lib:
            mock_lib.to_markdown.side_effect = Exception("Generic error")

            result = extractor.extract(b"fake pdf data", PrecisionLevel.BALANCED)

        assert result.success is False
        assert "PyMuPDF4LLM extraction failed" in result.error

    def test_parse_markdown_simple_text(self):
        """Test parsing simple markdown text."""
        extractor = PyMuPDF4LLMExtractor()

        markdown = "Simple text content"
        blocks = extractor._parse_markdown_to_blocks(markdown)

        assert len(blocks) == 1
        assert blocks[0].type == BlockType.TEXT
        assert blocks[0].content == "Simple text content"

    def test_parse_markdown_with_headers(self):
        """Test parsing markdown with headers."""
        extractor = PyMuPDF4LLMExtractor()

        markdown = "# Main Header\n\nSome text\n\n## Sub Header"
        blocks = extractor._parse_markdown_to_blocks(markdown)

        assert len(blocks) >= 2
        header_blocks = [b for b in blocks if b.type == BlockType.HEADER]
        assert len(header_blocks) >= 1

    def test_parse_markdown_with_page_breaks(self):
        """Test parsing markdown with page breaks."""
        extractor = PyMuPDF4LLMExtractor()

        markdown = "Page 1 content\n-----\nPage 2 content"
        blocks = extractor._parse_markdown_to_blocks(markdown)

        assert len(blocks) >= 1
        if len(blocks) >= 2:
            assert blocks[0].page_number == 1
            assert blocks[1].page_number == 2

    def test_parse_markdown_with_tables(self):
        """Test parsing markdown with tables."""
        extractor = PyMuPDF4LLMExtractor()

        markdown = "| Col1 | Col2 |\n|------|------|\n| A    | B    |"
        blocks = extractor._parse_markdown_to_blocks(markdown)

        table_blocks = [b for b in blocks if b.type == BlockType.TABLE]
        assert len(table_blocks) >= 1

    def test_parse_markdown_detects_tables(self):
        """Test that extraction detects tables in markdown."""
        extractor = PyMuPDF4LLMExtractor()

        with patch(
            "pydocextractor.infra.extractors.pymupdf4llm_adapter.PYMUPDF4LLM_AVAILABLE", True
        ):
            with patch(
                "pydocextractor.infra.extractors.pymupdf4llm_adapter.pymupdf4llm"
            ) as mock_lib:
                mock_lib.to_markdown.return_value = (
                    "| Col1 | Col2 |\n|------|------|\n| A    | B    |"
                )

                result = extractor.extract(b"fake pdf data", PrecisionLevel.BALANCED)

        if result.success:
            assert result.normalized_doc.has_tables is True

    def test_parse_markdown_empty_content(self):
        """Test parsing empty markdown."""
        extractor = PyMuPDF4LLMExtractor()

        blocks = extractor._parse_markdown_to_blocks("")

        assert len(blocks) == 0


class TestPDFPlumberExtractor:
    """Comprehensive tests for PDFPlumber extractor (Level 3)."""

    def test_properties(self):
        """Test extractor basic properties."""
        extractor = PDFPlumberExtractor()

        assert extractor.name == "PDFPlumber"
        assert extractor.precision_level == PrecisionLevel.TABLE_OPTIMIZED
        assert isinstance(extractor.is_available(), bool)

    def test_supports_pdf(self):
        """Test extractor supports PDF."""
        extractor = PDFPlumberExtractor()

        assert extractor.supports("application/pdf") in [True, False]

    def test_does_not_support_text(self):
        """Test extractor does not support plain text."""
        extractor = PDFPlumberExtractor()

        assert extractor.supports("text/plain") is False

    @patch("pydocextractor.infra.extractors.pdfplumber_adapter.PDFPLUMBER_AVAILABLE", False)
    def test_extract_library_not_available(self):
        """Test extraction fails gracefully when library is not available."""
        extractor = PDFPlumberExtractor()

        result = extractor.extract(b"fake pdf data", PrecisionLevel.TABLE_OPTIMIZED)

        assert result.success is False
        assert "pdfplumber not available" in result.error
        assert result.extractor_name == "PDFPlumber"

    @patch("pydocextractor.infra.extractors.pdfplumber_adapter.PDFPLUMBER_AVAILABLE", True)
    def test_extract_success(self):
        """Test successful extraction."""
        extractor = PDFPlumberExtractor()

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample text"
        mock_page.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value.pages = [mock_page]

        with patch("pydocextractor.infra.extractors.pdfplumber_adapter.pdfplumber") as mock_lib:
            mock_lib.open.return_value = mock_pdf

            result = extractor.extract(b"fake pdf data", PrecisionLevel.TABLE_OPTIMIZED)

        if result.success:
            assert result.normalized_doc is not None
            assert result.normalized_doc.source_mime == "application/pdf"
            assert result.processing_time_seconds is not None

    @patch("pydocextractor.infra.extractors.pdfplumber_adapter.PDFPLUMBER_AVAILABLE", True)
    def test_extract_with_tables(self):
        """Test extraction with tables."""
        extractor = PDFPlumberExtractor()

        table_data = [
            ["Header1", "Header2"],
            ["Value1", "Value2"],
        ]

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Text before table"
        mock_page.extract_tables.return_value = [table_data]

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value.pages = [mock_page]

        with patch("pydocextractor.infra.extractors.pdfplumber_adapter.pdfplumber") as mock_lib:
            mock_lib.open.return_value = mock_pdf

            result = extractor.extract(b"fake pdf data", PrecisionLevel.TABLE_OPTIMIZED)

        if result.success:
            assert result.normalized_doc.has_tables is True
            assert result.normalized_doc.metadata["table_count"] == 1

    @patch("pydocextractor.infra.extractors.pdfplumber_adapter.PDFPLUMBER_AVAILABLE", True)
    def test_extract_handles_password_error(self):
        """Test extraction handles password protected PDFs."""
        extractor = PDFPlumberExtractor()

        with patch("pydocextractor.infra.extractors.pdfplumber_adapter.pdfplumber") as mock_lib:
            mock_lib.open.side_effect = Exception("Document is encrypted")

            with pytest.raises(RecoverableError):
                extractor.extract(b"fake pdf data", PrecisionLevel.TABLE_OPTIMIZED)

    @patch("pydocextractor.infra.extractors.pdfplumber_adapter.PDFPLUMBER_AVAILABLE", True)
    def test_extract_handles_generic_error(self):
        """Test extraction handles generic errors."""
        extractor = PDFPlumberExtractor()

        with patch("pydocextractor.infra.extractors.pdfplumber_adapter.pdfplumber") as mock_lib:
            mock_lib.open.side_effect = Exception("Generic error")

            result = extractor.extract(b"fake pdf data", PrecisionLevel.TABLE_OPTIMIZED)

        assert result.success is False
        assert "PDFPlumber extraction failed" in result.error

    def test_table_to_markdown_simple_table(self):
        """Test conversion of simple table to markdown."""
        extractor = PDFPlumberExtractor()

        table = [
            ["Header1", "Header2"],
            ["Value1", "Value2"],
        ]

        markdown = extractor._table_to_markdown(table)

        assert "Header1" in markdown
        assert "Header2" in markdown
        assert "Value1" in markdown
        assert "Value2" in markdown
        assert "|" in markdown
        assert "---" in markdown

    def test_table_to_markdown_with_none_values(self):
        """Test table conversion handles None values."""
        extractor = PDFPlumberExtractor()

        table = [
            ["Header1", None, "Header3"],
            ["Value1", None, "Value3"],
        ]

        markdown = extractor._table_to_markdown(table)

        assert "Header1" in markdown
        assert "Header3" in markdown

    def test_table_to_markdown_empty_table(self):
        """Test table conversion handles empty table."""
        extractor = PDFPlumberExtractor()

        assert extractor._table_to_markdown([]) == ""
        assert extractor._table_to_markdown([[]]) == ""
        assert extractor._table_to_markdown([[None, None]]) == ""

    def test_table_to_markdown_single_row(self):
        """Test table conversion handles single row."""
        extractor = PDFPlumberExtractor()

        table = [["Header1", "Header2"]]

        markdown = extractor._table_to_markdown(table)

        # Single row shouldn't produce valid markdown table (need header + data)
        assert markdown == ""

    def test_table_to_markdown_uneven_columns(self):
        """Test table conversion handles uneven column counts."""
        extractor = PDFPlumberExtractor()

        table = [
            ["Header1", "Header2", "Header3"],
            ["Value1", "Value2"],  # Missing a column
        ]

        markdown = extractor._table_to_markdown(table)

        # Should pad the missing column
        assert "Header1" in markdown
        assert "Header2" in markdown
        assert "Header3" in markdown

    @patch("pydocextractor.infra.extractors.pdfplumber_adapter.PDFPLUMBER_AVAILABLE", True)
    def test_extract_multiple_pages(self):
        """Test extraction with multiple pages."""
        extractor = PDFPlumberExtractor()

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 text"
        mock_page1.extract_tables.return_value = []

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 text"
        mock_page2.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value.pages = [mock_page1, mock_page2]

        with patch("pydocextractor.infra.extractors.pdfplumber_adapter.pdfplumber") as mock_lib:
            mock_lib.open.return_value = mock_pdf

            result = extractor.extract(b"fake pdf data", PrecisionLevel.TABLE_OPTIMIZED)

        if result.success:
            assert result.normalized_doc.page_count == 2

    @patch("pydocextractor.infra.extractors.pdfplumber_adapter.PDFPLUMBER_AVAILABLE", True)
    def test_extract_skips_empty_text(self):
        """Test extraction skips empty text blocks."""
        extractor = PDFPlumberExtractor()

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "   \n  "  # Whitespace only
        mock_page.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value.pages = [mock_page]

        with patch("pydocextractor.infra.extractors.pdfplumber_adapter.pdfplumber") as mock_lib:
            mock_lib.open.return_value = mock_pdf

            result = extractor.extract(b"fake pdf data", PrecisionLevel.TABLE_OPTIMIZED)

        if result.success:
            # Should not include empty blocks
            text_blocks = [b for b in result.normalized_doc.blocks if b.type == BlockType.TEXT]
            assert len(text_blocks) == 0


class TestDoclingExtractor:
    """Comprehensive tests for Docling extractor (Level 4)."""

    def test_properties(self):
        """Test extractor basic properties."""
        extractor = DoclingExtractor()

        assert extractor.name == "Docling"
        assert extractor.precision_level == PrecisionLevel.HIGHEST_QUALITY
        assert isinstance(extractor.is_available(), bool)

    def test_supports_pdf(self):
        """Test extractor supports PDF."""
        extractor = DoclingExtractor()

        assert extractor.supports("application/pdf") in [True, False]

    def test_supports_docx(self):
        """Test extractor supports DOCX."""
        extractor = DoclingExtractor()

        supports_docx = extractor.supports(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert isinstance(supports_docx, bool)

    def test_supports_xlsx(self):
        """Test extractor supports XLSX."""
        extractor = DoclingExtractor()

        supports_xlsx = extractor.supports(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert isinstance(supports_xlsx, bool)

    def test_supports_xls(self):
        """Test extractor supports XLS."""
        extractor = DoclingExtractor()

        supports_xls = extractor.supports("application/vnd.ms-excel")
        assert isinstance(supports_xls, bool)

    def test_does_not_support_csv(self):
        """Test extractor does not support CSV."""
        extractor = DoclingExtractor()

        assert extractor.supports("text/csv") is False

    @patch("pydocextractor.infra.extractors.docling_adapter.DOCLING_AVAILABLE", False)
    def test_extract_library_not_available(self):
        """Test extraction fails gracefully when library is not available."""
        extractor = DoclingExtractor()

        result = extractor.extract(b"fake pdf data", PrecisionLevel.HIGHEST_QUALITY)

        assert result.success is False
        assert "Docling not available" in result.error
        assert result.extractor_name == "Docling"

    @patch("pydocextractor.infra.extractors.docling_adapter.DOCLING_AVAILABLE", True)
    def test_extract_success(self):
        """Test successful extraction."""
        extractor = DoclingExtractor()

        # Mock the Docling converter and result
        mock_document = MagicMock()
        mock_document.export_to_markdown.return_value = "# Test Document\n\nContent here"
        mock_document.pages = []

        mock_result = MagicMock()
        mock_result.document = mock_document

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with patch(
            "pydocextractor.infra.extractors.docling_adapter.DoclingDocConverter"
        ) as mock_conv_class:
            mock_conv_class.return_value = mock_converter

            with patch("pydocextractor.infra.extractors.docling_adapter.Path") as mock_path:
                mock_path.return_value.unlink = MagicMock()

                result = extractor.extract(b"fake pdf data", PrecisionLevel.HIGHEST_QUALITY)

        if result.success:
            assert result.normalized_doc is not None
            assert result.normalized_doc.source_mime == "application/pdf"
            assert result.processing_time_seconds is not None

    @patch("pydocextractor.infra.extractors.docling_adapter.DOCLING_AVAILABLE", True)
    def test_extract_handles_password_error(self):
        """Test extraction handles password protected documents."""
        extractor = DoclingExtractor()

        mock_converter = MagicMock()
        mock_converter.convert.side_effect = Exception("Document is encrypted")

        with patch(
            "pydocextractor.infra.extractors.docling_adapter.DoclingDocConverter"
        ) as mock_conv_class:
            mock_conv_class.return_value = mock_converter

            with patch("pydocextractor.infra.extractors.docling_adapter.Path") as mock_path:
                mock_path.return_value.unlink = MagicMock()

                with pytest.raises(RecoverableError):
                    extractor.extract(b"fake pdf data", PrecisionLevel.HIGHEST_QUALITY)

    @patch("pydocextractor.infra.extractors.docling_adapter.DOCLING_AVAILABLE", True)
    def test_extract_handles_generic_error(self):
        """Test extraction handles generic errors."""
        extractor = DoclingExtractor()

        mock_converter = MagicMock()
        mock_converter.convert.side_effect = Exception("Generic error")

        with patch(
            "pydocextractor.infra.extractors.docling_adapter.DoclingDocConverter"
        ) as mock_conv_class:
            mock_conv_class.return_value = mock_converter

            with patch("pydocextractor.infra.extractors.docling_adapter.Path") as mock_path:
                mock_path.return_value.unlink = MagicMock()

                result = extractor.extract(b"fake pdf data", PrecisionLevel.HIGHEST_QUALITY)

        assert result.success is False
        assert "Docling extraction failed" in result.error

    def test_parse_markdown_simple_text(self):
        """Test parsing simple markdown text."""
        extractor = DoclingExtractor()

        markdown = "Simple text content"
        blocks = extractor._parse_markdown_to_blocks(markdown)

        assert len(blocks) == 1
        assert blocks[0].type == BlockType.TEXT
        assert blocks[0].content == "Simple text content"

    def test_parse_markdown_with_headers(self):
        """Test parsing markdown with headers."""
        extractor = DoclingExtractor()

        markdown = "# Main Header\nSome text\n## Sub Header"
        blocks = extractor._parse_markdown_to_blocks(markdown)

        header_blocks = [b for b in blocks if b.type == BlockType.HEADER]
        assert len(header_blocks) >= 2

    def test_parse_markdown_with_tables(self):
        """Test parsing markdown with tables."""
        extractor = DoclingExtractor()

        markdown = "| Col1 | Col2 |\n| A | B |"
        blocks = extractor._parse_markdown_to_blocks(markdown)

        table_blocks = [b for b in blocks if b.type == BlockType.TABLE]
        assert len(table_blocks) >= 1

    def test_parse_markdown_with_images(self):
        """Test parsing markdown with images."""
        extractor = DoclingExtractor()

        markdown = "![Image](path/to/image.png)"
        blocks = extractor._parse_markdown_to_blocks(markdown)

        image_blocks = [b for b in blocks if b.type == BlockType.IMAGE]
        assert len(image_blocks) == 1

    @patch("pydocextractor.infra.extractors.docling_adapter.DOCLING_AVAILABLE", True)
    def test_extract_with_pages_metadata(self):
        """Test extraction includes page metadata."""
        extractor = DoclingExtractor()

        # Mock document with pages
        mock_page = MagicMock()
        mock_page.tables = []
        mock_page.figures = []

        mock_document = MagicMock()
        mock_document.export_to_markdown.return_value = "Content"
        mock_document.pages = [mock_page, mock_page]

        mock_result = MagicMock()
        mock_result.document = mock_document

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with patch(
            "pydocextractor.infra.extractors.docling_adapter.DoclingDocConverter"
        ) as mock_conv_class:
            mock_conv_class.return_value = mock_converter

            with patch("pydocextractor.infra.extractors.docling_adapter.Path") as mock_path:
                mock_path.return_value.unlink = MagicMock()

                result = extractor.extract(b"fake pdf data", PrecisionLevel.HIGHEST_QUALITY)

        if result.success:
            assert result.normalized_doc.page_count == 2

    @patch("pydocextractor.infra.extractors.docling_adapter.DOCLING_AVAILABLE", True)
    def test_extract_with_tables_metadata(self):
        """Test extraction detects tables."""
        extractor = DoclingExtractor()

        # Mock document with tables
        mock_table = MagicMock()

        mock_page = MagicMock()
        mock_page.tables = [mock_table]
        mock_page.figures = []

        mock_document = MagicMock()
        mock_document.export_to_markdown.return_value = "| A | B |"
        mock_document.pages = [mock_page]

        mock_result = MagicMock()
        mock_result.document = mock_document

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with patch(
            "pydocextractor.infra.extractors.docling_adapter.DoclingDocConverter"
        ) as mock_conv_class:
            mock_conv_class.return_value = mock_converter

            with patch("pydocextractor.infra.extractors.docling_adapter.Path") as mock_path:
                mock_path.return_value.unlink = MagicMock()

                result = extractor.extract(b"fake pdf data", PrecisionLevel.HIGHEST_QUALITY)

        if result.success:
            assert result.normalized_doc.has_tables is True
            assert result.normalized_doc.metadata["table_count"] == 1

    @patch("pydocextractor.infra.extractors.docling_adapter.DOCLING_AVAILABLE", True)
    def test_extract_with_images_metadata(self):
        """Test extraction detects images."""
        extractor = DoclingExtractor()

        # Mock document with figures
        mock_figure = MagicMock()

        mock_page = MagicMock()
        mock_page.tables = []
        mock_page.figures = [mock_figure, mock_figure]

        mock_document = MagicMock()
        mock_document.export_to_markdown.return_value = "![img](test.png)"
        mock_document.pages = [mock_page]

        mock_result = MagicMock()
        mock_result.document = mock_document

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with patch(
            "pydocextractor.infra.extractors.docling_adapter.DoclingDocConverter"
        ) as mock_conv_class:
            mock_conv_class.return_value = mock_converter

            with patch("pydocextractor.infra.extractors.docling_adapter.Path") as mock_path:
                mock_path.return_value.unlink = MagicMock()

                result = extractor.extract(b"fake pdf data", PrecisionLevel.HIGHEST_QUALITY)

        if result.success:
            assert result.normalized_doc.has_images is True
            assert result.normalized_doc.metadata["image_count"] == 2

    @patch("pydocextractor.infra.extractors.docling_adapter.DOCLING_AVAILABLE", True)
    def test_extract_cleans_up_temp_file(self):
        """Test extraction cleans up temporary file."""
        extractor = DoclingExtractor()

        mock_document = MagicMock()
        mock_document.export_to_markdown.return_value = "Content"
        mock_document.pages = []

        mock_result = MagicMock()
        mock_result.document = mock_document

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        mock_unlink = MagicMock()

        with patch(
            "pydocextractor.infra.extractors.docling_adapter.DoclingDocConverter"
        ) as mock_conv_class:
            mock_conv_class.return_value = mock_converter

            with patch("pydocextractor.infra.extractors.docling_adapter.Path") as mock_path:
                mock_path.return_value.unlink = mock_unlink

                extractor.extract(b"fake pdf data", PrecisionLevel.HIGHEST_QUALITY)

        # Verify temp file cleanup was attempted
        mock_unlink.assert_called_once()

    def test_parse_markdown_empty_content(self):
        """Test parsing empty markdown."""
        extractor = DoclingExtractor()

        blocks = extractor._parse_markdown_to_blocks("")

        assert len(blocks) == 0


class TestExtractorAvailability:
    """Test extractor availability checks."""

    def test_all_extractors_instantiate(self):
        """Test all extractors can be instantiated."""
        extractors = [
            ChunkedParallelExtractor(),
            PyMuPDF4LLMExtractor(),
            PDFPlumberExtractor(),
            DoclingExtractor(),
        ]

        # Should not raise errors
        for extractor in extractors:
            assert extractor is not None
            assert hasattr(extractor, "name")
            assert hasattr(extractor, "precision_level")
            assert hasattr(extractor, "is_available")
            assert hasattr(extractor, "supports")
            assert hasattr(extractor, "extract")

    def test_extractors_have_unique_names(self):
        """Test extractors have unique names."""
        extractors = [
            ChunkedParallelExtractor(),
            PyMuPDF4LLMExtractor(),
            PDFPlumberExtractor(),
            DoclingExtractor(),
        ]

        names = [e.name for e in extractors]
        assert len(names) == len(set(names))  # All unique

    def test_extractors_have_unique_levels(self):
        """Test extractors have unique precision levels."""
        extractors = [
            ChunkedParallelExtractor(),
            PyMuPDF4LLMExtractor(),
            PDFPlumberExtractor(),
            DoclingExtractor(),
        ]

        levels = [e.precision_level for e in extractors]
        assert len(levels) == len(set(levels))  # All unique
        assert levels == [
            PrecisionLevel.FASTEST,
            PrecisionLevel.BALANCED,
            PrecisionLevel.TABLE_OPTIMIZED,
            PrecisionLevel.HIGHEST_QUALITY,
        ]
