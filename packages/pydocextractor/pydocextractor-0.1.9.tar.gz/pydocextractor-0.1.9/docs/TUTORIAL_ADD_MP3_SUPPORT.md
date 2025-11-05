# Tutorial: Adding MP3 Audio File Support

This tutorial demonstrates how to extend pyDocExtractor to support MP3 audio files, showcasing the hexagonal architecture's flexibility.

## Architecture Overview

pyDocExtractor uses **Hexagonal Architecture (Ports & Adapters)**:

```
┌─────────────────────────────────────────────────────┐
│                   Application                        │
│              (app/service.py)                        │
└──────────────────┬──────────────────────────────────┘
                   │ uses
         ┌─────────▼─────────┐
         │   Domain Layer    │
         │  (domain/ports.py)│
         │    «Extractor»    │  ← Protocol (Interface)
         └─────────┬─────────┘
                   │ implements
         ┌─────────▼──────────────────┐
         │  Infrastructure Layer       │
         │  (infra/extractors/)        │
         │  - PDF Extractor            │
         │  - DOCX Extractor           │
         │  - MP3 Extractor  ← NEW!    │
         └─────────────────────────────┘
```

## Step 1: Understand the Domain Protocol

First, examine what an extractor must implement:

```bash
cat src/pydocextractor/domain/ports.py
```

Key points:
- **`supports(mime_type: str) -> bool`**: Check if extractor handles this file type
- **`extract(document: Document) -> list[Block]`**: Convert file to structured blocks
- **`is_available() -> bool`**: Check if dependencies are installed
- **`precision_level`**: Quality tier (1=highest, 5=fastest)
- **`name`**: Human-readable identifier

## Step 2: Create the MP3 Extractor Adapter

### 2.1 Create the file

```bash
touch src/pydocextractor/infra/extractors/mp3_adapter.py
```

### 2.2 Implement the extractor

```python
"""
MP3 audio file extractor adapter.

Extracts metadata and optionally transcribes audio to text.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydocextractor.domain.models import Block, BlockType
from pydocextractor.domain.ports import Extractor, PrecisionLevel

if TYPE_CHECKING:
    from pydocextractor.domain.models import Document

logger = logging.getLogger(__name__)


class MP3Extractor(Extractor):
    """
    Extract metadata and text from MP3 audio files.

    Features:
    - ID3 tag extraction (title, artist, album, year, etc.)
    - Audio properties (duration, bitrate, sample rate)
    - Optional speech-to-text transcription (if configured)

    Dependencies: mutagen (audio metadata)
    Optional: speech_recognition, pydub (transcription)
    """

    name = "MP3Extractor"
    precision_level = PrecisionLevel.BALANCED  # Level 2

    def __init__(self, enable_transcription: bool = False) -> None:
        """
        Initialize MP3 extractor.

        Args:
            enable_transcription: If True, transcribe audio to text
        """
        self.enable_transcription = enable_transcription

    def is_available(self) -> bool:
        """Check if required dependencies are installed."""
        try:
            import mutagen  # noqa: F401
            return True
        except ImportError:
            logger.debug("mutagen not installed, MP3 extraction unavailable")
            return False

    def supports(self, mime_type: str) -> bool:
        """Check if this extractor supports the given MIME type."""
        return mime_type in [
            "audio/mpeg",
            "audio/mp3",
        ]

    def extract(self, doc: Document) -> list[Block]:
        """
        Extract structured content from MP3 file.

        Args:
            doc: Document with MP3 file bytes

        Returns:
            List of blocks representing the audio content
        """
        if not self.is_available():
            raise ImportError(
                "mutagen required for MP3 extraction. "
                "Install with: pip install mutagen"
            )

        import io
        import mutagen
        from mutagen.id3 import ID3

        blocks: list[Block] = []

        try:
            # Load MP3 file
            audio_file = mutagen.File(io.BytesIO(doc.bytes))

            if audio_file is None:
                logger.warning("Could not parse MP3 file")
                return self._create_fallback_blocks(doc)

            # Extract metadata
            blocks.append(self._create_metadata_block(audio_file, doc))

            # Extract ID3 tags if present
            try:
                id3 = ID3(io.BytesIO(doc.bytes))
                blocks.append(self._create_id3_block(id3))
            except Exception as e:
                logger.debug(f"No ID3 tags found: {e}")

            # Extract audio properties
            if audio_file.info:
                blocks.append(self._create_audio_info_block(audio_file.info))

            # Optional: Transcribe audio
            if self.enable_transcription:
                transcription = self._transcribe_audio(doc.bytes)
                if transcription:
                    blocks.append(Block(
                        type=BlockType.TEXT,
                        content=f"**Transcription:**\n\n{transcription}",
                        page_number=1,
                    ))

        except Exception as e:
            logger.error(f"Error extracting MP3: {e}")
            return self._create_fallback_blocks(doc)

        return blocks

    def _create_metadata_block(self, audio_file, doc: Document) -> Block:
        """Create block with file metadata."""
        lines = [
            "# Audio File",
            "",
            f"- **Format**: MP3",
            f"- **File**: {doc.filename}",
        ]

        return Block(
            type=BlockType.SECTION,
            content="\n".join(lines),
            page_number=1,
        )

    def _create_id3_block(self, id3) -> Block:
        """Create block with ID3 tag information."""
        lines = ["## Metadata", ""]

        # Common ID3 tags
        tag_mapping = {
            "TIT2": "Title",
            "TPE1": "Artist",
            "TALB": "Album",
            "TDRC": "Year",
            "TCON": "Genre",
            "COMM": "Comment",
        }

        for tag_id, label in tag_mapping.items():
            if tag_id in id3:
                value = str(id3[tag_id].text[0])
                lines.append(f"- **{label}**: {value}")

        return Block(
            type=BlockType.TEXT,
            content="\n".join(lines),
            page_number=1,
        )

    def _create_audio_info_block(self, info) -> Block:
        """Create block with audio technical information."""
        duration_mins = int(info.length // 60)
        duration_secs = int(info.length % 60)

        lines = [
            "## Audio Properties",
            "",
            f"- **Duration**: {duration_mins}:{duration_secs:02d}",
            f"- **Bitrate**: {info.bitrate // 1000} kbps",
            f"- **Sample Rate**: {info.sample_rate} Hz",
            f"- **Channels**: {info.channels}",
        ]

        return Block(
            type=BlockType.TEXT,
            content="\n".join(lines),
            page_number=1,
        )

    def _transcribe_audio(self, audio_bytes: bytes) -> str | None:
        """
        Transcribe audio to text using speech recognition.

        Optional feature - requires speech_recognition and pydub.
        """
        try:
            import speech_recognition as sr
            from pydub import AudioSegment
            import io
            import tempfile

            # Convert MP3 to WAV for speech recognition
            audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))

            # Export to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                audio.export(temp_wav.name, format="wav")

                # Recognize speech
                recognizer = sr.Recognizer()
                with sr.AudioFile(temp_wav.name) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    return text

        except ImportError:
            logger.warning(
                "speech_recognition or pydub not installed, "
                "transcription disabled"
            )
            return None
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

    def _create_fallback_blocks(self, doc: Document) -> list[Block]:
        """Create fallback blocks when extraction fails."""
        return [
            Block(
                type=BlockType.TEXT,
                content=f"# Audio File\n\nMP3 audio file: {doc.filename}",
                page_number=1,
            )
        ]
```

