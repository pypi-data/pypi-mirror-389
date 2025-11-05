"""
Unit tests for TableProfiler.
"""

import pytest

from pydocextractor.domain.models import Block, BlockType, NormalizedDoc
from pydocextractor.domain.profilers.table_profiler import TableProfiler


class TestTableProfiler:
    """Tests for table profiling functionality."""

    @pytest.fixture
    def sample_table_markdown(self):
        """Sample table in markdown format."""
        return """| Name | Age | Country | Occupation |
|------|-----|---------|------------|
| Alice | 30 | USA | Engineer |
| Bob | 25 | Canada | Designer |
| Charlie | 35 | UK | Teacher |
| Diana | 28 | Australia | Doctor |
| Ethan | 40 | Germany | Architect |
| Fiona | 32 | Brazil | Developer |
| George | 29 | France | Chef |
| Hana | 27 | Japan | Artist |"""

    @pytest.fixture
    def profiler(self):
        """Create a TableProfiler instance."""
        return TableProfiler(max_sample_rows=5)

    def test_profiler_initialization(self):
        """Test profiler can be initialized with custom sample size."""
        profiler = TableProfiler(max_sample_rows=3)
        assert profiler.max_sample_rows == 3

    def test_profile_adds_statistics_block(self, profiler, sample_table_markdown):
        """Test that profiling adds a statistics block after table."""
        blocks = [Block(type=BlockType.TABLE, content=sample_table_markdown, metadata={})]
        ndoc = NormalizedDoc(
            blocks=tuple(blocks),
            source_mime="application/pdf",
            extractor_name="Test",
            metadata={},
        )

        enhanced = profiler.profile(ndoc)

        # Should have 2 blocks: original table + statistics
        assert len(enhanced.blocks) == 2
        assert enhanced.blocks[0].type == BlockType.TABLE
        assert enhanced.blocks[1].type == BlockType.TEXT
        assert enhanced.blocks[1].metadata.get("category") == "table_statistics"

    def test_profile_calculates_numerical_stats(self, profiler, sample_table_markdown):
        """Test that numerical statistics are calculated correctly."""
        blocks = [Block(type=BlockType.TABLE, content=sample_table_markdown, metadata={})]
        ndoc = NormalizedDoc(
            blocks=tuple(blocks),
            source_mime="application/pdf",
            extractor_name="Test",
            metadata={},
        )

        enhanced = profiler.profile(ndoc)

        # Check metadata
        stats = enhanced.metadata["table_statistics"]["table_0"]
        assert "Age" in stats["numerical_columns"]
        assert stats["numerical_stats"]["Age"]["min"] == 25.0
        assert stats["numerical_stats"]["Age"]["max"] == 40.0
        assert 30.0 <= stats["numerical_stats"]["Age"]["mean"] <= 32.0
        assert "std" in stats["numerical_stats"]["Age"]
        assert stats["numerical_stats"]["Age"]["std"] > 0

    def test_profile_calculates_categorical_stats(self, profiler, sample_table_markdown):
        """Test that categorical statistics include frequencies."""
        blocks = [Block(type=BlockType.TABLE, content=sample_table_markdown, metadata={})]
        ndoc = NormalizedDoc(
            blocks=tuple(blocks),
            source_mime="application/pdf",
            extractor_name="Test",
            metadata={},
        )

        enhanced = profiler.profile(ndoc)

        stats = enhanced.metadata["table_statistics"]["table_0"]
        assert "Name" in stats["categorical_columns"]
        assert "Occupation" in stats["categorical_columns"]

        # Check frequency distribution exists
        name_stats = stats["categorical_stats"]["Name"]
        assert "frequencies" in name_stats
        assert "unique_count" in name_stats
        assert "mode" in name_stats
        assert len(name_stats["frequencies"]) == name_stats["unique_count"]

    def test_profile_creates_sample(self, profiler):
        """Test that sample is limited to max_sample_rows."""
        # Create table with 10 rows
        table = """| Name | Age |
|------|-----|
| A | 20 |
| B | 21 |
| C | 22 |
| D | 23 |
| E | 24 |
| F | 25 |
| G | 26 |
| H | 27 |
| I | 28 |
| J | 29 |"""

        blocks = [Block(type=BlockType.TABLE, content=table, metadata={})]
        ndoc = NormalizedDoc(
            blocks=tuple(blocks),
            source_mime="application/pdf",
            extractor_name="Test",
            metadata={},
        )

        enhanced = profiler.profile(ndoc)

        stats = enhanced.metadata["table_statistics"]["table_0"]
        # Sample should have max 5 rows
        sample_lines = stats["sample_data"].split("\n")
        # Should have header + separator + 5 data rows = 7 lines
        assert len([line for line in sample_lines if line.strip() and "|" in line]) <= 7
        # But total rows should be 10
        assert stats["total_rows"] == 10

    def test_profile_handles_multiple_tables(self, profiler, sample_table_markdown):
        """Test profiling multiple tables in one document."""
        blocks = [
            Block(type=BlockType.TEXT, content="# Document", metadata={}),
            Block(type=BlockType.TABLE, content=sample_table_markdown, metadata={}),
            Block(type=BlockType.TEXT, content="Some text", metadata={}),
            Block(type=BlockType.TABLE, content=sample_table_markdown, metadata={}),
        ]
        ndoc = NormalizedDoc(
            blocks=tuple(blocks),
            source_mime="application/pdf",
            extractor_name="Test",
            metadata={},
        )

        enhanced = profiler.profile(ndoc)

        # Should have original 4 blocks + 2 statistics blocks = 6 blocks
        assert len(enhanced.blocks) == 6
        # Check that both tables have statistics
        assert "table_0" in enhanced.metadata["table_statistics"]
        assert "table_1" in enhanced.metadata["table_statistics"]

    def test_profile_skips_non_table_blocks(self, profiler):
        """Test that non-table blocks are not modified."""
        blocks = [
            Block(type=BlockType.TEXT, content="# Heading", metadata={}),
            Block(type=BlockType.TEXT, content="Paragraph", metadata={}),
        ]
        ndoc = NormalizedDoc(
            blocks=tuple(blocks),
            source_mime="application/pdf",
            extractor_name="Test",
            metadata={},
        )

        enhanced = profiler.profile(ndoc)

        # No additional blocks should be added
        assert len(enhanced.blocks) == 2
        assert (
            "table_statistics" not in enhanced.metadata or not enhanced.metadata["table_statistics"]
        )

    def test_profile_handles_empty_table(self, profiler):
        """Test graceful handling of empty or malformed tables."""
        blocks = [Block(type=BlockType.TABLE, content="", metadata={})]
        ndoc = NormalizedDoc(
            blocks=tuple(blocks),
            source_mime="application/pdf",
            extractor_name="Test",
            metadata={},
        )

        enhanced = profiler.profile(ndoc)

        # Should not crash, just skip the table
        assert len(enhanced.blocks) >= 1

    def test_profile_detects_duplicate_rows(self, profiler):
        """Test duplicate row detection."""
        table = """| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |
| Alice | 30 |
| Bob | 25 |"""

        blocks = [Block(type=BlockType.TABLE, content=table, metadata={})]
        ndoc = NormalizedDoc(
            blocks=tuple(blocks),
            source_mime="application/pdf",
            extractor_name="Test",
            metadata={},
        )

        enhanced = profiler.profile(ndoc)

        stats = enhanced.metadata["table_statistics"]["table_0"]
        assert stats["duplicate_count"] == 2  # 2 duplicate rows

    def test_statistics_block_format(self, profiler, sample_table_markdown):
        """Test that statistics block has correct format."""
        blocks = [Block(type=BlockType.TABLE, content=sample_table_markdown, metadata={})]
        ndoc = NormalizedDoc(
            blocks=tuple(blocks),
            source_mime="application/pdf",
            extractor_name="Test",
            metadata={},
        )

        enhanced = profiler.profile(ndoc)

        stats_block = enhanced.blocks[1]
        content = stats_block.content

        # Check for required sections
        assert "Table 1 Statistics" in content
        assert "Sample Data" in content
        assert "Numerical Columns" in content
        assert "Categorical Columns" in content
        assert "Data Quality" in content
        assert "min=" in content and "max=" in content and "mean=" in content
        assert "std=" in content  # Enhanced statistic
        assert "Frequency distribution" in content  # Enhanced statistic
        assert "Total rows:" in content
        assert "Total columns:" in content

    def test_profile_with_no_pandas(self, profiler, sample_table_markdown, monkeypatch):
        """Test graceful degradation when pandas not available."""
        # This test would require mocking pandas availability
        # For now, we assume pandas is available in test environment
        pass
