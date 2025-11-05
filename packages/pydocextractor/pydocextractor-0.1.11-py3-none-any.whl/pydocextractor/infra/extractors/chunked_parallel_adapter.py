"""
ChunkedParallel extractor adapter - Level 1 (Fastest).

Implements the Extractor Protocol using PyMuPDF with parallel processing.
"""

from __future__ import annotations

import io
import multiprocessing
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ...domain import (
    Block,
    BlockType,
    ExtractionResult,
    NormalizedDoc,
    PrecisionLevel,
    RecoverableError,
)
from . import PYMUPDF_AVAILABLE

# Constants for chunk size calculation
SMALL_DOCUMENT_PAGES = 10
MEDIUM_DOCUMENT_PAGES = 50
LARGE_DOCUMENT_PAGES = 200
SMALL_CHUNK_SIZE = 5
MEDIUM_CHUNK_SIZE = 10

if PYMUPDF_AVAILABLE:
    import fitz


class ChunkedParallelExtractor:
    """
    Level 1 extractor using PyMuPDF with parallel chunk processing.

    Optimized for speed with parallel page processing.
    """

    @property
    def name(self) -> str:
        return "ChunkedParallel"

    @property
    def precision_level(self) -> PrecisionLevel:
        return PrecisionLevel.FASTEST

    def is_available(self) -> bool:
        """Check if dependencies are installed."""
        return PYMUPDF_AVAILABLE

    def supports(self, mime: str) -> bool:
        """Check if this extractor supports the MIME type."""
        return mime == "application/pdf" and PYMUPDF_AVAILABLE

    def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
        """
        Extract content from PDF using parallel processing.

        Args:
            data: PDF bytes
            precision: Precision level (informational)

        Returns:
            ExtractionResult with normalized document or error
        """
        if not PYMUPDF_AVAILABLE:
            return ExtractionResult(
                success=False,
                error="PyMuPDF not available - install with: pip install PyMuPDF",
                extractor_name=self.name,
            )

        start_time = time.time()

        try:
            # Open PDF from bytes
            pdf_stream = io.BytesIO(data)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")
            total_pages = doc.page_count

            # Calculate optimal chunk size
            chunk_size = self._calculate_chunk_size(total_pages)

            # Create page chunks
            chunks = []
            for i in range(0, total_pages, chunk_size):
                end_page = min(i + chunk_size, total_pages)
                chunks.append((i, end_page))

            # Process chunks in parallel
            max_workers = min(len(chunks), multiprocessing.cpu_count())
            blocks: list[Block] = []

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_chunk = {
                    executor.submit(self._process_chunk, data, start, end): (start, end)
                    for start, end in chunks
                }

                chunk_results: dict[int, list[Block]] = {}

                for future in as_completed(future_to_chunk):
                    start_page, end_page = future_to_chunk[future]
                    try:
                        chunk_blocks = future.result(timeout=60)
                        chunk_results[start_page] = chunk_blocks
                    except Exception:
                        # Add error block for failed chunk
                        chunk_results[start_page] = [
                            Block(
                                type=BlockType.TEXT,
                                content=f"[Error processing pages {start_page + 1}-{end_page}]",
                                page_number=start_page + 1,
                                confidence=0.0,
                            )
                        ]

            # Combine results in order
            for start_page in sorted(chunk_results.keys()):
                blocks.extend(chunk_results[start_page])

            doc.close()

            # Create normalized document
            ndoc = NormalizedDoc(
                blocks=tuple(blocks),
                source_mime="application/pdf",
                page_count=total_pages,
                has_tables=False,  # Fast mode doesn't detect tables
                extractor_name=self.name,
                metadata={
                    "chunk_count": len(chunks),
                    "chunk_size": chunk_size,
                    "parallel_workers": max_workers,
                },
            )

            processing_time = time.time() - start_time

            return ExtractionResult(
                success=True,
                normalized_doc=ndoc,
                extractor_name=self.name,
                processing_time_seconds=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"ChunkedParallel extraction failed: {e}"

            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                raise RecoverableError(error_msg) from e

            return ExtractionResult(
                success=False,
                error=error_msg,
                extractor_name=self.name,
                processing_time_seconds=processing_time,
            )

    def _calculate_chunk_size(self, total_pages: int) -> int:
        """Calculate optimal chunk size based on document size."""
        if total_pages <= SMALL_DOCUMENT_PAGES:
            return total_pages
        elif total_pages <= MEDIUM_DOCUMENT_PAGES:
            return SMALL_CHUNK_SIZE
        elif total_pages <= LARGE_DOCUMENT_PAGES:
            return MEDIUM_CHUNK_SIZE
        else:
            return 20

    def _process_chunk(self, data: bytes, start_page: int, end_page: int) -> list[Block]:
        """
        Process a chunk of pages from the PDF.

        Args:
            data: PDF bytes
            start_page: Starting page index (0-based)
            end_page: Ending page index (exclusive)

        Returns:
            List of blocks for this chunk
        """
        blocks: list[Block] = []

        # Open document in worker thread
        pdf_stream = io.BytesIO(data)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")

        try:
            for page_num in range(start_page, end_page):
                if page_num < doc.page_count:
                    page = doc[page_num]
                    text = page.get_text()

                    if text.strip():
                        blocks.append(
                            Block(
                                type=BlockType.TEXT,
                                content=text.strip(),
                                page_number=page_num + 1,
                            )
                        )
        finally:
            doc.close()

        return blocks
