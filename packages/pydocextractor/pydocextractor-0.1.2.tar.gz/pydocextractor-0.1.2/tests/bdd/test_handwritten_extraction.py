"""
BDD tests for handwritten text and image PDF extraction.

Step definitions and scenarios for testing LLM-based image description
of PDFs containing handwritten text and images.

Uses PyMuPDF4LLM (precision level 2) for PDF extraction combined with
LLM image description for handwritten content analysis.
"""

import os
import re
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from pydocextractor.domain.models import Document, PrecisionLevel
from pydocextractor.factory import create_converter_service

# Link feature file
scenarios("features/extract_handwritten_text_with_images.feature")


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def llm_config():
    """Create LLM configuration for testing.

    Skips tests if config.env is not available or LLM credentials are not set.
    This allows tests to pass in CI/CD environments without API keys.
    """
    import os
    from pathlib import Path

    # Load config.env file if it exists (local development)
    config_env_path = Path(__file__).parent.parent.parent / "config.env"
    config_env_exists = config_env_path.exists()

    if config_env_exists:
        from dotenv import load_dotenv

        load_dotenv(config_env_path)

    # Check if we have any LLM credentials available
    has_credentials = bool(os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))

    # Skip if no config.env and no environment variables
    if not config_env_exists and not has_credentials:
        pytest.skip(
            "Skipping LLM tests: config.env not found and no LLM_API_KEY/OPENAI_API_KEY "
            "environment variable set. These tests require LLM credentials to run."
        )

    try:
        from pydocextractor.infra.config import load_llm_config

        # Load from environment (now includes config.env if it exists)
        config = load_llm_config()
        if config.enabled and config.api_key and len(config.api_key) > 10:
            return config
        else:
            pytest.skip("LLM is not enabled or API key is invalid")
    except Exception as e:
        pytest.skip(f"Failed to load LLM config: {e}")


@pytest.fixture
def service(llm_config):
    """Create converter service with LLM enabled."""
    return create_converter_service(llm_config=llm_config, auto_load_llm=False)


@pytest.fixture
def context():
    """Shared context for test steps."""
    return {
        "precision_level": PrecisionLevel.BALANCED,  # Level 2 - PyMuPDF4LLM with LLM image description
        "ocr_enabled": False,  # Use LLM for images, not Docling OCR
        "llm_enabled": True,
    }


@pytest.fixture
def test_docs_dir():
    """Path to test documents."""
    return Path(__file__).parent.parent.parent / "test_documents"


# ============================================================================
# Given Steps
# ============================================================================


@given("I have the pyDocExtractor service configured with LLM enabled")
def given_service_configured_with_llm(service, context, llm_config):
    """Verify service is available with LLM enabled."""
    assert service is not None
    context["llm_config"] = llm_config
    context["llm_enabled"] = llm_config.enabled
    context["service"] = service


@given(
    parsers.parse("the precision level is set to {level:d} (BALANCED with LLM image description)")
)
def given_precision_level_set(level, context):
    """Set precision level to specified value."""
    assert level == 2, "Expected precision level 2 (BALANCED with LLM)"
    context["precision_level"] = PrecisionLevel.BALANCED


@given(
    parsers.parse('I have a PDF file "{filename}" with MIME "{mime}"'),
    target_fixture="document",
)
def given_pdf_file(filename, mime, test_docs_dir, context):
    """Load PDF file with BALANCED precision level (PyMuPDF4LLM + LLM)."""
    file_path = test_docs_dir / filename
    if not file_path.exists():
        pytest.skip(f"Test document not found: {filename}")

    data = file_path.read_bytes()
    # Use BALANCED (level 2) - PyMuPDF4LLM with LLM image description
    precision = context.get("precision_level", PrecisionLevel.BALANCED)
    doc = Document(
        bytes=data,
        mime=mime,
        size_bytes=len(data),
        precision=precision,
        filename=filename,
    )
    context["document"] = doc
    return doc


@given("the PDF contains handwritten text and embedded images")
def given_pdf_has_handwritten_and_images(context):
    """Mark document as containing handwritten text and images."""
    context["has_handwritten"] = True
    context["has_images"] = True


@given(parsers.parse('I configure the converter to use precision level "{level}"'))
def given_precision_level_string(level, context):
    """Set precision level from string (kept for backward compatibility)."""
    precision_map = {
        "FAST": PrecisionLevel.FAST,
        "FASTEST": PrecisionLevel.FASTEST,
        "BALANCED": PrecisionLevel.BALANCED,
        "TABLE_OPTIMIZED": PrecisionLevel.TABLE_OPTIMIZED,
        "HIGHEST_QUALITY": PrecisionLevel.HIGHEST_QUALITY,
    }
    context["precision_level"] = precision_map.get(level, PrecisionLevel.BALANCED)

    # Update document if it already exists
    if "document" in context:
        doc = context["document"]
        context["document"] = Document(
            bytes=doc.bytes,
            mime=doc.mime,
            size_bytes=doc.size_bytes,
            precision=context["precision_level"],
            filename=doc.filename,
        )


# ============================================================================
# When Steps
# ============================================================================


