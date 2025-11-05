"""
Comprehensive tests for Pandas-based extractors (CSV and Excel).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pydocextractor.domain.errors import ExtractionError
from pydocextractor.domain.models import PrecisionLevel
from pydocextractor.infra.extractors.pandas_csv_adapter import PandasCSVExtractor
from pydocextractor.infra.extractors.pandas_excel_adapter import PandasExcelExtractor


class TestPandasCSVExtractor:
    """Comprehensive tests for PandasCSV extractor."""

    def test_properties(self):
        """Test extractor basic properties."""
        extractor = PandasCSVExtractor()

        assert extractor.name == "PandasCSV"
        assert extractor.precision_level == PrecisionLevel.HIGHEST_QUALITY
        assert isinstance(extractor.is_available(), bool)

    def test_supports_csv(self):
        """Test extractor supports CSV."""
        extractor = PandasCSVExtractor()

        # Support depends on pandas availability
        result = extractor.supports("text/csv")
        assert isinstance(result, bool)

    def test_does_not_support_pdf(self):
        """Test extractor does not support PDF."""
        extractor = PandasCSVExtractor()

        assert extractor.supports("application/pdf") is False

    @patch("pydocextractor.infra.extractors.pandas_csv_adapter.PANDAS_AVAILABLE", False)
    def test_extract_pandas_not_available(self):
        """Test extraction fails gracefully when pandas is not available."""
        extractor = PandasCSVExtractor()

        result = extractor.extract(b"fake csv data", PrecisionLevel.HIGHEST_QUALITY)

        assert result.success is False
        assert "Pandas not available" in result.error
        assert result.extractor_name == "PandasCSV"

    @patch("pydocextractor.infra.extractors.pandas_csv_adapter.PANDAS_AVAILABLE", True)
    def test_extract_success_simple_csv(self):
        """Test successful extraction of simple CSV."""
        extractor = PandasCSVExtractor()

        csv_data = b"name,age,city\nAlice,30,NYC\nBob,25,SF"

        with patch("pydocextractor.infra.extractors.pandas_csv_adapter.pd") as mock_pd:
            # Create mock DataFrame
            mock_df = MagicMock()
            mock_df.to_markdown.return_value = (
                "| name | age | city |\n|------|-----|------|\n| Alice | 30 | NYC |"
            )
            mock_df.__len__.return_value = 2

            # Mock columns as an object with tolist method
            mock_columns = MagicMock()
            mock_columns.tolist.return_value = ["name", "age", "city"]
            mock_df.columns = mock_columns

            # Mock select_dtypes for numerical and categorical columns
            numerical_cols = MagicMock()
            numerical_cols.columns.tolist.return_value = ["age"]
            categorical_cols = MagicMock()
            categorical_cols.columns.tolist.return_value = ["name", "city"]
            mock_df.select_dtypes.side_effect = [numerical_cols, categorical_cols]

            # Mock column access for statistics
            age_col = MagicMock()
            age_col.min.return_value = 25
            age_col.max.return_value = 30
            age_col.mean.return_value = 27.5

            name_col = MagicMock()
            mode_result = MagicMock()
            mode_result.iloc = ["Alice"]
            mode_result.__len__.return_value = 1
            name_col.mode.return_value = mode_result

            city_col = MagicMock()
            city_mode_result = MagicMock()
            city_mode_result.iloc = ["NYC"]
            city_mode_result.__len__.return_value = 1
            city_col.mode.return_value = city_mode_result

            def getitem_side_effect(key):
                if key == "age":
                    return age_col
                elif key == "name":
                    return name_col
                elif key == "city":
                    return city_col
                return MagicMock()

            mock_df.__getitem__.side_effect = getitem_side_effect
            mock_df.duplicated.return_value.sum.return_value = 0

            mock_pd.read_csv.return_value = mock_df
            mock_pd.errors.EmptyDataError = Exception
            mock_pd.errors.ParserError = Exception

            result = extractor.extract(csv_data, PrecisionLevel.HIGHEST_QUALITY)

        if result.success:
            assert result.normalized_doc is not None
            assert result.normalized_doc.source_mime == "text/csv"
            assert result.normalized_doc.has_tables is True
            assert result.processing_time_seconds is not None

    @patch("pydocextractor.infra.extractors.pandas_csv_adapter.PANDAS_AVAILABLE", True)
    def test_extract_empty_csv(self):
        """Test extraction handles empty CSV."""
        extractor = PandasCSVExtractor()

        with patch("pydocextractor.infra.extractors.pandas_csv_adapter.pd") as mock_pd:
            # Create proper exception classes that inherit from BaseException
            class MockEmptyDataError(Exception):
                pass

            class MockParserError(Exception):
                pass

            mock_pd.errors.EmptyDataError = MockEmptyDataError
            mock_pd.errors.ParserError = MockParserError
            mock_pd.read_csv.side_effect = MockEmptyDataError("Empty CSV")

            result = extractor.extract(b"", PrecisionLevel.HIGHEST_QUALITY)

        assert result.success is False
        assert "CSV file is empty" in result.error

    @patch("pydocextractor.infra.extractors.pandas_csv_adapter.PANDAS_AVAILABLE", True)
    def test_extract_malformed_csv(self):
        """Test extraction handles malformed CSV."""
        extractor = PandasCSVExtractor()

        with patch("pydocextractor.infra.extractors.pandas_csv_adapter.pd") as mock_pd:
            # Create proper exception classes that inherit from BaseException
            class MockParserError(Exception):
                pass

            class MockEmptyDataError(Exception):
                pass

            mock_pd.errors.ParserError = MockParserError
            mock_pd.errors.EmptyDataError = MockEmptyDataError
            mock_pd.read_csv.side_effect = MockParserError("Parser error")

            result = extractor.extract(b"malformed", PrecisionLevel.HIGHEST_QUALITY)

        assert result.success is False
        assert "CSV parsing error" in result.error

    @patch("pydocextractor.infra.extractors.pandas_csv_adapter.PANDAS_AVAILABLE", True)
    def test_extract_includes_statistics(self):
        """Test extraction includes statistics."""
        extractor = PandasCSVExtractor()

        csv_data = b"value\n10\n20\n30"

        with patch("pydocextractor.infra.extractors.pandas_csv_adapter.pd") as mock_pd:
            mock_df = MagicMock()
            mock_df.to_markdown.return_value = "| value |\n|-------|\n| 10 |"
            mock_df.__len__.return_value = 3

            # Mock columns with tolist method
            mock_columns = MagicMock()
            mock_columns.tolist.return_value = ["value"]
            mock_df.columns = mock_columns

            # Mock select_dtypes to return numerical columns
            numerical_mock = MagicMock()
            numerical_mock.columns.tolist.return_value = ["value"]
            categorical_mock = MagicMock()
            categorical_mock.columns.tolist.return_value = []

            mock_df.select_dtypes.side_effect = [numerical_mock, categorical_mock]

            # Mock column statistics
            col_mock = MagicMock()
            col_mock.min.return_value = 10
            col_mock.max.return_value = 30
            col_mock.mean.return_value = 20.0
            mock_df.__getitem__.return_value = col_mock

            mock_df.duplicated.return_value.sum.return_value = 0

            mock_pd.read_csv.return_value = mock_df

            result = extractor.extract(csv_data, PrecisionLevel.HIGHEST_QUALITY)

        if result.success:
            metadata = result.normalized_doc.metadata
            assert "numerical_stats" in metadata
            assert "categorical_stats" in metadata
            assert "duplicate_count" in metadata


class TestPandasExcelExtractor:
    """Comprehensive tests for PandasExcel extractor."""

    def test_properties(self):
        """Test extractor basic properties."""
        extractor = PandasExcelExtractor()

        assert extractor.name == "PandasExcel"
        assert extractor.precision_level == PrecisionLevel.HIGHEST_QUALITY
        assert isinstance(extractor.is_available(), bool)

    def test_supports_xlsx(self):
        """Test extractor supports XLSX."""
        extractor = PandasExcelExtractor()

        result = extractor.supports(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert isinstance(result, bool)

    def test_supports_xls(self):
        """Test extractor supports XLS."""
        extractor = PandasExcelExtractor()

        result = extractor.supports("application/vnd.ms-excel")
        assert isinstance(result, bool)

    def test_does_not_support_pdf(self):
        """Test extractor does not support PDF."""
        extractor = PandasExcelExtractor()

        assert extractor.supports("application/pdf") is False

    @patch("pydocextractor.infra.extractors.pandas_excel_adapter.PANDAS_AVAILABLE", False)
    def test_extract_pandas_not_available(self):
        """Test extraction fails gracefully when pandas is not available."""
        extractor = PandasExcelExtractor()

        result = extractor.extract(b"fake excel data", PrecisionLevel.HIGHEST_QUALITY)

        assert result.success is False
        assert "Pandas not available" in result.error
        assert result.extractor_name == "PandasExcel"

    @patch("pydocextractor.infra.extractors.pandas_excel_adapter.PANDAS_AVAILABLE", True)
    def test_extract_success_single_sheet(self):
        """Test successful extraction of single sheet Excel."""
        extractor = PandasExcelExtractor()

        with patch("pydocextractor.infra.extractors.pandas_excel_adapter.pd") as mock_pd:
            # Create mock Excel file
            mock_excel = MagicMock()
            mock_excel.sheet_names = ["Sheet1"]

            # Create mock DataFrame
            mock_df = MagicMock()
            mock_df.to_markdown.return_value = "| col1 | col2 |\n|------|------|\n| A | 1 |"
            mock_df.__len__.return_value = 1
            mock_df.columns = ["col1", "col2"]
            mock_df.select_dtypes.return_value.columns.tolist.side_effect = [
                ["col2"],  # numerical
                ["col1"],  # categorical
            ]
            mock_df.__getitem__.return_value.min.return_value = 1
            mock_df.__getitem__.return_value.max.return_value = 1
            mock_df.__getitem__.return_value.mean.return_value = 1.0
            mock_df.__getitem__.return_value.mode.return_value.iloc = {0: "A"}
            mock_df.__getitem__.return_value.mode.return_value.__len__.return_value = 1
            mock_df.duplicated.return_value.sum.return_value = 0

            mock_pd.ExcelFile.return_value = mock_excel
            mock_pd.read_excel.return_value = mock_df

            result = extractor.extract(b"fake excel data", PrecisionLevel.HIGHEST_QUALITY)

        if result.success:
            assert result.normalized_doc is not None
            assert result.normalized_doc.has_tables is True
            assert result.processing_time_seconds is not None

    @patch("pydocextractor.infra.extractors.pandas_excel_adapter.PANDAS_AVAILABLE", True)
    def test_extract_multiple_sheets(self):
        """Test extraction with multiple sheets."""
        extractor = PandasExcelExtractor()

        with patch("pydocextractor.infra.extractors.pandas_excel_adapter.pd") as mock_pd:
            # Create mock Excel file
            mock_excel = MagicMock()
            mock_excel.sheet_names = ["Sheet1", "Sheet2"]

            # Create mock DataFrames
            def create_mock_df(sheet_name):
                mock_df = MagicMock()
                mock_df.to_markdown.return_value = f"| data |\n|------|\n| {sheet_name} |"
                mock_df.__len__.return_value = 1
                mock_df.columns = ["data"]
                mock_df.select_dtypes.return_value.columns.tolist.side_effect = [
                    [],  # numerical
                    ["data"],  # categorical
                ]
                mock_df.__getitem__.return_value.mode.return_value.iloc = {0: sheet_name}
                mock_df.__getitem__.return_value.mode.return_value.__len__.return_value = 1
                mock_df.duplicated.return_value.sum.return_value = 0
                return mock_df

            mock_pd.ExcelFile.return_value = mock_excel
            mock_pd.read_excel.side_effect = [
                create_mock_df("Sheet1"),
                create_mock_df("Sheet2"),
            ]

            result = extractor.extract(b"fake excel data", PrecisionLevel.HIGHEST_QUALITY)

        if result.success:
            metadata = result.normalized_doc.metadata
            assert metadata["sheet_count"] == 2
            assert "Sheet1" in metadata["sheet_names"]
            assert "Sheet2" in metadata["sheet_names"]

    @patch("pydocextractor.infra.extractors.pandas_excel_adapter.PANDAS_AVAILABLE", True)
    def test_extract_handles_errors(self):
        """Test extraction handles generic errors."""
        extractor = PandasExcelExtractor()

        with patch("pydocextractor.infra.extractors.pandas_excel_adapter.pd") as mock_pd:
            mock_pd.ExcelFile.side_effect = Exception("Generic error")

            with pytest.raises(ExtractionError):
                extractor.extract(b"fake excel data", PrecisionLevel.HIGHEST_QUALITY)

    @patch("pydocextractor.infra.extractors.pandas_excel_adapter.PANDAS_AVAILABLE", True)
    def test_extract_includes_sheet_statistics(self):
        """Test extraction includes per-sheet statistics."""
        extractor = PandasExcelExtractor()

        with patch("pydocextractor.infra.extractors.pandas_excel_adapter.pd") as mock_pd:
            mock_excel = MagicMock()
            mock_excel.sheet_names = ["Data"]

            mock_df = MagicMock()
            mock_df.to_markdown.return_value = "| value |\n|-------|\n| 10 |"
            mock_df.__len__.return_value = 3
            mock_df.columns = ["value"]

            numerical_mock = MagicMock()
            numerical_mock.columns.tolist.return_value = ["value"]
            categorical_mock = MagicMock()
            categorical_mock.columns.tolist.return_value = []

            mock_df.select_dtypes.side_effect = [numerical_mock, categorical_mock]

            col_mock = MagicMock()
            col_mock.min.return_value = 10
            col_mock.max.return_value = 30
            col_mock.mean.return_value = 20.0
            mock_df.__getitem__.return_value = col_mock

            mock_df.duplicated.return_value.sum.return_value = 0

            mock_pd.ExcelFile.return_value = mock_excel
            mock_pd.read_excel.return_value = mock_df

            result = extractor.extract(b"fake excel data", PrecisionLevel.HIGHEST_QUALITY)

        if result.success:
            metadata = result.normalized_doc.metadata
            assert "numerical_stats" in metadata
            assert "Data" in metadata["numerical_stats"]
            assert "categorical_stats" in metadata
            assert "duplicate_counts" in metadata
