"""
Unit tests for application service layer.

Tests ConverterService using mocked Protocols (no infrastructure dependencies).
"""

from __future__ import annotations

import pytest

from pydocextractor.app.service import ConverterService
from pydocextractor.domain.errors import ConversionFailed, UnsupportedFormat
from pydocextractor.domain.models import (
    Block,
    BlockType,
    Document,
    ExtractionResult,
    NormalizedDoc,
    PrecisionLevel,
)


class TestConverterServiceInitialization:
    """Test ConverterService initialization."""

    def test_service_creation(self, mock_policy, mock_template_engine):
        """Test creating converter service."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
        )
        assert service is not None

    def test_service_with_quality_scorer(
        self, mock_policy, mock_template_engine, mock_quality_scorer
    ):
        """Test service with quality scorer."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
            quality_scorer=mock_quality_scorer,
        )
        assert service is not None

    def test_service_without_quality_scorer(self, mock_policy, mock_template_engine):
        """Test service without quality scorer."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
            quality_scorer=None,
        )
        assert service is not None


class TestConverterServiceConversion:
    """Test ConverterService conversion workflow."""

    def test_successful_conversion(
        self,
        sample_document,
        mock_policy,
        mock_template_engine,
        mock_quality_scorer,
    ):
        """Test successful conversion workflow."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
            quality_scorer=mock_quality_scorer,
        )

        result = service.convert_to_markdown(sample_document)

        # Verify result
        assert result.text == "# Rendered Markdown"
        assert result.metadata["extractor"] == "MockExtractor"
        assert result.quality_score == 0.85

        # Verify mocks were called
        assert mock_policy.choose_called
        assert mock_template_engine.render_called
        assert mock_quality_scorer.calculate_called

    def test_conversion_without_quality_scorer(
        self,
        sample_document,
        mock_policy,
        mock_template_engine,
    ):
        """Test conversion without quality scoring."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
            quality_scorer=None,
        )

        result = service.convert_to_markdown(sample_document)

        assert result.text == "# Rendered Markdown"
        assert result.quality_score >= 0.0  # Score is calculated from context if no scorer

    def test_custom_template(
        self,
        sample_document,
        mock_policy,
        mock_template_engine,
    ):
        """Test conversion with custom template."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
        )

        service.convert_to_markdown(sample_document, template_name="custom")

        assert mock_template_engine.render_called
        assert mock_template_engine.render_args[0] == "custom"

    def test_policy_receives_correct_parameters(
        self,
        sample_document,
        mock_policy,
        mock_template_engine,
    ):
        """Test policy receives correct document parameters."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
        )

        service.convert_to_markdown(sample_document)

        # Verify policy was called with correct parameters
        assert mock_policy.choose_called
        mime, size, has_tables, precision = mock_policy.choose_args
        assert mime == sample_document.mime
        assert size == sample_document.size_bytes
        assert isinstance(has_tables, bool)
        assert precision == sample_document.precision


class TestConverterServiceFallback:
    """Test ConverterService fallback mechanism."""

    def test_fallback_on_extractor_failure(
        self,
        sample_document,
        mock_template_engine,
    ):
        """Test fallback to next extractor on failure."""
        from tests.conftest import MockExtractor, MockPolicy

        # Create extractors: first fails, second succeeds
        failing_extractor = MockExtractor(name="FailingExtractor")
        success_extractor = MockExtractor(name="SuccessExtractor")

        # Make first extractor fail
        def failing_extract(data: bytes, precision: PrecisionLevel) -> ExtractionResult:
            return ExtractionResult(
                success=False,
                error="Intentional failure",
                extractor_name="FailingExtractor",
            )

        failing_extractor.extract = failing_extract  # type: ignore

        policy = MockPolicy(extractors=[failing_extractor, success_extractor])
        service = ConverterService(
            policy=policy,
            template_engine=mock_template_engine,
        )

        result = service.convert_to_markdown(sample_document)

        # Should use second extractor (verify fallback worked)
        assert result.metadata["extractor"] == "SuccessExtractor"
        assert result.text == "# Rendered Markdown"  # Template engine renders this
        # Verify the failing extractor was attempted
        assert "FailingExtractor" in result.metadata["attempted_extractors"]

    def test_no_fallback_when_disabled(
        self,
        sample_document,
        mock_template_engine,
    ):
        """Test no fallback when allow_fallback=False."""
        from tests.conftest import MockExtractor, MockPolicy

        # Create failing extractor
        failing_extractor = MockExtractor(name="FailingExtractor")

        def failing_extract(data: bytes, precision: PrecisionLevel) -> ExtractionResult:
            return ExtractionResult(
                success=False,
                error="Intentional failure",
                extractor_name="FailingExtractor",
            )

        failing_extractor.extract = failing_extract  # type: ignore

        policy = MockPolicy(extractors=[failing_extractor])
        service = ConverterService(
            policy=policy,
            template_engine=mock_template_engine,
        )

        # Should raise exception without fallback
        with pytest.raises(ConversionFailed):
            service.convert_to_markdown(sample_document, allow_fallback=False)

    def test_all_extractors_fail(
        self,
        sample_document,
        mock_template_engine,
    ):
        """Test when all extractors fail."""
        from tests.conftest import MockExtractor, MockPolicy

        # Create multiple failing extractors
        extractors = [MockExtractor(name=f"Extractor{i}") for i in range(3)]

        def failing_extract(data: bytes, precision: PrecisionLevel) -> ExtractionResult:
            return ExtractionResult(
                success=False,
                error="All extractors fail",
                extractor_name="FailingExtractor",
            )

        for ext in extractors:
            ext.extract = failing_extract  # type: ignore

        policy = MockPolicy(extractors=extractors)
        service = ConverterService(
            policy=policy,
            template_engine=mock_template_engine,
        )

        # Should raise ConversionFailed
        with pytest.raises(ConversionFailed):
            service.convert_to_markdown(sample_document)


class TestConverterServiceEdgeCases:
    """Test edge cases and error handling."""

    def test_unsupported_format(
        self,
        mock_policy,
        mock_template_engine,
    ):
        """Test conversion with unsupported format."""
        from tests.conftest import MockPolicy

        # Create policy that returns no extractors (empty list)
        policy = MockPolicy(extractors=[])

        service = ConverterService(
            policy=policy,
            template_engine=mock_template_engine,
        )

        # Try to convert unsupported format
        unsupported_doc = Document(
            bytes=b"test",
            mime="application/unsupported",
            size_bytes=4,
        )

        # Policy returns no extractors, should raise UnsupportedFormat
        with pytest.raises(UnsupportedFormat):
            service.convert_to_markdown(unsupported_doc)

    def test_empty_document(
        self,
        mock_policy,
        mock_template_engine,
    ):
        """Test conversion validates non-empty documents."""
        # Document model now validates that bytes cannot be empty
        with pytest.raises(ValueError, match="Document bytes cannot be empty"):
            Document(
                bytes=b"",
                mime="application/pdf",
                size_bytes=0,
            )

    def test_conversion_with_real_document(
        self,
        policy_report_pdf,
        load_test_document,
        mock_policy,
        mock_template_engine,
    ):
        """Test conversion workflow with real document (mocked extractors)."""
        doc = load_test_document(policy_report_pdf)

        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
        )

        result = service.convert_to_markdown(doc)

        # Verify workflow executed
        assert result.text is not None
        assert result.metadata["extractor"] == "MockExtractor"
        assert mock_policy.choose_called
        assert mock_template_engine.render_called


class TestConverterServiceAdditionalMethods:
    """Test additional service methods."""

    def test_convert_with_specific_extractor_success(
        self,
        sample_document,
        mock_policy,
        mock_template_engine,
    ):
        """Test converting with a specific extractor by name."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
        )

        result = service.convert_with_specific_extractor(
            sample_document,
            extractor_name="MockExtractor",
        )

        assert result.text is not None
        assert result.metadata["extractor"] == "MockExtractor"

    def test_convert_with_specific_extractor_not_found(
        self,
        sample_document,
        mock_policy,
        mock_template_engine,
    ):
        """Test error when requested extractor not found."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
        )

        with pytest.raises(ValueError, match="Extractor 'NonExistent' not found"):
            service.convert_with_specific_extractor(
                sample_document,
                extractor_name="NonExistent",
            )

    def test_list_available_templates(
        self,
        mock_policy,
        mock_template_engine,
    ):
        """Test listing available templates."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
        )

        templates = service.list_available_templates()

        assert isinstance(templates, (list, tuple))
        # Mock returns ["default", "simple"]
        assert "default" in templates

    def test_get_supported_formats(
        self,
        mock_policy,
        mock_template_engine,
    ):
        """Test getting supported MIME formats."""
        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
        )

        formats = service.get_supported_formats()

        assert isinstance(formats, (list, tuple))
        # Currently returns empty tuple due to implementation
        # This tests the method exists and doesn't crash

    def test_conversion_with_table_profilers(
        self,
        sample_document,
        mock_policy,
        mock_template_engine,
    ):
        """Test conversion with table profilers configured."""

        class MockTableProfiler:
            def profile(self, ndoc: NormalizedDoc) -> NormalizedDoc:
                # Return the document unchanged
                return ndoc

        profiler = MockTableProfiler()

        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
            table_profilers=[profiler],
        )

        result = service.convert_to_markdown(sample_document)

        assert result.text is not None
        # Verify conversion succeeded with table profiler

    def test_conversion_with_quality_scorer(
        self,
        sample_document,
        mock_policy,
        mock_template_engine,
    ):
        """Test conversion with custom quality scorer."""

        class MockQualityScorer:
            def calculate_score(
                self, ndoc: NormalizedDoc, markdown: str, original: Document
            ) -> float:
                return 0.95

        scorer = MockQualityScorer()

        service = ConverterService(
            policy=mock_policy,
            template_engine=mock_template_engine,
            quality_scorer=scorer,
        )

        result = service.convert_to_markdown(sample_document)

        # Should use custom scorer's score
        assert result.quality_score == 0.95


