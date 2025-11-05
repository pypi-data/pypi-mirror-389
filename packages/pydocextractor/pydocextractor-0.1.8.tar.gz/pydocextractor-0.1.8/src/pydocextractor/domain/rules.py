"""
Pure domain rules and business logic for pyDocExtractor.

These are pure functions with no side effects or external dependencies.
All logic here operates on domain models only.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

# Constants for quality scoring
from .models import Block, BlockType, Document, NormalizedDoc, TemplateContext

MIN_CONTENT_LENGTH = 100
GOOD_CONTENT_LENGTH = 1000
MIN_WORD_COUNT = 50
GOOD_WORD_COUNT = 200
MIN_LINE_COUNT = 5
SMALL_PDF_SIZE_MB = 0.5


def calculate_document_hash(doc: Document, algorithm: str = "sha256") -> str:
    """
    Calculate cryptographic hash of document for deduplication.

    Args:
        doc: Document to hash
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Hex digest of document hash
    """
    hash_func = getattr(hashlib, algorithm)()
    hash_func.update(doc.bytes)
    hash_func.update(doc.mime.encode("utf-8"))
    return str(hash_func.hexdigest())


def quality_score(ndoc: NormalizedDoc, markdown: str) -> float:
    """
    Calculate quality score for conversion.

    Scoring breakdown:
    - Content length (25%): Longer content scores higher
    - Structure (30%): Headers, tables improve score
    - Text quality (25%): Word count matters
    - Formatting (20%): Line structure, non-empty content

    Args:
        ndoc: Normalized document
        markdown: Rendered markdown

    Returns:
        Quality score between 0.0 and 1.0
    """
    if not markdown or len(markdown.strip()) == 0:
        return 0.0

    score = 0.0

    # Content length scoring (0-25%)
    if len(markdown) > MIN_CONTENT_LENGTH:
        score += 0.1
    if len(markdown) > GOOD_CONTENT_LENGTH:
        score += 0.15

    # Structure scoring (0-30%)
    if "#" in markdown or "##" in markdown:  # Headers
        score += 0.2
    if "|" in markdown and "-" in markdown:  # Tables
        score += 0.1

    # Text quality indicators (0-25%)
    word_count = len(markdown.split())
    if word_count > MIN_WORD_COUNT:
        score += 0.1
    if word_count > GOOD_WORD_COUNT:
        score += 0.15

    # Formatting and structure (0-20%)
    lines = markdown.split("\n")
    if len(lines) > MIN_LINE_COUNT:
        score += 0.1
    if any(line.strip() for line in lines):  # Non-empty lines
        score += 0.1

    return min(score, 1.0)


def hint_has_tables(doc: Document) -> bool:
    """
    Heuristic to guess if document likely contains tables.

    This is a hint for policy selection, not definitive.

    Args:
        doc: Document to analyze

    Returns:
        True if tables are likely present
    """
    # Size-based heuristic: very small PDFs unlikely to have complex tables
    if doc.mime == "application/pdf" and doc.size_mb < SMALL_PDF_SIZE_MB:
        return False

    # Spreadsheets always have tables
    if doc.mime in [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]:
        return True

    # For other formats, check metadata if available
    return bool(doc.metadata.get("has_tables", False))


def build_template_context(
    ndoc: NormalizedDoc, original: Document | None = None
) -> TemplateContext:
    """
    Build template context from normalized document.

    Pure function that transforms domain models into template-ready context.

    Args:
        ndoc: Normalized document
        original: Original document (optional)

    Returns:
        Template context for rendering
    """
    quality = quality_score(ndoc, ndoc.text_content)

    return TemplateContext.from_normalized_doc(
        ndoc=ndoc, original_doc=original, quality_score=quality
    )


def normalize_blocks(blocks: Sequence[Block]) -> tuple[Block, ...]:
    """
    Normalize and clean block sequence.

    Removes empty blocks, deduplicates, and ensures consistent ordering.

    Args:
        blocks: Raw block sequence

    Returns:
        Normalized, immutable block tuple
    """
    # Filter out empty blocks
    valid_blocks = [block for block in blocks if block.content.strip() and block.confidence > 0.0]

    # Sort by page number if available
    valid_blocks.sort(key=lambda b: (b.page_number or 0, b.type.value))

    return tuple(valid_blocks)


def merge_text_blocks(blocks: Sequence[Block]) -> tuple[Block, ...]:
    """
    Merge consecutive text blocks on the same page.

    Reduces fragmentation while preserving structure.

    Args:
        blocks: Block sequence

    Returns:
        Merged block sequence
    """
    if not blocks:
        return ()

    merged: list[Block] = []
    current_text: list[str] = []
    current_page: int | None = None

    for block in blocks:
        if block.type == BlockType.TEXT and block.page_number == current_page:
            # Accumulate text from same page
            current_text.append(block.content)
        else:
            # Flush accumulated text
            if current_text:
                merged_content = "\n\n".join(current_text)
                merged.append(
                    Block(
                        type=BlockType.TEXT,
                        content=merged_content,
                        page_number=current_page,
                    )
                )
                current_text = []

            # Start new accumulation or add non-text block
            if block.type == BlockType.TEXT:
                current_text.append(block.content)
                current_page = block.page_number
            else:
                merged.append(block)
                current_page = block.page_number

    # Flush remaining
    if current_text:
        merged_content = "\n\n".join(current_text)
        merged.append(
            Block(
                type=BlockType.TEXT,
                content=merged_content,
                page_number=current_page,
            )
        )

    return tuple(merged)


def validate_precision_level(level: int, available_levels: Sequence[int]) -> bool:
    """
    Validate precision level is available.

    Args:
        level: Requested precision level
        available_levels: Available levels

    Returns:
        True if level is available
    """
    return level in available_levels


def estimate_processing_time(doc: Document, precision_level: int) -> float:
    """
    Estimate processing time based on document characteristics.

    Pure heuristic function based on size and precision.

    Args:
        doc: Document to process
        precision_level: Precision level

    Returns:
        Estimated time in seconds
    """
    # Base time by precision level
    base_times = {
        1: 0.1,  # Fastest
        2: 0.5,  # Balanced
        3: 1.0,  # Table-optimized
        4: 60.0,  # Highest quality
    }

    # Size factor
    size_factors = {
        1: 0.01,
        2: 0.5,
        3: 0.05,
        4: 30.0,
    }

    base = base_times.get(precision_level, 1.0)
    factor = size_factors.get(precision_level, 0.1)

    return base + (doc.size_mb * factor)
