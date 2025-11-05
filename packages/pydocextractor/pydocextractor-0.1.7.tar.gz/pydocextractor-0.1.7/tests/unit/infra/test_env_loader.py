"""
Unit tests for environment configuration loader.

Tests load_llm_config with various environment configurations.
"""

from unittest.mock import patch

from pydocextractor.domain.config import LLMConfig
from pydocextractor.infra.config.env_loader import (
    _load_prompt_from_ini,
    get_llm_status_message,
    load_llm_config,
)


class TestLoadLLMConfig:
    """Test load_llm_config function."""

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_disabled_config(self, mock_getenv):
        """Test loading when LLM_ENABLED is false."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "false",
        }.get(key, default)

        config = load_llm_config()

        assert config is None

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_not_enabled(self, mock_getenv):
        """Test loading when LLM_ENABLED not set."""
        mock_getenv.side_effect = lambda key, default="": default

        config = load_llm_config()

        assert config is None

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_enabled_missing_url(self, mock_getenv):
        """Test loading when enabled but URL missing."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_KEY": "test-key",
        }.get(key, default)

        config = load_llm_config()

        assert config is None

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_enabled_missing_key(self, mock_getenv):
        """Test loading when enabled but API key missing."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
        }.get(key, default)

        config = load_llm_config()

        assert config is None

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_valid_minimal_config(self, mock_getenv):
        """Test loading minimal valid configuration."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.openai.com/v1/chat/completions",
            "LLM_API_KEY": "sk-test123",
        }.get(key, default)

        config = load_llm_config()

        assert config is not None
        assert isinstance(config, LLMConfig)
        assert config.enabled is True
        assert config.api_url == "https://api.openai.com/v1/chat/completions"
        assert config.api_key == "sk-test123"
        assert config.model_name == "gpt-4-vision-preview"  # default

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_full_custom_config(self, mock_getenv):
        """Test loading configuration with all custom values."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "http://localhost:8000",
            "LLM_API_KEY": "local-key",
            "LLM_MODEL_NAME": "llava:13b",
            "LLM_CONTEXT_LINES": "200",
            "LLM_TIMEOUT": "60",
            "LLM_MAX_RETRIES": "5",
            "LLM_IMAGE_SIZE": "512",
            "LLM_MAX_IMAGES": "10",
        }.get(key, default)

        config = load_llm_config()

        assert config is not None
        assert config.api_url == "http://localhost:8000"
        assert config.api_key == "local-key"
        assert config.model_name == "llava:13b"
        assert config.context_lines == 200
        assert config.timeout_seconds == 60
        assert config.max_retries == 5
        assert config.image_size == 512
        assert config.max_images_per_document == 10

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_enabled_variations(self, mock_getenv):
        """Test various ways to enable LLM."""
        test_cases = ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]

        for enabled_value in test_cases:

            def make_side_effect(value):
                return lambda key, default="": {
                    "LLM_ENABLED": value,
                    "LLM_API_URL": "https://api.test.com",
                    "LLM_API_KEY": "test-key",
                }.get(key, default)

            mock_getenv.side_effect = make_side_effect(enabled_value)
            config = load_llm_config()
            assert config is not None, f"Failed for LLM_ENABLED={enabled_value}"

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_invalid_integer_value(self, mock_getenv):
        """Test handling invalid integer values."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
            "LLM_API_KEY": "test-key",
            "LLM_CONTEXT_LINES": "not-a-number",
        }.get(key, default)

        config = load_llm_config()

        # Should return None due to ValueError
        assert config is None

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_whitespace_handling(self, mock_getenv):
        """Test that whitespace is stripped from values."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "  https://api.test.com  ",
            "LLM_API_KEY": "  test-key  ",
        }.get(key, default)

        config = load_llm_config()

        assert config is not None
        assert config.api_url == "https://api.test.com"
        assert config.api_key == "test-key"

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_empty_string_values(self, mock_getenv):
        """Test handling empty string values."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "",
            "LLM_API_KEY": "test-key",
        }.get(key, default)

        config = load_llm_config()

        # Empty URL should return None
        assert config is None

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_with_env_variables(self, mock_getenv):
        """Test loading directly from environment variables (dotenv not needed)."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
            "LLM_API_KEY": "test-key",
        }.get(key, default)

        config = load_llm_config()

        # Should work from environment variables
        assert config is not None

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_disabled_with_zero_max_images(self, mock_getenv):
        """Test that LLM_MAX_IMAGES=0 disables LLM features."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
            "LLM_API_KEY": "test-key",
            "LLM_MAX_IMAGES": "0",
        }.get(key, default)

        config = load_llm_config()

        # Should return None when max_images is 0
        assert config is None

    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_load_unlimited_max_images(self, mock_getenv):
        """Test that LLM_MAX_IMAGES=-1 enables unlimited processing."""
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
            "LLM_API_KEY": "test-key",
            "LLM_MAX_IMAGES": "-1",
        }.get(key, default)

        config = load_llm_config()

        assert config is not None
        assert config.max_images_per_document == -1


