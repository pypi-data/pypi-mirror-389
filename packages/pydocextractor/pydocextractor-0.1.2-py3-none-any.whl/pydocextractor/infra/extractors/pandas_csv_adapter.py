"""
Pandas-based CSV extractor adapter.

Extracts CSV files with rich metadata including column types and statistics.
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


class PandasCSVExtractor:
    """Extract CSV files using pandas with rich metadata."""

    @property
    def name(self) -> str:
        return "PandasCSV"

    @property
    def precision_level(self) -> PrecisionLevel:
        return PrecisionLevel.HIGHEST_QUALITY

    def is_available(self) -> bool:
        """Check if dependencies are installed."""
        return PANDAS_AVAILABLE

    def supports(self, mime: str) -> bool:
        """Check if this extractor supports the MIME type."""
        return mime == "text/csv" and PANDAS_AVAILABLE

    def extract(self, data: bytes, precision: PrecisionLevel) -> ExtractionResult:
        """
        Extract CSV content using pandas with metadata.

        Args:
            data: CSV bytes
            precision: Precision level (informational)

        Returns:
            ExtractionResult with normalized document or error
        """
        if not PANDAS_AVAILABLE:
            return ExtractionResult(
                success=False,
                error="Pandas not available - install with: pip install pandas",
                extractor_name=self.name,
            )

        start_time = time.time()

        try:
            # Read CSV with pandas, auto-detect delimiter
            import io

            # Try to auto-detect delimiter
            df = pd.read_csv(io.BytesIO(data), sep=None, engine="python")

            # Calculate content hash
            content_hash = hashlib.sha256(data).hexdigest()

            # Identify column types
            numerical_columns = df.select_dtypes(include=["number"]).columns.tolist()
            categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

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

            # Count duplicate rows
            duplicate_count = int(df.duplicated().sum())

            # Generate markdown table with sample (first 5 rows)
            sample_df = df.head(5)
            markdown_table = sample_df.to_markdown(index=False)

            # Create blocks
            blocks = []

            # Add table block (sample only)
            if markdown_table:
                blocks.append(
                    Block(
                        type=BlockType.TABLE,
                        content=markdown_table,
                        metadata={
                            "source": "pandas",
                            "is_sample": len(df) > SAMPLE_THRESHOLD,
                            "total_rows": len(df),
                        },
                    )
                )

            # Add statistics summary as text
            stats_lines = []
            stats_lines.append("\n## Statistics\n")

            if numerical_columns:
                stats_lines.append("\n### Numerical Columns\n")
                for col, stats in numerical_stats.items():
                    stats_lines.append(
                        f"- **{col}**: min={stats['min']:.2f}, max={stats['max']:.2f}, "
                        f"mean={stats['mean']:.2f}, std={stats['std']:.2f}\n"
                    )

            if categorical_columns:
                stats_lines.append("\n### Categorical Columns\n")
                for col, stats in categorical_stats.items():
                    stats_lines.append(f"- **{col}** ({stats['unique_count']} unique values):\n")
                    stats_lines.append(f"  - Mode: {stats['mode']}\n")
                    stats_lines.append("  - Frequency distribution:\n")

                    # Show top 5 most frequent values
                    freq_data: dict[str, int] = stats["frequencies"]  # type: ignore[assignment]
                    if isinstance(freq_data, dict):
                        sorted_freqs = sorted(freq_data.items(), key=lambda x: x[1], reverse=True)[
                            :5
                        ]
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
                        metadata={"category": "statistics"},
                    )
                )

            # Create metadata
            metadata: dict[str, Any] = {
                "content_hash": content_hash,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "numerical_columns": numerical_columns,
                "categorical_columns": categorical_columns,
                "numerical_stats": numerical_stats,
                "categorical_stats": categorical_stats,
                "duplicate_count": duplicate_count,
                "sheet_names": ["CSV"],  # CSV files are single sheet
            }

            # Create normalized document
            ndoc = NormalizedDoc(
                blocks=tuple(blocks),
                source_mime="text/csv",
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

        except pd.errors.EmptyDataError:
            return ExtractionResult(
                success=False,
                error="CSV file is empty",
                extractor_name=self.name,
            )
        except pd.errors.ParserError as e:
            return ExtractionResult(
                success=False,
                error=f"CSV parsing error: {e}",
                extractor_name=self.name,
            )
        except Exception as e:
            raise ExtractionError(f"Pandas CSV extraction failed: {e}") from e
