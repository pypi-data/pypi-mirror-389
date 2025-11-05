"""
Default policy implementation using heuristics.

Implements intelligent converter selection based on document characteristics.
"""

from __future__ import annotations

from collections.abc import Sequence

from ...domain import Extractor, PrecisionLevel
from ..extractors.chunked_parallel_adapter import ChunkedParallelExtractor
from ..extractors.docling_adapter import DoclingExtractor
from ..extractors.pandas_csv_adapter import PandasCSVExtractor
from ..extractors.pandas_excel_adapter import PandasExcelExtractor
from ..extractors.pdfplumber_adapter import PDFPlumberExtractor
from ..extractors.pymupdf4llm_adapter import PyMuPDF4LLMExtractor

# Constants for file size thresholds
LARGE_PDF_SIZE_MB = 20.0
SMALL_PDF_SIZE_MB = 2.0


class DefaultPolicy:
    """
    Default policy using heuristic rules for converter selection.

    Selection strategy:
    - Docling (Level 4): Small files (<2MB) or DOCX/XLSX formats
    - PDFPlumber (Level 3): PDFs with tables detected
    - ChunkedParallel (Level 1): Large files (>20MB)
    - PyMuPDF4LLM (Level 2): Default for most PDFs

    Fallback chain: Level 2 → Level 1 → Level 3 → Level 4
    """

    def __init__(self, llm_enabled: bool = False) -> None:
        """
        Initialize policy with available extractors.

        Args:
            llm_enabled: If True, extractors will extract images for LLM description
        """
        self._extractors: dict[PrecisionLevel, Extractor] = {}
        self._csv_extractor: Extractor | None = None
        self._excel_extractor: Extractor | None = None

        # Initialize all extractors (pass llm_enabled to those that support it)
        self._extractors[PrecisionLevel.FASTEST] = ChunkedParallelExtractor()
        self._extractors[PrecisionLevel.BALANCED] = PyMuPDF4LLMExtractor(
            enable_image_extraction=llm_enabled
        )
        self._extractors[PrecisionLevel.TABLE_OPTIMIZED] = PDFPlumberExtractor(
            enable_image_extraction=llm_enabled
        )
        self._extractors[PrecisionLevel.HIGHEST_QUALITY] = DoclingExtractor()

        # Initialize CSV extractor separately (not part of precision levels)
        csv_extractor = PandasCSVExtractor()
        if csv_extractor.is_available():
            self._csv_extractor = csv_extractor

        # Initialize Excel extractor separately (not part of precision levels)
        excel_extractor = PandasExcelExtractor()
        if excel_extractor.is_available():
            self._excel_extractor = excel_extractor

    def choose_extractors(
        self,
        mime: str,
        size_bytes: int,
        has_tables: bool,
        precision: PrecisionLevel,
    ) -> Sequence[Extractor]:
        """
        Choose ordered sequence of extractors to try.

        Args:
            mime: Document MIME type
            size_bytes: Document size in bytes
            has_tables: Whether document has tables (hint)
            precision: Desired precision level

        Returns:
            Ordered sequence of extractors to attempt
        """
        size_mb = size_bytes / (1024 * 1024)

        # 0. Check for specialized extractors first (before precision level checks)
        # CSV files always use PandasCSV extractor
        if mime == "text/csv" and self._csv_extractor:
            return (self._csv_extractor,)

        # Excel files always use PandasExcel extractor (multi-sheet support)
        if (
            mime
            in [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
            ]
            and self._excel_extractor
        ):
            return (self._excel_extractor,)

        # If specific precision level requested, try that first
        if precision in self._extractors:
            primary = self._extractors[precision]
            if primary.supports(mime):
                # Build fallback chain excluding the primary
                fallbacks = self._build_fallback_chain(mime, exclude=precision)
                return tuple([primary] + fallbacks)

        # Auto-selection based on heuristics
        selected: list[Extractor] = []

        # 1. Check for non-PDF formats (Docling only - DOCX)
        if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            docling = self._extractors[PrecisionLevel.HIGHEST_QUALITY]
            if docling.supports(mime):
                selected.append(docling)
            return tuple(selected)

        # 2. For PDFs, apply selection strategy
        if mime == "application/pdf":
            # Very large files -> ChunkedParallel (Level 1)
            if size_mb > LARGE_PDF_SIZE_MB:
                fastest = self._extractors[PrecisionLevel.FASTEST]
                if fastest.supports(mime):
                    selected.append(fastest)

            # Small files with high quality needs -> Docling (Level 4)
            elif size_mb < SMALL_PDF_SIZE_MB:
                highest = self._extractors[PrecisionLevel.HIGHEST_QUALITY]
                if highest.supports(mime):
                    selected.append(highest)

            # Files with tables -> PDFPlumber (Level 3)
            elif has_tables:
                table_opt = self._extractors[PrecisionLevel.TABLE_OPTIMIZED]
                if table_opt.supports(mime):
                    selected.append(table_opt)

        # 3. Add default (PyMuPDF4LLM - Level 2) if not selected yet
        if not selected:
            balanced = self._extractors[PrecisionLevel.BALANCED]
            if balanced.supports(mime):
                selected.append(balanced)

        # 4. Add fallback chain
        if selected:
            primary_level = selected[0].precision_level
            fallbacks = self._build_fallback_chain(mime, exclude=primary_level)
            selected.extend(fallbacks)

        return tuple(selected)

    def get_extractor_by_level(self, level: PrecisionLevel) -> Extractor | None:
        """Get specific extractor by precision level if available."""
        return self._extractors.get(level)

    def _build_fallback_chain(
        self, mime: str, exclude: PrecisionLevel | None = None
    ) -> list[Extractor]:
        """
        Build fallback chain for given MIME type.

        Fallback order: Level 2 → Level 1 → Level 3 → Level 4

        Args:
            mime: MIME type to support
            exclude: Precision level to exclude from chain

        Returns:
            List of fallback extractors
        """
        fallback_order = [
            PrecisionLevel.BALANCED,  # Level 2
            PrecisionLevel.FASTEST,  # Level 1
            PrecisionLevel.TABLE_OPTIMIZED,  # Level 3
            PrecisionLevel.HIGHEST_QUALITY,  # Level 4 (slowest, so last)
        ]

        fallbacks: list[Extractor] = []

        for level in fallback_order:
            if level == exclude:
                continue

            extractor = self._extractors.get(level)
            if extractor and extractor.supports(mime):
                fallbacks.append(extractor)

        return fallbacks

    def get_all_extractors(self) -> dict[PrecisionLevel, Extractor]:
        """Get all available extractors."""
        return dict(self._extractors)
