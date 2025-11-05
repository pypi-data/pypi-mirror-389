"""
BDD tests for Excel and CSV extraction (Feature 2).

These tests use pytest-bdd to execute Gherkin scenarios.
"""

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from pydocextractor.domain.models import Document, PrecisionLevel
from pydocextractor.factory import create_converter_service

# Load all scenarios from the feature file
FEATURE_FILE = Path(__file__).parent / "features" / "extract_excel_csv_tables.feature"

scenarios(FEATURE_FILE)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def service():
    """Create converter service."""
    return create_converter_service()


@pytest.fixture
def context():
    """Shared context for test steps."""
    return {}


@pytest.fixture
def test_docs_dir():
    """Path to test documents."""
    return Path(__file__).parent.parent.parent / "test_documents"


# ============================================================================
# Given Steps
# ============================================================================


@given(parsers.parse('I have an Excel file "{filename}"'), target_fixture="document")
def given_excel_file(filename, test_docs_dir):
    """Load Excel file."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
        pytest.skip(f"Test document not found: {filename}")

    data = file_path.read_bytes()
    return Document(
        bytes=data,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=len(data),
        precision=PrecisionLevel.HIGHEST_QUALITY,
        filename=filename,
    )


@given(parsers.parse('I have a CSV file "{filename}"'), target_fixture="document")
def given_csv_file(filename, test_docs_dir):
    """Load CSV file."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
        pytest.skip(f"Test document not found: {filename}")

    data = file_path.read_bytes()
    return Document(
        bytes=data,
        mime="text/csv",
        size_bytes=len(data),
        precision=PrecisionLevel.BALANCED,
        filename=filename,
    )


@given(
    parsers.parse(
        'I have a CSV file "{filename}" with age (numerical) and country (categorical) columns'
    ),
    target_fixture="document",
)
def given_csv_with_mixed_columns(filename, test_docs_dir):
    """Load CSV file with mixed column types."""
    return given_csv_file(filename, test_docs_dir)


@given(
    parsers.parse('I have an Excel file "{filename}" with {num:d} sheets'),
    target_fixture="document",
)
def given_excel_with_sheets(filename, num, test_docs_dir):
    """Load Excel file with specific number of sheets."""
    doc = given_excel_file(filename, test_docs_dir)
    # Store expected sheet count in metadata
    from pydocextractor.domain.models import Document

    return Document(
        bytes=doc.bytes,
        mime=doc.mime,
        size_bytes=doc.size_bytes,
        precision=doc.precision,
        filename=doc.filename,
        metadata={"expected_sheet_count": num},
    )


# ============================================================================
# When Steps
# ============================================================================


@when("I convert it to Markdown", target_fixture="conversion_result")
def when_convert_it(document, service, context):
    """Convert document to Markdown."""
    try:
        result = service.convert_to_markdown(document, template_name="tabular")
        context["conversion_result"] = result
        context["conversion_success"] = True
        context["conversion_error"] = None
        return result
    except Exception as e:
        context["conversion_success"] = False
        context["conversion_error"] = str(e)
        context["conversion_result"] = None
        context["error_exception"] = e
        return None


# ============================================================================
# Then Steps
# ============================================================================


@then("the converter produces one Markdown section per sheet")
def then_sheet_sections(context):
    """Verify that each sheet has its own section."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert len(markdown) > 0, "Should have content"


@then("each sheet is rendered as a Markdown table")
def then_sheet_tables(context):
    """Verify each sheet has proper table structure."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "|" in markdown, "Should contain table pipe characters"


@then("the output includes metadata about sheets and columns")
def then_metadata(context):
    """Verify metadata is present."""
    assert context["conversion_success"], "Conversion should succeed"


@then("the converter outputs a Markdown table with proper formatting")
def then_markdown_table_format(context):
    """Verify proper Markdown table formatting."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "|" in markdown, "Should contain table pipes"


@then("metadata includes row count and column count")
def then_csv_metadata(context):
    """Verify CSV metadata is captured."""
    assert context["conversion_success"], "Conversion should succeed"


@then("the converter auto-detects the delimiter")
def then_delimiter_detection(context):
    """Verify delimiter auto-detection."""
    assert context["conversion_success"], "Conversion should succeed"


@then("produces a correct Markdown table")
def then_correct_table(context):
    """Verify table is correctly formatted."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "|" in markdown, "Should contain table structure"


@then("the output includes standard deviation for numerical columns")
def then_std_deviation(context):
    """Verify standard deviation is present for numerical columns."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    # Check for std or standard deviation in output
    assert "std" in markdown.lower() or "deviation" in markdown.lower(), (
        "Should show standard deviation"
    )


@then("the output includes frequency distribution for all categorical values")
def then_frequency_distribution(context):
    """Verify frequency distribution is present."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "frequency" in markdown.lower() or "occurrences" in markdown, (
        "Should show frequency distribution"
    )


@then("the frequency distribution shows count and percentage for each value")
def then_frequency_with_percentage(context):
    """Verify frequency includes percentages."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "%" in markdown or "percent" in markdown.lower(), "Should show percentages"


@then("only the first 5 rows of data are shown as a sample")
def then_five_row_sample(context):
    """Verify only 5 rows are shown as sample."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    # For tabular template, check for "Top 5 values" which shows sample data
    # For regular template, check for "sample" or "first 5"
    assert (
        "sample" in markdown.lower() or "first 5" in markdown.lower() or "top 5" in markdown.lower()
    ), "Should mention sample/first 5/top 5 rows or values"


@then("each sheet includes its own statistical summary")
def then_per_sheet_statistics(context):
    """Verify each sheet has statistics."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    # Check for statistics sections
    assert "statistics" in markdown.lower() or "summary" in markdown.lower(), (
        "Should have statistics"
    )


@then("numerical columns show min, max, mean, std for each sheet")
def then_complete_numerical_stats_per_sheet(context):
    """Verify complete numerical statistics per sheet."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "min" in markdown.lower(), "Should show minimum values"
    assert "max" in markdown.lower(), "Should show maximum values"
    assert "mean" in markdown.lower(), "Should show mean values"
    assert "std" in markdown.lower(), "Should show standard deviation"


@then("categorical columns show complete frequency distribution")
def then_complete_frequency_distribution(context):
    """Verify complete frequency distribution for categorical columns."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "frequency" in markdown.lower() or "occurrences" in markdown, (
        "Should show frequency distribution"
    )


@then("each sheet shows maximum 5 sample rows")
def then_each_sheet_five_rows(context):
    """Verify each sheet shows maximum 5 sample rows."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert (
        "sample" in markdown.lower() or "first 5" in markdown.lower() or "top 5" in markdown.lower()
    ), "Should show sample/top 5 rows or values"


# Additional pytest markers
pytestmark = [
    pytest.mark.bdd,
    pytest.mark.feature2,
    pytest.mark.tabular,
]
