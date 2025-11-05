# Handwritten Text and Image Extraction BDD Tests

## Overview

These BDD tests verify that the pyDocExtractor can correctly extract content from PDFs containing handwritten text and images using LLM-powered image description.

## Test Files

- **Feature**: `features/extract_handwritten_text_with_images.feature`
- **Test Implementation**: `test_handwritten_extraction.py`
- **Test Document**: `test_documents/handwriten_text_and_image.pdf`

## Configuration

The tests require LLM credentials to run. There are two ways to provide them:

### Option 1: config.env file (Local Development)

Create a `config.env` file in the project root:

```bash
LLM_ENABLED=true
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=your-api-key-here
LLM_MODEL_NAME=gpt-4o-mini
LLM_MAX_IMAGES=-1
```

### Option 2: Environment Variables (CI/CD)

Set environment variables directly:

```bash
export LLM_API_KEY=your-api-key-here
export LLM_API_URL=https://api.openai.com/v1/chat/completions
export LLM_MODEL_NAME=gpt-4o-mini
export LLM_ENABLED=true
```

## Running the Tests

### Local Development

```bash
# Run all handwritten tests
pytest tests/bdd/test_handwritten_extraction.py -v

# Run with specific marker
pytest -m handwritten -v

# Run single scenario
pytest tests/bdd/test_handwritten_extraction.py::test_convert_pdf_with_handwritten_text_and_images_to_markdown -v
```

### CI/CD (GitHub Actions)

The tests will automatically **skip** if:
- No `config.env` file exists, AND
- No `LLM_API_KEY` or `OPENAI_API_KEY` environment variable is set

To run in CI/CD, add secrets to your GitHub repository and configure the workflow:

```yaml
- name: Run handwritten tests
  env:
    LLM_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    LLM_MODEL_NAME: gpt-4o-mini
  run: pytest tests/bdd/test_handwritten_extraction.py -v
```

### Excluding from CI/CD

If you want to completely exclude these tests from CI/CD:

```bash
# Skip LLM tests
pytest -m "not llm" 

# Skip handwritten tests specifically
pytest -m "not handwritten"
```

## Test Scenarios

1. **Convert PDF with handwritten text and images to Markdown**
   - Verifies basic conversion with all keywords present

2. **Verify all required keywords are extracted**
   - Table-driven test checking: leonardo, hate, meeting, like, skate

3. **Verify structure preservation**
   - Checks that document structure and images are preserved

4. **Convert with LLM image description**
   - Tests quality of LLM-described content

## Technical Details

- **Precision Level**: 2 (BALANCED) - Uses PyMuPDF4LLM
- **LLM Model**: gpt-4o-mini (or configured model)
- **Image Description**: LLM describes handwritten content in images
- **Keyword Matching**: Flexible matching with synonyms:
  - "hate" matches "dislike", "dislikes"
  - "like" matches "likes", "enjoy", "enjoys"
  - "skate" matches "skateboard", "skateboarding"
  - "meeting" matches "meetings"

## Troubleshooting

### Tests are skipped

This is expected behavior when LLM credentials are not available. The tests require:
- `config.env` file, OR
- `LLM_API_KEY` environment variable

### Tests fail with authentication error

Check that your API key is valid and has sufficient credits.

### Tests fail with keyword not found

The LLM may use different wording. The test includes synonym matching, but you can add more synonyms in `test_handwritten_extraction.py` if needed.

## Cost Considerations

Each test run calls the OpenAI API approximately 2 times per scenario (2 images in the test PDF). With 4 scenarios, that's about 8 API calls per full test run.

Consider:
- Using `gpt-4o-mini` for cost efficiency (default in config.env)
- Running these tests manually or on-demand in CI/CD
- Setting up API usage alerts in OpenAI dashboard