class TestGetLLMStatusMessage:
    """Test get_llm_status_message function."""

    def test_status_message_disabled(self):
        """Test status message when config is None."""
        message = get_llm_status_message(None)

        assert message == "LLM image description: Disabled"

    def test_status_message_enabled(self):
        """Test status message when config is provided."""
        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            max_images_per_document=5,
        )

        message = get_llm_status_message(config)

        assert "Enabled" in message
        assert "5 images" in message

    def test_status_message_custom_max_images(self):
        """Test status message with custom max images."""
        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            max_images_per_document=10,
        )

        message = get_llm_status_message(config)

        assert "10 images" in message

    def test_status_message_unlimited_images(self):
        """Test status message with unlimited images."""
        config = LLMConfig(
            api_url="https://api.test.com",
            api_key="test-key",
            max_images_per_document=-1,
        )

        message = get_llm_status_message(config)

        assert "Enabled" in message
        assert "unlimited" in message


class TestLoadPromptFromIni:
    """Test _load_prompt_from_ini function."""

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    def test_load_prompt_from_ini_file_exists(self, mock_cwd, tmp_path):
        """Test successful loading from INI file."""
        # Create a temporary INI file
        ini_file = tmp_path / "system_prompt.ini"
        ini_file.write_text("[llm]\nprompt = Test prompt from INI file\n")

        mock_cwd.return_value = tmp_path

        prompt = _load_prompt_from_ini()

        assert prompt == "Test prompt from INI file"

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    def test_load_prompt_from_ini_file_not_exists(self, mock_cwd, tmp_path):
        """Test return None when file doesn't exist."""
        mock_cwd.return_value = tmp_path

        prompt = _load_prompt_from_ini()

        assert prompt is None

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    def test_load_prompt_from_ini_empty_prompt(self, mock_cwd, tmp_path):
        """Test handling empty prompt in INI."""
        ini_file = tmp_path / "system_prompt.ini"
        ini_file.write_text("[llm]\nprompt = \n")

        mock_cwd.return_value = tmp_path

        prompt = _load_prompt_from_ini()

        assert prompt is None

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    def test_load_prompt_from_ini_missing_section(self, mock_cwd, tmp_path):
        """Test handling missing [llm] section."""
        ini_file = tmp_path / "system_prompt.ini"
        ini_file.write_text("[other]\nprompt = Test prompt\n")

        mock_cwd.return_value = tmp_path

        prompt = _load_prompt_from_ini()

        assert prompt is None

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    def test_load_prompt_from_ini_missing_key(self, mock_cwd, tmp_path):
        """Test handling missing 'prompt' key."""
        ini_file = tmp_path / "system_prompt.ini"
        ini_file.write_text("[llm]\nother_key = Test value\n")

        mock_cwd.return_value = tmp_path

        prompt = _load_prompt_from_ini()

        assert prompt is None

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    def test_load_prompt_from_ini_malformed_file(self, mock_cwd, tmp_path):
        """Test handling malformed INI syntax."""
        ini_file = tmp_path / "system_prompt.ini"
        ini_file.write_text("This is not valid INI syntax\n[[broken\n")

        mock_cwd.return_value = tmp_path

        prompt = _load_prompt_from_ini()

        # Should return None without crashing
        assert prompt is None

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    def test_load_prompt_from_ini_multiline(self, mock_cwd, tmp_path):
        """Test multiline prompts work correctly."""
        ini_file = tmp_path / "system_prompt.ini"
        ini_file.write_text("[llm]\nprompt = Line 1\n    Line 2\n    Line 3\n")

        mock_cwd.return_value = tmp_path

        prompt = _load_prompt_from_ini()

        assert prompt is not None
        assert "Line 1" in prompt
        assert "Line 2" in prompt
        assert "Line 3" in prompt

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    def test_load_prompt_from_ini_whitespace_handling(self, mock_cwd, tmp_path):
        """Test whitespace is properly stripped."""
        ini_file = tmp_path / "system_prompt.ini"
        ini_file.write_text("[llm]\nprompt =   Test prompt with spaces   \n")

        mock_cwd.return_value = tmp_path

        prompt = _load_prompt_from_ini()

        assert prompt == "Test prompt with spaces"


