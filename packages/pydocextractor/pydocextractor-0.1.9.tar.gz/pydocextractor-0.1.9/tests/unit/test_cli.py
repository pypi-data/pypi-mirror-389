"""
Unit tests for CLI module.

Tests the command-line interface functions and helpers.
"""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from pydocextractor.cli import _load_document, app
from pydocextractor.domain.models import Document, PrecisionLevel


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 test content")
    return pdf_file


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,age\nAlice,30\nBob,25")
    return csv_file


@pytest.fixture
def sample_docx(tmp_path):
    """Create a sample DOCX file for testing."""
    docx_file = tmp_path / "test.docx"
    docx_file.write_bytes(b"fake docx content")
    return docx_file


@pytest.fixture
def sample_xlsx(tmp_path):
    """Create a sample XLSX file for testing."""
    xlsx_file = tmp_path / "test.xlsx"
    xlsx_file.write_bytes(b"fake xlsx content")
    return xlsx_file


class TestLoadDocument:
    """Test _load_document helper function."""

    def test_load_pdf_document(self, sample_pdf):
        """Test loading a PDF document."""
        doc = _load_document(sample_pdf, PrecisionLevel.BALANCED)

        assert isinstance(doc, Document)
        assert doc.mime == "application/pdf"
        assert doc.filename == "test.pdf"
        assert doc.precision == PrecisionLevel.BALANCED
        assert doc.size_bytes > 0
        assert len(doc.bytes) > 0

    def test_load_csv_document(self, sample_csv):
        """Test loading a CSV document."""
        doc = _load_document(sample_csv, PrecisionLevel.HIGHEST_QUALITY)

        assert isinstance(doc, Document)
        assert doc.mime == "text/csv"
        assert doc.filename == "test.csv"
        assert doc.precision == PrecisionLevel.HIGHEST_QUALITY

    def test_load_docx_document(self, sample_docx):
        """Test loading a DOCX document."""
        doc = _load_document(sample_docx, PrecisionLevel.BALANCED)

        assert isinstance(doc, Document)
        assert doc.mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert doc.filename == "test.docx"

    def test_load_xlsx_document(self, sample_xlsx):
        """Test loading an XLSX document."""
        doc = _load_document(sample_xlsx, PrecisionLevel.BALANCED)

        assert isinstance(doc, Document)
        assert doc.mime == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert doc.filename == "test.xlsx"

    def test_load_unknown_extension(self, tmp_path):
        """Test loading document with unknown extension."""
        unknown_file = tmp_path / "test.unknown"
        unknown_file.write_bytes(b"some content")

        doc = _load_document(unknown_file, PrecisionLevel.BALANCED)

        assert doc.mime == "application/octet-stream"