class TestConverterServiceRetryLogic:
    """Test retry logic in extract_with_retry."""

    def test_retry_on_recoverable_error(
        self,
        sample_document,
        mock_template_engine,
    ):
        """Test retry mechanism on recoverable errors."""
        from tests.conftest import MockExtractor, MockPolicy

        extractor = MockExtractor()
        attempt_count = 0

        def failing_then_success(data: bytes, precision: PrecisionLevel) -> ExtractionResult:
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count < 2:
                # First attempt fails
                raise Exception("Temporary failure")

            # Second attempt succeeds
            blocks = (Block(type=BlockType.TEXT, content="Success after retry"),)
            ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf")
            return ExtractionResult(
                success=True,
                normalized_doc=ndoc,
                extractor_name="MockExtractor",
                processing_time_seconds=0.1,
            )

        extractor.extract = failing_then_success  # type: ignore

        policy = MockPolicy(extractors=[extractor])
        service = ConverterService(
            policy=policy,
            template_engine=mock_template_engine,
        )

        # Should succeed after retry
        result = service.convert_to_markdown(sample_document)

        assert result.text is not None
        assert attempt_count == 2  # Retried once

    def test_unexpected_exception_handling(
        self,
        sample_document,
        mock_template_engine,
    ):
        """Test handling of unexpected exceptions."""
        from tests.conftest import MockExtractor, MockPolicy

        extractor = MockExtractor()

        def raise_unexpected(data: bytes, precision: PrecisionLevel) -> ExtractionResult:
            raise RuntimeError("Unexpected error")

        extractor.extract = raise_unexpected  # type: ignore

        policy = MockPolicy(extractors=[extractor])
        service = ConverterService(
            policy=policy,
            template_engine=mock_template_engine,
        )

        # Should handle unexpected exception gracefully without fallback
        # Should convert unexpected exception to ConversionFailed with fallback disabled
        with pytest.raises(ConversionFailed):
            service.convert_to_markdown(sample_document, allow_fallback=False)