## Step 3: Register in Extractors Module

Edit `src/pydocextractor/infra/extractors/__init__.py`:

```python
from pydocextractor.infra.extractors.mp3_adapter import MP3Extractor

__all__ = [
    # ... existing extractors ...
    "MP3Extractor",
]
```

## Step 4: Update Factory to Include MP3 Extractor

Edit `src/pydocextractor/factory.py`:

### 4.1 Import the extractor

```python
from pydocextractor.infra.extractors import (
    # ... existing imports ...
    MP3Extractor,
)
```

### 4.2 Add to available extractors list

In the `get_available_extractors()` function:

```python
def get_available_extractors() -> list[Extractor]:
    """Get list of all available extractors."""
    extractors: list[Extractor] = [
        # ... existing extractors ...
        MP3Extractor(),  # Level 2 - Audio files
    ]

    # Filter to only available extractors
    return [e for e in extractors if e.is_available()]
```

## Step 5: Update Policy (Optional)

If you want the MP3 extractor available at specific precision levels, edit `src/pydocextractor/infra/policy/heuristics.py`:

```python
def __init__(self, llm_enabled: bool = False) -> None:
    """Initialize policy with available extractors."""
    self._extractors = {
        PrecisionLevel.HIGHEST_QUALITY: DoclingExtractor(),
        PrecisionLevel.BALANCED: PyMuPDF4LLMExtractor(
            enable_image_extraction=llm_enabled
        ),
        PrecisionLevel.TABLE_OPTIMIZED: PDFPlumberExtractor(
            enable_image_extraction=llm_enabled
        ),
        PrecisionLevel.FAST: ChunkedParallelExtractor(),
        # Add MP3 support at balanced level
        PrecisionLevel.AUDIO_OPTIMIZED: MP3Extractor(),  # New level if needed
    }
```

## Step 6: Add Tests

Create `tests/unit/infra/extractors/test_mp3_adapter.py`:

