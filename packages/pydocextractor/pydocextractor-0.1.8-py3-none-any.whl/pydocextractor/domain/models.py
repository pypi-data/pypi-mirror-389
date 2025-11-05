"""
Pure domain models for pyDocExtractor.

These are vendor-free, typed dataclasses with no external dependencies
beyond standard library typing and dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PrecisionLevel(int, Enum):
    """Precision levels for document extraction."""

    FASTEST = 1  # ChunkedParallel
    BALANCED = 2  # PyMuPDF4LLM (default)
    TABLE_OPTIMIZED = 3  # PDFPlumber
    HIGHEST_QUALITY = 4  # Docling


class BlockType(str, Enum):
    """Types of content blocks in normalized documents."""

    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    HEADER = "header"
    LIST = "list"
    CODE = "code"
    METADATA = "metadata"


@dataclass(frozen=True, slots=True)
class Document:
    """
    Input document for conversion.

    This is the primary input to the conversion pipeline.
    Immutable and hashable for caching.
    """

    bytes: bytes
    mime: str
    size_bytes: int
    precision: PrecisionLevel = PrecisionLevel.BALANCED
    filename: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def size_mb(self) -> float:
        """File size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    def __post_init__(self) -> None:
        """Validate document."""
        if not self.bytes:
            raise ValueError("Document bytes cannot be empty")
        if not self.mime:
            raise ValueError("MIME type is required")
        if self.size_bytes <= 0:
            raise ValueError("Document size must be positive")


@dataclass(frozen=True, slots=True)
class Block:
    """
    A normalized content block.

    Represents a semantic unit of content (text, table, image, etc.)
    extracted from a document.
    """

    type: BlockType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    page_number: int | None = None
    confidence: float = 1.0
    image_data: bytes | None = None

    def __post_init__(self) -> None:
        """Validate block."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class NormalizedDoc:
    """
    Normalized document representation.

    Vendor-agnostic intermediate format that all extractors
    must produce. Contains structured blocks of content.
    """

    blocks: tuple[Block, ...]
    source_mime: str
    page_count: int | None = None
    has_tables: bool = False
    has_images: bool = False
    extractor_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def text_content(self) -> str:
        """Concatenate all text blocks."""
        return "\n\n".join(block.content for block in self.blocks if block.type == BlockType.TEXT)

    @property
    def table_blocks(self) -> tuple[Block, ...]:
        """Get only table blocks."""
        return tuple(block for block in self.blocks if block.type == BlockType.TABLE)

    def __post_init__(self) -> None:
        """Validate normalized document."""
        if not self.blocks:
            raise ValueError("NormalizedDoc must have at least one block")
        if self.page_count is not None and self.page_count <= 0:
            raise ValueError("Page count must be positive if provided")


@dataclass(frozen=True, slots=True)
class TemplateContext:
    """
    Context data for template rendering.

    Pure data structure passed to template engines.
    """

    blocks: tuple[dict[str, Any], ...]
    metadata: dict[str, Any]
    has_tables: bool
    has_images: bool
    page_count: int | None
    quality_score: float | None = None

    @classmethod
    def from_normalized_doc(
        cls,
        ndoc: NormalizedDoc,
        original_doc: Document | None = None,
        quality_score: float | None = None,
    ) -> TemplateContext:
        """Create context from normalized document."""
        # Convert blocks to dicts for template consumption
        block_dicts = tuple(
            {
                "type": block.type.value,
                "content": block.content,
                "page": block.page_number,
                "confidence": block.confidence,
                **block.metadata,
            }
            for block in ndoc.blocks
        )

        metadata = dict(ndoc.metadata)
        if ndoc.extractor_name:
            metadata["extractor"] = ndoc.extractor_name
        if original_doc and original_doc.filename:
            metadata["filename"] = original_doc.filename

        return cls(
            blocks=block_dicts,
            metadata=metadata,
            has_tables=ndoc.has_tables,
            has_images=ndoc.has_images,
            page_count=ndoc.page_count,
            quality_score=quality_score,
        )


@dataclass(frozen=True, slots=True)
class Markdown:
    """
    Final markdown output.

    Result of the conversion pipeline.
    """

    text: str
    quality_score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate markdown."""
        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError("Quality score must be between 0 and 1")

    @property
    def char_count(self) -> int:
        """Number of characters in markdown."""
        return len(self.text)

    @property
    def word_count(self) -> int:
        """Approximate word count."""
        return len(self.text.split())


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """
    Result of an extraction attempt.

    Tracks success/failure and provides error details for diagnostics.
    """

    success: bool
    normalized_doc: NormalizedDoc | None = None
    error: str | None = None
    extractor_name: str | None = None
    processing_time_seconds: float = 0.0

    def __post_init__(self) -> None:
        """Validate result."""
        if self.success and self.normalized_doc is None:
            raise ValueError("Successful result must have normalized_doc")
        if not self.success and self.error is None:
            raise ValueError("Failed result must have error message")
