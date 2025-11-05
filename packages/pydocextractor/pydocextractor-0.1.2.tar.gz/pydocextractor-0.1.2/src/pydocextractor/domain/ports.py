"""
Port interfaces for pyDocExtractor using Protocols.

These are the contracts that adapters must implement.
No concrete implementations here - only type definitions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

from .models import Document, ExtractionResult, NormalizedDoc, PrecisionLevel


@runtime_checkable
class Extractor(Protocol):
    """
    Port for document extraction adapters.

    Extractors convert raw document bytes into normalized,
    vendor-agnostic block representations.
    """

    def supports(self, mime: str) -> bool:
        """Check if this extractor supports the given MIME type."""
        ...

    def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
        """
        Extract content from document bytes.

        Args:
            data: Raw document bytes
            precision: Desired precision level

        Returns:
            ExtractionResult with normalized document or error

        Raises:
            RecoverableError: When extraction fails but fallback should be attempted
            ExtractionError: When extraction fails permanently
        """
        ...

    @property
    def name(self) -> str:
        """Human-readable name of this extractor."""
        ...

    @property
    def precision_level(self) -> PrecisionLevel:
        """Precision level this extractor operates at."""
        ...


@runtime_checkable
class Policy(Protocol):
    """
    Port for converter selection policies.

    Policies decide which extractors to try and in what order,
    based on document characteristics.
    """

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
        ...

    def get_extractor_by_level(self, level: PrecisionLevel) -> Extractor | None:
        """Get specific extractor by precision level if available."""
        ...


@runtime_checkable
class TemplateEngine(Protocol):
    """
    Port for template rendering engines.

    Template engines convert normalized documents and contexts
    into final markdown output.
    """

    def render(self, template_name: str, context: Mapping[str, object]) -> str:
        """
        Render template with given context.

        Args:
            template_name: Name/path of template
            context: Template context data

        Returns:
            Rendered markdown text

        Raises:
            TemplateError: When rendering fails
        """
        ...

    def list_templates(self) -> Sequence[str]:
        """List available template names."""
        ...


@runtime_checkable
class DocumentValidator(Protocol):
    """
    Port for document validation.

    Validators check document constraints before processing.
    """

    def validate(self, doc: Document) -> tuple[bool, str | None]:
        """
        Validate document.

        Args:
            doc: Document to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        ...


@runtime_checkable
class QualityScorer(Protocol):
    """
    Port for quality scoring strategies.

    Scorers assess the quality of conversions.
    """

    def calculate_score(
        self,
        ndoc: NormalizedDoc,
        markdown: str,
        original: Document | None = None,
    ) -> float:
        """
        Calculate quality score for conversion.

        Args:
            ndoc: Normalized document
            markdown: Rendered markdown
            original: Original document (optional)

        Returns:
            Quality score between 0.0 and 1.0
        """
        ...


@runtime_checkable
class TableProfiler(Protocol):
    """
    Port for table detection and profiling.

    Profilers analyze documents for tables and structured data.
    """

    def profile(self, ndoc: NormalizedDoc) -> NormalizedDoc:
        """
        Analyze and enhance table information in normalized document.

        Args:
            ndoc: Normalized document

        Returns:
            Enhanced normalized document with table metadata
        """
        ...


@runtime_checkable
class Cache(Protocol):
    """
    Port for caching layer.

    Caches store conversion results by document hash.
    """

    def get(self, key: str) -> NormalizedDoc | None:
        """Get cached normalized document by key."""
        ...

    def set(self, key: str, value: NormalizedDoc, ttl_seconds: int | None = None) -> None:
        """Cache normalized document with optional TTL."""
        ...

    def clear(self) -> None:
        """Clear all cached entries."""
        ...


@runtime_checkable
class ImageDescriber(Protocol):
    """
    Port for image description using multimodal LLMs.

    Image describers analyze images in documents and generate
    textual descriptions based on surrounding context.
    """

    def describe_image(
        self,
        image_data: bytes,
        context_text: str,
        mime_type: str,
    ) -> str:
        """
        Describe an image given contextual information.

        Args:
            image_data: Raw image bytes
            context_text: Surrounding text context (e.g., previous 100 lines)
            mime_type: Image MIME type (e.g., "image/jpeg", "image/png")

        Returns:
            Textual description of the image

        Raises:
            Exception: If description fails (caller should handle gracefully)
        """
        ...
