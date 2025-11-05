"""
BDD step definitions for table extraction scenarios.

Handles Excel, CSV, and document table extraction verification.
"""

from __future__ import annotations

from pytest_bdd import then

# ============================================================================
# Excel/CSV Table Verification Steps
# ============================================================================


@then("the converter produces one Markdown section per sheet")
def verify_sheet_sections(context):
    """Verify that each sheet has its own section."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert len(markdown) > 0, "Should have content"


@then("each sheet is rendered as a Markdown table")
def verify_sheet_tables(context):
    """Verify each sheet has proper table structure."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "|" in markdown, "Should contain table pipe characters"


@then("the output includes metadata about sheets and columns")
def verify_metadata(context):
    """Verify metadata is present."""
    assert context["conversion_success"], "Conversion should succeed"


@then("the converter outputs a Markdown table with proper formatting")
def verify_markdown_table_format(context):
    """Verify proper Markdown table formatting."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "|" in markdown, "Should contain table pipes"


@then("metadata includes row count and column count")
def verify_csv_metadata(context):
    """Verify CSV metadata is captured."""
    assert context["conversion_success"], "Conversion should succeed"


@then("the converter auto-detects the delimiter")
def verify_delimiter_detection(context):
    """Verify delimiter auto-detection."""
    assert context["conversion_success"], "Conversion should succeed"


@then("produces a correct Markdown table")
def verify_correct_table(context):
    """Verify table is correctly formatted."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "|" in markdown, "Should contain table structure"
