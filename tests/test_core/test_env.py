"""Tests for secure environment variable handling.

Run with:
    uv run pytest -s --verbose --showlocals --tb=short tests/test_core/test_env.py
"""
import os
from pathlib import Path
from typing import Any, Dict

import pytest
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from boss_bot.core.env import BossSettings


@pytest.mark.env
class TestBossSettings:
    """Test suite for BossSettings configuration.

    Following TDD Red-Green-Refactor cycle:
    1. Write failing test
    2. Run test to verify failure
    3. Implement code
    4. Run test to verify pass
    5. Refactor if needed
    """

    def test_settings_loads_from_env_file(self, tmp_path: Path, mock_env_vars: dict[str, str]) -> None:
        """Test that settings can be loaded from .env file.

        Steps:
        1. Create temporary .env file
        2. Load settings
        3. Verify all settings are loaded correctly
        """
        # Arrange
        env_file = tmp_path / ".env"
        env_content = "\n".join(f"{k}={v}" for k, v in mock_env_vars.items())
        env_file.write_text(env_content)

        # Act
        settings = BossSettings(_env_file=env_file)

        # Assert
        assert isinstance(settings.discord_token, SecretStr)
        assert settings.discord_token.get_secret_value() == mock_env_vars["DISCORD_TOKEN"]
        assert settings.discord_client_id == int(mock_env_vars["DISCORD_CLIENT_ID"])
        assert settings.discord_server_id == int(mock_env_vars["DISCORD_SERVER_ID"])
        assert settings.discord_admin_user_id == int(mock_env_vars["DISCORD_ADMIN_USER_ID"])
        assert settings.discord_admin_user_invited is True
        assert settings.enable_ai is True
        assert settings.enable_redis is False
        assert settings.enable_sentry is False
        assert settings.sentry_dsn is None
        assert isinstance(settings.openai_api_key, SecretStr)
        assert settings.openai_api_key.get_secret_value() == mock_env_vars["OPENAI_API_KEY"]

    def test_settings_loads_from_environment(self, mock_settings: None) -> None:
        """Test that settings can be loaded from environment variables.

        Steps:
        1. Environment variables are set by mock_settings fixture
        2. Load settings
        3. Verify all settings match environment variables
        """
        # Act
        settings = BossSettings()

        # Assert - Using os.environ to avoid exposing secrets in test code
        assert settings.discord_token.get_secret_value() == os.environ["DISCORD_TOKEN"]
        assert settings.discord_client_id == int(os.environ["DISCORD_CLIENT_ID"])
        assert settings.discord_server_id == int(os.environ["DISCORD_SERVER_ID"])
        assert settings.discord_admin_user_id == int(os.environ["DISCORD_ADMIN_USER_ID"])
        assert settings.discord_admin_user_invited is True
        assert settings.enable_ai is True
        assert settings.enable_redis is False
        assert settings.enable_sentry is False
        assert settings.sentry_dsn is None
        assert settings.openai_api_key.get_secret_value() == os.environ["OPENAI_API_KEY"]

    def test_settings_validates_required_fields(self) -> None:
        """Test that settings validates required fields.

        Steps:
        1. Attempt to create settings without required fields
        2. Verify ValueError is raised
        """
        # Act/Assert
        with pytest.raises(ValueError, match="Field required"):
            BossSettings(_env_file=None)

    def test_settings_validates_discord_token_format(self, invalid_token_vars: dict[str, str]) -> None:
        """Test that settings validates Discord token format.

        Steps:
        1. Create settings with invalid token format
        2. Verify ValueError is raised
        """
        # Act/Assert
        with pytest.raises(ValueError, match="Invalid Discord token format"):
            BossSettings(**invalid_token_vars)

    def test_settings_validates_openai_key_format(self, invalid_api_key_vars: dict[str, str]) -> None:
        """Test that settings validates OpenAI API key format.

        Steps:
        1. Create settings with invalid API key format
        2. Verify ValueError is raised
        """
        # Act/Assert
        with pytest.raises(ValueError, match="Invalid OpenAI API key format"):
            BossSettings(**invalid_api_key_vars)

    @pytest.mark.security
    def test_settings_secrets_are_hidden_in_repr(self, mock_settings: None) -> None:
        """Test that sensitive settings are hidden in string representation.

        Steps:
        1. Create settings with sensitive data
        2. Get string representation
        3. Verify no secrets are visible in any form
        """
        # Act
        settings = BossSettings()
        settings_str = str(settings)

        # Assert - Check that secrets are hidden without exposing them in test code
        assert os.environ["DISCORD_TOKEN"] not in settings_str
        assert os.environ["OPENAI_API_KEY"] not in settings_str
        assert "********" in settings_str

        # Additional check to ensure no part of the secret is visible
        for secret in [os.environ["DISCORD_TOKEN"], os.environ["OPENAI_API_KEY"]]:
            for i in range(len(secret) - 3):
                assert secret[i:i+4] not in settings_str

    @pytest.mark.security
    def test_secretstr_no_leak_in_repr(self, mock_env_vars: dict[str, str]) -> None:
        """Test that SecretStr values cannot leak through repr or str.

        Steps:
        1. Create settings with sensitive data
        2. Test all possible string representations
        3. Verify no secrets are visible in any form
        """
        # Arrange
        settings = BossSettings(**mock_env_vars)

        # Act & Assert
        assert mock_env_vars["DISCORD_TOKEN"] not in repr(settings)
        assert mock_env_vars["DISCORD_TOKEN"] not in str(settings)
        assert mock_env_vars["DISCORD_TOKEN"] not in f"{settings}"
        assert mock_env_vars["DISCORD_TOKEN"] not in settings.__repr__()

        # Check that the secret is not exposed in debug output
        debug_output = str(pytest.main(["--verbose", "-k", "test_secretstr_no_leak_in_repr"]))
        assert mock_env_vars["DISCORD_TOKEN"] not in debug_output
