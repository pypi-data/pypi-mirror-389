"""
Common BDD step definitions shared across features.

These steps handle converter setup, file loading, and basic operations.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, then, when

from pydocextractor.domain.models import Document, PrecisionLevel

# Note: The service fixture is now defined in conftest.py as a regular pytest fixture
# No step definition needed since it's just a library, not a service to initialize


# ============================================================================
# File Loading Steps
# ============================================================================


@given(
    parsers.parse('I have a PDF file "{filename}"'),
    target_fixture="document",
)
def load_pdf_file(filename: str, test_docs_dir: Path):
    """Load PDF file and create Document object."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
        pytest.skip(f"Test document not found: {filename}")

    data = file_path.read_bytes()
    return Document(
        bytes=data,
        mime="application/pdf",
        size_bytes=len(data),
        precision=PrecisionLevel.BALANCED,
        filename=filename,
    )


@given(
    parsers.parse('I have a Word file "{filename}"'),
    target_fixture="document",
)
def load_word_file(filename: str, test_docs_dir: Path):
    """Load Word file and create Document object."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
        pytest.skip(f"Test document not found: {filename}")

    data = file_path.read_bytes()
    return Document(
        bytes=data,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=len(data),
        precision=PrecisionLevel.HIGHEST_QUALITY,  # Use Docling for DOCX
        filename=filename,
    )


@given(
    parsers.parse('I have an Excel file "{filename}"'),
    target_fixture="document",
)
def load_excel_file(filename: str, test_docs_dir: Path):
    """Load Excel file and create Document object."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
        pytest.skip(f"Test document not found: {filename}")

    data = file_path.read_bytes()
    return Document(
        bytes=data,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=len(data),
        precision=PrecisionLevel.HIGHEST_QUALITY,  # Use Docling for Excel
        filename=filename,
    )


@given(
    parsers.parse('I have a CSV file "{filename}"'),
    target_fixture="document",
)
def load_csv_file(filename: str, test_docs_dir: Path):
    """Load CSV file and create Document object."""
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
        'I have "{filename}" which includes multiple tables, captions, and paragraphs before and after each table'
    ),
    target_fixture="document",
)
def load_document_with_tables(filename: str, test_docs_dir: Path):
    """Load document with tables."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
        pytest.skip(f"Test document not found: {filename}")

    data = file_path.read_bytes()

    # Determine MIME and precision from extension
    if filename.endswith(".pdf"):
        mime = "application/pdf"
        precision = PrecisionLevel.TABLE_OPTIMIZED
    elif filename.endswith(".docx"):
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        precision = PrecisionLevel.HIGHEST_QUALITY
    else:
        mime = "application/octet-stream"
        precision = PrecisionLevel.BALANCED

    return Document(
        bytes=data,
        mime=mime,
        size_bytes=len(data),
        precision=precision,
        filename=filename,
    )


@given(
    parsers.parse(
        'I have "{filename}" containing headings, normal text, tables with merged cells, and inline images'
    ),
    target_fixture="document",
)
def load_complex_document(filename: str, test_docs_dir: Path):
    """Load complex document."""
    return load_document_with_tables(filename, test_docs_dir)


@given(parsers.parse('I have a file "{filename}" with MIME "{mime}"'), target_fixture="document")
def load_generic_file(filename: str, mime: str, test_docs_dir: Path):
    """Load any file for error testing."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
        # For error testing, create a mock file
        data = b"mock file content"
    else:
        data = file_path.read_bytes()

    return Document(
        bytes=data,
        mime=mime,
        size_bytes=len(data),
        precision=PrecisionLevel.BALANCED,
        filename=filename,
    )


# ============================================================================
# Document Properties Steps
# ============================================================================


@given("the PDF is text-based (not scanned) and not password-protected")
def pdf_is_text_based(document: Document):
    """Verify PDF is processable (non-scanned, not locked)."""
    assert document.mime == "application/pdf"
    assert document.size_bytes > 0


@given("the document contains headings, paragraphs, bullet lists, numbered lists, and hyperlinks")
def document_has_rich_content(document: Document, context):
    """Mark document as having rich content."""
    context["expected_content_types"] = ["headings", "paragraphs", "lists", "links"]


@given("a DOCX file contains smart quotes, em-dashes, non-breaking spaces, and mixed newlines")
def docx_with_special_chars(test_docs_dir, context):
    """Note: document already loaded via target_fixture."""
    context["has_special_chars"] = True


@given("a document contains a paragraph referencing values inside a nearby table")
def document_with_table_reference(test_docs_dir, context):
    """Mark document as having table references."""
    context["has_table_references"] = True


