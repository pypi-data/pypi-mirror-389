"""
Document extractor adapters.

Each adapter implements the Extractor Protocol from domain.ports.
"""

# Check library availability
try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pymupdf4llm

    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from docling.document_converter import DocumentConverter as DoclingDocConverter

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

__all__ = [
    "PYMUPDF_AVAILABLE",
    "PYMUPDF4LLM_AVAILABLE",
    "PDFPLUMBER_AVAILABLE",
    "DOCLING_AVAILABLE",
]
