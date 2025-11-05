"""
Domain profilers for pyDocExtractor.

Profilers analyze extracted content and enrich it with additional metadata
and statistics.
"""

from pydocextractor.domain.profilers.table_profiler import TableProfiler

__all__ = ["TableProfiler"]
