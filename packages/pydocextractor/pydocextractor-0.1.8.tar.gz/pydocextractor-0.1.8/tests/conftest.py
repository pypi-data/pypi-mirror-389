"""
Pytest configuration and shared fixtures for hexagonal architecture tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from pydocextractor.domain.models import (
    Block,
    BlockType,
    Document,
    ExtractionResult,
    NormalizedDoc,
    PrecisionLevel,
)

# Enable pytest-bdd plugin
pytest_plugins = ["pytest_bdd"]

# Test documents directory
TEST_DOCS_DIR = Path(__file__).parent.parent / "test_documents"


# ============================================================================
# Test Document Fixtures
# ============================================================================


@pytest.fixture
def test_docs_dir() -> Path:
    """Get test documents directory."""
    return TEST_DOCS_DIR


@pytest.fixture
def policy_report_pdf(test_docs_dir: Path) -> Path:
    """Path to Policy_Report.pdf test document."""
    path = test_docs_dir / "Policy_Report.pdf"
    if not path.exists():
        pytest.skip(f"Test document not found: {path}")
    return path


@pytest.fixture
def company_handbook_pdf(test_docs_dir: Path) -> Path:
    """Path to Company_Handbook.pdf test document."""
    path = test_docs_dir / "Company_Handbook.pdf"
    if not path.exists():
        pytest.skip(f"Test document not found: {path}")
    return path


@pytest.fixture
def sales_xlsx(test_docs_dir: Path) -> Path:
    """Path to Sales_2025.xlsx test document."""
    path = test_docs_dir / "Sales_2025.xlsx"
    if not path.exists():
        pytest.skip(f"Test document not found: {path}")
    return path


@pytest.fixture
def sales_xls(test_docs_dir: Path) -> Path:
    """Path to Sales_2025.xls test document."""
    path = test_docs_dir / "Sales_2025.xls"
    if not path.exists():
        pytest.skip(f"Test document not found: {path}")
    return path


# ============================================================================
# Domain Model Fixtures
# ============================================================================


@pytest.fixture
def sample_document() -> Document:
    """Create a sample Document for testing."""
    return Document(
        bytes=b"Sample PDF content here",
        mime="application/pdf",
        size_bytes=23,
        precision=PrecisionLevel.BALANCED,
        filename="sample.pdf",
        metadata={"test": True},
    )


@pytest.fixture
def sample_blocks() -> tuple[Block, ...]:
    """Create sample blocks for testing."""
    return (
        Block(type=BlockType.HEADER, content="# Test Document", metadata={"level": 1}),
        Block(type=BlockType.TEXT, content="This is a paragraph.", metadata={"page": 1}),
        Block(
            type=BlockType.TABLE,
            content="| Col1 | Col2 |\n|------|------|\n| A    | B    |",
            metadata={"rows": 2, "cols": 2},
        ),
    )


@pytest.fixture
def sample_normalized_doc(sample_blocks: tuple[Block, ...]) -> NormalizedDoc:
    """Create a sample NormalizedDoc for testing."""
    return NormalizedDoc(
        blocks=sample_blocks,
        source_mime="application/pdf",
        has_tables=True,
        metadata={"pages": 1, "extractor": "test"},
    )


@pytest.fixture
def sample_extraction_result(sample_normalized_doc: NormalizedDoc) -> ExtractionResult:
    """Create a sample ExtractionResult for testing."""
    return ExtractionResult(
        success=True,
        normalized_doc=sample_normalized_doc,
        extractor_name="TestExtractor",
        processing_time_seconds=0.5,
    )


# ============================================================================
# Mock Protocol Fixtures
# ============================================================================


class MockExtractor:
    """Mock Extractor for testing."""

    def __init__(
        self,
        name: str = "MockExtractor",
        level: PrecisionLevel = PrecisionLevel.BALANCED,
        supported_mime: str = "application/pdf",
        available: bool = True,
    ):
        self._name = name
        self._level = level
        self._supported_mime = supported_mime
        self._available = available
        self.extract_called = False
        self.extract_args: tuple[Any, ...] = ()

    @property
    def name(self) -> str:
        return self._name

    @property
    def precision_level(self) -> PrecisionLevel:
        return self._level

    def is_available(self) -> bool:
        return self._available

    def supports(self, mime: str) -> bool:
        return mime == self._supported_mime

    def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
        """Mock extract method."""
        self.extract_called = True
        self.extract_args = (data, precision)

        # Return success with mock data
        blocks = (Block(type=BlockType.TEXT, content="Mock extracted content"),)
        ndoc = NormalizedDoc(blocks=blocks, source_mime=self._supported_mime)
        return ExtractionResult(
            success=True,
            normalized_doc=ndoc,
            extractor_name=self._name,
            processing_time_seconds=0.1,
        )


class MockPolicy:
    """Mock Policy for testing."""

    def __init__(self, extractors: list[MockExtractor] | None = None):
        self._extractors = extractors if extractors is not None else [MockExtractor()]
        self.choose_called = False
        self.choose_args: tuple[Any, ...] = ()

    def choose_extractors(
        self,
        mime: str,
        size_bytes: int,
        has_tables: bool,
        precision: PrecisionLevel,
    ) -> tuple[MockExtractor, ...]:
        """Mock choose_extractors method."""
        self.choose_called = True
        self.choose_args = (mime, size_bytes, has_tables, precision)
        return tuple(self._extractors)


class MockTemplateEngine:
    """Mock TemplateEngine for testing."""

    def __init__(self, rendered_output: str = "# Rendered Markdown"):
        self._rendered_output = rendered_output
        self.render_called = False
        self.render_args: tuple[Any, ...] = ()

    def render(self, template_name: str, context: Any) -> str:
        """Mock render method."""
        self.render_called = True
        self.render_args = (template_name, context)
        return self._rendered_output

    def list_templates(self) -> tuple[str, ...]:
        """Mock list_templates method."""
        return ("default", "simple")


class MockQualityScorer:
    """Mock QualityScorer for testing."""

    def __init__(self, score: float = 0.85):
        self._score = score
        self.calculate_called = False
        self.calculate_args: tuple[Any, ...] = ()

    def calculate_score(
        self,
        ndoc: NormalizedDoc,
        markdown: str,
        original: Document | None = None,
    ) -> float:
        """Mock calculate_score method."""
        self.calculate_called = True
        self.calculate_args = (ndoc, markdown, original)
        return self._score


@pytest.fixture
def mock_extractor() -> MockExtractor:
    """Create a mock extractor."""
    return MockExtractor()


@pytest.fixture
def mock_policy(mock_extractor: MockExtractor) -> MockPolicy:
    """Create a mock policy."""
    return MockPolicy(extractors=[mock_extractor])


@pytest.fixture
def mock_template_engine() -> MockTemplateEngine:
    """Create a mock template engine."""
    return MockTemplateEngine()


@pytest.fixture
def mock_quality_scorer() -> MockQualityScorer:
    """Create a mock quality scorer."""
    return MockQualityScorer()


# ============================================================================
# Helper Functions
# ============================================================================


@pytest.fixture
def load_test_document():
    """Factory fixture to load test documents as Document objects."""

    def _load(path: Path, precision: PrecisionLevel = PrecisionLevel.BALANCED) -> Document:
        """Load a test document."""
        data = path.read_bytes()

        # Detect MIME type
        suffix = path.suffix.lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".csv": "text/csv",
        }
        mime = mime_map.get(suffix, "application/octet-stream")

        return Document(
            bytes=data,
            mime=mime,
            size_bytes=len(data),
            precision=precision,
            filename=path.name,
        )

    return _load
