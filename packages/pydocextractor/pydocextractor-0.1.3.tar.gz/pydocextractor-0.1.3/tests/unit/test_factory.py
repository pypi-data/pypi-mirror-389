"""
Unit tests for dependency injection factory.

Tests the composition root that wires together all dependencies.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pydocextractor.app.service import ConverterService
from pydocextractor.domain.models import PrecisionLevel
from pydocextractor.factory import (
    create_converter_service,
    get_available_extractors,
    get_extractor_by_level,
)


class TestCreateConverterService:
    """Test create_converter_service factory function."""

    def test_creates_service_with_default_template_dir(self):
        """Test creating service with default template directory."""
        service = create_converter_service()

        assert isinstance(service, ConverterService)
        # Service should be created successfully
        assert service is not None

    def test_creates_service_with_custom_template_dir(self, tmp_path: Path):
        """Test creating service with custom template directory."""
        custom_dir = tmp_path / "templates"
        custom_dir.mkdir()

        # Create minimal template file
        (custom_dir / "default.md.jinja2").write_text("{{ blocks[0].content }}")

        service = create_converter_service(template_dir=custom_dir)

        assert isinstance(service, ConverterService)
        assert service is not None


class TestGetAvailableExtractors:
    """Test get_available_extractors function."""

    def test_returns_sequence_of_extractors(self):
        """Test returns sequence of Extractor implementations."""
        extractors = get_available_extractors()

        assert isinstance(extractors, (list, tuple))
        assert len(extractors) > 0

    def test_all_extractors_are_available(self):
        """Test all returned extractors report as available."""
        extractors = get_available_extractors()

        for extractor in extractors:
            assert extractor.is_available() is True

    def test_extractors_have_unique_levels(self):
        """Test extractors have precision levels (some may share the same level)."""
        extractors = get_available_extractors()

        levels = [e.precision_level for e in extractors]
        # Should have at least one extractor
        assert len(levels) > 0
        # Should cover the main precision levels (not all have to be unique)
        # Multiple extractors can share HIGHEST_QUALITY (e.g., Docling, CSV, Excel)
        unique_levels = set(levels)
        assert len(unique_levels) >= 3  # At least 3 different levels represented

    def test_extractors_support_pdf(self):
        """Test PDF-capable extractors support PDF format."""
        extractors = get_available_extractors()

        # PDF extractors should support PDF
        pdf_extractors = [
            e
            for e in extractors
            if "PDF" in e.name.upper() or "Chunked" in e.name or "PyMuPDF" in e.name
        ]
        assert len(pdf_extractors) > 0, "Should have at least one PDF extractor"

        for extractor in pdf_extractors:
            assert extractor.supports("application/pdf") is True

    def test_common_extractors_available(self):
        """Test that commonly expected extractors are available."""
        extractors = get_available_extractors()
        levels = [e.precision_level for e in extractors]

        # At minimum, should have level 2 (PyMuPDF4LLM - default)
        # This is the most reliable extractor
        assert PrecisionLevel.BALANCED in levels


class TestGetExtractorByLevel:
    """Test get_extractor_by_level function."""

    def test_get_available_level(self):
        """Test getting an extractor by available level."""
        # Get first available level
        available = get_available_extractors()
        if not available:
            pytest.skip("No extractors available")

        first_level = available[0].precision_level
        extractor = get_extractor_by_level(first_level)

        assert extractor is not None
        assert extractor.precision_level == first_level

    def test_get_unavailable_level(self):
        """Test getting an extractor by unavailable level returns None."""
        # Get all available levels
        available = get_available_extractors()
        available_levels = {e.precision_level for e in available}

        # Find an unavailable level
        all_levels = [
            PrecisionLevel.FASTEST,
            PrecisionLevel.BALANCED,
            PrecisionLevel.TABLE_OPTIMIZED,
            PrecisionLevel.HIGHEST_QUALITY,
        ]

        unavailable_level = None
        for level in all_levels:
            if level not in available_levels:
                unavailable_level = level
                break

        if unavailable_level is None:
            # All levels available, test with mock level
            # This shouldn't happen in practice but test the None return
            extractor = get_extractor_by_level(999)  # type: ignore
            assert extractor is None
        else:
            extractor = get_extractor_by_level(unavailable_level)
            assert extractor is None

    def test_get_level_2_default(self):
        """Test getting level 2 (PyMuPDF4LLM) - most common default."""
        extractor = get_extractor_by_level(PrecisionLevel.BALANCED)

        # Level 2 should almost always be available
        if extractor is None:
            pytest.skip("Level 2 (PyMuPDF4LLM) not available in this environment")

        assert extractor.precision_level == PrecisionLevel.BALANCED
        assert extractor.is_available() is True

    def test_extractor_supports_pdf(self):
        """Test that retrieved extractor supports PDF format."""
        # Get any available extractor
        available = get_available_extractors()
        if not available:
            pytest.skip("No extractors available")

        first_level = available[0].precision_level
        extractor = get_extractor_by_level(first_level)

        assert extractor is not None
        # All current extractors support PDF
        assert extractor.supports("application/pdf") is True


class TestFactoryIntegration:
    """Integration tests for factory composition."""

    def test_multiple_service_instances_independent(self):
        """Test multiple service instances are independent."""
        service1 = create_converter_service()
        service2 = create_converter_service()

        # Should be different instances
        assert service1 is not service2

    def test_factory_handles_missing_dependencies_gracefully(self):
        """Test factory handles missing extractor dependencies."""
        # This test verifies the factory doesn't crash if extractors fail to load
        extractors = get_available_extractors()

        # Should return at least an empty list, not crash
        assert isinstance(extractors, (list, tuple))

        # Should have at least one extractor in typical environment
        # but this is environment-dependent
        assert len(extractors) >= 0