class TestPromptLoadingPriority:
    """Test priority-based prompt loading in load_llm_config."""

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_priority_ini_over_env(self, mock_getenv, mock_cwd, tmp_path):
        """Test INI file takes priority over LLM_PROMPT env var."""
        # Create INI file
        ini_file = tmp_path / "system_prompt.ini"
        ini_file.write_text("[llm]\nprompt = Prompt from INI\n")
        mock_cwd.return_value = tmp_path

        # Set environment variables
        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
            "LLM_API_KEY": "test-key",
            "LLM_PROMPT": "Prompt from environment",
        }.get(key, default)

        config = load_llm_config()

        assert config is not None
        assert config.prompt_template == "Prompt from INI"

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_fallback_to_env_when_no_ini(self, mock_getenv, mock_cwd, tmp_path):
        """Test env var used when INI doesn't exist."""
        mock_cwd.return_value = tmp_path  # No INI file created

        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
            "LLM_API_KEY": "test-key",
            "LLM_PROMPT": "Prompt from environment",
        }.get(key, default)

        config = load_llm_config()

        assert config is not None
        assert config.prompt_template == "Prompt from environment"

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_fallback_to_default_when_neither(self, mock_getenv, mock_cwd, tmp_path):
        """Test default used when both missing."""
        mock_cwd.return_value = tmp_path  # No INI file

        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
            "LLM_API_KEY": "test-key",
            # No LLM_PROMPT set
        }.get(key, default)

        config = load_llm_config()

        assert config is not None
        # Should have the default prompt
        assert "describe the image in detail" in config.prompt_template.lower()

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_env_var_still_works_alone(self, mock_getenv, mock_cwd, tmp_path):
        """Test existing behavior unchanged (backward compatibility)."""
        mock_cwd.return_value = tmp_path  # No INI file

        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
            "LLM_API_KEY": "test-key",
            "LLM_PROMPT": "Custom prompt",
        }.get(key, default)

        config = load_llm_config()

        assert config is not None
        assert config.prompt_template == "Custom prompt"

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_empty_ini_falls_back_to_env(self, mock_getenv, mock_cwd, tmp_path):
        """Test empty INI falls back to env var."""
        # Create INI with empty prompt
        ini_file = tmp_path / "system_prompt.ini"
        ini_file.write_text("[llm]\nprompt = \n")
        mock_cwd.return_value = tmp_path

        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
            "LLM_API_KEY": "test-key",
            "LLM_PROMPT": "Prompt from environment",
        }.get(key, default)

        config = load_llm_config()

        assert config is not None
        assert config.prompt_template == "Prompt from environment"

    @patch("pydocextractor.infra.config.env_loader.Path.cwd")
    @patch("pydocextractor.infra.config.env_loader.os.getenv")
    def test_both_set_ini_wins(self, mock_getenv, mock_cwd, tmp_path):
        """Test when both set, INI takes precedence."""
        # Create valid INI file
        ini_file = tmp_path / "system_prompt.ini"
        ini_file.write_text("[llm]\nprompt = INI wins\n")
        mock_cwd.return_value = tmp_path

        mock_getenv.side_effect = lambda key, default="": {
            "LLM_ENABLED": "true",
            "LLM_API_URL": "https://api.test.com",
            "LLM_API_KEY": "test-key",
            "LLM_PROMPT": "ENV should be ignored",
        }.get(key, default)

        config = load_llm_config()

        assert config is not None
        assert config.prompt_template == "INI wins"
        assert "ENV" not in config.prompt_template
