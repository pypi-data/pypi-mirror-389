# pyDocExtractor Contribution Guide

This guide provides detailed information on how to contribute to pyDocExtractor, including architectural principles, common tasks, and best practices.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Folder Structure Reference](#folder-structure-reference)
3. [Common Contribution Tasks](#common-contribution-tasks)
4. [Testing Strategy](#testing-strategy)
5. [Development Tools](#development-tools)

## Architecture Overview

pyDocExtractor follows **Hexagonal Architecture** (Ports and Adapters pattern) with three distinct layers:

```
┌─────────────────────────────────────────────────┐
│           Infrastructure Layer                   │
│  (Extractors, Templates, Scoring, Policy)       │
│                                                  │
│  ┌───────────────────────────────────────────┐ │
│  │      Application Layer                     │ │
│  │  (ConverterService - Orchestration)       │ │
│  │                                            │ │
│  │  ┌─────────────────────────────────────┐ │ │
│  │  │     Domain Layer                     │ │ │
│  │  │  (Models, Ports, Rules, Errors)     │ │ │
│  │  │  Pure Business Logic - No Deps      │ │ │
│  │  └─────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Key Principles

1. **Dependency Rule**: Dependencies point inward only
   - Domain depends on nothing
   - Application depends on Domain (via Protocols)
   - Infrastructure depends on Domain (implements Protocols)

2. **Protocol-Based**: All cross-layer communication uses Protocol interfaces

3. **Testability**: Each layer can be tested independently

4. **Flexibility**: Easy to swap implementations without changing business logic

## Folder Structure Reference

### Complete Directory Map

| Path | Purpose | Dependencies | When to Modify |
|------|---------|--------------|----------------|
| **Domain Layer** | | | |
| `src/pydocextractor/domain/` | Pure business logic | None (stdlib only) | Add new domain concepts |
| `src/pydocextractor/domain/models.py` | Immutable dataclasses:<br/>- `Document`<br/>- `Block` (with optional `image_data`)<br/>- `NormalizedDoc`<br/>- `Markdown`<br/>- `ExtractionResult`<br/>- `PrecisionLevel`<br/>- `BlockType` | None | - Add new document attributes<br/>- Add new block types<br/>- Modify domain models |
| `src/pydocextractor/domain/config.py` | Configuration models:<br/>- `LLMConfig` (optional LLM settings) | None | - Add new configuration models<br/>- Define optional feature configs |
| `src/pydocextractor/domain/ports.py` | Protocol definitions:<br/>- `Extractor`<br/>- `Policy`<br/>- `TemplateEngine`<br/>- `QualityScorer`<br/>- `TableProfiler`<br/>- `ImageDescriber` (optional LLM)<br/>- `Cache` | Domain models only | - Define new port interfaces<br/>- Add methods to protocols<br/>- Create new abstraction types |
| `src/pydocextractor/domain/rules.py` | Pure functions:<br/>- `quality_score()`<br/>- `calculate_document_hash()`<br/>- `normalize_blocks()` | Domain models only | - Add business validation rules<br/>- Add domain calculations<br/>- Add pure transformations |
| `src/pydocextractor/domain/errors.py` | Exception hierarchy:<br/>- `DomainError`<br/>- `ConversionFailed`<br/>- `RecoverableError`<br/>- `UnsupportedFormat` | None | - Add new error types<br/>- Refine error hierarchy |
| **Application Layer** | | | |
| `src/pydocextractor/app/` | Orchestration logic | Domain layer only | Change workflow behavior |
| `src/pydocextractor/app/service.py` | `ConverterService`:<br/>- Main conversion orchestration<br/>- Fallback chain handling<br/>- Quality score calculation<br/>- Optional image enhancement with LLM | Domain ports | - Modify conversion workflow<br/>- Add caching logic<br/>- Change fallback behavior<br/>- Add new service methods |
| `src/pydocextractor/app/image_context.py` | `ImageContextTracker`:<br/>- Tracks text context for images<br/>- Maintains rolling buffer of last N lines | Domain models | - Modify context tracking<br/>- Add context features |
| **Infrastructure Layer** | | | |
| `src/pydocextractor/infra/` | Concrete implementations | Domain + external libs | Add new adapters |
| `src/pydocextractor/infra/extractors/` | Extractor implementations | Domain + extraction libs | **Add new document support** |
| `infra/extractors/chunked_parallel_adapter.py` | ChunkedParallel (Level 1 - FASTEST)<br/>PyMuPDF parallel processing | PyMuPDF | Optimize parallel extraction |
| `infra/extractors/pymupdf4llm_adapter.py` | PyMuPDF4LLM (Level 2 - BALANCED)<br/>LLM-optimized extraction | pymupdf4llm | Improve LLM formatting |
| `infra/extractors/pdfplumber_adapter.py` | PDFPlumber (Level 3 - TABLE_OPTIMIZED)<br/>Superior table extraction | pdfplumber | Enhance table detection |
| `infra/extractors/docling_adapter.py` | Docling (Level 4 - HIGHEST_QUALITY)<br/>PDF/DOCX/Excel support | docling | Add format support |
| `infra/extractors/pandas_csv_adapter.py` | PandasCSV<br/>CSV with statistics | pandas | Add CSV features |
| `infra/extractors/pandas_excel_adapter.py` | PandasExcel<br/>Multi-sheet Excel support | pandas, openpyxl | Add Excel features |
| `src/pydocextractor/infra/policy/` | Selection policies | Domain + extractors | Change auto-selection |
| `infra/policy/heuristics.py` | `DefaultPolicy`:<br/>- Heuristic-based selection<br/>- Fallback chain building | Domain + all extractors | - Modify selection rules<br/>- Add new heuristics<br/>- Change size thresholds<br/>- Add new file type routing |
| `src/pydocextractor/infra/templates/` | Template rendering | Domain + Jinja2 | Add output formats |
| `infra/templates/engines.py` | `Jinja2TemplateEngine`:<br/>- Template rendering<br/>- Custom filters | Jinja2 | - Add template filters<br/>- Customize rendering |
| `infra/templates/templates/` | Jinja2 template files | N/A | **Add new templates** |
| `infra/templates/templates/simple.j2` | Simple markdown template | N/A | Modify default output |
| `infra/templates/templates/tabular.j2` | Tabular data template | N/A | Customize table output |
| `src/pydocextractor/infra/scoring/` | Quality scoring | Domain | Add scoring algorithms |
| `infra/scoring/default_scorer.py` | `DefaultQualityScorer`:<br/>- 0.0-1.0 score calculation<br/>- Multi-factor scoring | Domain models | - Modify quality metrics<br/>- Add scoring criteria<br/>- Change weights |
| `src/pydocextractor/infra/config/` | Configuration loaders | Domain + python-dotenv | Load feature configs |
| `infra/config/env_loader.py` | `load_llm_config()`:<br/>- Loads from config.env or .env<br/>- Graceful fallback on missing config | Domain config models | - Add new config loaders<br/>- Modify env variable names |
| `src/pydocextractor/infra/llm/` | LLM adapters (optional) | Domain + httpx, pillow | Add LLM providers |
| `infra/llm/openai_adapter.py` | `OpenAIImageDescriber`:<br/>- OpenAI-compatible API client<br/>- Image resizing (1024x1024)<br/>- Base64 encoding | httpx, pillow | - Add LLM providers<br/>- Modify image processing |
| `infra/llm/resilient_describer.py` | `ResilientImageDescriber`:<br/>- Retry logic with exponential backoff<br/>- Fallback on failure | Domain + httpx | - Modify retry strategy<br/>- Add resilience features |
| **Entry Points** | | | |
| `src/pydocextractor/factory.py` | Dependency injection:<br/>- `create_converter_service()`<br/>- `get_available_extractors()`<br/>- Component wiring | All layers | - Wire new components<br/>- Add factory methods<br/>- Configure dependencies |
| `src/pydocextractor/cli.py` | CLI interface:<br/>- Convert command<br/>- Batch command<br/>- Status/info commands | Factory + all layers | - Add CLI commands<br/>- Add command options<br/>- Improve CLI UX |
| **Tests** | | | |
| `tests/unit/` | Fast unit tests (no I/O) | Domain + app layers | Test business logic |
| `tests/unit/domain/` | Domain model tests | Domain only | Test models, rules, errors |
| `tests/unit/app/` | Service tests with mocks | Domain + mocked ports | Test orchestration logic |
| `tests/adapters/` | Infrastructure tests | All layers + real libs | Test extractors, templates |
| `tests/contract/` | Protocol compliance tests | Domain ports + infra | Verify protocol implementation |
| `tests/integration/` | End-to-end tests | All layers | Test full workflows |
| `tests/bdd/` | BDD tests (Gherkin) | All layers | Add behavior scenarios |
| `tests/bdd/features/` | Gherkin feature files | N/A | Define user scenarios |
| **Other** | | | |
| `test_documents/` | Sample files for testing | N/A | Add test documents |
| `pyproject.toml` | Project configuration:<br/>- Dependencies<br/>- Build config<br/>- Tool settings | N/A | - Add dependencies<br/>- Configure tools<br/>- Update metadata |
| `justfile` | Command runner recipes | N/A | Add dev commands |
| `.importlinter` | Architecture boundary rules | N/A | Add layer constraints |

## Common Contribution Tasks

### Task 1: Add Support for a New Document Type (e.g., RTF)

**Files to Create/Modify:**

1. **Create Extractor** → `src/pydocextractor/infra/extractors/rtf_adapter.py`
   ```python
   """RTF document extractor using rtf_library."""

   from pydocextractor.domain.models import (
       Block, BlockType, ExtractionResult, NormalizedDoc, PrecisionLevel
   )

   try:
       import rtf_library
       RTF_AVAILABLE = True
   except ImportError:
       RTF_AVAILABLE = False

   class RTFExtractor:
       @property
       def name(self) -> str:
           return "RTF"

       @property
       def precision_level(self) -> PrecisionLevel:
           return PrecisionLevel.BALANCED

       def is_available(self) -> bool:
           return RTF_AVAILABLE

       def supports(self, mime: str) -> bool:
           return mime in ["application/rtf", "text/rtf"] and RTF_AVAILABLE

       def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
           # Implementation here
           pass
   ```

2. **Update Policy** → `src/pydocextractor/infra/policy/heuristics.py`
   ```python
   # Import the new extractor
   from ..extractors.rtf_adapter import RTFExtractor

   class DefaultPolicy:
       def __init__(self) -> None:
           # ... existing code ...

           # Add RTF extractor
           self._rtf_extractor: Extractor | None = None
           rtf_extractor = RTFExtractor()
           if rtf_extractor.is_available():
               self._rtf_extractor = rtf_extractor

       def choose_extractors(self, mime: str, ...) -> Sequence[Extractor]:
           # Add RTF handling
           if mime in ["application/rtf", "text/rtf"] and self._rtf_extractor:
               return tuple([self._rtf_extractor])
           # ... rest of method ...
   ```

3. **Add Dependency** → `pyproject.toml`
   ```toml
   [project.optional-dependencies]
   rtf = ["rtf-library>=1.0.0"]
   all = [
       # ... existing ...
       "rtf-library>=1.0.0",
   ]
   ```

4. **Add Tests** → `tests/adapters/test_extractors.py`
   ```python
   class TestRTFExtractor:
       def test_rtf_extraction(self):
           extractor = RTFExtractor()
           # ... test implementation ...
   ```

5. **Add Sample File** → `test_documents/sample.rtf`

**Commands to Run:**
```bash
just fmt           # Format code
just typecheck     # Verify types
just guard         # Check architecture
just test-adapters # Test your extractor
```

### Task 2: Add a Custom Template

**Files to Create:**

1. **Create Template** → `src/pydocextractor/infra/templates/templates/custom.j2`
   ```jinja2
   {# Custom template example #}
   ---
   title: {{ metadata.filename }}
   extractor: {{ metadata.extractor }}
   quality: {{ quality_score }}
   ---

   # Document: {{ metadata.filename }}

   {% for block in blocks %}
   {% if block.type == 'text' %}
   {{ block.content }}

   {% elif block.type == 'table' %}
   ## Table (Page {{ block.page }})

   {{ block.content }}

   {% endif %}
   {% endfor %}
   ```

**Usage:**
```python
result = service.convert_to_markdown(doc, template_name="custom")
```

### Task 3: Modify Quality Scoring

**Files to Modify:**

1. **Create Custom Scorer** → `src/pydocextractor/infra/scoring/ml_scorer.py`
   ```python
   """ML-based quality scorer."""

   from pydocextractor.domain.models import Document, NormalizedDoc

   class MLQualityScorer:
       def calculate_score(
           self,
           ndoc: NormalizedDoc,
           markdown: str,
           original: Document | None = None,
       ) -> float:
           # Your custom scoring logic
           score = 0.0

           # Add your criteria
           if len(markdown) > 1000:
               score += 0.3

           if ndoc.has_tables:
               score += 0.4

           # ... more criteria ...

           return min(1.0, max(0.0, score))
   ```

**Usage:**
```python
from pydocextractor.infra.scoring.ml_scorer import MLQualityScorer

scorer = MLQualityScorer()
service = ConverterService(
    policy=policy,
    template_engine=template_engine,
    quality_scorer=scorer,
)
```

### Task 4: Modify Selection Policy Thresholds

**Files to Modify:**

1. **Edit Policy** → `src/pydocextractor/infra/policy/heuristics.py`
   ```python
   def choose_extractors(self, mime: str, size_bytes: int, ...) -> Sequence[Extractor]:
       size_mb = size_bytes / (1024 * 1024)

       if mime == "application/pdf":
           # Change threshold from 20MB to 50MB
           if size_mb > 50.0:  # <-- Modified
               fastest = self._extractors[PrecisionLevel.FASTEST]
               if fastest.supports(mime):
                   selected.append(fastest)
           # ... rest of logic ...
   ```

### Task 5: Add a Domain Rule

**Files to Modify:**

1. **Add Rule** → `src/pydocextractor/domain/rules.py`
   ```python
   def is_document_encrypted(doc: Document) -> bool:
       """Check if document appears to be encrypted."""
       # Check for encryption markers in first 100 bytes
       header = doc.bytes[:100]
       return b'/Encrypt' in header

   def estimate_word_count(doc: Document) -> int:
       """Estimate word count from document size."""
       # Rough heuristic: 1 word ≈ 6 bytes
       return doc.size_bytes // 6
   ```

**Usage in Application Layer:**
```python
# In service.py
from ..domain.rules import is_document_encrypted

if is_document_encrypted(doc):
    raise ValidationError("Encrypted documents not supported")
```

## Testing Strategy

### Test Pyramid

```
        /\
       /  \  Integration Tests (few, slow)
      /────\
     /      \  Adapter Tests (medium)
    /────────\
   /          \  Unit Tests (many, fast)
  /────────────\
```

### What to Test Where

| Test Type | Location | What to Test | Dependencies |
|-----------|----------|--------------|--------------|
| **Unit Tests** | `tests/unit/domain/` | - Model validation<br/>- Domain rules<br/>- Pure functions | None (stdlib only) |
| **Unit Tests** | `tests/unit/app/` | - Service orchestration<br/>- Fallback logic<br/>- Error handling | Mocked ports |
| **Adapter Tests** | `tests/adapters/` | - Extractor output<br/>- Template rendering<br/>- Scoring accuracy | Real libraries + test files |
| **Contract Tests** | `tests/contract/` | - Protocol compliance<br/>- Interface contracts | Domain ports + adapters |
| **Integration Tests** | `tests/integration/` | - Full conversion pipeline<br/>- Multiple extractors<br/>- End-to-end flows | All layers |
| **BDD Tests** | `tests/bdd/` | - User scenarios<br/>- Acceptance criteria | All layers |

### Test Examples

#### Unit Test (Domain)
```python
# tests/unit/domain/test_models.py
def test_document_validates_size():
    with pytest.raises(ValueError, match="size must be positive"):
        Document(bytes=b"test", mime="application/pdf", size_bytes=-1)
```

#### Unit Test (Application with Mocks)
```python
# tests/unit/app/test_service.py
def test_service_uses_fallback_on_failure(mock_policy, mock_extractor):
    mock_extractor.extract.side_effect = [
        ExtractionResult(success=False, error="Failed"),
        ExtractionResult(success=True, normalized_doc=ndoc),
    ]

    service = ConverterService(policy=mock_policy, ...)
    result = service.convert_to_markdown(doc)

    assert result.metadata["extractor"] == "Fallback"
```

#### Adapter Test (Real Implementation)
```python
# tests/adapters/test_extractors.py
def test_csv_extractor_with_real_file():
    extractor = PandasCSVExtractor()
    data = Path("test_documents/customers.csv").read_bytes()

    result = extractor.extract(data, PrecisionLevel.HIGHEST_QUALITY)

    assert result.success
    assert result.normalized_doc.has_tables
    assert "rows" in result.normalized_doc.metadata
```

## Development Tools

### Just Commands Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `just bootstrap` | Install all dev dependencies | First time setup |
| `just install` | Install package (editable, all extras) | After pulling changes |
| `just fmt` | Format code with ruff | Before committing |
| `just lint` | Check linting issues | During development |
| `just fix` | Auto-fix linting issues | To clean up code |
| `just typecheck` | Run mypy type checking | After adding types |
| `just guard` | Verify architecture boundaries | After imports changes |
| `just check` | Run all quality checks | Before committing |
| `just test` | Run all tests | After changes |
| `just test-unit` | Fast unit tests only | During TDD |
| `just test-adapters` | Infrastructure tests | After extractor changes |
| `just test-cov` | Tests with coverage report | To check coverage |
| `just clean` | Remove build artifacts | To start fresh |
| `just ci` | Full CI pipeline locally | Before pushing |

### Pre-commit Workflow

```bash
# 1. Make your changes
vim src/pydocextractor/infra/extractors/my_extractor.py

# 2. Format code
just fmt

# 3. Run quick checks
just lint
just typecheck

# 4. Run relevant tests
just test-adapters  # or just test-unit

# 5. Full verification
just check
just test

# 6. Verify architecture
just guard

# 7. Commit
git add .
git commit -m "Add MY_FORMAT extractor"
```

### Architecture Validation

The project uses `import-linter` to enforce layer boundaries:

```bash
# Verify no violations
just guard

# Example violations that will be caught:
# ❌ Domain importing from infra
# ❌ Domain importing from app
# ❌ Circular dependencies
```

**Import Rules:**
- ✅ Infra can import from: Domain, App, External libs
- ✅ App can import from: Domain
- ✅ Domain can import from: Nothing (stdlib only)
- ❌ Domain cannot import from: App, Infra
- ❌ App cannot import from: Infra

### Type Checking

```bash
just typecheck  # Run mypy

# Common fixes:
# - Add type hints to all functions
# - Use Protocol for interfaces
# - Avoid Any when possible
# - Use proper Optional[T] and Union types
```

### Code Coverage

```bash
just test-cov  # Generate coverage report

# View in browser
open htmlcov/index.html

# Target: 70% minimum coverage
```

## Quick Reference Cards

### New Extractor Checklist

- [ ] Create adapter in `infra/extractors/`
- [ ] Implement `Extractor` Protocol
- [ ] Add dependency to `pyproject.toml`
- [ ] Update `DefaultPolicy` in `infra/policy/heuristics.py`
- [ ] Add tests in `tests/adapters/`
- [ ] Add sample file in `test_documents/`
- [ ] Run `just fmt && just check && just test`
- [ ] Verify with `just guard`

### New Template Checklist

- [ ] Create `.j2` file in `infra/templates/templates/`
- [ ] Use available context variables
- [ ] Test with various document types
- [ ] Document template variables
- [ ] Add example usage to docs

### Pull Request Checklist

- [ ] Code follows hexagonal architecture
- [ ] All tests pass (`just test`)
- [ ] Code formatted (`just fmt`)
- [ ] Type hints complete (`just typecheck`)
- [ ] Architecture respected (`just guard`)
- [ ] Documentation updated
- [ ] Test coverage maintained
- [ ] Commit messages clear

---

**Need Help?**

- **Main Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Issues**: [GitHub Issues](https://github.com/AminiTech/pyDocExtractor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AminiTech/pyDocExtractor/discussions)
