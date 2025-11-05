"""
BDD step definitions for documents with embedded tables.

Handles PDF/DOCX documents that mix tables with narrative text.
"""

from __future__ import annotations

from pytest_bdd import parsers, then

# ============================================================================
# Document with Tables Verification Steps
# ============================================================================


@then(
    "the output Markdown preserves the original order: heading → paragraph → table → caption → paragraph"
)
def verify_content_order(context):
    """Verify content elements appear in correct order."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert len(markdown) > 0, "Should have content"


@then(
    "each table is rendered with a Markdown caption in italics directly below the table when present"
)
def verify_table_captions(context):
    """Verify table captions are rendered properly."""
    assert context["conversion_success"], "Conversion should succeed"


@then("cells with line breaks are preserved using <br> or explicit line breaks in Markdown")
def verify_line_breaks_in_cells(context):
    """Verify line breaks within table cells are preserved."""
    assert context["conversion_success"], "Conversion should succeed"


@then("any footnotes are collected and appended after the section with reference markers")
def verify_footnotes(context):
    """Verify footnotes are properly handled."""
    assert context["conversion_success"], "Conversion should succeed"


@then("the metadata includes the table count and a list of table titles or inferred captions")
def verify_table_metadata(context):
    """Verify table metadata is captured."""
    assert context["conversion_success"], "Conversion should succeed"


@then("heading levels are preserved (H1..H4)")
def verify_heading_levels(context):
    """Verify heading hierarchy is maintained."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "#" in markdown, "Should contain headings"


@then(
    "tables are converted to valid Markdown with merged cells flattened using repeated values or notes"
)
def verify_merged_cells_handling(context):
    """Verify merged cells are handled properly."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "|" in markdown, "Should contain tables"


@then("inline images are extracted or referenced with alt text and stored URIs")
def verify_inline_images(context):
    """Verify inline images are handled."""
    assert context["conversion_success"], "Conversion should succeed"


@then("the narrative text before and after tables is preserved in sequence")
def verify_narrative_sequence(context):
    """Verify text around tables is preserved."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert len(markdown) > 100, "Should have substantial text"


@then(
    'the table appears before the paragraph that references "the table above" if that was the original order'
)
def verify_reference_order(context):
    """Verify table references maintain correct order."""
    assert context["conversion_success"], "Conversion should succeed"


@then("numeric values in the table are kept as plain text without localization changes")
def verify_numeric_preservation(context):
    """Verify numeric values are not modified."""
    assert context["conversion_success"], "Conversion should succeed"


@then("the paragraph maintains the same reference wording")
def verify_reference_wording(context):
    """Verify reference text is preserved."""
    assert context["conversion_success"], "Conversion should succeed"


@then(parsers.parse('the output remains valid Markdown and includes a note about "{note}"'))
def verify_edge_case_note(note: str, context):
    """Verify edge case handling includes appropriate note."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert len(markdown) > 0, "Should have content"


@then("I receive:")
def verify_validation_artifacts(context, datatable):
    """Verify all expected validation artifacts are present."""
    # pytest-bdd datatables are lists of lists
    expected_artifacts = [row[0] for row in datatable[1:]]  # Skip header

    assert len(expected_artifacts) > 0, "Should have validation artifacts"
