# Contributing to pyDocExtractor

Thank you for your interest in contributing to pyDocExtractor! This guide will help you understand the project structure and how to add new features effectively.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [How to Add Support for a New Document Type](#how-to-add-support-for-a-new-document-type)
- [How to Add a Custom Template](#how-to-add-a-custom-template)
- [How to Add a Custom Quality Scorer](#how-to-add-a-custom-quality-scorer)
- [How to Modify the Selection Policy](#how-to-modify-the-selection-policy)
- [Testing Guidelines](#testing-guidelines)
- [Code Quality Standards](#code-quality-standards)
- [Pull Request Process](#pull-request-process)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [just](https://github.com/casey/just) command runner
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# macOS - Install just
brew install just

# Linux - Install just
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Clone the repository
git clone https://github.com/AminiTech/pyDocExtractor.git
cd pyDocExtractor

# Bootstrap development environment
just bootstrap

# Verify installation
just test
just check
```

## Project Structure

pyDocExtractor follows **Hexagonal Architecture** (Ports and Adapters) with three distinct layers:

| Directory | Purpose | What to Change For |
|-----------|---------|-------------------|
| `src/pydocextractor/domain/` | **Pure business logic** - No external dependencies | Add new domain models, ports (interfaces), business rules |
| `src/pydocextractor/domain/models.py` | Immutable dataclasses (Document, Block, NormalizedDoc, etc.) | Add new document attributes, block types |
| `src/pydocextractor/domain/ports.py` | Protocol definitions (interfaces) | Define new port interfaces (e.g., new adapter types) |
| `src/pydocextractor/domain/rules.py` | Pure functions for business logic | Add validation rules, quality calculations |
| `src/pydocextractor/domain/errors.py` | Domain exception hierarchy | Add new exception types |
| `src/pydocextractor/app/` | **Application orchestration layer** | Modify conversion workflow logic |
| `src/pydocextractor/app/service.py` | ConverterService - main orchestration | Change how extractors are called, add caching logic |
| `src/pydocextractor/infra/` | **Infrastructure - concrete implementations** | Add new extractors, templates, scoring algorithms |
| `src/pydocextractor/infra/extractors/` | Document extractors (PDF, DOCX, CSV, Excel) | **Add new document type support** |
| `src/pydocextractor/infra/policy/` | Extractor selection logic | Modify auto-selection heuristics |
| `src/pydocextractor/infra/templates/` | Jinja2 markdown templates | Add new output formats |
| `src/pydocextractor/infra/scoring/` | Quality scoring implementations | Add custom quality metrics |
| `src/pydocextractor/factory.py` | Dependency injection / service creation | Wire up new components |
| `src/pydocextractor/cli.py` | Command-line interface | Add CLI commands or options |
| `tests/unit/` | Unit tests (fast, no infrastructure) | Test domain & app layer logic |
| `tests/adapters/` | Adapter tests (infrastructure) | Test extractors, templates, scoring |
| `tests/contract/` | Protocol compliance tests | Verify implementations match protocols |
| `tests/integration/` | End-to-end tests | Test full conversion pipeline |
| `tests/bdd/` | BDD tests with Gherkin scenarios | Add behavior-driven test scenarios |
| `test_documents/` | Sample documents for testing | Add test files for new document types |

### Layer Dependencies (Architecture Rules)

```
Domain Layer (Pure)
    ↑
    | depends on
    |
Application Layer (Orchestration)
    ↑
    | depends on
    |
Infrastructure Layer (Implementations)
```

**Important:** Domain layer MUST NOT import from `app` or `infra` layers. This is enforced by `import-linter`.

## Development Workflow

### Available Commands

```bash
# Installation
just bootstrap        # Install all dev dependencies
just install          # Install package with all extras

# Code Quality
just fmt              # Format code with ruff
just lint             # Lint code with ruff
just fix              # Auto-fix linting issues
just typecheck        # Type check with mypy
just guard            # Verify architectural boundaries
just check            # Run all quality checks

# Testing
just test             # Run all tests
just test-unit        # Fast unit tests only
just test-adapters    # Infrastructure tests
just test-contract    # Protocol compliance tests
just test-bdd         # BDD tests
just test-cov         # Tests with coverage report

# Utilities
just clean            # Remove build artifacts
just build            # Build package distribution
```

### Pre-commit Checklist

Before submitting a PR, ensure:

```bash
just fmt           # Code is formatted
just check         # All quality checks pass
just test          # All tests pass
just guard         # Architecture boundaries respected
```

Or run everything at once:

```bash
just ci            # Full CI pipeline locally
```

## How to Add Support for a New Document Type

Adding support for a new document type involves creating a new extractor that implements the `Extractor` Protocol.

### Step 1: Create a New Extractor Adapter

Create a new file in `src/pydocextractor/infra/extractors/` (e.g., `my_format_adapter.py`):

```python
"""
Extractor for MY_FORMAT documents.

This adapter converts MY_FORMAT files to normalized blocks.
"""

from __future__ import annotations

import time
from typing import Any

from pydocextractor.domain.errors import ExtractionError
from pydocextractor.domain.models import (
    Block,
    BlockType,
    ExtractionResult,
    NormalizedDoc,
    PrecisionLevel,
)

# Check if the required library is available
try:
    import my_format_library  # Replace with actual library
    MY_FORMAT_AVAILABLE = True
except ImportError:
    MY_FORMAT_AVAILABLE = False


class MyFormatExtractor:
    """Extract MY_FORMAT files using my_format_library."""

    @property
    def name(self) -> str:
        """Human-readable name of this extractor."""
        return "MyFormat"

    @property
    def precision_level(self) -> PrecisionLevel:
        """Precision level this extractor operates at."""
        # Choose appropriate level (1=FASTEST, 2=BALANCED, 3=TABLE_OPTIMIZED, 4=HIGHEST_QUALITY)
        return PrecisionLevel.HIGHEST_QUALITY

    def is_available(self) -> bool:
        """Check if dependencies are installed."""
        return MY_FORMAT_AVAILABLE

    def supports(self, mime: str) -> bool:
        """Check if this extractor supports the MIME type."""
        # Add all MIME types your extractor supports
        return mime in [
            "application/my-format",
            "application/x-my-format",
        ] and MY_FORMAT_AVAILABLE

    def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
        """
        Extract content from MY_FORMAT document.

        Args:
            data: Raw document bytes
            precision: Desired precision level (informational)

        Returns:
            ExtractionResult with normalized document or error
        """
        if not MY_FORMAT_AVAILABLE:
            return ExtractionResult(
                success=False,
                error="my_format_library not available - install with: pip install my-format-lib",
                extractor_name=self.name,
            )

        start_time = time.time()

        try:
            # 1. Use your library to parse the document
            document = my_format_library.parse(data)

            # 2. Extract content and convert to blocks
            blocks = []

            # Example: Extract text content
            if document.has_text():
                text_content = document.get_text()
                blocks.append(
                    Block(
                        type=BlockType.TEXT,
                        content=text_content,
                        metadata={"source": "my_format_library"},
                    )
                )

            # Example: Extract tables
            if document.has_tables():
                for table in document.get_tables():
                    table_markdown = self._convert_table_to_markdown(table)
                    blocks.append(
                        Block(
                            type=BlockType.TABLE,
                            content=table_markdown,
                            metadata={"rows": len(table.rows), "columns": len(table.columns)},
                        )
                    )

            # Example: Extract images
            if document.has_images():
                for idx, image in enumerate(document.get_images()):
                    blocks.append(
                        Block(
                            type=BlockType.IMAGE,
                            content=f"![Image {idx}](data:image/png;base64,{image.to_base64()})",
                            metadata={"format": image.format, "size": image.size},
                        )
                    )

            # 3. Prepare metadata
            metadata: dict[str, Any] = {
                "page_count": document.page_count if hasattr(document, "page_count") else None,
                "author": document.author if hasattr(document, "author") else None,
                "title": document.title if hasattr(document, "title") else None,
            }

            # 4. Create normalized document
            ndoc = NormalizedDoc(
                blocks=tuple(blocks),
                source_mime="application/my-format",
                page_count=document.page_count if hasattr(document, "page_count") else None,
                has_tables=document.has_tables(),
                has_images=document.has_images(),
                extractor_name=self.name,
                metadata=metadata,
            )

            elapsed = time.time() - start_time

            return ExtractionResult(
                success=True,
                normalized_doc=ndoc,
                extractor_name=self.name,
                processing_time_seconds=elapsed,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return ExtractionResult(
                success=False,
                error=f"MY_FORMAT extraction failed: {e}",
                extractor_name=self.name,
                processing_time_seconds=elapsed,
            )

    def _convert_table_to_markdown(self, table: Any) -> str:
        """Convert table object to markdown format."""
        # Implement table-to-markdown conversion
        # You can use pandas or implement manually
        lines = []

        # Header
        header = " | ".join(str(cell) for cell in table.headers)
        lines.append(f"| {header} |")

        # Separator
        separator = " | ".join("---" for _ in table.headers)
        lines.append(f"| {separator} |")

        # Rows
        for row in table.rows:
            row_str = " | ".join(str(cell) for cell in row)
            lines.append(f"| {row_str} |")

        return "\n".join(lines)
```

### Step 2: Update the Selection Policy

Add your extractor to `src/pydocextractor/infra/policy/heuristics.py`:

```python
# Import your extractor
from ..extractors.my_format_adapter import MyFormatExtractor

class DefaultPolicy:
    def __init__(self) -> None:
        """Initialize policy with available extractors."""
        self._extractors: dict[PrecisionLevel, Extractor] = {}
        # ... existing code ...

        # Add your extractor
        self._my_format_extractor: Extractor | None = None
        my_format_extractor = MyFormatExtractor()
        if my_format_extractor.is_available():
            self._my_format_extractor = my_format_extractor

    def choose_extractors(
        self,
        mime: str,
        size_bytes: int,
        has_tables: bool,
        precision: PrecisionLevel,
    ) -> Sequence[Extractor]:
        """Choose ordered sequence of extractors to try."""
        # Add your MIME type check
        if mime in ["application/my-format", "application/x-my-format"] and self._my_format_extractor:
            return tuple([self._my_format_extractor])

        # ... rest of the method ...
```

### Step 3: Add Optional Dependency

Update `pyproject.toml` to include your library as an optional dependency:

```toml
[project.optional-dependencies]
# ... existing extras ...
myformat = [
    "my-format-library>=1.0.0",
]
all = [
    # ... existing dependencies ...
    "my-format-library>=1.0.0",
]
```

### Step 4: Write Tests

Create tests in `tests/adapters/test_extractors.py`:

```python
import pytest
from pydocextractor.domain.models import PrecisionLevel
from pydocextractor.infra.extractors.my_format_adapter import MyFormatExtractor

class TestMyFormatExtractor:
    def test_supports_mime_type(self):
        extractor = MyFormatExtractor()
        assert extractor.supports("application/my-format")

    def test_extract_text(self, sample_my_format_file):
        extractor = MyFormatExtractor()
        data = sample_my_format_file.read_bytes()

        result = extractor.extract(data, PrecisionLevel.HIGHEST_QUALITY)

        assert result.success
        assert result.normalized_doc is not None
        assert len(result.normalized_doc.blocks) > 0

    def test_graceful_failure_when_library_missing(self, monkeypatch):
        # Test that extractor handles missing dependencies gracefully
        monkeypatch.setattr("pydocextractor.infra.extractors.my_format_adapter.MY_FORMAT_AVAILABLE", False)
        extractor = MyFormatExtractor()
        assert not extractor.is_available()
```

### Step 5: Add Test Documents

Place sample documents in `test_documents/`:

```bash
cp my_sample_document.myformat test_documents/
```

### Step 6: Verify Architecture Compliance

```bash
just guard         # Verify no architecture violations
just typecheck     # Verify type annotations
just test          # Run all tests
```

## How to Add a Custom Template

Templates control how the normalized document is rendered to Markdown.

### Step 1: Create Template File

Create a new Jinja2 template in `src/pydocextractor/infra/templates/templates/`:

```jinja2
{# my_custom_template.j2 #}
---
title: {{ metadata.filename }}
extractor: {{ metadata.extractor }}
quality_score: {{ quality_score }}
---

# {{ metadata.filename }}

{% for block in blocks %}
{% if block.type == 'text' %}
{{ block.content }}

{% elif block.type == 'table' %}
## Table

{{ block.content }}

{% elif block.type == 'header' %}
## {{ block.content }}

{% endif %}
{% endfor %}

---
**Generated by pyDocExtractor** | Quality: {{ quality_score }}
```

### Step 2: Use the Template

```python
from pydocextractor import create_converter_service

service = create_converter_service()
result = service.convert_to_markdown(doc, template_name="my_custom_template")
```

### Template Context Variables

Available variables in templates:

- `blocks`: List of block dictionaries with `type`, `content`, `page`, `confidence`
- `metadata`: Document metadata (filename, extractor, custom fields)
- `quality_score`: Quality score (0.0-1.0)
- `has_tables`: Boolean indicating presence of tables
- `has_images`: Boolean indicating presence of images
- `page_count`: Total page count (if available)

## How to Add a Custom Quality Scorer

Quality scorers calculate a 0.0-1.0 score for conversions.

### Step 1: Create Scorer Class

Create a new file in `src/pydocextractor/infra/scoring/`:

```python
"""Custom quality scoring implementation."""

from pydocextractor.domain.models import Document, NormalizedDoc


class MyCustomQualityScorer:
    """Custom quality scorer with specific metrics."""

    def calculate_score(
        self,
        ndoc: NormalizedDoc,
        markdown: str,
        original: Document | None = None,
    ) -> float:
        """
        Calculate quality score.

        Args:
            ndoc: Normalized document
            markdown: Rendered markdown
            original: Original document (optional)

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0

        # Criterion 1: Content length (30%)
        word_count = len(markdown.split())
        if word_count > 1000:
            score += 0.3
        elif word_count > 100:
            score += 0.15

        # Criterion 2: Structure (40%)
        if ndoc.has_tables:
            score += 0.2
        if ndoc.page_count and ndoc.page_count > 0:
            score += 0.2

        # Criterion 3: Block diversity (30%)
        block_types = {block.type for block in ndoc.blocks}
        diversity = len(block_types) / 7  # 7 total block types
        score += diversity * 0.3

        return min(1.0, max(0.0, score))
```

### Step 2: Use Custom Scorer

```python
from pydocextractor.app.service import ConverterService
from pydocextractor.infra.policy.heuristics import DefaultPolicy
from pydocextractor.infra.templates.engines import Jinja2TemplateEngine
from pydocextractor.infra.scoring.my_custom_scorer import MyCustomQualityScorer

policy = DefaultPolicy()
template_engine = Jinja2TemplateEngine()
quality_scorer = MyCustomQualityScorer()

service = ConverterService(
    policy=policy,
    template_engine=template_engine,
    quality_scorer=quality_scorer,
)
```

## How to Modify the Selection Policy

The selection policy determines which extractor to use based on document characteristics.

### Option 1: Modify DefaultPolicy

Edit `src/pydocextractor/infra/policy/heuristics.py`:

```python
def choose_extractors(
    self,
    mime: str,
    size_bytes: int,
    has_tables: bool,
    precision: PrecisionLevel,
) -> Sequence[Extractor]:
    # Add your custom logic
    size_mb = size_bytes / (1024 * 1024)

    # Example: Use different threshold for large files
    if mime == "application/pdf":
        if size_mb > 50.0:  # Changed from 20.0
            return tuple([self._extractors[PrecisionLevel.FASTEST]])
        # ... rest of logic ...
```

### Option 2: Create Custom Policy

```python
"""Custom selection policy."""

from collections.abc import Sequence
from pydocextractor.domain.models import PrecisionLevel
from pydocextractor.domain.ports import Extractor


class MyCustomPolicy:
    """Custom policy with specific selection rules."""

    def __init__(self) -> None:
        # Initialize extractors
        pass

    def choose_extractors(
        self,
        mime: str,
        size_bytes: int,
        has_tables: bool,
        precision: PrecisionLevel,
    ) -> Sequence[Extractor]:
        """Implement your selection logic."""
        # Your custom logic here
        pass
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Fast unit tests, no I/O
│   ├── domain/       # Test domain models, rules
│   └── app/          # Test service with mocked dependencies
├── adapters/         # Test infrastructure adapters
├── contract/         # Test protocol compliance
├── integration/      # End-to-end tests
└── bdd/              # BDD tests with Gherkin
```

### Writing Tests

#### Unit Tests (Domain Layer)

```python
# tests/unit/domain/test_models.py
from pydocextractor.domain.models import Document, PrecisionLevel

def test_document_creation():
    doc = Document(
        bytes=b"test content",
        mime="application/pdf",
        size_bytes=12,
        precision=PrecisionLevel.BALANCED,
    )
    assert doc.size_bytes == 12
    assert doc.mime == "application/pdf"
```

#### Adapter Tests

```python
# tests/adapters/test_extractors.py
from pathlib import Path
from pydocextractor.infra.extractors.my_format_adapter import MyFormatExtractor

def test_extractor_with_real_file():
    extractor = MyFormatExtractor()
    if not extractor.is_available():
        pytest.skip("MyFormat library not available")

    data = Path("test_documents/sample.myformat").read_bytes()
    result = extractor.extract(data, PrecisionLevel.HIGHEST_QUALITY)

    assert result.success
    assert len(result.normalized_doc.blocks) > 0
```

#### BDD Tests

Create a feature file in `tests/bdd/features/`:

```gherkin
# my_format_extraction.feature
Feature: Extract MY_FORMAT documents to Markdown

  Scenario: Convert a MY_FORMAT file to Markdown
    Given I have a MY_FORMAT file "sample.myformat"
    When I submit the file for extraction
    Then the service produces a Markdown document
    And the Markdown contains extracted text
    And a quality score is calculated
```

### Running Tests

```bash
just test              # All tests
just test-unit         # Fast unit tests
just test-adapters     # Adapter tests
just test-bdd          # BDD tests
just test-cov          # With coverage
```

## Code Quality Standards

### Type Hints

All code must have type hints:

```python
def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
    """Extract content from document."""
    ...
```

### Formatting

Use ruff for formatting:

```bash
just fmt    # Format all code
```

### Linting

```bash
just lint   # Check linting issues
just fix    # Auto-fix issues
```

### Type Checking

```bash
just typecheck   # Run mypy
```

### Architecture Boundaries

Verify layer boundaries are respected:

```bash
just guard   # Run import-linter
```

## Pull Request Process

1. **Fork the repository** and create a feature branch:
   ```bash
   git checkout -b feature/add-myformat-support
   ```

2. **Make your changes** following the guidelines above

3. **Add tests** for your changes:
   - Unit tests for domain/app logic
   - Adapter tests for infrastructure
   - Integration tests for end-to-end flows

4. **Run quality checks**:
   ```bash
   just fmt
   just check
   just test
   just guard
   ```

5. **Commit your changes** with clear messages:
   ```bash
   git commit -m "Add support for MY_FORMAT documents"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/add-myformat-support
   ```

7. **Create a Pull Request** with:
   - Clear description of changes
   - Link to any related issues
   - Screenshots/examples if applicable
   - List of testing performed

### PR Checklist

- [ ] Code follows hexagonal architecture principles
- [ ] All tests pass (`just test`)
- [ ] Code is formatted (`just fmt`)
- [ ] Type hints are complete (`just typecheck`)
- [ ] Architecture boundaries respected (`just guard`)
- [ ] Documentation updated (README.md, docstrings)
- [ ] Test coverage maintained or improved
- [ ] Commit messages are clear and descriptive

## Questions or Need Help?

- **Issues**: [GitHub Issues](https://github.com/AminiTech/pyDocExtractor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AminiTech/pyDocExtractor/discussions)
- **Documentation**: [Project Wiki](https://github.com/AminiTech/pyDocExtractor/wiki)

Thank you for contributing to pyDocExtractor!