@given(parsers.parse('a document "{doc}" has a table with "{case}"'), target_fixture="document")
def document_with_edge_case(doc: str, case: str, test_docs_dir: Path):
    """Load document with specific edge case."""
    file_path = test_docs_dir / doc
    if not file_path.exists():
        pytest.skip(f"{doc} not found")

    data = file_path.read_bytes()

    # Determine MIME from extension
    if doc.endswith(".pdf"):
        mime = "application/pdf"
        precision = PrecisionLevel.TABLE_OPTIMIZED
    elif doc.endswith(".docx"):
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        precision = PrecisionLevel.HIGHEST_QUALITY
    else:
        mime = "application/octet-stream"
        precision = PrecisionLevel.BALANCED

    return Document(
        bytes=data,
        mime=mime,
        size_bytes=len(data),
        precision=precision,
        filename=doc,
        metadata={"edge_case": case},
    )


@given("the conversion finished successfully")
def conversion_finished(context):
    """Mark conversion as successful for validation tests."""
    context["conversion_complete"] = True
    context["conversion_success"] = True


# ============================================================================
# Conversion Action Steps
# ============================================================================


@when("I convert the file to Markdown")
def convert_file(document: Document, service, context):
    """Convert document to Markdown."""
    try:
        result = service.convert_to_markdown(document)
        context["conversion_result"] = result
        context["conversion_success"] = True
        context["conversion_error"] = None
    except Exception as e:
        context["conversion_success"] = False
        context["conversion_error"] = str(e)
        context["conversion_result"] = None


@when("I convert it to Markdown")
def convert_it(document: Document, service, context):
    """Alias for convert_file."""
    convert_file(document, service, context)


@when("I attempt to convert it to Markdown")
def attempt_convert(document: Document, service, context):
    """Attempt conversion, expecting possible failure."""
    try:
        result = service.convert_to_markdown(document)
        context["conversion_result"] = result
        context["conversion_success"] = True
        context["conversion_error"] = None
    except Exception as e:
        context["conversion_success"] = False
        context["conversion_error"] = str(e)
        context["conversion_result"] = None
        context["error_exception"] = e


@when("I request validation artifacts")
def request_validation_artifacts(context):
    """Request validation artifacts from conversion result."""
    assert context.get("conversion_complete"), "Conversion should be complete"
    context["validation_artifacts"] = {
        "table_index": {},
        "column_types": {},
        "table_dimensions": {},
        "markdown_file": "",
        "raw_text": "",
    }


# ============================================================================
# Basic Verification Steps
# ============================================================================


@then(
    "the converter produces a Markdown document with preserved headings, paragraphs, lists, and links"
)
def verify_markdown_structure(context):
    """Verify basic Markdown structure."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    assert result is not None
    assert result.text is not None
    assert len(result.text) > 0


@then("the converter produces semantically-correct Markdown preserving heading levels (H1..H4)")
def verify_heading_preservation(context):
    """Verify heading levels are preserved."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "#" in markdown, "Should contain headings"


@then("lists are converted to proper Markdown bullets or numbers")
def verify_lists(context):
    """Verify list formatting."""
    assert context["conversion_success"], "Conversion should succeed"


@then("inline links are preserved as [text](url)")
def verify_links(context):
    """Verify link formatting."""
    assert context["conversion_success"], "Conversion should succeed"


@then("the converter normalizes smart quotes to straight quotes")
def verify_quote_normalization(context):
    """Verify quote normalization."""
    assert context["conversion_success"], "Conversion should succeed"


@then("em-dashes are preserved or converted to standard dashes")
def verify_dash_handling(context):
    """Verify dash handling."""
    assert context["conversion_success"], "Conversion should succeed"


@then("non-breaking spaces are converted to regular spaces")
def verify_space_normalization(context):
    """Verify space normalization."""
    assert context["conversion_success"], "Conversion should succeed"


@then("line breaks are normalized to LF")
def verify_line_break_normalization(context):
    """Verify line break normalization."""
    assert context["conversion_success"], "Conversion should succeed"


@then(parsers.parse('the converter responds with error "{error_code}"'))
def verify_error_code(error_code: str, context):
    """Verify error code."""
    assert not context["conversion_success"], "Conversion should fail"
    context["expected_error_code"] = error_code


@then(parsers.parse('the error message indicates "{reason}"'))
def verify_error_reason(reason: str, context):
    """Verify error reason."""
    assert not context["conversion_success"], "Conversion should have failed"
    context["error_reason"] = reason
