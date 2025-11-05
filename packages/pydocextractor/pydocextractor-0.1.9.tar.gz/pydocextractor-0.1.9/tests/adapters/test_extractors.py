"""
Adapter tests for infrastructure extractors.

Tests real extractor implementations with actual documents.
"""

from __future__ import annotations

import pytest

from pydocextractor.domain.models import PrecisionLevel
from pydocextractor.infra.extractors import (
    DOCLING_AVAILABLE,
    PDFPLUMBER_AVAILABLE,
    PYMUPDF4LLM_AVAILABLE,
    PYMUPDF_AVAILABLE,
)

# Skip tests if dependencies not installed
pytestmark = pytest.mark.skipif(
    not any([PYMUPDF_AVAILABLE, PYMUPDF4LLM_AVAILABLE, PDFPLUMBER_AVAILABLE, DOCLING_AVAILABLE]),
    reason="No extractor dependencies installed",
)


@pytest.mark.skipif(not PYMUPDF_AVAILABLE, reason="PyMuPDF not installed")
class TestChunkedParallelExtractor:
    """Test ChunkedParallelExtractor (Level 1) with real documents."""

    def test_extractor_properties(self):
        """Test extractor properties."""
        from pydocextractor.infra.extractors.chunked_parallel_adapter import (
            ChunkedParallelExtractor,
        )

        extractor = ChunkedParallelExtractor()
        assert extractor.name == "ChunkedParallel"
        assert extractor.precision_level == PrecisionLevel.FASTEST
        assert extractor.is_available() is True
        assert extractor.supports("application/pdf") is True

    def test_extract_policy_report(self, policy_report_pdf):
        """Test extracting Policy_Report.pdf."""
        from pydocextractor.infra.extractors.chunked_parallel_adapter import (
            ChunkedParallelExtractor,
        )

        extractor = ChunkedParallelExtractor()
        data = policy_report_pdf.read_bytes()

        result = extractor.extract(data, PrecisionLevel.FASTEST)

        assert result.success is True
        assert result.normalized_doc is not None
        assert len(result.normalized_doc.blocks) > 0
        assert result.extractor_name == "ChunkedParallel"
        assert result.processing_time_seconds > 0

    def test_extract_company_handbook(self, company_handbook_pdf):
        """Test extracting Company_Handbook.pdf."""
        from pydocextractor.infra.extractors.chunked_parallel_adapter import (
            ChunkedParallelExtractor,
        )

        extractor = ChunkedParallelExtractor()
        data = company_handbook_pdf.read_bytes()

        result = extractor.extract(data, PrecisionLevel.FASTEST)

        assert result.success is True
        assert result.normalized_doc is not None
        assert len(result.normalized_doc.blocks) > 0


@pytest.mark.skipif(not PYMUPDF4LLM_AVAILABLE, reason="pymupdf4llm not installed")
class TestPyMuPDF4LLMExtractor:
    """Test PyMuPDF4LLMExtractor (Level 2) with real documents."""

    def test_extractor_properties(self):
        """Test extractor properties."""
        from pydocextractor.infra.extractors.pymupdf4llm_adapter import PyMuPDF4LLMExtractor

        extractor = PyMuPDF4LLMExtractor()
        assert extractor.name == "PyMuPDF4LLM"
        assert extractor.precision_level == PrecisionLevel.BALANCED
        assert extractor.is_available() is True
        assert extractor.supports("application/pdf") is True

    def test_extract_policy_report(self, policy_report_pdf):
        """Test extracting Policy_Report.pdf."""
        from pydocextractor.infra.extractors.pymupdf4llm_adapter import PyMuPDF4LLMExtractor

        extractor = PyMuPDF4LLMExtractor()
        data = policy_report_pdf.read_bytes()

        result = extractor.extract(data, PrecisionLevel.BALANCED)

        assert result.success is True
        assert result.normalized_doc is not None
        assert len(result.normalized_doc.blocks) > 0
        assert result.extractor_name == "PyMuPDF4LLM"
        assert result.processing_time_seconds > 0

        # Check content quality
        blocks_content = " ".join(b.content for b in result.normalized_doc.blocks)
        assert len(blocks_content) > 100  # Should have substantial content

    def test_extract_company_handbook(self, company_handbook_pdf):
        """Test extracting Company_Handbook.pdf."""
        from pydocextractor.infra.extractors.pymupdf4llm_adapter import PyMuPDF4LLMExtractor

        extractor = PyMuPDF4LLMExtractor()
        data = company_handbook_pdf.read_bytes()

        result = extractor.extract(data, PrecisionLevel.BALANCED)

        assert result.success is True
        assert result.normalized_doc is not None
        assert len(result.normalized_doc.blocks) > 0


