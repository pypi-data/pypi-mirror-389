"""
Unit tests for policy heuristics infrastructure.

Tests for DefaultPolicy implementation.
"""

from __future__ import annotations

from pydocextractor.domain.models import PrecisionLevel
from pydocextractor.infra.policy.heuristics import DefaultPolicy


class TestDefaultPolicy:
    """Test DefaultPolicy heuristic selection."""

    def test_init_creates_extractors(self):
        """Test policy initializes with extractors."""
        policy = DefaultPolicy()
        assert policy is not None

    def test_choose_extractors_for_small_pdf(self):
        """Test extractor selection for small PDF."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=500_000,  # 500 KB - small
            has_tables=False,
            precision=PrecisionLevel.BALANCED,
        )

        assert len(extractors) > 0
        # Should return at least the requested precision level
        levels = [e.precision_level for e in extractors]
        assert PrecisionLevel.BALANCED in levels

    def test_choose_extractors_for_large_pdf(self):
        """Test extractor selection for large PDF (>20MB)."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=25 * 1024 * 1024,  # 25 MB - large
            has_tables=False,
            precision=PrecisionLevel.BALANCED,
        )

        assert len(extractors) > 0
        # Large files might prefer fast extractor
        assert all(e.precision_level in [1, 2, 3, 4] for e in extractors)

    def test_choose_extractors_with_tables(self):
        """Test extractor selection for PDF with tables."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=2 * 1024 * 1024,  # 2 MB
            has_tables=True,  # Has tables
            precision=PrecisionLevel.TABLE_OPTIMIZED,
        )

        assert len(extractors) > 0
        levels = [e.precision_level for e in extractors]
        # Should include table-optimized extractor
        assert PrecisionLevel.TABLE_OPTIMIZED in levels

    def test_choose_extractors_highest_quality(self):
        """Test extractor selection for highest quality."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=1 * 1024 * 1024,  # 1 MB
            has_tables=False,
            precision=PrecisionLevel.HIGHEST_QUALITY,
        )

        assert len(extractors) > 0
        levels = [e.precision_level for e in extractors]
        assert PrecisionLevel.HIGHEST_QUALITY in levels

    def test_choose_extractors_fastest(self):
        """Test extractor selection for fastest processing."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=10 * 1024 * 1024,  # 10 MB
            has_tables=False,
            precision=PrecisionLevel.FASTEST,
        )

        assert len(extractors) > 0
        levels = [e.precision_level for e in extractors]
        assert PrecisionLevel.FASTEST in levels

    def test_choose_extractors_returns_fallback_chain(self):
        """Test that policy returns multiple extractors for fallback."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=5 * 1024 * 1024,
            has_tables=False,
            precision=PrecisionLevel.BALANCED,
        )

        # Should return multiple extractors for fallback
        assert len(extractors) >= 1

    def test_get_all_extractors(self):
        """Test getting all extractors."""
        policy = DefaultPolicy()

        extractors_dict = policy.get_all_extractors()

        assert isinstance(extractors_dict, dict)
        assert len(extractors_dict) > 0
        # Should have common levels
        assert PrecisionLevel.BALANCED in extractors_dict

    def test_choose_extractors_docx_file(self):
        """Test extractor selection for DOCX files."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=1 * 1024 * 1024,
            has_tables=False,
            precision=PrecisionLevel.HIGHEST_QUALITY,
        )

        # DOCX should prefer level 4 (Docling)
        assert len(extractors) > 0
        levels = [e.precision_level for e in extractors]
        assert PrecisionLevel.HIGHEST_QUALITY in levels

    def test_choose_extractors_xlsx_file(self):
        """Test extractor selection for XLSX files."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            size_bytes=500_000,
            has_tables=True,  # Spreadsheets have tables
            precision=PrecisionLevel.HIGHEST_QUALITY,
        )

        # XLSX should use Docling
        assert len(extractors) > 0

    def test_extractors_are_available(self):
        """Test that returned extractors report as available."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=1024 * 1024,
            has_tables=False,
            precision=PrecisionLevel.BALANCED,
        )

        for extractor in extractors:
            assert extractor.is_available() is True

    def test_extractors_support_requested_mime(self):
        """Test that returned extractors support the MIME type."""
        policy = DefaultPolicy()

        mime = "application/pdf"
        extractors = policy.choose_extractors(
            mime=mime,
            size_bytes=1024 * 1024,
            has_tables=False,
            precision=PrecisionLevel.BALANCED,
        )

        for extractor in extractors:
            assert extractor.supports(mime) is True

    def test_policy_consistency(self):
        """Test policy returns consistent results for same input."""
        policy = DefaultPolicy()

        params = {
            "mime": "application/pdf",
            "size_bytes": 2 * 1024 * 1024,
            "has_tables": False,
            "precision": PrecisionLevel.BALANCED,
        }

        extractors1 = policy.choose_extractors(**params)
        extractors2 = policy.choose_extractors(**params)

        # Should return same extractors in same order
        assert len(extractors1) == len(extractors2)
        assert [e.name for e in extractors1] == [e.name for e in extractors2]

    def test_edge_case_very_small_file(self):
        """Test extractor selection for very small file."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=1024,  # 1 KB - very small
            has_tables=False,
            precision=PrecisionLevel.BALANCED,
        )

        assert len(extractors) > 0
        # Should still work for tiny files

    def test_edge_case_huge_file(self):
        """Test extractor selection for huge file."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=100 * 1024 * 1024,  # 100 MB
            has_tables=False,
            precision=PrecisionLevel.FASTEST,
        )

        assert len(extractors) > 0
        # Should prefer fast extractors for huge files


class TestDefaultPolicyFallbackChain:
    """Test fallback chain building logic."""

    def test_get_extractor_by_level(self):
        """Test getting specific extractor by level."""
        policy = DefaultPolicy()

        extractor = policy.get_extractor_by_level(PrecisionLevel.BALANCED)

        assert extractor is not None
        assert extractor.precision_level == PrecisionLevel.BALANCED

    def test_get_extractor_by_unavailable_level(self):
        """Test getting extractor for level that doesn't exist."""
        policy = DefaultPolicy()

        # Use a mock level (type: ignore to bypass type checking)
        extractor = policy.get_extractor_by_level(999)  # type: ignore

        assert extractor is None

    def test_fallback_chain_excludes_primary(self):
        """Test that fallback chain excludes the primary extractor."""
        policy = DefaultPolicy()

        # Get extractors for balanced (level 2)
        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=1 * 1024 * 1024,
            has_tables=False,
            precision=PrecisionLevel.BALANCED,
        )

        # First should be balanced, others should be fallbacks
        assert extractors[0].precision_level == PrecisionLevel.BALANCED

        # Rest should not include balanced (no duplicates)
        fallback_levels = [e.precision_level for e in extractors[1:]]
        assert PrecisionLevel.BALANCED not in fallback_levels

    def test_policy_provides_multiple_extractors_for_robustness(self):
        """Test that policy provides multiple extractors for robustness."""
        policy = DefaultPolicy()

        extractors = policy.choose_extractors(
            mime="application/pdf",
            size_bytes=5 * 1024 * 1024,
            has_tables=False,
            precision=PrecisionLevel.BALANCED,
        )

        # Should have multiple extractors for fallback
        assert len(extractors) > 1, "Policy should provide fallback extractors"
