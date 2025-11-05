"""
Table profiler for analyzing tables in extracted documents.

Detects tables in markdown format and computes comprehensive statistics
including numerical summaries and categorical frequency distributions.
"""

from __future__ import annotations

import re
from typing import Any

from pydocextractor.domain.models import Block, BlockType, NormalizedDoc

# Constants for table validation
MIN_TABLE_LINES = 3  # Need at least header, separator, and one data row
MIN_TABLE_ROWS = 2  # Need at least header and one data row

# Check pandas availability
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class TableProfiler:
    """
    Analyzes tables detected in PDF/Word documents and enriches them with statistics.

    This profiler:
    - Detects TABLE blocks in NormalizedDoc
    - Parses markdown tables back to DataFrames
    - Calculates comprehensive statistics (min, max, mean, std, frequencies)
    - Creates sample output (max 5 rows)
    - Injects statistics blocks into the document
    """

    def __init__(self, max_sample_rows: int = 5):
        """
        Initialize the table profiler.

        Args:
            max_sample_rows: Maximum number of rows to include in sample output
        """
        self.max_sample_rows = max_sample_rows

    def profile(self, ndoc: NormalizedDoc) -> NormalizedDoc:
        """
        Find all TABLE blocks in document and add statistics.

        Args:
            ndoc: Normalized document with blocks

        Returns:
            Enhanced NormalizedDoc with statistics blocks added
        """
        if not PANDAS_AVAILABLE:
            # Return unchanged if pandas not available
            return ndoc

        # Skip profiling for CSV/Excel extractors since they already generate
        # comprehensive statistics from the full dataset
        if ndoc.extractor_name in ["PandasCSV", "PandasExcel"]:
            return ndoc

        enhanced_blocks = []
        table_stats_metadata = {}
        table_index = 0

        for _idx, block in enumerate(ndoc.blocks):
            enhanced_blocks.append(block)

            # Process TABLE blocks
            if block.type == BlockType.TABLE:
                try:
                    # Profile this table
                    stats = self.profile_table(block.content)

                    if stats:
                        # Store in metadata
                        table_stats_metadata[f"table_{table_index}"] = stats

                        # Create a new STATISTICS block to insert after table
                        stats_block = self._create_statistics_block(stats, table_index)
                        enhanced_blocks.append(stats_block)

                        table_index += 1
                except Exception as e:
                    # If table profiling fails, continue with next block
                    # Log error in metadata
                    table_stats_metadata[f"table_{table_index}_error"] = {"error": str(e)}
                    table_index += 1

        # Update metadata with table statistics
        updated_metadata = {**ndoc.metadata, "table_statistics": table_stats_metadata}

        # Create enhanced normalized document
        return NormalizedDoc(
            blocks=tuple(enhanced_blocks),
            source_mime=ndoc.source_mime,
            page_count=ndoc.page_count,
            has_tables=ndoc.has_tables,
            has_images=ndoc.has_images,
            extractor_name=ndoc.extractor_name,
            metadata=updated_metadata,
        )

    def profile_table(self, markdown_table: str) -> dict[str, Any] | None:
        """
        Analyze a markdown table and return comprehensive statistics.

        Args:
            markdown_table: Table in markdown pipe format

        Returns:
            Dictionary with statistics or None if parsing fails
        """
        if not PANDAS_AVAILABLE or not markdown_table:
            return None

        try:
            # Parse markdown table to DataFrame
            df = self._parse_markdown_table(markdown_table)

            if df is None or df.empty:
                return None

            # Create sample (first N rows)
            sample_df = df.head(self.max_sample_rows)
            sample_markdown = sample_df.to_markdown(index=False)

            # Identify column types
            numerical_columns = df.select_dtypes(include=["number"]).columns.tolist()
            categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

            # Calculate enhanced statistics
            numerical_stats = self._calculate_numerical_stats(df, numerical_columns)
            categorical_stats = self._calculate_categorical_stats(df, categorical_columns)

            # Count duplicate rows
            duplicate_count = int(df.duplicated().sum())

            return {
                "sample_data": sample_markdown,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "numerical_columns": numerical_columns,
                "categorical_columns": categorical_columns,
                "numerical_stats": numerical_stats,
                "categorical_stats": categorical_stats,
                "duplicate_count": duplicate_count,
            }

        except Exception:
            # Return None if table parsing/profiling fails
            return None

    def _split_merged_table_rows(self, markdown: str) -> str:
        """
        Split table rows that have multiple values merged with <br> tags.

        Some PDF extractors merge multiple logical rows into single cells using
        <br> as separator. This method detects and splits them back into proper rows.

        Args:
            markdown: Markdown table with potentially merged rows

        Returns:
            Markdown table with rows properly split
        """
        # Check if table has <br> tags indicating merged rows
        if "<br>" not in markdown:
            return markdown

        try:
            lines = [line.strip() for line in markdown.strip().split("\n") if line.strip()]

            if len(lines) < MIN_TABLE_LINES:  # Need at least header, separator, and one data row
                return markdown

            # Find header and separator
            header_line = None
            separator_idx = None

            for idx, line in enumerate(lines):
                if "|" in line and header_line is None:
                    header_line = line
                    # Next line should be separator
                    if idx + 1 < len(lines) and re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[idx + 1]):
                        separator_idx = idx + 1
                        break

            if header_line is None or separator_idx is None:
                return markdown

            # Parse header (and clean any <br> tags to just keep the first part)
            raw_headers = self._parse_table_row(header_line)
            headers = []
            for header in raw_headers:
                # If header has <br>, only keep the part before data starts
                # (some extractors put data values in headers)
                if "<br>" in header:
                    parts = [p.strip() for p in header.split("<br>")]
                    # Keep only non-numeric parts for the header
                    header_parts = []
                    for part in parts:
                        # Stop at first numeric value or $ sign alone
                        clean_part = part.strip().strip("*").strip()
                        if clean_part and not (
                            clean_part.replace(",", "").replace(".", "").replace("-", "").isdigit()
                            or clean_part == "$"
                        ):
                            header_parts.append(part)
                        else:
                            break
                    headers.append("<br>".join(header_parts) if header_parts else parts[0])
                else:
                    headers.append(header)

            # Parse separator to preserve alignment
            separator_parts = [s.strip() for s in lines[separator_idx].split("|") if s.strip()]

            # Process data rows
            new_data_rows = []
            for line in lines[separator_idx + 1 :]:
                if "|" not in line:
                    continue

                cells = self._parse_table_row(line)

                # Check if any cell has <br> tags
                has_br = any("<br>" in str(cell) for cell in cells)

                if has_br:
                    # Split cells by <br>
                    split_cells = []
                    for cell in cells:
                        # Split by <br> and clean each part
                        parts = [part.strip() for part in str(cell).split("<br>")]
                        split_cells.append(parts)

                    # Find maximum number of splits
                    max_splits = max(len(parts) for parts in split_cells)

                    # Create new rows
                    for i in range(max_splits):
                        new_row = []
                        for cell_parts in split_cells:
                            if i < len(cell_parts):
                                new_row.append(cell_parts[i])
                            else:
                                new_row.append("")  # Empty cell
                        new_data_rows.append(new_row)
                else:
                    # Keep row as-is
                    new_data_rows.append(cells)

            # Reconstruct markdown table
            result_lines = []

            # Add header
            result_lines.append("| " + " | ".join(headers) + " |")

            # Add separator
            result_lines.append("| " + " | ".join(separator_parts) + " |")

            # Add data rows
            for row in new_data_rows:
                # Pad row if needed to match header length
                while len(row) < len(headers):
                    row.append("")
                result_lines.append("| " + " | ".join(row[: len(headers)]) + " |")

            return "\n".join(result_lines)

        except Exception:
            # If splitting fails, return original markdown
            return markdown

    def _parse_table_row(self, line: str) -> list[str]:
        """
        Parse a markdown table row into cells.

        Args:
            line: Markdown table row with | delimiters

        Returns:
            List of cell contents
        """
        cells = [cell.strip() for cell in line.split("|")]
        # Remove empty first/last elements from | at start/end
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        return cells

    def _parse_markdown_table(self, markdown: str) -> pd.DataFrame | None:
        """
        Parse markdown pipe table to DataFrame.

        Args:
            markdown: Markdown table string with | delimiters

        Returns:
            DataFrame or None if parsing fails
        """
        if not PANDAS_AVAILABLE:
            return None

        try:
            # Preprocess: split merged rows with <br> tags
            markdown = self._split_merged_table_rows(markdown)

            # Split into lines and clean
            lines = [line.strip() for line in markdown.strip().split("\n") if line.strip()]

            if len(lines) < MIN_TABLE_ROWS:
                return None

            # Find header line (first line with |)
            header_line = None
            separator_idx = None

            for idx, line in enumerate(lines):
                if "|" in line and header_line is None:
                    header_line = line
                    # Next line should be separator (---|---|---)
                    if idx + 1 < len(lines) and re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[idx + 1]):
                        separator_idx = idx + 1
                        break

            if header_line is None or separator_idx is None:
                return None

            # Parse header
            header = [col.strip() for col in header_line.split("|") if col.strip()]

            # Parse data rows (skip header and separator)
            data_rows = []
            for line in lines[separator_idx + 1 :]:
                if "|" in line:
                    row = [cell.strip() for cell in line.split("|") if cell or cell == ""]
                    # Remove empty first/last elements from | at start/end
                    if row and row[0] == "":
                        row = row[1:]
                    if row and row[-1] == "":
                        row = row[:-1]
                    if row:
                        data_rows.append(row)

            if not data_rows:
                return None

            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=header if header else None)

            # Try to infer numeric types
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    # Keep as string/object
                    pass

            return df

        except Exception:
            return None

    def _calculate_numerical_stats(
        self, df: pd.DataFrame, columns: list[str]
    ) -> dict[str, dict[str, float]]:
        """
        Calculate min, max, mean, std for numerical columns.

        Args:
            df: DataFrame with data
            columns: List of numerical column names

        Returns:
            Dictionary mapping column names to statistics
        """
        stats = {}
        for col in columns:
            stats[col] = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "count": int(df[col].count()),
            }
        return stats

    def _calculate_categorical_stats(
        self, df: pd.DataFrame, columns: list[str]
    ) -> dict[str, dict[str, Any]]:
        """
        Calculate mode and frequency distribution for categorical columns.

        Args:
            df: DataFrame with data
            columns: List of categorical column names

        Returns:
            Dictionary mapping column names to statistics including frequencies
        """
        stats = {}
        for col in columns:
            value_counts = df[col].value_counts()
            mode_val = value_counts.index[0] if len(value_counts) > 0 else "N/A"

            # Convert frequencies to regular dict for JSON serialization
            frequencies = {str(k): int(v) for k, v in value_counts.items()}

            stats[col] = {
                "mode": str(mode_val),
                "frequencies": frequencies,
                "unique_count": len(value_counts),
                "count": int(df[col].count()),
            }
        return stats

    def _create_statistics_block(self, stats: dict[str, Any], table_index: int) -> Block:
        """
        Create a formatted statistics block from computed statistics.

        Args:
            stats: Statistics dictionary from profile_table
            table_index: Index of the table in document

        Returns:
            Block with formatted statistics
        """
        lines = [f"\n### Table {table_index + 1} Statistics\n"]

        # Add sample data section
        lines.append("\n**Sample Data (first 5 rows):**\n\n")
        lines.append(stats["sample_data"])
        lines.append("\n")

        # Add numerical statistics
        if stats["numerical_columns"]:
            lines.append("\n**Numerical Columns:**\n")
            for col, col_stats in stats["numerical_stats"].items():
                lines.append(
                    f"- **{col}**: min={col_stats['min']:.2f}, "
                    f"max={col_stats['max']:.2f}, "
                    f"mean={col_stats['mean']:.2f}, "
                    f"std={col_stats['std']:.2f}\n"
                )

        # Add categorical statistics with frequencies
        if stats["categorical_columns"]:
            lines.append("\n**Categorical Columns:**\n")
            for col, col_stats in stats["categorical_stats"].items():
                lines.append(f"- **{col}** ({col_stats['unique_count']} unique values):\n")
                lines.append(f"  - Mode: {col_stats['mode']}\n")
                lines.append("  - Frequency distribution:\n")

                # Show top 5 most frequent values
                sorted_freqs = sorted(
                    col_stats["frequencies"].items(), key=lambda x: x[1], reverse=True
                )[:5]

                for value, count in sorted_freqs:
                    percentage = (count / stats["total_rows"]) * 100
                    lines.append(f"    - `{value}`: {count} ({percentage:.1f}%)\n")

        # Add data quality metrics
        lines.append("\n**Data Quality:**\n")
        lines.append(f"- Total rows: {stats['total_rows']}\n")
        lines.append(f"- Total columns: {stats['total_columns']}\n")
        if stats["duplicate_count"] > 0:
            lines.append(f"- ⚠️ Duplicate rows: {stats['duplicate_count']}\n")

        return Block(
            type=BlockType.TEXT,
            content="".join(lines),
            metadata={"category": "table_statistics", "table_index": table_index},
        )
