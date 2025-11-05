"""
Unit tests for template engine infrastructure.

Smoke tests for template rendering functionality.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pydocextractor.domain.models import Block, BlockType
from pydocextractor.infra.templates.engines import Jinja2TemplateEngine


class TestJinja2TemplateEngine:
    """Test Jinja2 template engine implementation."""

    def test_init_with_default_template_dir(self):
        """Test engine initializes with default template directory."""
        engine = Jinja2TemplateEngine()
        assert engine is not None

    def test_init_with_custom_template_dir(self, tmp_path: Path):
        """Test engine with custom template directory."""
        custom_dir = tmp_path / "templates"
        custom_dir.mkdir()

        engine = Jinja2TemplateEngine(template_dir=custom_dir)
        assert engine is not None

    def test_render_with_default_template(self):
        """Test rendering with default template."""
        engine = Jinja2TemplateEngine()

        ctx = {
            "blocks": [
                Block(type=BlockType.TEXT, content="Test content"),
            ],
            "metadata": {},
            "has_tables": False,
            "has_images": False,
            "page_count": 1,
            "quality_score": 0.8,
        }

        result = engine.render("default.j2", ctx)
        assert result is not None
        assert isinstance(result, str)
        assert "Test content" in result

    def test_render_with_headers_and_tables(self):
        """Test rendering document with headers and tables."""
        engine = Jinja2TemplateEngine()

        ctx = {
            "blocks": [
                Block(type=BlockType.HEADER, content="# Main Title"),
                Block(type=BlockType.TEXT, content="Some text"),
                Block(type=BlockType.TABLE, content="| A | B |\n|---|---|\n| 1 | 2 |"),
            ],
            "metadata": {},
            "has_tables": True,
            "has_images": False,
            "page_count": 1,
            "quality_score": 0.9,
        }

        result = engine.render("default.j2", ctx)
        assert "# Main Title" in result
        assert "Some text" in result
        assert "| A | B |" in result

    def test_render_with_custom_template(self, tmp_path: Path):
        """Test rendering with custom template."""
        custom_dir = tmp_path / "templates"
        custom_dir.mkdir()

        # Create simple custom template
        template_path = custom_dir / "custom.j2"
        template_path.write_text("{% for block in blocks %}{{ block.content }}\n{% endfor %}")

        engine = Jinja2TemplateEngine(template_dir=custom_dir)

        ctx = {
            "blocks": [
                Block(type=BlockType.TEXT, content="Line 1"),
                Block(type=BlockType.TEXT, content="Line 2"),
            ],
            "metadata": {},
            "has_tables": False,
            "has_images": False,
            "page_count": 1,
            "quality_score": 0.7,
        }

        result = engine.render("custom.j2", ctx)
        assert "Line 1" in result
        assert "Line 2" in result

    def test_render_empty_blocks(self):
        """Test rendering with no blocks."""
        engine = Jinja2TemplateEngine()

        ctx = {
            "blocks": [],
            "metadata": {},
            "has_tables": False,
            "has_images": False,
            "page_count": 0,
            "quality_score": 0.0,
        }

        result = engine.render("default.j2", ctx)
        assert result is not None
        assert isinstance(result, str)

    def test_render_with_metadata(self):
        """Test rendering includes metadata."""
        engine = Jinja2TemplateEngine()

        ctx = {
            "blocks": [Block(type=BlockType.TEXT, content="Content")],
            "metadata": {"author": "Test Author", "title": "Test Doc"},
            "has_tables": False,
            "has_images": False,
            "page_count": 1,
            "quality_score": 0.85,
        }

        result = engine.render("default.j2", ctx)
        assert result is not None


class TestJinja2TemplateEngineErrors:
    """Test Jinja2 template engine error handling."""

    def test_render_template_not_found(self):
        """Test rendering with non-existent template."""
        from pydocextractor.domain.errors import TemplateError

        engine = Jinja2TemplateEngine()

        ctx = {
            "blocks": [],
            "metadata": {},
            "has_tables": False,
            "has_images": False,
            "page_count": 0,
            "quality_score": 0.0,
        }

        with pytest.raises(TemplateError, match="not found"):
            engine.render("nonexistent.j2", ctx)

    def test_render_with_invalid_template_syntax(self, tmp_path: Path):
        """Test rendering with template containing syntax errors."""
        from pydocextractor.domain.errors import TemplateError

        custom_dir = tmp_path / "templates"
        custom_dir.mkdir()

        # Create template with invalid Jinja2 syntax
        template_path = custom_dir / "broken.j2"
        template_path.write_text(
            "{% for block in blocks %} {{ block.content "
        )  # Missing closing tag

        engine = Jinja2TemplateEngine(template_dir=custom_dir)

        ctx = {
            "blocks": [Block(type=BlockType.TEXT, content="Test")],
            "metadata": {},
            "has_tables": False,
            "has_images": False,
            "page_count": 1,
            "quality_score": 0.8,
        }

        with pytest.raises(TemplateError):
            engine.render("broken.j2", ctx)

    def test_list_templates(self):
        """Test listing available templates."""
        engine = Jinja2TemplateEngine()

        templates = engine.list_templates()

        assert isinstance(templates, (list, tuple))
        assert len(templates) > 0
        assert "default.j2" in templates or "default" in [t.replace(".j2", "") for t in templates]
