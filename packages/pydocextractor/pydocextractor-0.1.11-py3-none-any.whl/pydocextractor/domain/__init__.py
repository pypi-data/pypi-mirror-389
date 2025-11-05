"""
Domain layer for pyDocExtractor.

Pure, typed, vendor-free business logic. No infrastructure dependencies.
"""

from .errors import (
    ConversionFailed,
    DomainError,
    ExtractionError,
    RecoverableError,
    TemplateError,
    UnsupportedFormat,
    ValidationError,
)
from .models import (
    Block,
    BlockType,
    Document,
    ExtractionResult,
    Markdown,
    NormalizedDoc,
    PrecisionLevel,
    TemplateContext,
)
from .ports import (
    Cache,
    DocumentValidator,
    Extractor,
    Policy,
    QualityScorer,
    TableProfiler,
    TemplateEngine,
)
from .rules import (
    build_template_context,
    calculate_document_hash,
    estimate_processing_time,
    hint_has_tables,
    merge_text_blocks,
    normalize_blocks,
    quality_score,
    validate_precision_level,
)

__all__ = [
    # Errors
    "DomainError",
    "ConversionFailed",
    "RecoverableError",
    "UnsupportedFormat",
    "ValidationError",
    "ExtractionError",
    "TemplateError",
    # Models
    "Document",
    "Block",
    "BlockType",
    "NormalizedDoc",
    "TemplateContext",
    "Markdown",
    "PrecisionLevel",
    "ExtractionResult",
    # Ports
    "Extractor",
    "Policy",
    "TemplateEngine",
    "DocumentValidator",
    "QualityScorer",
    "TableProfiler",
    "Cache",
    # Rules
    "quality_score",
    "hint_has_tables",
    "build_template_context",
    "calculate_document_hash",
    "normalize_blocks",
    "merge_text_blocks",
    "validate_precision_level",
    "estimate_processing_time",
]
