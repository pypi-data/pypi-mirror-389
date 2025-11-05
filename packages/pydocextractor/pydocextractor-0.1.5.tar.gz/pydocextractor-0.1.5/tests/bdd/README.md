# BDD Tests with pytest-bdd

Behavior-Driven Development tests using Gherkin feature files and pytest-bdd.

## Structure

```
tests/bdd/
├── features/                               # Gherkin feature files
│   ├── extract_pdf_word_to_markdown.feature    # Feature 1: PDF/Word → Markdown
│   ├── extract_excel_csv_tables.feature        # Feature 2: Excel/CSV → Tables
│   └── extract_documents_with_tables.feature   # Feature 3: Mixed content
├── steps/                                  # Step definitions
│   ├── common_steps.py                        # Shared steps (Given/When/Then)
│   └── pdf_word_steps.py                      # Feature 1-specific steps
├── conftest.py                            # BDD-specific fixtures
├── test_pdf_word_extraction.py           # Test runner for Feature 1
├── test_excel_csv_extraction.py          # Test runner for Feature 2
└── test_documents_with_tables.py         # Test runner for Feature 3
```

## Features

### Feature 1: Extract PDF and Word to Markdown

Tests conversion of textual documents (PDF, DOCX) to clean Markdown.

**Scenarios:**
- Convert text-based PDF to Markdown
- Convert Word document (DOCX) to Markdown
- Normalize whitespace and special characters
- Reject unreadable or unsupported documents

**Tags:** `@happy_path`, `@pdf`, `@docx`, `@formatting`, `@error_handling`

### Feature 2: Extract Excel and CSV Tables

Tests conversion of tabular files (Excel, CSV) to Markdown tables.

**Scenarios:**
- Convert multi-sheet Excel workbook to Markdown
- Convert CSV file to Markdown table
- Handle CSV dialects and encodings
- Truncate extremely wide tables
- Fail gracefully on malformed files

**Tags:** `@happy_path`, `@xlsx`, `@csv`, `@dialect_detection`, `@data_cleaning`

### Feature 3: Extract Documents with Embedded Tables

Tests conversion of documents containing both tables and surrounding text.

**Scenarios:**
- Convert PDF with tables and descriptive paragraphs
- Convert DOCX with mixed content (text + tables + images)
- Verify consistency between table text and narrative
- Handle edge cases in embedded tables
- Emit validation artifacts for QA

**Tags:** `@pdf_with_tables`, `@docx_with_tables`, `@integrity`, `@edge_cases`, `@validation`

## Running BDD Tests

```bash
# Run all BDD tests
pytest tests/bdd/ -v

# Run specific feature
pytest tests/bdd/test_pdf_word_extraction.py -v

# Run by tag
pytest tests/bdd/ -m "happy_path" -v
pytest tests/bdd/ -m "pdf" -v
pytest tests/bdd/ -m "error_handling" -v

# Run specific scenario
pytest tests/bdd/ -k "Convert a text-based PDF" -v

# Show step definitions
pytest tests/bdd/ --collect-only

# Generate BDD report (requires pytest-bdd-html)
pytest tests/bdd/ --html=report.html --self-contained-html
```

## Tags and Markers

- `@bdd` - All BDD tests
- `@feature1` - Feature 1 tests
- `@feature2` - Feature 2 tests
- `@feature3` - Feature 3 tests
- `@happy_path` - Happy path scenarios
- `@error_handling` - Error handling scenarios
- `@slow` - Slow-running tests

## Writing New Steps

Step definitions use pytest-bdd decorators:

```python
from pytest_bdd import given, when, then, parsers

@given("the service is running")
def service_running(context):
    context["service_status"] = "running"

@when(parsers.parse('I upload "{filename}"'))
def upload_file(filename: str, context):
    context["uploaded_file"] = filename

@then(parsers.parse('the result should contain "{text}"'))
def verify_result(text: str, context):
    assert text in context["result"]
```

## Context Sharing

The `context` fixture provides a shared dictionary for passing data between steps:

```python
# Given step
context["document"] = Document(...)

# When step
result = service.convert(context["document"])
context["result"] = result

# Then step
assert context["result"].quality > 0.8
```

## Test Documents

BDD tests use real documents from `test_documents/`:
- `Company_Handbook.pdf` - Multi-page PDF
- `Policy_Report.pdf` - PDF with tables
- `Sales_2025.xlsx` - Excel workbook
- `customers.csv` - CSV file
- Various other CSV/TSV files

## Dependencies

- `pytest>=8.0.0`
- `pytest-bdd>=7.0.0`
- `pytest-cov>=4.0.0`

Install with:
```bash
uv sync --all-extras --group dev
```

## Benefits of BDD Tests

1. **Business-Readable**: Feature files use natural language (Gherkin)
2. **Specification**: Serves as living documentation
3. **Collaboration**: Business analysts can write/review scenarios
4. **Traceability**: Maps requirements to test cases
5. **Reusability**: Step definitions are reused across scenarios
6. **Coverage**: Ensures user stories are tested

## Integration with CI/CD

```yaml
# Example GitHub Actions workflow
- name: Run BDD Tests
  run: |
    uv run pytest tests/bdd/ -v --junitxml=bdd-results.xml

- name: Publish BDD Results
  uses: EnricoMi/publish-unit-test-result-action@v2
  with:
    files: bdd-results.xml
```

## References

- [pytest-bdd Documentation](https://pytest-bdd.readthedocs.io/)
- [Gherkin Reference](https://cucumber.io/docs/gherkin/reference/)
- [Hexagonal Architecture Tests](../README.md)
