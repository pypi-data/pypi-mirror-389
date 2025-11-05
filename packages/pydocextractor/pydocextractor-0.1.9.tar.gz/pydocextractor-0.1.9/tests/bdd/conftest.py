"""
Pytest-BDD configuration and fixtures.

Provides shared context and fixtures for BDD tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_bdd import given

# Import ALL step definitions at module level to register them with pytest-bdd
# These imports MUST happen before any scenarios are collected
from tests.bdd.steps import (
    common_steps,  # noqa: F401
    document_tables_steps,  # noqa: F401
    pdf_word_steps,  # noqa: F401
    table_extraction_steps,  # noqa: F401
)

# ============================================================================
# BDD Context Fixture
# ============================================================================


@pytest.fixture
def context():
    """
    Shared context dictionary for BDD scenarios.

    This provides a way to share state between Given/When/Then steps
    within a single scenario execution.
    """
    return {}


@pytest.fixture
def service():
    """
    Create converter service instance.

    This is automatically available to all scenarios without needing a step definition.
    """
    from pydocextractor.factory import create_converter_service

    service = create_converter_service()
    assert service is not None
    return service


@pytest.fixture
def test_docs_dir():
    """
    Return the path to test documents directory.

    Points to the project's test_documents directory.
    """
    # Go up from tests/bdd to project root, then to test_documents
    docs_dir = Path(__file__).parent.parent.parent / "test_documents"
    if not docs_dir.exists():
        pytest.skip(f"Test documents directory not found: {docs_dir}")
    return docs_dir


@pytest.fixture
def load_test_document():
    """Helper fixture to load test documents."""
    from pydocextractor.domain.models import Document, PrecisionLevel

    def _load(
        file_path: Path, mime: str = None, precision: PrecisionLevel = PrecisionLevel.BALANCED
    ):
        """Load a test document from file path."""
        if not file_path.exists():
            pytest.skip(f"Test document not found: {file_path}")

        data = file_path.read_bytes()

        # Auto-detect MIME if not provided
        if mime is None:
            if file_path.suffix == ".pdf":
                mime = "application/pdf"
            elif file_path.suffix == ".docx":
                mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif file_path.suffix == ".xlsx":
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif file_path.suffix == ".csv":
                mime = "text/csv"
            else:
                mime = "application/octet-stream"

        return Document(
            bytes=data,
            mime=mime,
            size_bytes=len(data),
            precision=precision,
            filename=file_path.name,
        )

    return _load


@pytest.fixture
def policy_report_pdf(test_docs_dir):
    """Return path to Policy_Report.pdf."""
    return test_docs_dir / "Policy_Report.pdf"


# ============================================================================
# BDD Configuration Steps
# ============================================================================


# Note: "a DOCX file contains smart quotes..." step is defined in common_steps.py


@given("an Excel sheet has more than 40 columns", target_fixture="document")
def excel_wide_sheet(test_docs_dir):
    """Create mock Excel with many columns."""
    from pydocextractor.domain.models import Document, PrecisionLevel

    mock_content = b"Mock wide Excel"

    return Document(
        bytes=mock_content,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=len(mock_content),
        precision=PrecisionLevel.HIGHEST_QUALITY,
        filename="wide_sheet.xlsx",
        metadata={"columns": 50},
    )


# Note: "a document contains a paragraph referencing..." step is defined in common_steps.py


# Note: "the conversion finished successfully" step is defined in common_steps.py


# ============================================================================
# Table Configuration Steps
# ============================================================================


@given("the tabular extraction rules are configured to:")
def configure_tabular_rules(context, datatable):
    """Configure tabular extraction rules from table."""
    rules = {}
    # pytest-bdd datatables are lists of lists, first row is header
    for row in datatable[1:]:  # Skip header row
        rule_name = row[0].lower().replace(" ", "_")
        rules[rule_name] = True
    context["tabular_rules"] = rules


@given("statistical summaries are enabled")
def enable_statistics(context):
    """Enable statistical summaries."""
    context["statistics_enabled"] = True


@given("the renderer is configured to:")
def configure_renderer(context, datatable):
    """Configure renderer settings from table."""
    settings = {}
    # pytest-bdd datatables are lists of lists, first row is header
    for row in datatable[1:]:  # Skip header row
        setting_name = row[0].lower().replace(" ", "_")
        settings[setting_name] = True
    context["renderer_settings"] = settings


# ============================================================================
# Document Property Fixtures
# ============================================================================


@given(
    'I have "Policy_Report.pdf" which includes multiple tables, captions, and paragraphs before and after each table',
    target_fixture="document",
)
def policy_report_with_tables(policy_report_pdf, load_test_document):
    """Load Policy Report PDF."""
    return load_test_document(policy_report_pdf)


@given(
    'I have "HR_Guide.docx" containing headings, normal text, tables with merged cells, and inline images',
    target_fixture="document",
)
def hr_guide_docx(test_docs_dir):
    """Load HR Guide DOCX (or skip if not available)."""
    from pydocextractor.domain.models import Document, PrecisionLevel

    file_path = test_docs_dir / "HR_Guide.docx"
    if not file_path.exists():
        pytest.skip("HR_Guide.docx not found")

    data = file_path.read_bytes()
    return Document(
        bytes=data,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=len(data),
        precision=PrecisionLevel.HIGHEST_QUALITY,
        filename="HR_Guide.docx",
    )


# Note: 'a document "<doc>" has a table with "<case>"' step is defined in common_steps.py


# ============================================================================
# Pytest-BDD Hooks
# ============================================================================


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Hook to handle step errors for better debugging."""
    # Use logging instead of print for better test output
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"\nBDD Step Error in {feature.name}/{scenario.name}")
    logger.error(f"Step: {step.keyword} {step.name}")
    logger.error(f"Exception: {exception}")


def pytest_bdd_before_scenario(request, feature, scenario):
    """Hook called before each scenario."""
    # Use logging instead of print for better test output
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"\n▶ Running BDD Scenario: {scenario.name}")


def pytest_bdd_after_scenario(request, feature, scenario):
    """Hook called after each scenario."""
    # Use logging instead of print for better test output
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"✓ Completed BDD Scenario: {scenario.name}")
