"""
Environment configuration loader for LLM settings.

This module safely loads LLM configuration from environment variables,
with graceful fallbacks if configuration is missing or invalid.
"""

from __future__ import annotations

import configparser
import logging
import os
from pathlib import Path

from pydocextractor.domain.config import LLMConfig

logger = logging.getLogger(__name__)


def _load_prompt_from_ini() -> str | None:
    """
    Load prompt template from system_prompt.ini file.

    This function looks for system_prompt.ini in the current working directory
    and attempts to read the prompt from the [llm] section, prompt key.

    Returns:
        Prompt string if file exists and is valid, None otherwise.

    File format:
        [llm]
        prompt = Your custom prompt here
    """
    ini_path = Path.cwd() / "system_prompt.ini"

    if not ini_path.exists():
        logger.debug("system_prompt.ini not found, will use environment variable or default")
        return None

    try:
        config = configparser.ConfigParser()
        config.read(ini_path)

        # Validate INI structure and content
        if not config.has_section("llm"):
            logger.warning("system_prompt.ini exists but missing [llm] section")
        elif not config.has_option("llm", "prompt"):
            logger.warning("system_prompt.ini exists but missing 'prompt' key in [llm] section")
        else:
            prompt = config.get("llm", "prompt").strip()
            if prompt:
                logger.info(f"Loaded prompt template from {ini_path}")
                return prompt
            logger.warning("system_prompt.ini exists but prompt is empty")

    except configparser.Error as e:
        logger.warning(
            f"Error parsing system_prompt.ini: {e}. Will use environment variable or default."
        )
    except Exception as e:
        logger.debug(f"Could not load system_prompt.ini: {e}")

    return None


def _load_dotenv_file() -> None:
    """Load environment variables from .env or config.env file if available."""
    try:
        from dotenv import load_dotenv

        config_env_path = Path.cwd() / "config.env"
        env_path = Path.cwd() / ".env"

        if config_env_path.exists():
            load_dotenv(config_env_path)
            logger.info(f"Loaded config.env from {config_env_path}")
        elif env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded .env from {env_path}")
    except ImportError:
        logger.debug("python-dotenv not available, using environment variables")
    except Exception as e:
        logger.debug(f"Could not load environment file: {e}")


def _get_prompt_template() -> str:
    """
    Get prompt template with priority-based loading.

    Priority: system_prompt.ini > LLM_PROMPT env var > default
    """
    # Priority 1: system_prompt.ini file
    prompt_template = _load_prompt_from_ini()

    # Priority 2: LLM_PROMPT environment variable
    if prompt_template is None:
        prompt_env = os.getenv("LLM_PROMPT", "").strip()
        if prompt_env:
            logger.info("Using prompt template from LLM_PROMPT environment variable")
            return prompt_env

    # Priority 3: Default fallback prompt
    if not prompt_template:
        logger.info("Using default prompt template")
        return (
            "Please describe the image in detail, considering the context provided. "
            "Focus on how the image relates to the surrounding content. "
            "Keep the description concise (2-3 sentences)."
        )

    return prompt_template


def load_llm_config() -> LLMConfig | None:
    """
    Load LLM configuration from environment variables.

    This function attempts to load configuration from:
    1. A .env file in the current directory (if python-dotenv is installed)
    2. System environment variables

    Returns:
        LLMConfig if properly configured and enabled, None otherwise.
        The system will work without LLM features if None is returned.

    Environment Variables:
        LLM_ENABLED: Enable LLM features (default: false)
        LLM_API_URL: API endpoint URL (required if enabled)
        LLM_API_KEY: API key (required if enabled)
        LLM_MODEL_NAME: Model name (default: gpt-4-vision-preview)
        LLM_CONTEXT_LINES: Context lines to include (default: 100)
        LLM_IMAGE_SIZE: Image resize dimension (default: 1024)
        LLM_MAX_IMAGES: Max images per document (default: 5)
        LLM_TIMEOUT: Request timeout in seconds (default: 30)
        LLM_MAX_RETRIES: Max retry attempts (default: 3)
        LLM_PROMPT: Prompt template for image description (default: standard prompt)

    Prompt Loading Priority:
        1. system_prompt.ini file (if exists) - RECOMMENDED for longer prompts
        2. LLM_PROMPT environment variable - for backward compatibility
        3. Default fallback prompt - if neither is set
    """
    # Load environment file if available
    _load_dotenv_file()

    # Check if LLM is enabled (default: false)
    enabled = os.getenv("LLM_ENABLED", "false").lower() in ("true", "1", "yes")

    if not enabled:
        logger.info("LLM image description is disabled (LLM_ENABLED=false or not set)")
        return None

    # Get required fields
    api_url = os.getenv("LLM_API_URL", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()

    # Validate required fields - early exit for missing configuration
    missing_config_reasons = []
    if not api_url:
        missing_config_reasons.append("LLM_API_URL not set")
    if not api_key:
        missing_config_reasons.append("LLM_API_KEY not set")

    if missing_config_reasons:
        logger.warning(
            f"LLM enabled but {', '.join(missing_config_reasons)}. Disabling LLM features."
        )
        return None

    # Get optional fields with defaults
    try:
        # Check if max images is set to 0 (disabled)
        max_images = int(os.getenv("LLM_MAX_IMAGES", "5"))
        if max_images == 0:
            logger.info("LLM_MAX_IMAGES=0. Disabling LLM features.")
            return None

        # Get prompt template with priority-based loading
        prompt_template = _get_prompt_template()

        config = LLMConfig(
            api_url=api_url,
            api_key=api_key,
            model_name=os.getenv("LLM_MODEL_NAME", "gpt-4-vision-preview"),
            context_lines=int(os.getenv("LLM_CONTEXT_LINES", "100")),
            enabled=True,
            timeout_seconds=int(os.getenv("LLM_TIMEOUT", "30")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            image_size=int(os.getenv("LLM_IMAGE_SIZE", "1024")),
            max_images_per_document=max_images,
            prompt_template=prompt_template,
        )

        max_images_str = (
            "unlimited"
            if config.max_images_per_document == -1
            else str(config.max_images_per_document)
        )
        logger.info(
            f"LLM configuration loaded: model={config.model_name}, max_images={max_images_str}"
        )
        return config

    except ValueError as e:
        logger.error(f"Invalid LLM configuration: {e}. Disabling LLM features.")
        return None
    except Exception as e:
        logger.error(f"Error loading LLM configuration: {e}. Disabling LLM features.")
        return None


def get_llm_status_message(config: LLMConfig | None) -> str:
    """
    Get a human-readable status message for LLM configuration.

    Args:
        config: LLM configuration or None if disabled

    Returns:
        Status message describing LLM state
    """
    if config is None:
        return "LLM image description: Disabled"
    max_images_str = (
        "unlimited"
        if config.max_images_per_document == -1
        else f"max {config.max_images_per_document}"
    )
    return f"LLM image description: Enabled ({max_images_str} images per document)"
