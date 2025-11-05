# Testing Guide

## Test Organization

pyDocExtractor follows a structured testing approach with different test categories:

```
tests/
├── unit/              # Fast unit tests (domain + app layer, mocked)
│   ├── domain/       # Pure domain logic tests
│   ├── app/          # Application service tests (mocked)
│   └── infra/        # Infrastructure unit tests
├── adapters/         # Adapter/infrastructure tests (real implementations)
├── contract/         # Protocol compliance tests
├── integration/      # End-to-end integration tests
└── bdd/              # BDD tests with Gherkin scenarios
```

## Test Commands

### Quick Commands (For Development)

These run focused test subsets and are **fast**:

```bash
just test-unit        # Unit tests only (domain + app) - ~229 tests
just test-bdd         # BDD tests only - ~20+ tests
just test-integration # Integration tests only
just test-adapters    # Adapter tests (infrastructure)
just test-contract    # Contract/protocol tests
```

### Full Test Suite

```bash
just test            # ALL tests (~280+ tests)
just test-cov        # All tests with coverage report
```

## Current Test Status

### ✅ Passing Test Suites

- **Unit Tests** (`just test-unit`): All 229 tests pass
- **BDD Tests** (`just test-bdd`): All BDD scenarios pass

### ⚠️ Known Issues in Full Suite

When running `just test` (all tests), you may see failures in:

1. **Adapter Tests** (`tests/adapters/`):
   - `processing_time` attribute issues
   - PyMuPDF4LLM BytesIO compatibility issues
   - Docling `has_tables` flag not set correctly

2. **Contract Tests** (`tests/contract/`):
   - Protocol runtime checking issues
   - Missing `@runtime_checkable` decorator on Protocols
   - Document immutability issues (`_replace` not available)

## Test Descriptions

### Unit Tests (`tests/unit/`)

**Purpose**: Test business logic in isolation without external dependencies.

**Characteristics**:
- Fast (no I/O, no real extractors)
- Use mocks for dependencies
- Test domain models, rules, and application service logic

**Run**:
```bash
just test-unit        # All unit tests
just test-unit-coverage  # With coverage report
```

**Example Tests**:
- Domain model validation
- Business rule logic
- Service orchestration (with mocked extractors)

### Adapter Tests (`tests/adapters/`)

**Purpose**: Test infrastructure adapters with real libraries.

**Characteristics**:
- Use real extractor libraries (PyMuPDF, pandas, etc.)
- Test with actual documents
- Slower than unit tests

**Run**:
```bash
just test-adapters
```

**Example Tests**:
- PDF extraction with PyMuPDF4LLM
- CSV parsing with pandas
- Excel multi-sheet extraction

**Known Issues**:
- Some tests expect `processing_time` but get `processing_time_seconds`
- PyMuPDF4LLM needs file paths, not BytesIO
- Docling metadata issues

### Contract Tests (`tests/contract/`)

**Purpose**: Verify that implementations comply with Protocol interfaces.

**Characteristics**:
- Test Protocol compliance
- Verify extractors implement required methods
- Test factory returns correct types

**Run**:
```bash
just test-contract
```

**Example Tests**:
- Extractor implements Protocol correctly
- Policy implements Protocol correctly
- Service uses Protocol types

**Known Issues**:
- Protocols need `@runtime_checkable` decorator for `isinstance()` checks
- Document dataclass is immutable (no `_replace()` method)

### Integration Tests (`tests/integration/`)

**Purpose**: End-to-end tests of the complete conversion pipeline.

**Characteristics**:
- Use real documents
- Test full conversion flow
- Test multiple extractors together

**Run**:
```bash
just test-integration
```

**Example Tests**:
- Convert PDF end-to-end
- Quality scoring integration
- Template rendering with real data

### BDD Tests (`tests/bdd/`)

**Purpose**: Behavior-driven tests using Gherkin scenarios.

**Characteristics**:
- Written in Gherkin (Given/When/Then)
- Test user-facing features
- Readable by non-technical stakeholders

**Run**:
```bash
just test-bdd                      # All BDD tests
just test-bdd-feature FEATURE      # Specific feature
just test-bdd-scenario "SCENARIO"  # Specific scenario
```

**Example Scenarios**:
```gherkin
Scenario: Convert a text-based PDF to Markdown
  Given I have a PDF file "Company_Handbook.pdf"
  When I submit the file for extraction
  Then the service produces a Markdown document
  And a content ID is generated and returned
```

## Development Workflow

### During Development (Fast Feedback)

Run focused tests while developing:

```bash
# Test domain logic changes
just test-unit

# Test BDD scenarios
just test-bdd

# Test specific extractor
uv run pytest tests/adapters/test_extractors.py::TestPandasCSVExtractor -v
```

### Before Committing

Run pre-commit checks:

```bash
just pre-commit  # fmt + check + test-unit + test-contract
```

