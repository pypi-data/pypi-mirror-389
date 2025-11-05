"""
Pandas-based Excel extractor adapter.

Extracts Excel files with multi-sheet support and rich metadata.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from pydocextractor.domain.errors import ExtractionError
from pydocextractor.domain.models import (
    Block,
    BlockType,
    ExtractionResult,
    NormalizedDoc,
    PrecisionLevel,
)

# Check pandas availability
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Constants for sample detection
SAMPLE_THRESHOLD = 5


class PandasExcelExtractor:
    """Extract Excel files using pandas with multi-sheet support and rich metadata."""

    @property
    def name(self) -> str:
        return "PandasExcel"

    @property
    def precision_level(self) -> PrecisionLevel:
        return PrecisionLevel.HIGHEST_QUALITY

    def is_available(self) -> bool:
        """Check if dependencies are installed."""
        return PANDAS_AVAILABLE

    def supports(self, mime: str) -> bool:
        """Check if this extractor supports the MIME type."""
        supported_mimes = [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # XLSX
            "application/vnd.ms-excel",  # XLS
        ]
        return mime in supported_mimes and PANDAS_AVAILABLE

    def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
        """
        Extract Excel content using pandas with multi-sheet metadata.

        Args:
            data: Excel file bytes
            precision: Precision level (informational)

        Returns:
            ExtractionResult with normalized document or error
        """
        if not PANDAS_AVAILABLE:
            return ExtractionResult(
                success=False,
                error="Pandas not available - install with: pip install pandas openpyxl",
                extractor_name=self.name,
            )

        start_time = time.time()

        try:
            # Read Excel file with all sheets
            import io

            excel_file = pd.ExcelFile(io.BytesIO(data))
            sheet_names = excel_file.sheet_names

            # Calculate content hash
            content_hash = hashlib.sha256(data).hexdigest()

            blocks = []
            all_numerical_columns = {}
            all_categorical_columns = {}
            all_numerical_stats = {}
            all_categorical_stats = {}
            all_duplicate_counts = {}
            total_rows = 0

            # Process each sheet
            for sheet_name in sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)

                # Identify column types
                numerical_columns = df.select_dtypes(include=["number"]).columns.tolist()
                categorical_columns = df.select_dtypes(
                    include=["object", "category"]
                ).columns.tolist()

                all_numerical_columns[sheet_name] = numerical_columns
                all_categorical_columns[sheet_name] = categorical_columns

                # Calculate enhanced statistics for numerical columns
                numerical_stats = {}
                for col in numerical_columns:
                    numerical_stats[col] = {
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "mean": float(df[col].mean()),
                        "std": float(df[col].std()),
                        "count": int(df[col].count()),
                    }
                all_numerical_stats[sheet_name] = numerical_stats

                # Calculate mode and frequency distribution for categorical columns
                categorical_stats: dict[str, dict[str, Any]] = {}
                for col in categorical_columns:
                    value_counts = df[col].value_counts()
                    mode_val = value_counts.index[0] if len(value_counts) > 0 else "N/A"

                    # Convert frequencies to dict for serialization
                    frequencies: dict[str, int] = {str(k): int(v) for k, v in value_counts.items()}

                    categorical_stats[col] = {
                        "mode": str(mode_val),
                        "frequencies": frequencies,
                        "unique_count": len(value_counts),
                        "count": int(df[col].count()),
                    }
                all_categorical_stats[sheet_name] = categorical_stats

                # Count duplicate rows
                duplicate_count = int(df.duplicated().sum())
                all_duplicate_counts[sheet_name] = duplicate_count

                total_rows += len(df)

                # Add sheet heading
                blocks.append(
                    Block(
                        type=BlockType.TEXT,
                        content=f"## {sheet_name}\n",
                        metadata={"category": "sheet_heading", "sheet_name": sheet_name},
                    )
                )

                # Generate markdown table for this sheet (sample first 5 rows)
                sample_df = df.head(5)
                markdown_table = sample_df.to_markdown(index=False)
                if markdown_table:
                    blocks.append(
                        Block(
                            type=BlockType.TABLE,
                            content=markdown_table,
                            metadata={
                                "source": "pandas",
                                "sheet_name": sheet_name,
                                "is_sample": len(df) > SAMPLE_THRESHOLD,
                                "total_rows": len(df),
                            },
                        )
                    )

                # Add statistics summary for this sheet
                stats_lines = []
                stats_lines.append(f"\n### Statistics for {sheet_name}\n")

                if numerical_columns:
                    stats_lines.append("\n**Numerical Columns:**\n")
                    for col, stats in numerical_stats.items():
                        stats_lines.append(
                            f"- **{col}**: min={stats['min']:.2f}, max={stats['max']:.2f}, "
                            f"mean={stats['mean']:.2f}, std={stats['std']:.2f}\n"
                        )

                if categorical_columns:
                    stats_lines.append("\n**Categorical Columns:**\n")
                    for col, stats in categorical_stats.items():
                        stats_lines.append(
                            f"- **{col}** ({stats['unique_count']} unique values):\n"
                        )
                        stats_lines.append(f"  - Mode: {stats['mode']}\n")
                        stats_lines.append("  - Frequency distribution:\n")

                        # Show top 5 most frequent values
                        freq_data: dict[str, int] = stats["frequencies"]  # type: ignore[assignment]
                        if isinstance(freq_data, dict):
                            sorted_freqs = sorted(
                                freq_data.items(), key=lambda x: x[1], reverse=True
                            )[:5]
                        else:
                            sorted_freqs = []
                        for value, count in sorted_freqs:
                            percentage = (count / len(df)) * 100
                            stats_lines.append(f"    - `{value}`: {count} ({percentage:.1f}%)\n")

                if duplicate_count > 0:
                    stats_lines.append(f"\n**Duplicate rows**: {duplicate_count}")

                if stats_lines:
                    blocks.append(
                        Block(
                            type=BlockType.TEXT,
                            content="".join(stats_lines),
                            metadata={"category": "statistics", "sheet_name": sheet_name},
                        )
                    )

            # Create global metadata
            metadata: dict[str, Any] = {
                "content_hash": content_hash,
                "total_rows": total_rows,
                "sheet_names": sheet_names,
                "sheet_count": len(sheet_names),
                "numerical_columns": all_numerical_columns,
                "categorical_columns": all_categorical_columns,
                "numerical_stats": all_numerical_stats,
                "categorical_stats": all_categorical_stats,
                "duplicate_counts": all_duplicate_counts,
            }

            # Create normalized document
            ndoc = NormalizedDoc(
                blocks=tuple(blocks),
                source_mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                page_count=None,
                has_tables=True,
                has_images=False,
                extractor_name=self.name,
                metadata=metadata,
            )

            elapsed = time.time() - start_time

            return ExtractionResult(
                success=True,
                normalized_doc=ndoc,
                extractor_name=self.name,
                processing_time_seconds=elapsed,
            )

        except Exception as e:
            raise ExtractionError(f"Pandas Excel extraction failed: {e}") from e