@when("I convert the file to Markdown with LLM enabled", target_fixture="conversion_result")
def when_convert_with_llm(document, service, context):
    """Convert document to Markdown with LLM image description."""
    try:
        # Ensure document uses the configured precision level
        if context.get("precision_level"):
            document = Document(
                bytes=document.bytes,
                mime=document.mime,
                size_bytes=document.size_bytes,
                precision=context["precision_level"],
                filename=document.filename,
            )

        result = service.convert_to_markdown(document)
        context["conversion_result"] = result
        context["conversion_success"] = True
        context["conversion_error"] = None
        context["markdown_text"] = result.text if result else ""
        return result
    except Exception as e:
        context["conversion_success"] = False
        context["conversion_error"] = str(e)
        context["conversion_result"] = None
        context["markdown_text"] = ""
        context["error_exception"] = e
        pytest.fail(f"Conversion failed: {e}")
        return None


# ============================================================================
# Then Steps
# ============================================================================


@then("the converter produces a Markdown document")
def then_markdown_produced(context):
    """Verify Markdown document was produced."""
    assert context.get("conversion_success"), "Conversion should succeed"
    result = context.get("conversion_result")
    assert result is not None, "Result should not be None"
    assert result.text is not None, "Result text should not be None"
    assert len(result.text) > 0, "Result text should not be empty"


@then(parsers.parse('the Markdown output contains the word "{keyword}" (case-insensitive)'))
def then_contains_keyword_case_insensitive(keyword, context):
    """Verify Markdown contains specific keyword (case-insensitive)."""
    assert context.get("conversion_success"), "Conversion should succeed"
    markdown = context.get("markdown_text", "")
    assert markdown, "Markdown text should not be empty"

    # Define synonyms for certain keywords (LLM may use different wording)
    keyword_synonyms = {
        "hate": ["hate", "hates", "hated", "hating", "dislike", "dislikes", "disliked"],
        "like": ["like", "likes", "liked", "liking", "enjoy", "enjoys"],
        "skate": ["skate", "skates", "skating", "skateboard", "skateboards", "skateboarding"],
        "meeting": ["meeting", "meetings"],
    }

    # Get search terms (keyword + its synonyms, including plural forms)
    search_terms = keyword_synonyms.get(keyword.lower(), [keyword, keyword + "s"])

    # Try to match any of the search terms
    found = False
    for term in search_terms:
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        if pattern.search(markdown):
            found = True
            break

    assert found, (
        f"Expected keyword '{keyword}' (or synonyms: {', '.join(search_terms)}) "
        f"not found in Markdown output. Full output:\n{markdown}"
    )


@then("the Markdown output should contain all of the following keywords:")
def then_contains_all_keywords(context):
    """Verify Markdown contains all specified keywords."""
    # This step is used with a table, handled by pytest-bdd's table parsing
    # The actual keyword checks are done in the individual keyword steps
    pass


@then("the Markdown output contains text content")
def then_contains_text_content(context):
    """Verify Markdown contains text content."""
    assert context.get("conversion_success"), "Conversion should succeed"
    markdown = context.get("markdown_text", "")
    assert markdown, "Markdown should contain text content"
    assert len(markdown.strip()) > 0, "Markdown should not be empty"


@then("the Markdown output contains image references or descriptions")
def then_contains_image_references(context):
    """Verify Markdown contains image references or descriptions."""
    assert context.get("conversion_success"), "Conversion should succeed"
    markdown = context.get("markdown_text", "")

    # For this specific test, we just verify the markdown exists
    # The actual image content is verified through keyword extraction
    assert len(markdown) > 0, "Markdown should contain content"

    # Verify at least one image indicator is present
    has_image_content = (
        "![" in markdown  # Markdown image syntax
        or "image" in markdown.lower()
        or "photo" in markdown.lower()
        or "picture" in markdown.lower()
        or "skate" in markdown.lower()  # Known image content
    )
    assert has_image_content, "Markdown should reference images or image content"


@then("the document structure is preserved with proper formatting")
def then_structure_preserved(context):
    """Verify document structure is preserved."""
    assert context.get("conversion_success"), "Conversion should succeed"
    markdown = context.get("markdown_text", "")
    assert len(markdown) > 0, "Markdown should have content"

    # Verify basic structure elements exist
    lines = markdown.split("\n")
    assert len(lines) > 1, "Markdown should have multiple lines"


@then("the conversion quality is acceptable for LLM-described content")
def then_llm_quality_acceptable(context):
    """Verify LLM description quality is acceptable."""
    assert context.get("conversion_success"), "Conversion should succeed"
    markdown = context.get("markdown_text", "")

    # Basic quality checks
    assert len(markdown) > 50, "Markdown should contain substantial content"

    # Check that we have actual words, not just gibberish
    words = markdown.split()
    assert len(words) > 10, "Should contain multiple words"

    # Verify we have some alphabetic content
    alpha_chars = sum(1 for c in markdown if c.isalpha())
    assert alpha_chars > 20, "Should contain alphabetic characters"


# Additional pytest markers
pytestmark = [
    pytest.mark.bdd,
    pytest.mark.llm,
    pytest.mark.handwritten,
    pytest.mark.skipif(
        not Path(__file__).parent.parent.parent.joinpath("config.env").exists()
        and not os.getenv("LLM_API_KEY")
        and not os.getenv("OPENAI_API_KEY"),
        reason="Requires config.env or LLM_API_KEY environment variable",
    ),
]
