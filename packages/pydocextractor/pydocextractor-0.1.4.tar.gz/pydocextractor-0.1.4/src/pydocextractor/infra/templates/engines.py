"""
Template engine implementations.

Jinja2-based template engine for markdown rendering.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

from ...domain import TemplateError


class Jinja2TemplateEngine:
    """
    Jinja2-based template engine.

    Renders normalized documents using Jinja2 templates.
    """

    def __init__(self, template_dir: str | Path | None = None) -> None:
        """
        Initialize Jinja2 template engine.

        Args:
            template_dir: Directory containing templates (defaults to bundled templates)
        """
        if template_dir is None:
            # Use bundled templates
            template_dir = Path(__file__).parent / "templates"
        else:
            template_dir = Path(template_dir)

        if not template_dir.exists():
            raise TemplateError(f"Template directory not found: {template_dir}")

        self._template_dir = template_dir
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(enabled_extensions=("html", "xml")),  # Safe for markdown
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self._env.filters["word_count"] = lambda s: len(str(s).split())
        self._env.filters["char_count"] = lambda s: len(str(s))

    def render(self, template_name: str, context: Mapping[str, object]) -> str:
        """
        Render template with given context.

        Args:
            template_name: Name/path of template (e.g., "default.j2")
            context: Template context data

        Returns:
            Rendered markdown text

        Raises:
            TemplateError: When rendering fails
        """
        try:
            # Add .j2 extension if not present
            if not template_name.endswith(".j2"):
                template_name = f"{template_name}.j2"

            template = self._env.get_template(template_name)
            return template.render(**context)

        except TemplateNotFound as e:
            available = self.list_templates()
            raise TemplateError(
                f"Template '{template_name}' not found. Available: {available}"
            ) from e
        except Exception as e:
            raise TemplateError(f"Template rendering failed: {e}") from e

    def list_templates(self) -> Sequence[str]:
        """List available template names."""
        try:
            templates = self._env.list_templates(extensions=["j2"])
            return tuple(templates)
        except Exception:
            return ()

    def render_string(self, template_string: str, context: Mapping[str, object]) -> str:
        """
        Render template from string.

        Args:
            template_string: Template content as string
            context: Template context data

        Returns:
            Rendered markdown text

        Raises:
            TemplateError: When rendering fails
        """
        try:
            template = self._env.from_string(template_string)
            return template.render(**context)
        except Exception as e:
            raise TemplateError(f"String template rendering failed: {e}") from e
