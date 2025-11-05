"""
Docling extractor adapter - Level 4 (Highest Quality).

Implements the Extractor Protocol using Docling library.
"""

from __future__ import annotations

import tempfile
import time
import warnings
from pathlib import Path
from typing import Any

from ...domain import (
    Block,
    BlockType,
    ExtractionResult,
    NormalizedDoc,
    PrecisionLevel,
    RecoverableError,
)
from . import DOCLING_AVAILABLE

if DOCLING_AVAILABLE:
    from docling.document_converter import DocumentConverter as DoclingDocConverter


class DoclingExtractor:
    """
    Level 4 extractor using Docling.

    Provides highest quality with comprehensive layout analysis.
    Supports multiple formats: PDF, DOCX, XLSX, XLS.
    """

    def __init__(self) -> None:
        self._converter: DoclingDocConverter | None = None

    @property
    def name(self) -> str:
        return "Docling"

    @property
    def precision_level(self) -> PrecisionLevel:
        return PrecisionLevel.HIGHEST_QUALITY

    def is_available(self) -> bool:
        """Check if dependencies are installed."""
        return DOCLING_AVAILABLE

    def supports(self, mime: str) -> bool:
        """Check if this extractor supports the MIME type."""
        supported = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # XLSX
            "application/vnd.ms-excel",  # XLS
            # Note: CSV is handled by PandasCSVExtractor for better statistics
        ]
        return mime in supported and DOCLING_AVAILABLE

    def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
        """
        Extract content using Docling for maximum quality.

        Args:
            data: Document bytes
            precision: Precision level (informational)

        Returns:
            ExtractionResult with normalized document or error
        """
        if not DOCLING_AVAILABLE:
            return ExtractionResult(
                success=False,
                error="Docling not available - install with: pip install docling",
                extractor_name=self.name,
            )

        start_time = time.time()

        try:
            # Initialize Docling converter if not already done
            if self._converter is None:
                self._converter = DoclingDocConverter()

            # Docling requires a file path, so write to temporary file
            # Detect proper extension based on data (for image extraction)
            suffix = ".pdf"  # default
            # Check magic bytes for file type
            if data[:4] == b"PK\x03\x04":  # ZIP-based Office format
                # Check for Office Open XML markers
                if b"[Content_Types].xml" in data[:200]:
                    # It's an Office file, determine which type
                    if b"word/" in data[:5000]:
                        suffix = ".docx"
                    elif b"xl/" in data[:5000]:
                        suffix = ".xlsx"
            elif data[:4] == b"%PDF":
                suffix = ".pdf"

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(data)
                temp_path = temp_file.name

            try:
                # Perform conversion
                # Suppress known Docling numpy warnings (GitHub issue #1648)
                # These warnings occur when Docling calculates statistics on empty page regions
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message="Mean of empty slice")
                    warnings.filterwarnings(
                        "ignore", message="invalid value encountered in scalar divide"
                    )
                    result: Any = self._converter.convert(temp_path)
                    markdown_content = result.document.export_to_markdown()

                # Extract raw images from document (for LLM description)
                image_data_by_page = self._extract_images_from_file(temp_path)

                # Extract image page mapping from Docling's structured API
                image_page_mapping = self._extract_image_page_mapping(result.document)

                # Parse markdown into blocks
                blocks = self._parse_markdown_to_blocks(
                    markdown_content, image_data_by_page, image_page_mapping
                )

                # Extract metadata from Docling result
                page_count = None
                table_count = 0
                image_count = 0

                try:
                    if hasattr(result.document, "pages") and result.document.pages:
                        pages_len = len(result.document.pages)
                        page_count = pages_len if pages_len > 0 else None
                    if hasattr(result.document, "tables"):
                        table_count = len(
                            [t for page in result.document.pages for t in page.tables]
                        )
                    if hasattr(result.document, "figures"):
                        image_count = len(
                            [f for page in result.document.pages for f in page.figures]
                        )
                except Exception:
                    pass

                # Detect tables from blocks if metadata doesn't have them
                if table_count == 0:
                    table_count = sum(1 for b in blocks if b.type == BlockType.TABLE)

                # Detect images from blocks if metadata doesn't have them
                if image_count == 0:
                    image_count = sum(1 for b in blocks if b.type == BlockType.IMAGE)

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
                        "docling_version": getattr(result, "version", "unknown"),
                    },
                )

                processing_time = time.time() - start_time

                return ExtractionResult(
                    success=True,
                    normalized_doc=ndoc,
                    extractor_name=self.name,
                    processing_time_seconds=processing_time,
                )

            finally:
                # Clean up temporary file
                Path(temp_path).unlink(missing_ok=True)

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Docling extraction failed: {e}"

            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                raise RecoverableError(error_msg) from e

            return ExtractionResult(
                success=False,
                error=error_msg,
                extractor_name=self.name,
                processing_time_seconds=processing_time,
            )

    def _parse_markdown_to_blocks(
        self,
        markdown: str,
        image_data_by_page: dict[int, list[bytes]] | None = None,
        image_page_mapping: list[int] | None = None,
    ) -> list[Block]:
        """
        Parse Docling markdown into structured blocks.

        Args:
            markdown: Markdown from Docling
            image_data_by_page: Dictionary mapping page numbers to image bytes
            image_page_mapping: List mapping image index to page number

        Returns:
            List of Block objects
        """
        blocks: list[Block] = []
        lines = markdown.split("\n")
        current_page = 1
        current_text: list[str] = []
        in_table = False
        table_lines: list[str] = []
        image_index_by_page: dict[int, int] = {}  # Track image index per page
        global_image_index = 0  # Track global image index for page mapping

        for line in lines:
            # Detect headers
            if line.strip().startswith("#"):
                # Flush table if in one
                if in_table and table_lines:
                    blocks.append(
                        Block(
                            type=BlockType.TABLE,
                            content="\n".join(table_lines),
                            page_number=current_page,
                        )
                    )
                    table_lines = []
                    in_table = False

                # Flush current text
                if current_text:
                    content = "\n".join(current_text).strip()
                    if content:
                        blocks.append(
                            Block(
                                type=BlockType.HEADER,
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

            # Detect tables (markdown table syntax)
            if "|" in line and line.strip().startswith("|"):
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

            # Detect images (markdown syntax or HTML comment)
            if line.strip().startswith("![") or line.strip() == "<!-- image -->":
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

                # Determine page number for this image
                image_page = current_page
                if image_page_mapping and global_image_index < len(image_page_mapping):
                    image_page = image_page_mapping[global_image_index]

                # Get image data if available
                img_data = None
                if image_data_by_page:
                    page_images = image_data_by_page.get(image_page, [])
                    img_idx = image_index_by_page.get(image_page, 0)

                    if img_idx < len(page_images):
                        img_data = page_images[img_idx]
                    image_index_by_page[image_page] = img_idx + 1

                blocks.append(
                    Block(
                        type=BlockType.IMAGE,
                        content="",
                        page_number=image_page,
                        image_data=img_data,
                    )
                )
                global_image_index += 1
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

        return blocks

    def _extract_images_from_file(self, file_path: str) -> dict[int, list[bytes]]:
        """
        Extract raw images from document file.

        Args:
            file_path: Path to document file (PDF or DOCX)

        Returns:
            Dictionary mapping page numbers to lists of image bytes
        """
        import logging

        logger = logging.getLogger(__name__)
        images: dict[int, list[bytes]] = {}

        # Determine file type from extension
        file_lower = file_path.lower()
        is_pdf = file_lower.endswith(".pdf")
        is_docx = file_lower.endswith(".docx") or file_lower.endswith(".doc")

        try:
            # Try DOCX extraction first for Word documents
            if is_docx:
                try:
                    import docx

                    doc = docx.Document(file_path)
                    doc_images = []

                    # Extract images from document relationships
                    for rel in doc.part.rels.values():
                        if "image" in rel.target_ref:
                            try:
                                doc_images.append(rel.target_part.blob)
                                logger.debug(f"Extracted image from DOCX: {rel.target_ref}")
                            except Exception as e:
                                logger.debug(f"Could not extract image from DOCX: {e}")

                    # Map all images to page 1 (DOCX doesn't have page concept in API)
                    if doc_images:
                        images[1] = doc_images
                        logger.info(f"Extracted {len(doc_images)} image(s) from DOCX")
                        return images

                except ImportError:
                    logger.debug("python-docx not available for image extraction")
                except Exception as e:
                    logger.debug(f"DOCX image extraction failed: {e}")

            # Try PDF extraction for PDF documents
            if is_pdf or not images:
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
                    logger.debug(f"PDF image extraction failed: {e}")

        except Exception as e:
            logger.warning(f"Image extraction failed: {e}")

        return images

    def _extract_image_page_mapping(self, document: Any) -> list[int]:
        """
        Extract page numbers for each image from Docling's document structure.

        Args:
            document: Docling Document object

        Returns:
            List mapping image index to page number (1-indexed)
        """
        import logging

        logger = logging.getLogger(__name__)
        page_mapping: list[int] = []

        try:
            # Iterate through document items to find pictures
            for item, _level in document.iterate_items(with_groups=False):
                # Check if this is a picture item
                if hasattr(item, "label") and "picture" in str(item.label).lower():
                    # Extract page number from provenance
                    if hasattr(item, "prov") and item.prov:
                        page_no = item.prov[0].page_no
                        page_mapping.append(page_no)
                        logger.debug(f"Image at index {len(page_mapping) - 1} is on page {page_no}")

            logger.info(f"Extracted page mapping for {len(page_mapping)} image(s)")

        except Exception as e:
            logger.warning(f"Failed to extract image page mapping: {e}")

        return page_mapping
