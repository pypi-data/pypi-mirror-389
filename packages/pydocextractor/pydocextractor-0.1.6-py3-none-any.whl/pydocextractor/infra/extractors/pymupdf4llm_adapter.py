"""
PyMuPDF4LLM extractor adapter - Level 2 (Balanced, Default).

Implements the Extractor Protocol using pymupdf4llm library.
"""

from __future__ import annotations

import time
from typing import Any

from ...domain import (
    Block,
    BlockType,
    ExtractionResult,
    NormalizedDoc,
    PrecisionLevel,
    RecoverableError,
)
from . import PYMUPDF4LLM_AVAILABLE

if PYMUPDF4LLM_AVAILABLE:
    import pymupdf4llm


class PyMuPDF4LLMExtractor:
    """
    Level 2 extractor using PyMuPDF4LLM.

    Provides balanced speed/quality, optimized for LLM consumption.
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
        return "PyMuPDF4LLM"

    @property
    def precision_level(self) -> PrecisionLevel:
        return PrecisionLevel.BALANCED

    def is_available(self) -> bool:
        """Check if dependencies are installed."""
        return PYMUPDF4LLM_AVAILABLE

    def supports(self, mime: str) -> bool:
        """Check if this extractor supports the MIME type."""
        return mime == "application/pdf" and PYMUPDF4LLM_AVAILABLE

    def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
        """
        Extract content from PDF using PyMuPDF4LLM.

        Args:
            data: PDF bytes
            precision: Precision level (informational, this extractor is Level 2)

        Returns:
            ExtractionResult with normalized document or error
        """
        if not PYMUPDF4LLM_AVAILABLE:
            return ExtractionResult(
                success=False,
                error="pymupdf4llm not available - install with: pip install pymupdf4llm",
                extractor_name=self.name,
            )

        start_time = time.time()

        try:
            # pymupdf4llm requires a file path, not BytesIO
            # Write to temporary file
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                # Convert to markdown using pymupdf4llm with page chunks
                page_chunks = pymupdf4llm.to_markdown(tmp_path, page_chunks=True)

                # Extract raw images if LLM is enabled
                image_data_by_page = None
                if self.enable_image_extraction:
                    image_data_by_page = self._extract_images_from_file(tmp_path)
            finally:
                # Clean up temp file
                import os

                os.unlink(tmp_path)

            # Parse page chunks into blocks (with images if extracted)
            blocks = self._parse_page_chunks_to_blocks(page_chunks, image_data_by_page)

            # Reconstruct markdown for metadata
            markdown_text = "\n\n".join(chunk["text"] for chunk in page_chunks)

            # Count images from blocks
            image_count = sum(1 for b in blocks if b.type == BlockType.IMAGE)

            # Create normalized document
            ndoc = NormalizedDoc(
                blocks=tuple(blocks),
                source_mime="application/pdf",
                has_tables="|" in markdown_text and "-" in markdown_text,
                has_images=image_count > 0,
                extractor_name=self.name,
                metadata={
                    "raw_markdown_length": len(markdown_text),
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
            error_msg = f"PyMuPDF4LLM extraction failed: {e}"

            # Determine if error is recoverable
            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                raise RecoverableError(error_msg) from e

            return ExtractionResult(
                success=False,
                error=error_msg,
                extractor_name=self.name,
                processing_time_seconds=processing_time,
            )

    def _parse_page_chunks_to_blocks(
        self,
        page_chunks: list[dict[str, Any]],
        image_data_by_page: dict[int, list[bytes]] | None = None,
    ) -> list[Block]:
        """
        Parse page chunks from PyMuPDF4LLM into structured blocks.

        Args:
            page_chunks: List of page chunks with 'text' and 'metadata' keys
            image_data_by_page: Optional dict mapping page numbers to image bytes

        Returns:
            List of Block objects
        """
        all_blocks: list[Block] = []
        global_image_index = 0

        for chunk in page_chunks:
            text = chunk["text"]
            page_number = chunk["metadata"]["page"]

            # Parse this chunk's text into blocks
            chunk_blocks = self._parse_markdown_to_blocks(text, image_data_by_page)

            # Update page numbers and track images
            for block in chunk_blocks:
                # Update block's page number
                updated_block = Block(
                    type=block.type,
                    content=block.content,
                    page_number=page_number,
                    metadata=block.metadata,
                    confidence=block.confidence,
                    image_data=None,  # Will update for images
                )

                # If this is an image block, get image data from correct page
                if block.type == BlockType.IMAGE:
                    if image_data_by_page:
                        page_images = image_data_by_page.get(page_number, [])
                        # Use global index modulo page images to handle multiple images
                        if page_images:
                            img_idx = global_image_index % len(page_images)
                            updated_block = Block(
                                type=block.type,
                                content=block.content,
                                page_number=page_number,
                                metadata=block.metadata,
                                confidence=block.confidence,
                                image_data=page_images[img_idx],
                            )
                        global_image_index += 1

                all_blocks.append(updated_block)

        return all_blocks

    def _parse_markdown_to_blocks(
        self, markdown: str, image_data_by_page: dict[int, list[bytes]] | None = None
    ) -> list[Block]:
        """
        Parse markdown text into structured blocks.

        Args:
            markdown: Raw markdown from pymupdf4llm
            image_data_by_page: Optional dict mapping page numbers to image bytes

        Returns:
            List of Block objects
        """
        blocks: list[Block] = []
        current_page = 1

        # Split by common page markers
        lines = markdown.split("\n")
        current_text: list[str] = []
        in_table = False
        table_lines: list[str] = []
        image_index_by_page: dict[int, int] = {}  # Track image index per page

        for line in lines:
            # Detect page breaks (pymupdf4llm includes page markers)
            if line.strip().startswith("-----"):
                # Flush current text block
                if current_text:
                    content = "\n".join(current_text).strip()
                    if content:
                        blocks.append(
                            Block(
                                type=BlockType.TEXT,
                                content=content,
                                page_number=current_page,
                            )
                        )
                    current_text = []

                # Insert any images from this page at page break
                if image_data_by_page:
                    page_images = image_data_by_page.get(current_page, [])
                    for _img_data in page_images:
                        blocks.append(
                            Block(
                                type=BlockType.IMAGE,
                                content="",
                                page_number=current_page,
                                image_data=_img_data,
                            )
                        )

                current_page += 1
                continue

            # Detect tables (markdown table syntax)
            if "|" in line and (line.strip().startswith("|") or "---" in line or in_table):
                # Flush current text if starting a table
                if not in_table and current_text:
                    content = "\n".join(current_text).strip()
                    if content:
                        blocks.append(
                            Block(
                                type=BlockType.TEXT,
                                content=content,
                                page_number=current_page,
                            )
                        )
                    current_text = []

                # Collect table lines
                in_table = True
                table_lines.append(line)
                continue
            elif in_table:
                # End of table - flush collected table
                if table_lines:
                    blocks.append(
                        Block(
                            type=BlockType.TABLE,
                            content="\n".join(table_lines),
                            page_number=current_page,
                        )
                    )
                table_lines = []
                in_table = False
                # Don't continue - process this line normally

            # Detect headers
            if line.strip().startswith("#"):
                # Flush current text
                if current_text:
                    content = "\n".join(current_text).strip()
                    if content:
                        blocks.append(
                            Block(
                                type=BlockType.TEXT,
                                content=content,
                                page_number=current_page,
                            )
                        )
                    current_text = []

                blocks.append(
                    Block(
                        type=BlockType.HEADER,
                        content=line.strip(),
                        page_number=current_page,
                    )
                )
                continue

            # Detect images (markdown syntax)
            if line.strip().startswith("!["):
                # Flush current text
                if current_text:
                    content = "\n".join(current_text).strip()
                    if content:
                        blocks.append(
                            Block(
                                type=BlockType.TEXT,
                                content=content,
                                page_number=current_page,
                            )
                        )
                    current_text = []

                # Get image data if available
                if image_data_by_page:
                    page_images = image_data_by_page.get(current_page, [])
                    img_idx = image_index_by_page.get(current_page, 0)

                    if img_idx < len(page_images):
                        current_img_data = page_images[img_idx]
                        blocks.append(
                            Block(
                                type=BlockType.IMAGE,
                                content="<!-- image -->",
                                page_number=current_page,
                                image_data=current_img_data,
                            )
                        )
                    image_index_by_page[current_page] = img_idx + 1

                blocks.append(
                    Block(
                        type=BlockType.IMAGE,
                        content=line.strip(),
                        page_number=current_page,
                        image_data=_img_data,
                    )
                )
                continue

            # Accumulate regular text
            current_text.append(line)

        # Flush remaining table if any
        if table_lines:
            blocks.append(
                Block(
                    type=BlockType.TABLE,
                    content="\n".join(table_lines),
                    page_number=current_page,
                )
            )

        # Flush remaining text
        if current_text:
            content = "\n".join(current_text).strip()
            if content:
                blocks.append(
                    Block(
                        type=BlockType.TEXT,
                        content=content,
                        page_number=current_page,
                    )
                )

        # Insert any images from the last page
        if image_data_by_page:
            page_images = image_data_by_page.get(current_page, [])
            for _img_data in page_images:
                blocks.append(
                    Block(
                        type=BlockType.IMAGE,
                        content="",
                        page_number=current_page,
                        image_data=_img_data,
                    )
                )

        return blocks

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
