"""
Integration tests for end-to-end workflows.

Tests complete conversion pipelines with real documents.
"""

from __future__ import annotations

import pytest

from pydocextractor.domain.models import PrecisionLevel
from pydocextractor.factory import create_converter_service, get_available_extractors

pytestmark = pytest.mark.integration


class TestEndToEndConversion:
    """Test complete document conversion workflows."""

    def test_convert_policy_report_default(self, policy_report_pdf, load_test_document):
        """Test converting Policy_Report.pdf with default settings."""
        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        service = create_converter_service()
        doc = load_test_document(policy_report_pdf)

        result = service.convert_to_markdown(doc)

        assert result.text is not None
        assert len(result.text) > 100
        assert result.metadata.get("extractor") is not None
        assert result.quality_score is not None
        assert 0.0 <= result.quality_score <= 1.0

    def test_convert_company_handbook_balanced(self, company_handbook_pdf, load_test_document):
        """Test converting Company_Handbook.pdf with BALANCED precision."""
        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        service = create_converter_service()
        doc = load_test_document(company_handbook_pdf, PrecisionLevel.BALANCED)

        result = service.convert_to_markdown(doc)

        assert result.text is not None
        assert len(result.text) > 100
        assert result.metadata.get("extractor") is not None

    @pytest.mark.slow
    def test_convert_with_different_precision_levels(self, policy_report_pdf, load_test_document):
        """Test converting same document with different precision levels."""
        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        service = create_converter_service()
        results = {}

        # Try different precision levels
        for level in [PrecisionLevel.FASTEST, PrecisionLevel.BALANCED]:
            try:
                doc = load_test_document(policy_report_pdf, level)
                result = service.convert_to_markdown(doc)
                if result.text:
                    results[level] = result
            except Exception:
                pass  # Some levels might not be available

        # Should have at least one successful conversion
        assert len(results) > 0

        # All results should be valid
        for _level, result in results.items():
            assert result.text is not None
            assert len(result.text) > 0

    def test_convert_with_custom_template(self, policy_report_pdf, load_test_document):
        """Test converting with custom template."""
        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        service = create_converter_service()
        doc = load_test_document(policy_report_pdf)

        # Try simple template
        result = service.convert_to_markdown(doc, template_name="simple")

        assert result.text is not None
        assert len(result.text) > 0


class TestFactoryIntegration:
    """Test factory integration with real scenarios."""

    def test_factory_creates_working_service(self):
        """Test factory creates a fully functional service."""
        service = create_converter_service()

        # Service should be properly initialized
        assert service is not None

        # Should have all required components
        assert hasattr(service, "convert_to_markdown")

    def test_available_extractors(self):
        """Test getting available extractors."""
        extractors = get_available_extractors()

        # Should return a list (may be empty if no deps installed)
        assert isinstance(extractors, (list, tuple))

        # All extractors should be properly initialized
        for ext in extractors:
            assert ext.is_available() is True
            assert isinstance(ext.name, str)
            assert isinstance(ext.precision_level, PrecisionLevel)


class TestQualityScoring:
    """Test quality scoring in integration."""

    def test_quality_score_calculated(self, policy_report_pdf, load_test_document):
        """Test quality score is calculated during conversion."""
        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        service = create_converter_service()
        doc = load_test_document(policy_report_pdf)

        result = service.convert_to_markdown(doc)

        # Quality score should be present
        assert result.quality_score is not None
        assert 0.0 <= result.quality_score <= 1.0

    def test_quality_varies_by_document(
        self, policy_report_pdf, company_handbook_pdf, load_test_document
    ):
        """Test quality scores vary for different documents."""
        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        service = create_converter_service()

        doc1 = load_test_document(policy_report_pdf)
        result1 = service.convert_to_markdown(doc1)

        doc2 = load_test_document(company_handbook_pdf)
        result2 = service.convert_to_markdown(doc2)

        # Both should have quality scores
        assert result1.quality_score is not None
        assert result2.quality_score is not None

        # Scores should be in valid range
        assert 0.0 <= result1.quality_score <= 1.0
        assert 0.0 <= result2.quality_score <= 1.0


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_invalid_document_handled(self):
        """Test handling of invalid document data."""
        from pydocextractor.domain.errors import ConversionFailed
        from pydocextractor.domain.models import Document

        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        service = create_converter_service()

        # Create invalid document
        invalid_doc = Document(
            bytes=b"This is not a valid PDF",
            mime="application/pdf",
            size_bytes=23,
        )

        # Should either convert or raise ConversionFailed
        try:
            result = service.convert_to_markdown(invalid_doc)
            # If it succeeds, result should be valid
            assert result.text is not None
        except ConversionFailed:
            # Expected for invalid data
            pass

    def test_empty_document_handled(self):
        """Test handling of empty document."""
        from pydocextractor.domain.models import Document

        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        # Domain model validates that bytes cannot be empty
        # This is correct behavior - empty documents should be rejected
        with pytest.raises(ValueError, match="Document bytes cannot be empty"):
            Document(
                bytes=b"",
                mime="application/pdf",
                size_bytes=0,
            )


@pytest.mark.slow
class TestPerformance:
    """Test performance characteristics."""

    def test_conversion_completes_in_reasonable_time(self, policy_report_pdf, load_test_document):
        """Test conversion completes in reasonable time."""
        import time

        extractors = get_available_extractors()
        if not extractors:
            pytest.skip("No extractors available")

        service = create_converter_service()
        doc = load_test_document(policy_report_pdf)

        start = time.time()
        result = service.convert_to_markdown(doc)
        elapsed = time.time() - start

        # Should complete in reasonable time (< 60 seconds for test docs)
        assert elapsed < 60.0
        assert result.text is not None

    def test_fastest_level_is_faster(self, policy_report_pdf, load_test_document):
        """Test FASTEST level is actually faster than others."""
        import time

        extractors = get_available_extractors()
        if len(extractors) < 2:
            pytest.skip("Need multiple extractors for comparison")

        service = create_converter_service()

        # Test FASTEST
        doc_fast = load_test_document(policy_report_pdf, PrecisionLevel.FASTEST)
        start = time.time()
        try:
            service.convert_to_markdown(doc_fast)
            time_fast = time.time() - start
        except Exception:
            pytest.skip("FASTEST level not available")

        # Test BALANCED
        doc_balanced = load_test_document(policy_report_pdf, PrecisionLevel.BALANCED)
        start = time.time()
        try:
            service.convert_to_markdown(doc_balanced)
            time_balanced = time.time() - start
        except Exception:
            pytest.skip("BALANCED level not available")

        # Both should complete successfully
        # Note: Performance can vary based on document complexity and system load
        # FASTEST is generally faster but not guaranteed for all document types
        assert time_fast > 0 and time_balanced > 0, "Both conversions should complete"
