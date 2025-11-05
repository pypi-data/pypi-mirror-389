"""
BDD step definitions package.

All step definitions are imported here to be registered with pytest-bdd.
"""

# Import all step definition modules to register them
from . import (
    common_steps,  # noqa: F401
    document_tables_steps,  # noqa: F401
    pdf_word_steps,  # noqa: F401
    table_extraction_steps,  # noqa: F401
)

__all__ = [
    "common_steps",
    "document_tables_steps",
    "pdf_word_steps",
    "table_extraction_steps",
]