class TestConvertCommand:
    """Test the convert command."""

    @patch("pydocextractor.cli.create_converter_service")
    def test_convert_pdf_success(self, mock_service_factory, runner, sample_pdf, tmp_path):
        """Test successful PDF conversion."""
        # Mock service
        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# Converted Content"
        mock_result.quality_score = 0.85
        mock_result.metadata = {"extractor": "TestExtractor"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service

        output_file = tmp_path / "output.md"

        result = runner.invoke(app, ["convert", str(sample_pdf), "-o", str(output_file), "-l", "2"])

        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.read_text() == "# Converted Content"

    def test_convert_file_not_found(self, runner, tmp_path):
        """Test conversion with non-existent file."""
        non_existent = tmp_path / "does_not_exist.pdf"

        result = runner.invoke(app, ["convert", str(non_existent)])

        assert result.exit_code == 1
        assert "File not found" in result.stdout

    @patch("pydocextractor.cli.create_converter_service")
    def test_convert_with_default_output(self, mock_service_factory, runner, sample_pdf):
        """Test conversion with default output filename."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# Content"
        mock_result.quality_score = 0.8
        mock_result.metadata = {"extractor": "Test"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service

        result = runner.invoke(app, ["convert", str(sample_pdf)])

        assert result.exit_code == 0
        # Should create test.md next to test.pdf
        output_path = sample_pdf.with_suffix(".md")
        assert output_path.exists()

    @patch("pydocextractor.cli.create_converter_service")
    def test_convert_csv_auto_selects_tabular_template(
        self, mock_service_factory, runner, sample_csv, tmp_path
    ):
        """Test that CSV files auto-select tabular template."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# CSV Content"
        mock_result.quality_score = 0.9
        mock_result.metadata = {"extractor": "PandasCSV"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service

        output_file = tmp_path / "output.md"

        result = runner.invoke(app, ["convert", str(sample_csv), "-o", str(output_file)])

        assert result.exit_code == 0
        # Check that tabular template was used
        call_args = mock_service.convert_to_markdown.call_args
        assert call_args.kwargs["template_name"] == "tabular"

    @patch("pydocextractor.cli.create_converter_service")
    def test_convert_with_all_precision_levels(
        self, mock_service_factory, runner, sample_pdf, tmp_path
    ):
        """Test conversion with all precision levels."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# Content"
        mock_result.quality_score = 0.8
        mock_result.metadata = {"extractor": "Test"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service

        for level in [1, 2, 3, 4]:
            output_file = tmp_path / f"output_{level}.md"
            result = runner.invoke(
                app, ["convert", str(sample_pdf), "-o", str(output_file), "-l", str(level)]
            )
            assert result.exit_code == 0

    @patch("pydocextractor.cli.create_converter_service")
    def test_convert_with_quality_score(self, mock_service_factory, runner, sample_pdf, tmp_path):
        """Test conversion with quality score display."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# Content"
        mock_result.quality_score = 0.85
        mock_result.metadata = {"extractor": "Test"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service

        output_file = tmp_path / "output.md"

        result = runner.invoke(
            app, ["convert", str(sample_pdf), "-o", str(output_file), "--show-score"]
        )

        assert result.exit_code == 0
        assert "Quality score" in result.stdout
        assert "0.85" in result.stdout

    @patch("pydocextractor.cli.create_converter_service")
    @patch("pydocextractor.cli.calculate_document_hash")
    def test_convert_with_hash(self, mock_hash, mock_service_factory, runner, sample_pdf, tmp_path):
        """Test conversion with hash display."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# Content"
        mock_result.quality_score = 0.8
        mock_result.metadata = {"extractor": "Test"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service
        mock_hash.return_value = "abc123def456"

        output_file = tmp_path / "output.md"

        result = runner.invoke(
            app, ["convert", str(sample_pdf), "-o", str(output_file), "--show-hash"]
        )

        assert result.exit_code == 0
        assert "SHA-256" in result.stdout
        assert "abc123def456" in result.stdout

    @patch("pydocextractor.cli.create_converter_service")
    def test_convert_with_custom_template(self, mock_service_factory, runner, sample_pdf, tmp_path):
        """Test conversion with custom template."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# Content"
        mock_result.quality_score = 0.8
        mock_result.metadata = {"extractor": "Test"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service

        output_file = tmp_path / "output.md"

        result = runner.invoke(
            app, ["convert", str(sample_pdf), "-o", str(output_file), "--template", "simple"]
        )

        assert result.exit_code == 0
        call_args = mock_service.convert_to_markdown.call_args
        assert call_args.kwargs["template_name"] == "simple"

    @patch("pydocextractor.cli.create_converter_service")
    def test_convert_service_initialization_fails(self, mock_service_factory, runner, sample_pdf):
        """Test handling of service initialization failure."""
        mock_service_factory.side_effect = Exception("Service init failed")

        result = runner.invoke(app, ["convert", str(sample_pdf)])

        assert result.exit_code == 1
        assert "Failed to initialize converter" in result.stdout

    @patch("pydocextractor.cli.create_converter_service")
    def test_convert_conversion_fails(self, mock_service_factory, runner, sample_pdf, tmp_path):
        """Test handling of conversion failure."""
        mock_service = Mock()
        mock_service.convert_to_markdown.side_effect = Exception("Conversion error")
        mock_service_factory.return_value = mock_service

        output_file = tmp_path / "output.md"

        result = runner.invoke(app, ["convert", str(sample_pdf), "-o", str(output_file)])

        assert result.exit_code == 1
        assert "Conversion failed" in result.stdout

    @patch("pydocextractor.cli.create_converter_service")
    def test_convert_conversion_fails_verbose(
        self, mock_service_factory, runner, sample_pdf, tmp_path
    ):
        """Test handling of conversion failure with verbose output."""
        mock_service = Mock()
        mock_service.convert_to_markdown.side_effect = Exception("Conversion error")
        mock_service_factory.return_value = mock_service

        output_file = tmp_path / "output.md"

        result = runner.invoke(
            app, ["convert", str(sample_pdf), "-o", str(output_file), "--verbose"]
        )

        assert result.exit_code == 1
        assert "Conversion failed" in result.stdout
        # Verbose should show traceback
        assert "Traceback" in result.stdout or "Exception" in result.stdout

    @patch("pydocextractor.cli.create_converter_service")
    def test_convert_write_output_fails(self, mock_service_factory, runner, sample_pdf, tmp_path):
        """Test handling of output write failure."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# Content"
        mock_result.quality_score = 0.8
        mock_result.metadata = {"extractor": "Test"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service

        # Use a directory as output file (will fail to write)
        output_file = tmp_path / "subdir"
        output_file.mkdir()

        result = runner.invoke(app, ["convert", str(sample_pdf), "-o", str(output_file)])

        assert result.exit_code == 1
        assert "Failed to write output file" in result.stdout


class TestBatchCommand:
    """Test the batch command."""

    @patch("pydocextractor.cli.create_converter_service")
    def test_batch_convert_multiple_files(self, mock_service_factory, runner, tmp_path):
        """Test batch conversion of multiple files."""
        # Create input directory with files
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "doc1.pdf").write_bytes(b"%PDF-1.4 content1")
        (input_dir / "doc2.pdf").write_bytes(b"%PDF-1.4 content2")

        output_dir = tmp_path / "output"

        # Mock service
        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# Converted"
        mock_result.quality_score = 0.8
        mock_result.metadata = {"extractor": "Test"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service

        result = runner.invoke(
            app, ["batch", str(input_dir), str(output_dir), "--pattern", "*.pdf"]
        )

        assert result.exit_code == 0
        assert (output_dir / "doc1.md").exists()
        assert (output_dir / "doc2.md").exists()

    def test_batch_input_directory_not_found(self, runner, tmp_path):
        """Test batch with non-existent input directory."""
        input_dir = tmp_path / "does_not_exist"
        output_dir = tmp_path / "output"

        result = runner.invoke(app, ["batch", str(input_dir), str(output_dir)])

        assert result.exit_code == 1
        assert "Directory not found" in result.stdout

    @patch("pydocextractor.cli.create_converter_service")
    def test_batch_no_matching_files(self, mock_service_factory, runner, tmp_path):
        """Test batch with no matching files."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        result = runner.invoke(
            app, ["batch", str(input_dir), str(output_dir), "--pattern", "*.pdf"]
        )

        assert result.exit_code == 0
        assert "No files found" in result.stdout

    @patch("pydocextractor.cli.create_converter_service")
    def test_batch_creates_output_directory(self, mock_service_factory, runner, tmp_path):
        """Test that batch creates output directory if it doesn't exist."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "doc.pdf").write_bytes(b"%PDF-1.4 content")

        output_dir = tmp_path / "nonexistent" / "output"

        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# Converted"
        mock_result.quality_score = 0.8
        mock_result.metadata = {"extractor": "Test"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service

        result = runner.invoke(app, ["batch", str(input_dir), str(output_dir)])

        assert result.exit_code == 0
        assert output_dir.exists()
        assert output_dir.is_dir()

    @patch("pydocextractor.cli.create_converter_service")
    def test_batch_with_precision_level(self, mock_service_factory, runner, tmp_path):
        """Test batch with specific precision level."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "doc.pdf").write_bytes(b"%PDF-1.4 content")

        output_dir = tmp_path / "output"

        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "# Converted"
        mock_result.quality_score = 0.8
        mock_result.metadata = {"extractor": "Test"}
        mock_service.convert_to_markdown.return_value = mock_result
        mock_service_factory.return_value = mock_service

        result = runner.invoke(app, ["batch", str(input_dir), str(output_dir), "--level", "4"])

        assert result.exit_code == 0


class TestInfoCommand:
    """Test the info command."""

    @patch("pydocextractor.cli.get_available_extractors")
    @patch("pydocextractor.cli.calculate_document_hash")
    def test_info_shows_document_information(
        self, mock_hash, mock_get_extractors, runner, sample_pdf
    ):
        """Test that info command shows document information."""
        mock_hash.return_value = "abc123def456"
        mock_get_extractors.return_value = []

        result = runner.invoke(app, ["info", str(sample_pdf)])

        assert result.exit_code == 0
        assert "Document Information" in result.stdout
        assert "test.pdf" in result.stdout
        assert "MIME" in result.stdout
        assert "SHA-256" in result.stdout

    def test_info_file_not_found(self, runner, tmp_path):
        """Test info command with non-existent file."""
        non_existent = tmp_path / "does_not_exist.pdf"

        result = runner.invoke(app, ["info", str(non_existent)])

        assert result.exit_code == 1
        assert "File not found" in result.stdout

    @patch("pydocextractor.cli.get_available_extractors")
    @patch("pydocextractor.cli.calculate_document_hash")
    @patch("pydocextractor.cli.hint_has_tables")
    def test_info_shows_recommended_converter(
        self, mock_tables, mock_hash, mock_get_extractors, runner, sample_pdf
    ):
        """Test that info command shows recommended converter."""
        mock_hash.return_value = "abc123"
        mock_tables.return_value = True
        mock_extractor = Mock()
        mock_get_extractors.return_value = [mock_extractor]

        result = runner.invoke(app, ["info", str(sample_pdf)])

        assert result.exit_code == 0
        assert "Recommended converter" in result.stdout
