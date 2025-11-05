"""
Contract tests for Protocol compliance.

Tests that infrastructure adapters properly implement domain Protocols.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from pydocextractor.domain.models import PrecisionLevel
from pydocextractor.domain.ports import Extractor, Policy, QualityScorer, TemplateEngine
from pydocextractor.infra.extractors import (
    DOCLING_AVAILABLE,
    PDFPLUMBER_AVAILABLE,
    PYMUPDF4LLM_AVAILABLE,
    PYMUPDF_AVAILABLE,
)


class TestExtractorProtocol:
    """Test that extractors implement the Extractor Protocol."""

    @pytest.mark.skipif(not PYMUPDF_AVAILABLE, reason="PyMuPDF not installed")
    def test_chunked_parallel_implements_protocol(self):
        """Test ChunkedParallelExtractor implements Extractor Protocol."""
        from pydocextractor.infra.extractors.chunked_parallel_adapter import (
            ChunkedParallelExtractor,
        )

        extractor = ChunkedParallelExtractor()

        # Protocol compliance checks
        assert isinstance(extractor, Extractor)
        assert hasattr(extractor, "name")
        assert hasattr(extractor, "precision_level")
        assert hasattr(extractor, "is_available")
        assert hasattr(extractor, "supports")
        assert hasattr(extractor, "extract")

        # Call methods to verify signatures
        assert isinstance(extractor.name, str)
        assert isinstance(extractor.precision_level, PrecisionLevel)
        assert isinstance(extractor.is_available(), bool)
        assert isinstance(extractor.supports("application/pdf"), bool)

    @pytest.mark.skipif(not PYMUPDF4LLM_AVAILABLE, reason="pymupdf4llm not installed")
    def test_pymupdf4llm_implements_protocol(self):
        """Test PyMuPDF4LLMExtractor implements Extractor Protocol."""
        from pydocextractor.infra.extractors.pymupdf4llm_adapter import PyMuPDF4LLMExtractor

        extractor = PyMuPDF4LLMExtractor()

        assert isinstance(extractor, Extractor)
        assert isinstance(extractor.name, str)
        assert isinstance(extractor.precision_level, PrecisionLevel)
        assert isinstance(extractor.is_available(), bool)
        assert isinstance(extractor.supports("application/pdf"), bool)

    @pytest.mark.skipif(not PDFPLUMBER_AVAILABLE, reason="pdfplumber not installed")
    def test_pdfplumber_implements_protocol(self):
        """Test PDFPlumberExtractor implements Extractor Protocol."""
        from pydocextractor.infra.extractors.pdfplumber_adapter import PDFPlumberExtractor

        extractor = PDFPlumberExtractor()

        assert isinstance(extractor, Extractor)
        assert isinstance(extractor.name, str)
        assert isinstance(extractor.precision_level, PrecisionLevel)
        assert isinstance(extractor.is_available(), bool)
        assert isinstance(extractor.supports("application/pdf"), bool)

    @pytest.mark.skipif(not DOCLING_AVAILABLE, reason="docling not installed")
    def test_docling_implements_protocol(self):
        """Test DoclingExtractor implements Extractor Protocol."""
        from pydocextractor.infra.extractors.docling_adapter import DoclingExtractor

        extractor = DoclingExtractor()

        assert isinstance(extractor, Extractor)
        assert isinstance(extractor.name, str)
        assert isinstance(extractor.precision_level, PrecisionLevel)
        assert isinstance(extractor.is_available(), bool)
        assert isinstance(extractor.supports("application/pdf"), bool)

    def test_extractor_extract_returns_result(self, policy_report_pdf):
        """Test extractor.extract() returns ExtractionResult."""
        from pydocextractor.domain.models import ExtractionResult
        from pydocextractor.factory import get_available_extractors

        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        extractor = extractors[0]
        data = policy_report_pdf.read_bytes()

        result = extractor.extract(data, PrecisionLevel.BALANCED)

        assert isinstance(result, ExtractionResult)
        assert isinstance(result.success, bool)
        assert isinstance(result.extractor_name, str)


class TestPolicyProtocol:
    """Test that Policy implements the Policy Protocol."""

    def test_default_policy_implements_protocol(self):
        """Test DefaultPolicy implements Policy Protocol."""
        from pydocextractor.factory import get_available_extractors
        from pydocextractor.infra.policy.heuristics import DefaultPolicy

        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        policy = DefaultPolicy()

        assert isinstance(policy, Policy)
        assert hasattr(policy, "choose_extractors")

        # Call method to verify signature
        chosen = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=1024,
            has_tables=False,
            precision=PrecisionLevel.BALANCED,
        )

        assert isinstance(chosen, (list, tuple))
        for ext in chosen:
            assert isinstance(ext, Extractor)


class TestTemplateEngineProtocol:
    """Test that TemplateEngine implements the TemplateEngine Protocol."""

    def test_jinja2_engine_implements_protocol(self):
        """Test Jinja2TemplateEngine implements TemplateEngine Protocol."""
        from pydocextractor.infra.templates.engines import Jinja2TemplateEngine

        engine = Jinja2TemplateEngine()

        assert isinstance(engine, TemplateEngine)
        assert hasattr(engine, "render")

        # Test render method signature
        from pydocextractor.domain.models import Block, BlockType, NormalizedDoc, TemplateContext

        ndoc = NormalizedDoc(
            blocks=(Block(type=BlockType.TEXT, content="Test"),),
            source_mime="application/pdf",
        )
        context = TemplateContext.from_normalized_doc(ndoc)

        # Convert context to dict for engine.render()
        context_dict = {
            "blocks": context.blocks,
            "metadata": context.metadata,
            "has_tables": context.has_tables,
            "has_images": context.has_images,
            "page_count": context.page_count,
            "quality_score": context.quality_score,
        }

        result = engine.render("default", context_dict)
        assert isinstance(result, str)


class TestQualityScorerProtocol:
    """Test that QualityScorer implements the QualityScorer Protocol."""

    def test_default_scorer_implements_protocol(self):
        """Test DefaultQualityScorer implements QualityScorer Protocol."""
        from pydocextractor.infra.scoring.default_scorer import DefaultQualityScorer

        scorer = DefaultQualityScorer()

        assert isinstance(scorer, QualityScorer)
        assert hasattr(scorer, "calculate_score")

        # Test calculate_score method signature
        from pydocextractor.domain.models import Block, BlockType, NormalizedDoc

        ndoc = NormalizedDoc(
            blocks=(Block(type=BlockType.TEXT, content="Test content"),),
            source_mime="application/pdf",
        )
        markdown = "Test content"

        score = scorer.calculate_score(ndoc, markdown)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestProtocolInteroperability:
    """Test that Protocols work together correctly."""

    def test_service_accepts_protocol_implementations(
        self,
        sample_document,
        policy_report_pdf,
    ):
        """Test ConverterService accepts Protocol implementations."""
        from pydocextractor.factory import create_converter_service

        # This should work because all implementations follow Protocols
        service = create_converter_service()

        # Load real document
        data = policy_report_pdf.read_bytes()
        doc = replace(sample_document, bytes=data, size_bytes=len(data))

        # Should successfully convert using Protocol contracts
        try:
            result = service.convert_to_markdown(doc)
            assert result.text is not None
        except Exception as e:
            # If extractors aren't available, that's OK for this test
            if "No extractors available" not in str(e):
                raise

    def test_factory_returns_protocol_compliant_service(self):
        """Test factory returns service with Protocol-compliant dependencies."""
        from pydocextractor.factory import create_converter_service

        service = create_converter_service()

        # Service should have Protocol-compliant dependencies
        assert isinstance(service.policy, Policy)
        assert isinstance(service.template_engine, TemplateEngine)
        if service.quality_scorer is not None:
            assert isinstance(service.quality_scorer, QualityScorer)