This runs:
- Code formatting
- Quality checks
- Unit tests
- Contract tests

### Before Pushing

Run full CI locally:

```bash
just ci  # check + test-cov + guard
```

### Full Test Suite

When you want to run everything:

```bash
just test         # All tests (may have some failures)
just test-cov     # All tests with coverage
```

## Understanding Test Failures

### Why `just test` Fails but `just test-unit` Passes

**Answer**: `just test` runs ALL test directories including `tests/adapters/` and `tests/contract/`, which have known issues. `just test-unit` only runs `tests/unit/` which are all passing.

This is **expected behavior** - the full suite reveals real issues that need fixing.

### Should I Fix the Failing Tests?

**Yes, eventually**. The failing tests indicate:
1. **API inconsistencies**: `processing_time` vs `processing_time_seconds`
2. **Missing Protocol decorators**: Need `@runtime_checkable`
3. **Extractor compatibility**: PyMuPDF4LLM file handling
4. **Metadata issues**: Docling not setting `has_tables` correctly

### Can I Ignore the Failures?

**For development**: Yes, use `just test-unit` and `just test-bdd` for fast feedback.

**For production/CI**: No, the full suite should pass. Fix the issues or mark as `pytest.mark.skip` with reason.

## Fixing Common Test Issues

### Issue 1: `processing_time` AttributeError

**Problem**: Tests expect `result.processing_time` but model has `processing_time_seconds`.

**Fix**: Update test assertions:
```python
# Old
assert hasattr(result, 'processing_time')

# New
assert hasattr(result, 'processing_time_seconds')
assert result.processing_time_seconds >= 0
```

### Issue 2: Protocol Runtime Checking

**Problem**: `isinstance(obj, Protocol)` fails without `@runtime_checkable`.

**Fix**: Add decorator to Protocols:
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Extractor(Protocol):
    ...
```

### Issue 3: Document Immutability

**Problem**: `Document` is a frozen dataclass, no `_replace()` method.

**Fix**: Use `dataclasses.replace()`:
```python
from dataclasses import replace

# Old
doc = sample_document._replace(bytes=data)

# New
doc = replace(sample_document, bytes=data, size_bytes=len(data))
```

### Issue 4: PyMuPDF4LLM Needs File Paths

**Problem**: PyMuPDF4LLM can't handle BytesIO objects directly.

**Fix**: Write to temp file:
```python
import tempfile

with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
    tmp.write(data)
    tmp_path = tmp.name

result = extractor.extract(data, precision)
os.unlink(tmp_path)
```

## Test Coverage

Target coverage: **70% minimum** (currently ~88%)

Check coverage:
```bash
just test-cov              # Generate HTML report
just coverage-check        # Verify 70% threshold
open htmlcov/index.html    # View report
```

## Writing New Tests

### Unit Test Example

```python
# tests/unit/domain/test_models.py
def test_document_validates_size():
    with pytest.raises(ValueError, match="size must be positive"):
        Document(
            bytes=b"test",
            mime="application/pdf",
            size_bytes=-1
        )
```

### Adapter Test Example

```python
# tests/adapters/test_extractors.py
def test_csv_extraction(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("col1,col2\nval1,val2\n")

    extractor = PandasCSVExtractor()
    data = csv_file.read_bytes()

    result = extractor.extract(data, PrecisionLevel.HIGHEST_QUALITY)

    assert result.success
    assert result.normalized_doc.has_tables
```

### BDD Test Example

```gherkin
# tests/bdd/features/conversion.feature
Scenario: Convert CSV to Markdown
  Given I have a CSV file "sales.csv"
  When I convert the file with tabular template
  Then the output contains statistical summaries
  And the output includes column types
```

## Continuous Integration

The CI pipeline runs:

```yaml
# .github/workflows/ci.yml
- Format check: ruff format --check
- Lint: ruff check
- Type check: mypy
- Architecture guard: lint-imports
- Tests: pytest with coverage
```

## Summary

| Command | What It Tests | Speed | Status |
|---------|---------------|-------|--------|
| `just test-unit` | Domain + App (mocked) | ⚡ Fast | ✅ All pass |
| `just test-bdd` | BDD scenarios | 🔄 Medium | ✅ All pass |
| `just test-adapters` | Infrastructure adapters | 🐌 Slow | ⚠️ Some fail |
| `just test-contract` | Protocol compliance | ⚡ Fast | ⚠️ Some fail |
| `just test-integration` | End-to-end | 🐌 Slow | ✅ Most pass |
| `just test` | **ALL tests** | 🐢 Slowest | ⚠️ Some fail |

**Recommendation**: Use `just test-unit` and `just test-bdd` during development for fast feedback. Fix failing adapter/contract tests before release.

## Related Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [CONTRIBUTING_GUIDE.md](CONTRIBUTING_GUIDE.md#testing-strategy) - Testing strategy
- [../tests/bdd/README.md](../tests/bdd/README.md) - BDD testing guide
