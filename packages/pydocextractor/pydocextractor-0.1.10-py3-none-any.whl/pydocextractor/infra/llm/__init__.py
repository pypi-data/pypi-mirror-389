"""LLM infrastructure for image description."""

from pydocextractor.infra.llm.openai_adapter import OpenAIImageDescriber
from pydocextractor.infra.llm.resilient_describer import ResilientImageDescriber

__all__ = ["OpenAIImageDescriber", "ResilientImageDescriber"]
