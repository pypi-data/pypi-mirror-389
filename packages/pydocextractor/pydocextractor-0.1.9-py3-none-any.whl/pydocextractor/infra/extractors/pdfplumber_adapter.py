"""
PDFPlumber extractor adapter - Level 3 (Table-Optimized).

Implements the Extractor Protocol using pdfplumber library.
"""

from __future__ import annotations

import io
import time

from ...domain import (
    Block,
    BlockType,
    ExtractionResult,
    NormalizedDoc,
    PrecisionLevel,
    RecoverableError,
)
from . import PDFPLUMBER_AVAILABLE

if PDFPLUMBER_AVAILABLE:
    import pdfplumber

# Constants for table validation
MIN_TABLE_ROWS = 2  # Need at least header and one data row


class PDFPlumberExtractor:
    """
    Level 3 extractor using PDFPlumber.

    Optimized for table extraction and structured data.
    """

    def __init__(self, enable_image_extraction: bool = False) -> None:
        """
        Initialize extractor.

        Args:
            enable_image_extraction: If True, extract raw images for LLM description
        """
        self.enable_image_extraction = enable_image_extraction

    @property
    def name(self) -> str:
        return "PDFPlumber"

    @property
    def precision_level(self) -> PrecisionLevel:
        return PrecisionLevel.TABLE_OPTIMIZED

    def is_available(self) -> bool:
        """Check if dependencies are installed."""
        return PDFPLUMBER_AVAILABLE

    def supports(self, mime: str) -> bool:
        """Check if this extractor supports the MIME type."""
        return mime == "application/pdf" and PDFPLUMBER_AVAILABLE

    def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
        """
        Extract content from PDF with table optimization.

        Args:
            data: PDF bytes
            precision: Precision level (informational)

        Returns:
            ExtractionResult with normalized document or error
        """
        if not PDFPLUMBER_AVAILABLE:
            return ExtractionResult(
                success=False,
                error="pdfplumber not available - install with: pip install pdfplumber",
                extractor_name=self.name,
            )

        start_time = time.time()

        try:
            # Open PDF from bytes
            pdf_stream = io.BytesIO(data)
            blocks: list[Block] = []
            table_count = 0
            page_count = 0
            image_count = 0

            # Extract images if LLM is enabled (write to temp file for image extraction)
            image_data_by_page = None
            if self.enable_image_extraction:
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name
                try:
                    image_data_by_page = self._extract_images_from_file(tmp_path)
                finally:
                    import os

                    os.unlink(tmp_path)

            with pdfplumber.open(pdf_stream) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_count += 1

                    # Find table regions first
                    table_regions = page.find_tables()

                    # Extract text excluding table regions
                    if table_regions:
                        # Get bounding boxes of all tables
                        table_bboxes = [table.bbox for table in table_regions]

                        # Filter page to exclude table regions
                        filtered_page = page
                        for bbox in table_bboxes:
                            # outside_bbox returns a cropped page excluding the given bbox
                            filtered_page = filtered_page.outside_bbox(bbox)

                        text = filtered_page.extract_text()
                    else:
                        # No tables, extract all text normally
                        text = page.extract_text()

                    if text and text.strip():
                        blocks.append(
                            Block(
                                type=BlockType.TEXT,
                                content=text.strip(),
                                page_number=page_num + 1,
                            )
                        )

                    # Extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            # Convert None values to empty strings
                            clean_table = [[cell or "" for cell in row] for row in table]
                            table_md = self._table_to_markdown(clean_table)
                            if table_md:
                                blocks.append(
                                    Block(
                                        type=BlockType.TABLE,
                                        content=table_md,
                                        page_number=page_num + 1,
                                        metadata={"table_index": table_count},
                                    )
                                )
                                table_count += 1

                    # Extract images if available
                    if image_data_by_page:
                        page_images = image_data_by_page.get(page_num + 1, [])
                        for img_data in page_images:
                            blocks.append(
                                Block(
                                    type=BlockType.IMAGE,
                                    content="",
                                    page_number=page_num + 1,
                                    image_data=img_data,
                                )
                            )
                            image_count += 1

            # Create normalized document
            ndoc = NormalizedDoc(
                blocks=tuple(blocks),
                source_mime="application/pdf",
                page_count=page_count,
                has_tables=table_count > 0,
                has_images=image_count > 0,
                extractor_name=self.name,
                metadata={
                    "table_count": table_count,
                    "image_count": image_count,
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
            error_msg = f"PDFPlumber extraction failed: {e}"

            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                raise RecoverableError(error_msg) from e

            return ExtractionResult(
                success=False,
                error=error_msg,
                extractor_name=self.name,
                processing_time_seconds=processing_time,
            )

    def _table_to_markdown(self, table: list[list[str]]) -> str:
        """
        Convert table to well-formatted markdown.

        Args:
            table: Table data as list of lists

        Returns:
            Markdown table representation
        """
        if not table or not any(table):
            return ""

        # Filter out None values and convert to strings
        clean_table: list[list[str]] = []
        for row in table:
            if row:
                clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
                if any(clean_row):
                    clean_table.append(clean_row)

        if len(clean_table) < MIN_TABLE_ROWS:  # Need at least header + one data row
            return ""

        try:
            # Ensure consistent column count
            max_cols = max(len(row) for row in clean_table)
            for row in clean_table:
                while len(row) < max_cols:
                    row.append("")

            # Create markdown table
            md_lines = []

            # Header row
            header_row = clean_table[0]
            md_lines.append("| " + " | ".join(header_row) + " |")

            # Separator row
            md_lines.append("| " + " | ".join(["---"] * len(header_row)) + " |")

            # Data rows
            for row in clean_table[1:]:
                md_lines.append("| " + " | ".join(row) + " |")

            return "\n".join(md_lines)

        except Exception:
            return ""

    def _extract_images_from_file(self, file_path: str) -> dict[int, list[bytes]]:
        """
        Extract raw images from PDF file using PyMuPDF.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary mapping page numbers to lists of image bytes
        """
        import logging

        logger = logging.getLogger(__name__)
        images: dict[int, list[bytes]] = {}

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_images = []

                # Get images from page
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    try:
                        base_image = doc.extract_image(xref)
                        page_images.append(base_image["image"])
                    except Exception as e:
                        logger.debug(
                            f"Could not extract image {img_index} from page {page_num}: {e}"
                        )

                if page_images:
                    images[page_num + 1] = page_images  # 1-indexed pages

            doc.close()
            if images:
                total_images = sum(len(imgs) for imgs in images.values())
                logger.info(f"Extracted {total_images} image(s) from PDF")

        except ImportError:
            logger.debug("PyMuPDF not available for image extraction")
        except Exception as e:
            logger.warning(f"Image extraction failed: {e}")

        return images
