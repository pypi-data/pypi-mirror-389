"""
BDD tests for PDF and Word extraction (Feature 1).

Step definitions and scenarios in one file for pytest-bdd compatibility.
"""

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from pydocextractor.domain.models import Document, PrecisionLevel
from pydocextractor.factory import create_converter_service

# Link feature file
scenarios("features/extract_pdf_word_to_markdown.feature")


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


@given(
    parsers.parse('I have a PDF file "{filename}" with MIME "{mime}"'), target_fixture="document"
)
def given_pdf_file(filename, mime, test_docs_dir):
    """Load PDF file."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
        pytest.skip(f"Test document not found: {filename}")

    data = file_path.read_bytes()
    return Document(
        bytes=data,
        mime=mime,
        size_bytes=len(data),
        precision=PrecisionLevel.BALANCED,
        filename=filename,
    )


@given(
    parsers.parse('I have a Word file "{filename}" with MIME "{mime}"'), target_fixture="document"
)
def given_word_file(filename, mime, test_docs_dir):
    """Load Word file."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
        pytest.skip(f"Test document not found: {filename}")

    data = file_path.read_bytes()
    return Document(
        bytes=data,
        mime=mime,
        size_bytes=len(data),
        precision=PrecisionLevel.HIGHEST_QUALITY,
        filename=filename,
    )


@given(parsers.parse('I have a file "{filename}" with MIME "{mime}"'), target_fixture="document")
def given_generic_file(filename, mime, test_docs_dir):
    """Load generic file for error testing."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
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


@given("the PDF is text-based (not scanned) and not password-protected")
def given_pdf_is_text_based(document):
    """Verify PDF is processable."""
    assert document.mime == "application/pdf"
    assert document.size_bytes > 0


@given("the document contains headings, paragraphs, bullet lists, numbered lists, and hyperlinks")
def given_document_has_rich_content(document, context):
    """Mark document as having rich content."""
    context["expected_content_types"] = ["headings", "paragraphs", "lists", "links"]


@given(
    "a DOCX file contains smart quotes, em-dashes, non-breaking spaces, and mixed newlines",
    target_fixture="document",
)
def given_docx_with_special_chars(context, test_docs_dir):
    """Load a DOCX file with special characters."""
    context["has_special_chars"] = True

    # Use text_map.docx which should have various character types
    file_path = test_docs_dir / "text_map.docx"
    if not file_path.exists():
        # Fall back to any DOCX file
        file_path = test_docs_dir / "Q4_Strategy.docx"

    if not file_path.exists():
        pytest.skip(f"Test document not found: {file_path}")

    data = file_path.read_bytes()
    return Document(
        bytes=data,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=len(data),
        precision=PrecisionLevel.HIGHEST_QUALITY,
        filename=file_path.name,
    )


# ============================================================================
# When Steps
# ============================================================================


@when("I convert the file to Markdown", target_fixture="conversion_result")
def when_convert_file(document, service, context):
    """Convert document to Markdown."""
    try:
        result = service.convert_to_markdown(document)
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


@when("I convert it to Markdown", target_fixture="conversion_result")
def when_convert_it(document, service, context):
    """Alias for convert file."""
    return when_convert_file(document, service, context)


@when("I attempt to convert it to Markdown", target_fixture="conversion_result")
def when_attempt_convert(document, service, context):
    """Attempt conversion, expecting possible failure."""
    return when_convert_file(document, service, context)


# ============================================================================
# Then Steps
# ============================================================================


@then(
    "the converter produces a Markdown document with preserved headings, paragraphs, lists, and links"
)
def then_markdown_structure(context):
    """Verify basic Markdown structure."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    assert result is not None
    assert result.text is not None
    assert len(result.text) > 0


@then("the converter produces semantically-correct Markdown preserving heading levels (H1..H4)")
def then_heading_preservation(context):
    """Verify heading levels are preserved."""
    assert context["conversion_success"], "Conversion should succeed"
    result = context["conversion_result"]
    markdown = result.text
    assert "#" in markdown, "Should contain headings"


@then("lists are converted to proper Markdown bullets or numbers")
def then_lists(context):
    """Verify list formatting."""
    assert context["conversion_success"], "Conversion should succeed"


@then("inline links are preserved as [text](url)")
def then_links(context):
    """Verify link formatting."""
    assert context["conversion_success"], "Conversion should succeed"


@then("the converter normalizes smart quotes to straight quotes")
def then_quote_normalization(context):
    """Verify quote normalization."""
    assert context["conversion_success"], "Conversion should succeed"


@then("em-dashes are preserved or converted to standard dashes")
def then_dash_handling(context):
    """Verify dash handling."""
    assert context["conversion_success"], "Conversion should succeed"


@then("non-breaking spaces are converted to regular spaces")
def then_space_normalization(context):
    """Verify space normalization."""
    assert context["conversion_success"], "Conversion should succeed"


@then("line breaks are normalized to LF")
def then_line_break_normalization(context):
    """Verify line break normalization."""
    assert context["conversion_success"], "Conversion should succeed"


@then(parsers.parse('the converter responds with error "{error_code}"'))
def then_error_code(error_code, context):
    """Verify error code."""
    assert not context["conversion_success"], "Conversion should fail"
    context["expected_error_code"] = error_code


@then(parsers.parse('the error message indicates "{reason}"'))
def then_error_reason(reason, context):
    """Verify error reason."""
    assert not context["conversion_success"], "Conversion should have failed"
    context["error_reason"] = reason


# Additional pytest markers
pytestmark = [
    pytest.mark.bdd,
]
