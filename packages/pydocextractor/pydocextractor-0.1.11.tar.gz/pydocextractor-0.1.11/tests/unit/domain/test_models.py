"""
Unit tests for domain models.

Tests pure domain dataclasses with no external dependencies.
"""

from __future__ import annotations

import pytest

from pydocextractor.domain.models import (
    Block,
    BlockType,
    Document,
    Markdown,
    NormalizedDoc,
    PrecisionLevel,
    TemplateContext,
)


class TestPrecisionLevel:
    """Test PrecisionLevel enum."""

    def test_precision_levels(self):
        """Test all precision levels are defined."""
        assert PrecisionLevel.FASTEST.value == 1
        assert PrecisionLevel.BALANCED.value == 2
        assert PrecisionLevel.TABLE_OPTIMIZED.value == 3
        assert PrecisionLevel.HIGHEST_QUALITY.value == 4

    def test_precision_level_names(self):
        """Test precision level names."""
        assert PrecisionLevel.FASTEST.name == "FASTEST"
        assert PrecisionLevel.BALANCED.name == "BALANCED"


class TestBlockType:
    """Test BlockType enum."""

    def test_block_types(self):
        """Test all block types are defined."""
        assert BlockType.TEXT == "text"
        assert BlockType.HEADER == "header"
        assert BlockType.TABLE == "table"
        assert BlockType.LIST == "list"
        assert BlockType.CODE == "code"
        assert BlockType.IMAGE == "image"
        assert BlockType.METADATA == "metadata"


class TestBlock:
    """Test Block dataclass."""

    def test_block_creation(self):
        """Test creating a block."""
        block = Block(
            type=BlockType.TEXT,
            content="Hello world",
            metadata={"page": 1},
        )
        assert block.type == BlockType.TEXT
        assert block.content == "Hello world"
        assert block.metadata["page"] == 1

    def test_block_immutable(self):
        """Test blocks are immutable."""
        block = Block(type=BlockType.TEXT, content="Test")
        with pytest.raises(AttributeError):
            block.content = "Changed"  # type: ignore

    def test_block_default_metadata(self):
        """Test block has default empty metadata."""
        block = Block(type=BlockType.TEXT, content="Test")
        assert block.metadata == {}


class TestDocument:
    """Test Document dataclass."""

    def test_document_creation(self):
        """Test creating a document."""
        data = b"PDF content here"
        doc = Document(
            bytes=data,
            mime="application/pdf",
            size_bytes=len(data),
            precision=PrecisionLevel.BALANCED,
            filename="test.pdf",
        )
        assert doc.bytes == data
        assert doc.mime == "application/pdf"
        assert doc.size_bytes == len(data)
        assert doc.precision == PrecisionLevel.BALANCED
        assert doc.filename == "test.pdf"

    def test_document_default_precision(self):
        """Test document defaults to BALANCED precision."""
        doc = Document(
            bytes=b"test",
            mime="application/pdf",
            size_bytes=4,
        )
        assert doc.precision == PrecisionLevel.BALANCED

    def test_document_optional_filename(self):
        """Test filename is optional."""
        doc = Document(
            bytes=b"test",
            mime="application/pdf",
            size_bytes=4,
        )
        assert doc.filename is None

    def test_document_immutable(self):
        """Test documents are immutable."""
        doc = Document(
            bytes=b"test",
            mime="application/pdf",
            size_bytes=4,
        )
        with pytest.raises(AttributeError):
            doc.mime = "application/json"  # type: ignore


class TestNormalizedDoc:
    """Test NormalizedDoc dataclass."""

    def test_normalized_doc_creation(self):
        """Test creating a normalized document."""
        blocks = (
            Block(type=BlockType.HEADER, content="Title"),
            Block(type=BlockType.TEXT, content="Content"),
        )
        ndoc = NormalizedDoc(
            blocks=blocks,
            source_mime="application/pdf",
            has_tables=False,
            metadata={"pages": 1},
        )
        assert len(ndoc.blocks) == 2
        assert ndoc.source_mime == "application/pdf"
        assert ndoc.has_tables is False
        assert ndoc.metadata["pages"] == 1

    def test_normalized_doc_default_values(self):
        """Test default values."""
        blocks = (Block(type=BlockType.TEXT, content="Test"),)
        ndoc = NormalizedDoc(
            blocks=blocks,
            source_mime="application/pdf",
        )
        assert ndoc.has_tables is False
        assert ndoc.metadata == {}

    def test_normalized_doc_immutable_blocks(self):
        """Test blocks tuple is immutable."""
        blocks = (Block(type=BlockType.TEXT, content="Test"),)
        ndoc = NormalizedDoc(blocks=blocks, source_mime="application/pdf")

        with pytest.raises(TypeError):
            ndoc.blocks[0] = Block(type=BlockType.HEADER, content="New")  # type: ignore

    def test_empty_blocks(self):
        """Test normalized doc requires at least one block."""
        with pytest.raises(ValueError, match="NormalizedDoc must have at least one block"):
            NormalizedDoc(blocks=(), source_mime="application/pdf")


class TestMarkdown:
    """Test Markdown dataclass."""

    def test_markdown_creation(self):
        """Test creating markdown result."""
        md = Markdown(
            text="# Title\n\nContent",
            quality_score=0.85,
            metadata={"blocks": 2},
        )
        assert md.text == "# Title\n\nContent"
        assert md.quality_score == 0.85
        assert md.metadata["blocks"] == 2

    def test_markdown_optional_quality(self):
        """Test quality score is required."""
        # Quality score is required in the new model
        md = Markdown(
            text="# Title",
            quality_score=0.0,
        )
        assert md.quality_score == 0.0

    def test_markdown_default_metadata(self):
        """Test default empty metadata."""
        md = Markdown(
            text="# Title",
            quality_score=0.75,
        )
        assert md.metadata == {}

    def test_markdown_immutable(self):
        """Test markdown is immutable."""
        md = Markdown(text="# Title", quality_score=0.5)
        with pytest.raises(AttributeError):
            md.text = "Changed"  # type: ignore


class TestTemplateContext:
    """Test TemplateContext dataclass."""

    def test_template_context_creation(self):
        """Test creating template context from normalized doc."""
        ndoc = NormalizedDoc(
            blocks=(Block(type=BlockType.TEXT, content="Test"),),
            source_mime="application/pdf",
        )
        ctx = TemplateContext.from_normalized_doc(
            ndoc=ndoc,
            quality_score=0.75,
        )
        assert len(ctx.blocks) == 1
        assert ctx.quality_score == 0.75
        assert ctx.has_tables is False
        assert ctx.has_images is False

    def test_template_context_optional_quality(self):
        """Test quality score is optional."""
        ndoc = NormalizedDoc(
            blocks=(Block(type=BlockType.TEXT, content="Test"),),
            source_mime="application/pdf",
        )
        ctx = TemplateContext.from_normalized_doc(ndoc=ndoc)
        assert ctx.quality_score is None

    def test_template_context_default_custom_vars(self):
        """Test metadata from normalized doc."""
        ndoc = NormalizedDoc(
            blocks=(Block(type=BlockType.TEXT, content="Test"),),
            source_mime="application/pdf",
            extractor_name="PyMuPDF4LLM",
        )
        ctx = TemplateContext.from_normalized_doc(ndoc=ndoc)
        assert ctx.metadata["extractor"] == "PyMuPDF4LLM"