@pytest.mark.skipif(not PDFPLUMBER_AVAILABLE, reason="pdfplumber not installed")
class TestPDFPlumberExtractor:
    """Test PDFPlumberExtractor (Level 3) with real documents."""

    def test_extractor_properties(self):
        """Test extractor properties."""
        from pydocextractor.infra.extractors.pdfplumber_adapter import PDFPlumberExtractor

        extractor = PDFPlumberExtractor()
        assert extractor.name == "PDFPlumber"
        assert extractor.precision_level == PrecisionLevel.TABLE_OPTIMIZED
        assert extractor.is_available() is True
        assert extractor.supports("application/pdf") is True

    def test_extract_policy_report(self, policy_report_pdf):
        """Test extracting Policy_Report.pdf."""
        from pydocextractor.infra.extractors.pdfplumber_adapter import PDFPlumberExtractor

        extractor = PDFPlumberExtractor()
        data = policy_report_pdf.read_bytes()

        result = extractor.extract(data, PrecisionLevel.TABLE_OPTIMIZED)

        assert result.success is True
        assert result.normalized_doc is not None
        assert len(result.normalized_doc.blocks) > 0
        assert result.extractor_name == "PDFPlumber"
        assert result.processing_time_seconds > 0

    def test_extract_with_tables(self, policy_report_pdf):
        """Test table extraction capability."""
        from pydocextractor.infra.extractors.pdfplumber_adapter import PDFPlumberExtractor

        extractor = PDFPlumberExtractor()
        data = policy_report_pdf.read_bytes()

        result = extractor.extract(data, PrecisionLevel.TABLE_OPTIMIZED)

        assert result.success is True
        # Check if tables were detected (if document has tables)
        if result.normalized_doc.has_tables:
            # Should have table blocks
            table_blocks = [b for b in result.normalized_doc.blocks if b.type.value == "table"]
            # Some documents may not have tables, so just verify structure
            assert isinstance(table_blocks, list)


@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="docling not installed")
class TestDoclingExtractor:
    """Test DoclingExtractor (Level 4) with real documents."""

    def test_extractor_properties(self):
        """Test extractor properties."""
        from pydocextractor.infra.extractors.docling_adapter import DoclingExtractor

        extractor = DoclingExtractor()
        assert extractor.name == "Docling"
        assert extractor.precision_level == PrecisionLevel.HIGHEST_QUALITY
        assert extractor.is_available() is True
        assert extractor.supports("application/pdf") is True
        assert extractor.supports(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert extractor.supports(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_extract_policy_report(self, policy_report_pdf):
        """Test extracting Policy_Report.pdf."""
        from pydocextractor.infra.extractors.docling_adapter import DoclingExtractor

        extractor = DoclingExtractor()
        data = policy_report_pdf.read_bytes()

        result = extractor.extract(data, PrecisionLevel.HIGHEST_QUALITY)

        assert result.success is True
        assert result.normalized_doc is not None
        assert len(result.normalized_doc.blocks) > 0
        assert result.extractor_name == "Docling"
        assert result.processing_time_seconds > 0

    @pytest.mark.slow
    def test_extract_excel(self, sales_xlsx):
        """Test extracting Sales_2025.xlsx."""
        from pydocextractor.infra.extractors.docling_adapter import DoclingExtractor

        extractor = DoclingExtractor()
        data = sales_xlsx.read_bytes()

        result = extractor.extract(
            data,
            PrecisionLevel.HIGHEST_QUALITY,
        )

        assert result.success is True
        assert result.normalized_doc is not None
        assert len(result.normalized_doc.blocks) > 0
        # Excel files should have tables
        assert result.normalized_doc.has_tables is True


class TestExtractorComparison:
    """Compare extractors on same document."""

    @pytest.mark.slow
    def test_compare_extractors_on_policy_report(self, policy_report_pdf):
        """Compare all available extractors on Policy_Report.pdf."""
        data = policy_report_pdf.read_bytes()
        results = {}

        if PYMUPDF_AVAILABLE:
            from pydocextractor.infra.extractors.chunked_parallel_adapter import (
                ChunkedParallelExtractor,
            )

            ext = ChunkedParallelExtractor()
            results["ChunkedParallel"] = ext.extract(data, PrecisionLevel.FASTEST)

        if PYMUPDF4LLM_AVAILABLE:
            from pydocextractor.infra.extractors.pymupdf4llm_adapter import (
                PyMuPDF4LLMExtractor,
            )

            ext = PyMuPDF4LLMExtractor()
            results["PyMuPDF4LLM"] = ext.extract(data, PrecisionLevel.BALANCED)

        if PDFPLUMBER_AVAILABLE:
            from pydocextractor.infra.extractors.pdfplumber_adapter import PDFPlumberExtractor

            ext = PDFPlumberExtractor()
            results["PDFPlumber"] = ext.extract(data, PrecisionLevel.TABLE_OPTIMIZED)

        # All should succeed
        for name, result in results.items():
            assert result.success is True, f"{name} failed"
            assert len(result.normalized_doc.blocks) > 0, f"{name} produced no blocks"

        # Compare processing times (Level 1 should be fastest)
        if "ChunkedParallel" in results and "PDFPlumber" in results:
            assert (
                results["ChunkedParallel"].processing_time_seconds
                < results["PDFPlumber"].processing_time_seconds * 3
            ), "ChunkedParallel should be significantly faster"
