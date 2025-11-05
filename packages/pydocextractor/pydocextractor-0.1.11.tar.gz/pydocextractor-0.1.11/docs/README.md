# pyDocExtractor Documentation

Welcome to the pyDocExtractor documentation! This directory contains detailed guides and references for contributors and users.

## Documentation Index

### For Contributors

| Document | Purpose | Audience |
|----------|---------|----------|
| **[CONTRIBUTING_GUIDE.md](CONTRIBUTING_GUIDE.md)** | Comprehensive contribution guide with architecture reference, folder structure map, and task-specific tutorials | Developers adding features |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Quick start contribution guide with step-by-step instructions for common tasks | New contributors |
| **[TEMPLATES.md](TEMPLATES.md)** | Template system guide with Jinja2 examples, context variables, and custom template creation | Developers customizing output |
| **[../tests/bdd/README.md](../tests/bdd/README.md)** | BDD testing guide using Gherkin scenarios | QA engineers, developers |

### For Users

| Document | Purpose | Audience |
|----------|---------|----------|
| **[../README.md#llm-image-description](../README.md#llm-image-description)** | LLM image description feature guide with configuration and usage examples | Users wanting AI-powered image descriptions |
| **[../.env.example](../.env.example)** | LLM configuration template with all available options | Users configuring LLM features |

### Architecture & Design

| Document | Description |
|----------|-------------|
| **[CONTRIBUTING_GUIDE.md#architecture-overview](CONTRIBUTING_GUIDE.md#architecture-overview)** | Hexagonal architecture principles and layer dependencies |
| **[CONTRIBUTING_GUIDE.md#folder-structure-reference](CONTRIBUTING_GUIDE.md#folder-structure-reference)** | Complete folder map with "when to modify" guide |
| **[../README.md#architecture](../README.md#architecture)** | High-level architecture diagrams and explanations |

### Task-Specific Guides

All located in [CONTRIBUTING_GUIDE.md](CONTRIBUTING_GUIDE.md):

- **[Adding a New Document Type](CONTRIBUTING_GUIDE.md#task-1-add-support-for-a-new-document-type-eg-rtf)** - Step-by-step guide with code examples
- **[Creating Custom Templates](CONTRIBUTING_GUIDE.md#task-2-add-a-custom-template)** - Jinja2 template creation
- **[Modifying Quality Scoring](CONTRIBUTING_GUIDE.md#task-3-modify-quality-scoring)** - Custom scoring algorithms
- **[Changing Selection Policy](CONTRIBUTING_GUIDE.md#task-4-modify-selection-policy-thresholds)** - Extractor selection heuristics
- **[Adding Domain Rules](CONTRIBUTING_GUIDE.md#task-5-add-a-domain-rule)** - Business logic functions

### Testing

| Document | Description |
|----------|-------------|
| **[CONTRIBUTING_GUIDE.md#testing-strategy](CONTRIBUTING_GUIDE.md#testing-strategy)** | Test pyramid, what to test where, and examples |
| **[../tests/bdd/README.md](../tests/bdd/README.md)** | BDD scenarios and Gherkin syntax |

### Development Tools

| Document | Description |
|----------|-------------|
| **[CONTRIBUTING_GUIDE.md#development-tools](CONTRIBUTING_GUIDE.md#development-tools)** | Just commands reference and workflows |
| **[../README.md#development-workflow](../README.md#development-workflow)** | Available just commands |

### Sample Output

| Document | Description |
|----------|-------------|
| **[tabular_data_sample.md](tabular_data_sample.md)** | Example output from Excel/CSV extraction |
| **[text_data_sample.md](text_data_sample.md)** | Example output from text document extraction |

### Internal References

| Document | Description |
|----------|-------------|
| **[current_rag_strategy.md](current_rag_strategy.md)** | RAG (Retrieval-Augmented Generation) integration strategy |

## Quick Start for Contributors

1. **First Time Setup**
   ```bash
   git clone https://github.com/AminiTech/pyDocExtractor.git
   cd pyDocExtractor
   just bootstrap
   ```

2. **Read Contributing Guide**
   - Start with [CONTRIBUTING.md](CONTRIBUTING.md) for quick overview
   - Then read [CONTRIBUTING_GUIDE.md](CONTRIBUTING_GUIDE.md) for detailed reference

3. **Pick a Task**
   - Add document type support → [Guide](CONTRIBUTING_GUIDE.md#task-1-add-support-for-a-new-document-type-eg-rtf)
   - Create custom template → [Guide](CONTRIBUTING_GUIDE.md#task-2-add-a-custom-template)
   - Modify scoring → [Guide](CONTRIBUTING_GUIDE.md#task-3-modify-quality-scoring)

4. **Follow Workflow**
   ```bash
   # Make changes
   just fmt           # Format code (auto-fix)
   just check         # Quality checks (lint + type check)
   just test          # Run tests
   just guard         # Verify architecture
   ```

5. **Fix Common CI/CD Errors**

   If CI/CD fails with formatting errors:
   ```bash
   # Check what needs formatting
   uv run ruff format --check src tests

   # Auto-fix formatting issues
   uv run ruff format src tests
   # Or use: just fmt

   # Verify formatting is correct
   uv run ruff format --check src tests
   ```

   If CI/CD fails with linting errors:
   ```bash
   # Check linting issues
   uv run ruff check src tests

   # Auto-fix linting issues (where possible)
   uv run ruff check --fix src tests

   # Verify linting is correct
   uv run ruff check src tests
   ```

6. **Submit PR**
   - Use checklist from [CONTRIBUTING_GUIDE.md](CONTRIBUTING_GUIDE.md#pull-request-checklist)

## Architecture Quick Reference

### Layer Responsibilities

| Layer | Location | Purpose | Dependencies |
|-------|----------|---------|--------------|
| **Domain** | `src/pydocextractor/domain/` | Pure business logic | None (stdlib only) |
| **Application** | `src/pydocextractor/app/` | Orchestration | Domain only |
| **Infrastructure** | `src/pydocextractor/infra/` | Implementations | Domain + external libs |

### Key Design Patterns

- **Hexagonal Architecture**: Clean separation of concerns
- **Protocol-Based**: All interfaces use Python Protocols
- **Dependency Injection**: Factory pattern for component wiring
- **Immutable Models**: Dataclasses with `frozen=True`

## Features

### LLM Image Description

pyDocExtractor supports automatic AI-powered image descriptions using OpenAI-compatible multimodal LLMs. This optional feature provides context-aware image descriptions by analyzing images alongside surrounding text.

**Key Components:**
- `domain/config.py` - LLMConfig model for configuration
- `domain/ports.py` - ImageDescriber protocol
- `app/image_context.py` - Tracks text context for images
- `infra/config/` - Environment-based configuration loading
- `infra/llm/` - OpenAI adapter with resilient retry logic

**Documentation:**
- Configuration guide: [../README.md#llm-image-description](../README.md#llm-image-description)
- Environment template: [../.env.example](../.env.example)

**Features:**
- Context-aware descriptions (previous 100 lines of text)
- Works with PDF and DOCX files
- All extractors support image extraction when LLM enabled
- Graceful degradation (works without LLM)
- Cost control (configurable max images per document)

## Common Questions

### "Where do I add support for a new file format?"

1. Create extractor in `src/pydocextractor/infra/extractors/`
2. Update policy in `src/pydocextractor/infra/policy/heuristics.py`
3. See: [CONTRIBUTING_GUIDE.md#task-1-add-support-for-a-new-document-type-eg-rtf](CONTRIBUTING_GUIDE.md#task-1-add-support-for-a-new-document-type-eg-rtf)

### "Where do I change the markdown output format?"

1. Create template in `src/pydocextractor/infra/templates/templates/`
2. See: [CONTRIBUTING_GUIDE.md#task-2-add-a-custom-template](CONTRIBUTING_GUIDE.md#task-2-add-a-custom-template)

### "Where do I modify how extractors are chosen?"

1. Edit `src/pydocextractor/infra/policy/heuristics.py`
2. See: [CONTRIBUTING_GUIDE.md#task-4-modify-selection-policy-thresholds](CONTRIBUTING_GUIDE.md#task-4-modify-selection-policy-thresholds)

### "Where do I add new quality metrics?"

1. Create scorer in `src/pydocextractor/infra/scoring/`
2. See: [CONTRIBUTING_GUIDE.md#task-3-modify-quality-scoring](CONTRIBUTING_GUIDE.md#task-3-modify-quality-scoring)

### "Where do I add business logic rules?"

1. Add to `src/pydocextractor/domain/rules.py`
2. See: [CONTRIBUTING_GUIDE.md#task-5-add-a-domain-rule](CONTRIBUTING_GUIDE.md#task-5-add-a-domain-rule)

## Folder Structure at a Glance

```
pyDocExtractor/
├── src/pydocextractor/
│   ├── domain/              # Pure business logic (no deps)
│   │   ├── models.py        # Document, Block, NormalizedDoc
│   │   ├── ports.py         # Protocol definitions
│   │   ├── rules.py         # Pure functions
│   │   └── errors.py        # Exception hierarchy
│   ├── app/
│   │   └── service.py       # ConverterService orchestration
│   ├── infra/
│   │   ├── extractors/      # PDF, DOCX, CSV, Excel extractors
│   │   ├── policy/          # Selection logic
│   │   ├── templates/       # Jinja2 templates
│   │   └── scoring/         # Quality scorers
│   ├── factory.py           # Dependency injection
│   └── cli.py               # Command-line interface
├── tests/
│   ├── unit/                # Fast tests (mocked)
│   ├── adapters/            # Infrastructure tests
│   ├── contract/            # Protocol compliance
│   ├── integration/         # End-to-end tests
│   └── bdd/                 # BDD scenarios
├── test_documents/          # Sample test files
├── docs/                    # THIS DIRECTORY
│   ├── README.md           # This file
│   ├── CONTRIBUTING.md     # Quick start guide
│   ├── CONTRIBUTING_GUIDE.md  # Detailed guide
│   └── *.md                # Sample outputs, strategies
└── README.md                # Project README
```

## External Resources

- **GitHub Repository**: https://github.com/AminiTech/pyDocExtractor
- **Issues**: https://github.com/AminiTech/pyDocExtractor/issues
- **Discussions**: https://github.com/AminiTech/pyDocExtractor/discussions
- **PyPI**: https://pypi.org/project/pydocextractor/

## Need Help?

1. Check [CONTRIBUTING_GUIDE.md](CONTRIBUTING_GUIDE.md) first
2. Search [GitHub Issues](https://github.com/AminiTech/pyDocExtractor/issues)
3. Ask in [GitHub Discussions](https://github.com/AminiTech/pyDocExtractor/discussions)
4. Open a new issue with the `question` label

---

**Happy Contributing!** 🚀
