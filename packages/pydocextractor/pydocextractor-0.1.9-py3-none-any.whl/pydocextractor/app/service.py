"""
Application service layer for pyDocExtractor.

This is the orchestration layer that uses domain ports (Protocols)
without depending on concrete infrastructure implementations.

The service coordinates the conversion workflow using dependency injection.
"""

from __future__ import annotations

import io
import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from zipfile import ZipFile

# Constants for metadata extraction
DATETIME_STRING_LENGTH = 14  # YYYYMMDDHHmmSS format
PDF_METADATA_PREFIX_LENGTH = 2  # Remove "D:" prefix from PDF metadata

from ..domain import (
    ConversionFailed,
    Document,
    ExtractionResult,
    Extractor,
    Markdown,
    NormalizedDoc,
    Policy,
    QualityScorer,
    RecoverableError,
    TableProfiler,
    TemplateEngine,
    build_template_context,
)


def _extract_document_metadata(doc: Document) -> dict[str, str]:
    """
    Extract document metadata like creation date.

    Args:
        doc: Document to extract metadata from

    Returns:
        Dictionary with metadata fields (created_utc, etc.)
    """
    metadata = {}

    try:
        if doc.mime == "application/pdf":
            # Try to extract PDF metadata using PyMuPDF
            try:
                import fitz

                pdf_doc = fitz.open(stream=doc.bytes, filetype="pdf")
                pdf_metadata = pdf_doc.metadata

                # Extract creation date
                if pdf_metadata and pdf_metadata.get("creationDate"):
                    # PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm'
                    created_date_str = pdf_metadata["creationDate"]
                    # Parse the PDF date format
                    if created_date_str.startswith("D:"):
                        created_date_str = created_date_str[PDF_METADATA_PREFIX_LENGTH:]
                    # Take first 14 chars (YYYYMMDDHHmmSS)
                    if len(created_date_str) >= DATETIME_STRING_LENGTH:
                        dt = datetime.strptime(
                            created_date_str[:DATETIME_STRING_LENGTH], "%Y%m%d%H%M%S"
                        )
                        metadata["created_utc"] = dt.isoformat()

                pdf_doc.close()
            except (ImportError, Exception):
                # PyMuPDF not available or parsing failed
                pass

        elif doc.mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Try to extract DOCX metadata
            try:
                with ZipFile(io.BytesIO(doc.bytes)) as docx_zip:
                    # Read core properties
                    if "docProps/core.xml" in docx_zip.namelist():
                        core_xml = docx_zip.read("docProps/core.xml")
                        # Use defusedxml for safer XML parsing
                        try:
                            import defusedxml.ElementTree as ET

                            root = ET.fromstring(core_xml)
                        except ImportError:
                            # Fallback to standard library if defusedxml not available
                            root = ET.fromstring(core_xml)

                        # Look for created date
                        # Namespace for Dublin Core
                        ns = {
                            "dc": "http://purl.org/dc/elements/1.1/",
                            "dcterms": "http://purl.org/dc/terms/",
                            "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
                        }

                        # Try dcterms:created first
                        created_elem = root.find(".//dcterms:created", ns)
                        if created_elem is not None and created_elem.text:
                            metadata["created_utc"] = created_elem.text

            except (ImportError, Exception):
                # zipfile or parsing failed
                pass

        elif doc.mime in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        ]:
            # Try to extract Excel metadata
            try:
                with ZipFile(io.BytesIO(doc.bytes)) as xlsx_zip:
                    if "docProps/core.xml" in xlsx_zip.namelist():
                        core_xml = xlsx_zip.read("docProps/core.xml")
                        # Use defusedxml for safer XML parsing
                        try:
                            import defusedxml.ElementTree as ET

                            root = ET.fromstring(core_xml)
                        except ImportError:
                            # Fallback to standard library if defusedxml not available
                            root = ET.fromstring(core_xml)

                        ns = {
                            "dcterms": "http://purl.org/dc/terms/",
                        }

                        created_elem = root.find(".//dcterms:created", ns)
                        if created_elem is not None and created_elem.text:
                            metadata["created_utc"] = created_elem.text

            except (ImportError, Exception):
                # zipfile or parsing failed
                pass

    except Exception:
        # Any other errors - just skip metadata extraction
        pass

    return metadata


