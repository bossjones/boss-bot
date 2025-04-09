"""Tests for environment settings."""

import os
from pathlib import Path
from collections.abc import Generator

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from boss_bot.core.env import BossSettings, Environment


@pytest.fixture
def mock_env(monkeypatch: MonkeyPatch) -> Generator[None, None, None]:
    """Set up test environment variables."""
    env_vars = {
        "DISCORD_TOKEN": "test_token_123",
        "DISCORD_CLIENT_ID": "123456789012345678",
        "DISCORD_SERVER_ID": "876543210987654321",
        "DISCORD_ADMIN_USER_ID": "111222333444555666",
        "STORAGE_ROOT": "/tmp/boss-bot",
        "MAX_FILE_SIZE_MB": "50",
        "MAX_CONCURRENT_DOWNLOADS": "5",
        "MAX_QUEUE_SIZE": "50",
        "LOG_LEVEL": "INFO",
        "ENABLE_METRICS": "true",
        "METRICS_PORT": "9090",
        "ENABLE_HEALTH_CHECK": "true",
        "HEALTH_CHECK_PORT": "8080",
        "RATE_LIMIT_REQUESTS": "100",
        "RATE_LIMIT_WINDOW_SECONDS": "60",
        "ENABLE_FILE_VALIDATION": "true",
        "DEBUG": "false",
        "ENVIRONMENT": "development",
        "OPENAI_API_KEY": "sk-test-key-123456789abcdef",
        "COHERE_API_KEY": "test-cohere-key-123456789",
        "DEBUG_AIDER": "true",
        "FIRECRAWL_API_KEY": "test-firecrawl-key-123456789",
        "LANGCHAIN_API_KEY": "test-langchain-key-123456789",
        "LANGCHAIN_DEBUG_LOGS": "true",
        "LANGCHAIN_ENDPOINT": "http://localhost:8000",
        "LANGCHAIN_HUB_API_KEY": "test-hub-key-123456789",
        "LANGCHAIN_HUB_API_URL": "http://localhost:8001",
        "LANGCHAIN_PROJECT": "test-project",
        "LANGCHAIN_TRACING_V2": "true",
        "PINECONE_API_KEY": "test-pinecone-key-123456789",
        "PINECONE_ENV": "test-env",
        "PINECONE_INDEX": "test-index",
        "TAVILY_API_KEY": "test-tavily-key-123456789",
        "UNSTRUCTURED_API_KEY": "test-unstructured-key-123456789",
        "UNSTRUCTURED_API_URL": "http://localhost:8002",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    yield


def test_settings_load(mock_env: None) -> None:
    """Test that settings load correctly from environment variables."""
    settings = BossSettings()

    # Test Discord settings
    assert settings.discord_token.get_secret_value() == "test_token_123"
    assert settings.discord_client_id == 123456789012345678
    assert settings.discord_server_id == 876543210987654321
    assert settings.discord_admin_user_id == 111222333444555666

    # Test Storage settings
    assert settings.storage_root == Path("/tmp/boss-bot")
    assert settings.max_file_size_mb == 50
    assert settings.max_concurrent_downloads == 5
    assert settings.max_queue_size == 50

    # Test Monitoring settings
    assert settings.log_level == "INFO"
    assert settings.enable_metrics is True
    assert settings.metrics_port == 9090
    assert settings.enable_health_check is True
    assert settings.health_check_port == 8080

    # Test Security settings
    assert settings.rate_limit_requests == 100
    assert settings.rate_limit_window_seconds == 60
    assert settings.enable_file_validation is True

    # Test Development settings
    assert settings.debug is False
    assert settings.environment == Environment.DEVELOPMENT

    # Test API Keys
    assert settings.openai_api_key.get_secret_value() == "sk-test-key-123456789abcdef"
    assert settings.cohere_api_key.get_secret_value() == "test-cohere-key-123456789"
    assert settings.debug_aider is True
    assert settings.firecrawl_api_key.get_secret_value() == "test-firecrawl-key-123456789"
    assert settings.langchain_api_key.get_secret_value() == "test-langchain-key-123456789"
    assert settings.langchain_debug_logs is True
    assert str(settings.langchain_endpoint) == "http://localhost:8000/"
    assert settings.langchain_hub_api_key.get_secret_value() == "test-hub-key-123456789"
    assert str(settings.langchain_hub_api_url) == "http://localhost:8001/"
    assert settings.langchain_project == "test-project"
    assert settings.langchain_tracing_v2 is True
    assert settings.pinecone_api_key.get_secret_value() == "test-pinecone-key-123456789"
    assert settings.pinecone_env == "test-env"
    assert settings.pinecone_index == "test-index"
    assert settings.tavily_api_key.get_secret_value() == "test-tavily-key-123456789"
    assert settings.unstructured_api_key.get_secret_value() == "test-unstructured-key-123456789"
    assert str(settings.unstructured_api_url) == "http://localhost:8002/"


def test_invalid_log_level(mock_env: None, monkeypatch: MonkeyPatch) -> None:
    """Test that invalid log level raises validation error."""
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    with pytest.raises(ValidationError, match="Invalid log level"):
        BossSettings()


def test_invalid_storage_root(mock_env: None, monkeypatch: MonkeyPatch) -> None:
    """Test that relative storage root path raises validation error."""
    monkeypatch.setenv("STORAGE_ROOT", "relative/path")
    with pytest.raises(ValidationError, match="Storage root must be an absolute path"):
        BossSettings()


def test_invalid_positive_integers(mock_env: None, monkeypatch: MonkeyPatch) -> None:
    """Test that negative values raise validation error for positive integer fields."""
    fields = [
        "MAX_FILE_SIZE_MB",
        "MAX_CONCURRENT_DOWNLOADS",
        "MAX_QUEUE_SIZE",
        "METRICS_PORT",
        "HEALTH_CHECK_PORT",
        "RATE_LIMIT_REQUESTS",
        "RATE_LIMIT_WINDOW_SECONDS"
    ]

    for field in fields:
        monkeypatch.setenv(field, "-1")
        with pytest.raises(ValidationError, match=f"{field.lower()} must be a positive integer"):
            BossSettings()
        monkeypatch.setenv(field, "0")
        with pytest.raises(ValidationError, match=f"{field.lower()} must be a positive integer"):
            BossSettings()


def test_invalid_urls(mock_env: None, monkeypatch: MonkeyPatch) -> None:
    """Test that invalid URLs raise validation error."""
    url_fields = {
        "LANGCHAIN_ENDPOINT": "not_a_url",
        "LANGCHAIN_HUB_API_URL": "invalid_url",
        "UNSTRUCTURED_API_URL": "also_not_a_url"
    }

    for field, value in url_fields.items():
        monkeypatch.setenv(field, value)
        with pytest.raises(ValidationError, match="URL"):
            BossSettings()


def test_environment_validation(mock_env: None, monkeypatch: MonkeyPatch) -> None:
    """Test environment enum validation."""
    # Test valid environments
    for env in ["development", "staging", "production"]:
        monkeypatch.setenv("ENVIRONMENT", env)
        settings = BossSettings()
        assert settings.environment == getattr(Environment, env.upper())

    # Test invalid environment
    monkeypatch.setenv("ENVIRONMENT", "invalid")
    with pytest.raises(ValidationError):
        BossSettings()


def test_str_representation(mock_env: None) -> None:
    """Test string representation masks sensitive values."""
    settings = BossSettings()
    str_repr = str(settings)

    # Check that sensitive values are masked
    assert "**********" in str_repr
    assert "sk-test-key-123456789abcdef" not in str_repr
    assert "test-cohere-key-123456789" not in str_repr
    assert "test-firecrawl-key-123456789" not in str_repr

    # Check that non-sensitive values are included
    assert str(settings.storage_root) in str_repr
    assert str(settings.max_file_size_mb) in str_repr
    assert str(settings.environment) in str_repr
