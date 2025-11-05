"""
Domain exceptions for pyDocExtractor.

These exceptions are pure domain concepts and have no dependencies on infrastructure.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for all domain errors."""

    pass


class ConversionFailed(DomainError):
    """Raised when document conversion fails after all attempts."""

    def __init__(self, message: str, attempted_extractors: list[str] | None = None) -> None:
        super().__init__(message)
        self.attempted_extractors = attempted_extractors or []


class RecoverableError(DomainError):
    """Raised when an extractor fails but fallback should be attempted."""

    pass


class UnsupportedFormat(DomainError):
    """Raised when document format is not supported by any extractor."""

    def __init__(self, mime_type: str, available_formats: list[str] | None = None) -> None:
        super().__init__(f"Unsupported format: {mime_type}")
        self.mime_type = mime_type
        self.available_formats = available_formats or []


class ValidationError(DomainError):
    """Raised when document fails validation rules."""

    pass


class ExtractionError(DomainError):
    """Raised when extraction process encounters an error."""

    pass


class TemplateError(DomainError):
    """Raised when template rendering fails."""

    pass