```python
"""Unit tests for MP3 extractor adapter."""

import pytest
from unittest.mock import Mock, patch
from pydocextractor.domain.models import Document, BlockType
from pydocextractor.infra.extractors.mp3_adapter import MP3Extractor


@pytest.fixture
def sample_mp3_document():
    """Create a sample MP3 document."""
    return Document(
        filename="test.mp3",
        bytes=b"fake mp3 bytes",  # In real test, use actual MP3
        mime="audio/mpeg",
    )


class TestMP3Extractor:
    """Test MP3 extractor."""

    def test_extractor_name(self):
        """Test extractor has correct name."""
        extractor = MP3Extractor()
        assert extractor.name == "MP3Extractor"

    def test_supports_audio_mpeg(self):
        """Test extractor supports audio/mpeg MIME type."""
        extractor = MP3Extractor()
        assert extractor.supports("audio/mpeg") is True
        assert extractor.supports("audio/mp3") is True

    def test_does_not_support_other_types(self):
        """Test extractor rejects non-audio types."""
        extractor = MP3Extractor()
        assert extractor.supports("application/pdf") is False
        assert extractor.supports("video/mp4") is False

    @patch("pydocextractor.infra.extractors.mp3_adapter.mutagen")
    def test_extract_basic_metadata(self, mock_mutagen, sample_mp3_document):
        """Test basic metadata extraction."""
        # Mock mutagen file
        mock_file = Mock()
        mock_file.info.length = 180  # 3 minutes
        mock_file.info.bitrate = 128000
        mock_file.info.sample_rate = 44100
        mock_file.info.channels = 2
        mock_mutagen.File.return_value = mock_file

        extractor = MP3Extractor()
        blocks = extractor.extract(sample_mp3_document)

        # Should have metadata blocks
        assert len(blocks) > 0
        assert any(b.type == BlockType.SECTION for b in blocks)

        # Check duration formatting
        audio_block = next(b for b in blocks if "Duration" in b.content)
        assert "3:00" in audio_block.content

    def test_is_available_without_mutagen(self):
        """Test availability check when mutagen not installed."""
        with patch.dict("sys.modules", {"mutagen": None}):
            extractor = MP3Extractor()
            # Actual behavior depends on import mechanism
            # This is a simplified test
```

## Step 7: Add Integration Test

Create `tests/integration/test_mp3_extraction.py`:

```python
"""Integration tests for MP3 extraction."""

import pytest
from pathlib import Path
from pydocextractor.factory import create_document_service


@pytest.mark.integration
def test_extract_real_mp3_file():
    """Test extracting a real MP3 file."""
    # Create a simple test MP3 file
    test_file = Path("tests/fixtures/samples/test.mp3")

    if not test_file.exists():
        pytest.skip("Test MP3 file not available")

    service = create_document_service()

    with open(test_file, "rb") as f:
        document = service.extract(
            file_bytes=f.read(),
            filename="test.mp3",
        )

    # Verify extraction
    assert document is not None
    assert len(document.blocks) > 0

    # Check for expected content
    content = document.to_markdown()
    assert "Audio File" in content or "MP3" in content
```

## Step 8: Update Documentation

### 8.1 Update README.md

Add MP3 to supported formats:

```markdown
## Supported Formats

- PDF (`.pdf`)
- Word Documents (`.docx`)
- Excel Spreadsheets (`.xlsx`, `.xls`)
- CSV Files (`.csv`)
- **Audio Files (`.mp3`)** ← NEW!
```

### 8.2 Update CONTRIBUTING_GUIDE.md

Add MP3 extractor to the component table.

## Step 9: Add Dependencies

Update `pyproject.toml`:

```toml
[project.optional-dependencies]
# ... existing dependencies ...

# Audio support
audio = [
    "mutagen>=1.47.0",  # Audio metadata
]

# Full audio with transcription
audio-full = [
    "mutagen>=1.47.0",
    "SpeechRecognition>=3.10.0",
    "pydub>=0.25.1",
]
```

## Step 10: Test the Implementation

```bash
# Install with audio support
pip install -e ".[audio]"

# Run tests
pytest tests/unit/infra/extractors/test_mp3_adapter.py -v

# Test with a real file
python -c "
from pydocextractor import create_document_service

service = create_document_service()
with open('test.mp3', 'rb') as f:
    doc = service.extract(f.read(), 'test.mp3')
    print(doc.to_markdown())
"
```

## Architecture Benefits Demonstrated

This tutorial shows how hexagonal architecture provides:

1. **Loose Coupling**: New extractor doesn't modify existing code
2. **Open/Closed Principle**: System is open for extension, closed for modification
3. **Dependency Inversion**: Application depends on abstractions (protocols), not concrete implementations
4. **Testability**: Easy to mock and unit test each layer
5. **Flexibility**: Can add/remove extractors without breaking the system

## Summary of Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `infra/extractors/mp3_adapter.py` | **CREATE** | New MP3 extractor implementation |
| `infra/extractors/__init__.py` | **EDIT** | Export MP3Extractor |
| `factory.py` | **EDIT** | Register MP3Extractor |
| `infra/policy/heuristics.py` | **EDIT** (optional) | Add to precision levels |
| `tests/unit/infra/extractors/test_mp3_adapter.py` | **CREATE** | Unit tests |
| `tests/integration/test_mp3_extraction.py` | **CREATE** | Integration tests |
| `pyproject.toml` | **EDIT** | Add mutagen dependency |
| `README.md` | **EDIT** | Document MP3 support |

## Key Takeaways

1. **Protocol-based design** makes adding extractors straightforward
2. **Factory pattern** centralizes extractor management
3. **Policy pattern** allows flexible selection strategies
4. **Dependency injection** keeps components decoupled
5. **Test at each layer** ensures reliability

This same pattern applies to adding **any** new format: PPTX, HTML, JSON, video files, etc.
