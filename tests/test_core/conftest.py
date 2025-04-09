"""Test fixtures for boss-bot."""
import pytest
from typing import Dict, Any


@pytest.fixture
def mock_env_vars() -> dict[str, str]:
    """Fixture providing mock environment variables for testing."""
    return {
        "DISCORD_TOKEN": "test_token",  # Safe test value
        "DISCORD_CLIENT_ID": "123456789",
        "DISCORD_SERVER_ID": "987654321",
        "DISCORD_ADMIN_USER_ID": "11111111",
        "DISCORD_ADMIN_USER_INVITED": "true",
        "ENABLE_AI": "true",
        "ENABLE_REDIS": "false",
        "ENABLE_SENTRY": "false",
        "SENTRY_DSN": "",
        "OPENAI_API_KEY": "sk-testkey123456",  # Safe test value that matches validation
    }


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch, mock_env_vars: dict[str, str]) -> None:
    """Fixture to set up mock environment variables."""
    for key, value in mock_env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def invalid_token_vars(mock_env_vars: dict[str, str]) -> dict[str, str]:
    """Fixture providing environment variables with invalid token."""
    vars = mock_env_vars.copy()
    vars["DISCORD_TOKEN"] = "invalid-token"
    return vars


@pytest.fixture
def invalid_api_key_vars(mock_env_vars: dict[str, str]) -> dict[str, str]:
    """Fixture providing environment variables with invalid API key."""
    vars = mock_env_vars.copy()
    vars["OPENAI_API_KEY"] = "invalid-key"
    return vars
