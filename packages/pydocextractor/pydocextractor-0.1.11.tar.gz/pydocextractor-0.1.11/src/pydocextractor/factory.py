"""
Dependency injection factory for hexagonal architecture.

This is the composition root where all dependencies are wired together.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .app.service import ConverterService
from .domain.models import PrecisionLevel
from .domain.ports import Extractor
from .domain.profilers.table_profiler import TableProfiler
from .infra.extractors.chunked_parallel_adapter import ChunkedParallelExtractor
from .infra.extractors.docling_adapter import DoclingExtractor
from .infra.extractors.pandas_csv_adapter import PandasCSVExtractor
from .infra.extractors.pandas_excel_adapter import PandasExcelExtractor
from .infra.extractors.pdfplumber_adapter import PDFPlumberExtractor
from .infra.extractors.pymupdf4llm_adapter import PyMuPDF4LLMExtractor
from .infra.policy.heuristics import DefaultPolicy
from .infra.scoring.default_scorer import DefaultQualityScorer
from .infra.templates.engines import Jinja2TemplateEngine


def create_converter_service(
    template_dir: Path | None = None,
    llm_config: object | None = None,
    auto_load_llm: bool = True,
) -> ConverterService:
    """
    Create a fully configured ConverterService with all dependencies.

    This is the composition root for the hexagonal architecture.

    Args:
        template_dir: Optional custom template directory
        llm_config: Optional LLM configuration. If None and auto_load_llm is True,
                   will attempt to load from environment variables.
        auto_load_llm: If True, automatically load LLM config from environment

    Returns:
        Configured ConverterService ready to use (works with or without LLM)
    """
    import logging

    logger = logging.getLogger(__name__)

    # Load LLM config if requested and not provided
    if llm_config is None and auto_load_llm:
        try:
            from .infra.config import load_llm_config

            llm_config = load_llm_config()
        except Exception as e:
            logger.warning(f"Failed to load LLM config, continuing without: {e}")
            llm_config = None

    # Initialize image describer if config available
    image_describer: object | None = None

    if llm_config and hasattr(llm_config, "enabled") and llm_config.enabled:
        try:
            from .infra.llm import OpenAIImageDescriber, ResilientImageDescriber

            base_describer = OpenAIImageDescriber(llm_config)  # type: ignore[arg-type]
            image_describer = ResilientImageDescriber(base_describer, llm_config)  # type: ignore[arg-type]

            max_images = getattr(llm_config, "max_images_per_document", 5)
            logger.info(f"LLM image description: Enabled (max {max_images} images per document)")

        except ImportError as e:
            logger.warning(
                f"LLM dependencies not available: {e}. "
                "Install with: pip install pydocextractor[llm]"
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
    else:
        logger.info("LLM image description: Disabled")

    # Check if LLM is enabled for image extraction
    llm_enabled = llm_config is not None and hasattr(llm_config, "enabled") and llm_config.enabled

    # Create policy (pass llm_enabled so extractors know whether to extract images)
    policy = DefaultPolicy(llm_enabled=llm_enabled)

    # Create template engine
    if template_dir is None:
        template_engine = Jinja2TemplateEngine()
    else:
        template_engine = Jinja2TemplateEngine(template_dir=template_dir)

    # Create quality scorer
    quality_scorer = DefaultQualityScorer()

    # Create table profiler for PDF/Word documents
    table_profiler = TableProfiler(max_sample_rows=5)

    # Compose service with optional LLM support
    return ConverterService(
        policy=policy,
        template_engine=template_engine,
        quality_scorer=quality_scorer,
        table_profilers=[table_profiler],
        image_describer=image_describer,
        llm_config=llm_config,
    )


def _create_extractors() -> Sequence[Extractor]:
    """
    Create all available extractors.

    Only includes extractors whose dependencies are installed.

    Returns:
        List of available Extractor implementations
    """
    extractors: list[Extractor] = []

    # Level 1: ChunkedParallel (PyMuPDF - fitz)
    try:
        chunked_extractor = ChunkedParallelExtractor()
        if chunked_extractor.is_available():
            extractors.append(chunked_extractor)
    except Exception:
        pass  # Dependencies not installed

    # Level 2: PyMuPDF4LLM (default)
    try:
        pymupdf_extractor = PyMuPDF4LLMExtractor()
        if pymupdf_extractor.is_available():
            extractors.append(pymupdf_extractor)
    except Exception:
        pass  # Dependencies not installed

    # Level 3: PDFPlumber
    try:
        pdfplumber_extractor = PDFPlumberExtractor()
        if pdfplumber_extractor.is_available():
            extractors.append(pdfplumber_extractor)
    except Exception:
        pass  # Dependencies not installed

    # Level 4: Docling
    try:
        docling_extractor = DoclingExtractor()
        if docling_extractor.is_available():
            extractors.append(docling_extractor)
    except Exception:
        pass  # Dependencies not installed

    # CSV: PandasCSV (specialized for CSV files)
    try:
        csv_extractor = PandasCSVExtractor()
        if csv_extractor.is_available():
            extractors.append(csv_extractor)
    except Exception:
        pass  # Dependencies not installed

    # Excel: PandasExcel (specialized for Excel files with multi-sheet support)
    try:
        excel_extractor = PandasExcelExtractor()
        if excel_extractor.is_available():
            extractors.append(excel_extractor)
    except Exception:
        pass  # Dependencies not installed

    return extractors


def get_available_extractors() -> Sequence[Extractor]:
    """
    Get list of available extractors.

    Returns:
        List of Extractor implementations that are available
    """
    return _create_extractors()


def get_extractor_by_level(level: PrecisionLevel) -> Extractor | None:
    """
    Get a specific extractor by precision level.

    Args:
        level: Desired precision level

    Returns:
        Extractor for that level if available, None otherwise
    """
    extractors = _create_extractors()
    for extractor in extractors:
        if extractor.precision_level == level:
            return extractor
    return None