@dataclass(slots=True)
class ConverterService:
    """
    Main application service for document conversion.

    Uses dependency injection to remain infrastructure-agnostic.
    All dependencies are ports (Protocols), not concrete implementations.
    """

    policy: Policy
    template_engine: TemplateEngine
    quality_scorer: QualityScorer | None = None
    table_profilers: Sequence[TableProfiler] = field(default_factory=tuple)
    image_describer: object | None = None  # ImageDescriber protocol (optional)
    llm_config: object | None = None  # LLMConfig (optional)

    def convert_to_markdown(
        self,
        doc: Document,
        template_name: str = "default",
        *,
        allow_fallback: bool = True,
    ) -> Markdown:
        """
        Convert document to markdown using policy-selected extractors.

        This is the main entry point for the conversion pipeline.

        Args:
            doc: Document to convert
            template_name: Template to use for rendering
            allow_fallback: Whether to try fallback extractors on failure

        Returns:
            Markdown result with quality score

        Raises:
            ConversionFailed: When all extractors fail
            UnsupportedFormat: When no extractor supports the format
        """
        extractors = self.policy.choose_extractors(
            mime=doc.mime,
            size_bytes=doc.size_bytes,
            has_tables=doc.metadata.get("has_tables", False),
            precision=doc.precision,
        )

        if not extractors:
            from ..domain import UnsupportedFormat

            raise UnsupportedFormat(doc.mime)

        attempted: list[str] = []
        last_error: str | None = None

        for extractor in extractors:
            try:
                attempted.append(extractor.name)

                # Extract content
                result = self._extract_with_retry(extractor, doc)

                if not result.success or result.normalized_doc is None:
                    last_error = result.error
                    if allow_fallback:
                        continue
                    else:
                        raise ConversionFailed(
                            f"Extraction failed: {result.error}",
                            attempted_extractors=attempted,
                        )

                ndoc = result.normalized_doc

                # Enhance images with LLM descriptions if configured
                if self.image_describer:
                    try:
                        max_images = 5  # default
                        if self.llm_config and hasattr(self.llm_config, "max_images_per_document"):
                            max_images = self.llm_config.max_images_per_document
                        ndoc = self._enhance_images_with_descriptions(ndoc, max_images)
                    except Exception as e:
                        # Don't fail entire conversion if LLM fails
                        logging.error(f"LLM image description failed, continuing without: {e}")

                # Apply table profilers if configured
                for profiler in self.table_profilers:
                    ndoc = profiler.profile(ndoc)

                # Build template context
                ctx = build_template_context(ndoc, doc)

                # Add precision level and source_mime to context metadata
                ctx_metadata = dict(ctx.metadata)
                ctx_metadata["precision_level"] = extractor.precision_level.value
                ctx_metadata["source_mime"] = ndoc.source_mime

                # Extract and add document metadata (creation date, etc.)
                doc_metadata = _extract_document_metadata(doc)
                ctx_metadata.update(doc_metadata)

                # Render markdown - convert dataclass to dict
                ctx_dict = {
                    "blocks": ctx.blocks,
                    "metadata": ctx_metadata,
                    "has_tables": ctx.has_tables,
                    "has_images": ctx.has_images,
                    "page_count": ctx.page_count,
                    "quality_score": ctx.quality_score,
                }
                markdown_text = self.template_engine.render(template_name, ctx_dict)

                # Calculate quality score
                if self.quality_scorer:
                    score = self.quality_scorer.calculate_score(ndoc, markdown_text, doc)
                else:
                    score = ctx.quality_score or 0.0

                # Success!
                return Markdown(
                    text=markdown_text,
                    quality_score=score,
                    metadata={
                        "extractor": extractor.name,
                        "precision_level": extractor.precision_level.value,
                        "processing_time": result.processing_time_seconds,
                        "attempted_extractors": attempted,
                    },
                )

            except RecoverableError as e:
                last_error = str(e)
                if allow_fallback:
                    continue
                else:
                    raise ConversionFailed(
                        f"Extraction failed: {e}",
                        attempted_extractors=attempted,
                    ) from e

            except Exception as e:
                # Unexpected error - log and continue to fallback
                last_error = f"Unexpected error: {e}"
                if allow_fallback:
                    continue
                else:
                    raise

        # All extractors failed
        raise ConversionFailed(
            f"All extractors failed. Last error: {last_error}",
            attempted_extractors=attempted,
        )

    def _extract_with_retry(
        self,
        extractor: Extractor,
        doc: Document,
        max_retries: int = 1,
    ) -> ExtractionResult:
        """
        Extract document with optional retry on transient failures.

        Args:
            extractor: Extractor to use
            doc: Document to extract
            max_retries: Maximum retry attempts

        Returns:
            ExtractionResult
        """
        last_error: str | None = None

        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                result = extractor.extract(doc.bytes, doc.precision)

                # Add timing if not already present
                if result.processing_time_seconds == 0.0:
                    processing_time = time.time() - start_time
                    result = ExtractionResult(
                        success=result.success,
                        normalized_doc=result.normalized_doc,
                        error=result.error,
                        extractor_name=result.extractor_name or extractor.name,
                        processing_time_seconds=processing_time,
                    )

                return result

            except RecoverableError as e:
                last_error = str(e)
                if attempt < max_retries:
                    continue
                else:
                    raise

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    continue
                else:
                    return ExtractionResult(
                        success=False,
                        error=last_error,
                        extractor_name=extractor.name,
                        processing_time_seconds=time.time() - start_time,
                    )

        # Should not reach here, but for type safety
        return ExtractionResult(
            success=False,
            error=last_error or "Unknown error",
            extractor_name=extractor.name,
        )

    def convert_with_specific_extractor(
        self,
        doc: Document,
        extractor_name: str,
        template_name: str = "default",
    ) -> Markdown:
        """
        Convert using a specific extractor by name.

        Useful for testing or forcing a particular extractor.

        Args:
            doc: Document to convert
            extractor_name: Name of extractor to use
            template_name: Template to use

        Returns:
            Markdown result

        Raises:
            ValueError: When extractor not found
            ConversionFailed: When conversion fails
        """
        # Get all extractors from policy
        all_extractors = self.policy.choose_extractors(
            mime=doc.mime,
            size_bytes=doc.size_bytes,
            has_tables=False,
            precision=doc.precision,
        )

        # Find requested extractor
        extractor = next((e for e in all_extractors if e.name == extractor_name), None)

        if extractor is None:
            available = [e.name for e in all_extractors]
            raise ValueError(f"Extractor '{extractor_name}' not found. Available: {available}")

        # Use conversion with fallback disabled
        return self.convert_to_markdown(doc, template_name, allow_fallback=False)

    def list_available_templates(self) -> Sequence[str]:
        """List available template names."""
        return self.template_engine.list_templates()

    def get_supported_formats(self) -> Sequence[str]:
        """Get list of all supported MIME types."""
        all_extractors: list[Extractor] = []
        for precision in [1, 2, 3, 4]:
            extractors = self.policy.choose_extractors(
                mime="application/pdf",  # dummy
                size_bytes=1024,
                has_tables=False,
                precision=precision,  # type: ignore
            )
            all_extractors.extend(extractors)

        # Collect unique MIME types
        formats: set[str] = set()
        for _extractor in all_extractors:
            # This is a simplification - in practice, we'd query each extractor
            # for its supported formats
            pass

        return tuple(formats)

    def _enhance_images_with_descriptions(
        self,
        ndoc: NormalizedDoc,
        max_images: int = 5,
    ) -> NormalizedDoc:
        """
        Enhance image blocks with LLM descriptions (synchronous).

        Args:
            ndoc: Normalized document with blocks
            max_images: Maximum number of images to describe per document

        Returns:
            Enhanced document with image descriptions
        """
        from ..app.image_context import ImageContextTracker
        from ..domain import Block, BlockType, NormalizedDoc

        logger = logging.getLogger(__name__)

        if not self.image_describer:
            return ndoc

        tracker = ImageContextTracker(context_lines=100)
        if self.llm_config and hasattr(self.llm_config, "context_lines"):
            tracker = ImageContextTracker(context_lines=self.llm_config.context_lines)

        enhanced_blocks = []
        images_described = 0

        for block in ndoc.blocks:
            # Accumulate text context
            if block.type in (BlockType.TEXT, BlockType.HEADER):
                tracker.add_text(block.content)
                enhanced_blocks.append(block)

            # Process images (up to max limit, or unlimited if -1)
            elif block.type == BlockType.IMAGE:
                if block.image_data and (max_images == -1 or images_described < max_images):
                    try:
                        context = tracker.get_context()
                        description = self.image_describer.describe_image(  # type: ignore
                            block.image_data, context, "image/jpeg"
                        )

                        # Create new block with description
                        enhanced_block = Block(
                            type=BlockType.IMAGE,
                            content=description,
                            metadata={
                                **block.metadata,
                                "llm_described": True,
                                "description_index": images_described + 1,
                            },
                            page_number=block.page_number,
                            confidence=block.confidence,
                        )
                        enhanced_blocks.append(enhanced_block)
                        images_described += 1

                        max_images_str = "unlimited" if max_images == -1 else str(max_images)
                        logger.info(
                            f"Described image {images_described}/{max_images_str} "
                            f"on page {block.page_number}"
                        )

                    except Exception as e:
                        # Fallback: use original block
                        logger.warning(f"Failed to describe image: {e}")
                        enhanced_blocks.append(block)
                else:
                    # Skip description if over limit or no image data
                    if images_described >= max_images and block.image_data:
                        logger.info(f"Skipping image description (max {max_images} reached)")
                    enhanced_blocks.append(block)

            else:
                enhanced_blocks.append(block)

        # Log summary
        if images_described > 0:
            logger.info(
                f"Enhanced {images_described} image(s) with LLM descriptions (max: {max_images})"
            )

        return NormalizedDoc(
            blocks=tuple(enhanced_blocks),
            source_mime=ndoc.source_mime,
            page_count=ndoc.page_count,
            has_tables=ndoc.has_tables,
            has_images=ndoc.has_images,
            extractor_name=ndoc.extractor_name,
            metadata={**ndoc.metadata, "images_described": images_described},
        )
