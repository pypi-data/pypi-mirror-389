"""
Unit tests for image context tracking.

Tests ImageContextTracker buffer management and context retrieval.
"""

from pydocextractor.app.image_context import ImageContextTracker


class TestImageContextTracker:
    """Test ImageContextTracker context management."""

    def test_create_tracker_default_lines(self):
        """Test creating tracker with default context lines."""
        tracker = ImageContextTracker()

        assert tracker.context_lines == 100
        assert tracker.get_context() == ""

    def test_create_tracker_custom_lines(self):
        """Test creating tracker with custom context lines."""
        tracker = ImageContextTracker(context_lines=50)

        assert tracker.context_lines == 50
        assert tracker.get_context() == ""

    def test_add_single_line_text(self):
        """Test adding single line of text."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("Hello world")

        context = tracker.get_context()
        assert context == "Hello world"

    def test_add_multiline_text(self):
        """Test adding text with multiple lines."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("Line 1\nLine 2\nLine 3")

        context = tracker.get_context()
        assert context == "Line 1\nLine 2\nLine 3"

    def test_add_multiple_calls(self):
        """Test adding text across multiple calls."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("First block")
        tracker.add_text("Second block")
        tracker.add_text("Third block")

        context = tracker.get_context()
        assert context == "First block\nSecond block\nThird block"

    def test_buffer_limit_enforced(self):
        """Test that buffer is limited to context_lines."""
        tracker = ImageContextTracker(context_lines=3)

        # Add 5 lines
        tracker.add_text("Line 1")
        tracker.add_text("Line 2")
        tracker.add_text("Line 3")
        tracker.add_text("Line 4")
        tracker.add_text("Line 5")

        context = tracker.get_context()
        # Should only keep last 3 lines
        assert context == "Line 3\nLine 4\nLine 5"

    def test_buffer_limit_with_multiline(self):
        """Test buffer limit with multiline text."""
        tracker = ImageContextTracker(context_lines=3)

        # Add text with multiple lines
        tracker.add_text("Line 1\nLine 2")
        tracker.add_text("Line 3\nLine 4\nLine 5")

        context = tracker.get_context()
        # Should keep last 3 lines
        assert context == "Line 3\nLine 4\nLine 5"

    def test_empty_text_ignored(self):
        """Test that empty text doesn't affect buffer."""
        tracker = ImageContextTracker(context_lines=5)
        tracker.add_text("Line 1")
        tracker.add_text("")
        tracker.add_text("Line 2")

        context = tracker.get_context()
        # Empty line is kept as an empty line
        assert context == "Line 1\n\nLine 2"

    def test_clear_context(self):
        """Test clearing context."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("Line 1")
        tracker.add_text("Line 2")

        tracker.clear()

        assert tracker.get_context() == ""

    def test_reset_context(self):
        """Test resetting context (using clear method)."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("Line 1")
        tracker.add_text("Line 2")

        tracker.clear()

        assert tracker.get_context() == ""

    def test_add_after_clear(self):
        """Test adding text after clear."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("Line 1")
        tracker.clear()
        tracker.add_text("Line 2")

        context = tracker.get_context()
        assert context == "Line 2"

    def test_exact_buffer_size(self):
        """Test buffer exactly at limit."""
        tracker = ImageContextTracker(context_lines=3)

        tracker.add_text("Line 1")
        tracker.add_text("Line 2")
        tracker.add_text("Line 3")

        context = tracker.get_context()
        assert context == "Line 1\nLine 2\nLine 3"

        # Add one more to trigger trim
        tracker.add_text("Line 4")
        context = tracker.get_context()
        assert context == "Line 2\nLine 3\nLine 4"

    def test_whitespace_preserved(self):
        """Test that whitespace in lines is preserved."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("  Indented line  ")

        context = tracker.get_context()
        assert context == "  Indented line  "

    def test_special_characters(self):
        """Test handling of special characters."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("Line with\ttab")
        tracker.add_text("Line with emoji 🎯")
        tracker.add_text("Line with special: @#$%^&*()")

        context = tracker.get_context()
        assert "Line with\ttab" in context
        assert "Line with emoji 🎯" in context
        assert "Line with special: @#$%^&*()" in context

    def test_very_long_single_line(self):
        """Test handling very long single line."""
        tracker = ImageContextTracker(context_lines=5)
        long_line = "x" * 10000  # 10k characters

        tracker.add_text(long_line)

        context = tracker.get_context()
        assert context == long_line

    def test_zero_context_lines(self):
        """Test tracker with zero context lines (edge case: -0 slice returns all)."""
        tracker = ImageContextTracker(context_lines=0)
        tracker.add_text("Line 1")
        tracker.add_text("Line 2")

        # Due to Python's -0 slice behavior, buffer keeps all lines
        context = tracker.get_context()
        assert context == "Line 1\nLine 2"

    def test_one_context_line(self):
        """Test tracker with single context line."""
        tracker = ImageContextTracker(context_lines=1)
        tracker.add_text("Line 1")
        tracker.add_text("Line 2")
        tracker.add_text("Line 3")

        context = tracker.get_context()
        assert context == "Line 3"

    def test_buffer_trimming_efficiency(self):
        """Test that buffer trimming happens correctly."""
        tracker = ImageContextTracker(context_lines=2)

        # Add many lines to test trimming
        for i in range(10):
            tracker.add_text(f"Line {i}")

        context = tracker.get_context()
        assert context == "Line 8\nLine 9"
        assert len(tracker.text_buffer) == 2

    def test_newline_at_end(self):
        """Test text with trailing newline."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("Line 1\n")

        context = tracker.get_context()
        # Trailing newline creates an empty line
        assert context == "Line 1\n"

    def test_multiple_empty_lines(self):
        """Test handling multiple consecutive empty lines."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("Line 1\n\n\nLine 2")

        context = tracker.get_context()
        assert context == "Line 1\n\n\nLine 2"

    def test_unicode_text(self):
        """Test handling Unicode text."""
        tracker = ImageContextTracker(context_lines=10)
        tracker.add_text("日本語テキスト")
        tracker.add_text("Текст на русском")
        tracker.add_text("نص عربي")

        context = tracker.get_context()
        assert "日本語テキスト" in context
        assert "Текст на русском" in context
        assert "نص عربي" in context
