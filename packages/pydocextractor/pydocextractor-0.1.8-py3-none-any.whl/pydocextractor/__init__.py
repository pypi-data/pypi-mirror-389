"""
pyDocExtractor - Document to Markdown Converter Library

A Python library for converting documents (PDF, DOCX, XLSX, CSV) to Markdown with
hexagonal architecture and multiple precision levels.

Example:
    >>> from pydocextractor import create_converter_service
    >>> from pydocextractor.domain import Document, PrecisionLevel
    >>>
    >>> service = create_converter_service()
    >>>
    >>> # Load document
    >>> with open("document.pdf", "rb") as f:
    >>>     data = f.read()
    >>>
    >>> doc = Document(
    >>>     bytes=data,
    >>>     mime="application/pdf",
    >>>     size_bytes=len(data),
    >>>     filename="document.pdf",
    >>>     precision=PrecisionLevel.BALANCED
    >>> )
    >>>
    >>> # Convert to markdown
    >>> result = service.convert_to_markdown(doc)
    >>> print(result.text)
"""

__version__ = "0.2.0"

# Factory functions
# Application service
from .app.service import ConverterService

# Domain models and types
from .domain import (
    Block,
    BlockType,
    ConversionFailed,
    Document,
    ExtractionError,
    ExtractionResult,
    Extractor,
    Markdown,
    NormalizedDoc,
    Policy,
    PrecisionLevel,
    QualityScorer,
    RecoverableError,
    TemplateContext,
    TemplateEngine,
    TemplateError,
    UnsupportedFormat,
    build_template_context,
    calculate_document_hash,
    hint_has_tables,
    quality_score,
)
from .factory import (
    create_converter_service,
    get_available_extractors,
    get_extractor_by_level,
)

__all__ = [
    # Version
    "__version__",
    # Factory functions
    "create_converter_service",
    "get_available_extractors",
    "get_extractor_by_level",
    # Domain models
    "Document",
    "Block",
    "BlockType",
    "NormalizedDoc",
    "Markdown",
    "ExtractionResult",
    "TemplateContext",
    "PrecisionLevel",
    # Domain protocols (interfaces)
    "Extractor",
    "Policy",
    "QualityScorer",
    "TemplateEngine",
    # Domain functions
    "build_template_context",
    "calculate_document_hash",
    "hint_has_tables",
    "quality_score",
    # Errors
    "ExtractionError",
    "ConversionFailed",
    "UnsupportedFormat",
    "RecoverableError",
    "TemplateError",
    # Application service
    "ConverterService",
]
