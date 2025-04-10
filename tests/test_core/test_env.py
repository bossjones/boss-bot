"""Tests for environment settings."""
# pylint: disable=no-member
# pylint: disable=possibly-used-before-assignment
# pyright: reportImportCycles=false
# pyright: reportFunctionMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownVariableType=false
# pyright: reportInvalidTypeForm=false
# mypy: disable-error-code="index"
# mypy: disable-error-code="no-redef"
# pylint: disable=consider-using-with, consider-using-min-builtin

import os
from pathlib import Path
from collections.abc import Generator

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from boss_bot.core.env import BossSettings, Environment


def test_settings_load(mock_env_vars_unit: None) -> None:
    """Test that settings load correctly from environment variables."""
    test_settings = BossSettings()

    # Test Discord settings
    assert test_settings.discord_token.get_secret_value() == "test_token_123"
    assert test_settings.discord_client_id == 123456789012345678
    assert test_settings.discord_server_id == 876543210987654321
    assert test_settings.discord_admin_user_id == 111222333444555666

    # Test Storage settings
    assert test_settings.storage_root == Path("/tmp/boss-bot")
    assert test_settings.max_file_size_mb == 50
    assert test_settings.max_concurrent_downloads == 5
    assert test_settings.max_queue_size == 50

    # Test Monitoring settings
    assert test_settings.log_level == "INFO"
    assert test_settings.enable_metrics is True
    assert test_settings.metrics_port == 9090
    assert test_settings.enable_health_check is True
    assert test_settings.health_check_port == 8080

    # Test Security settings
    assert test_settings.rate_limit_requests == 100
    assert test_settings.rate_limit_window_seconds == 60
    assert test_settings.enable_file_validation is True

    # Test Development settings
    assert test_settings.debug is False
    assert test_settings.environment == Environment.DEVELOPMENT

    # Test API Keys
    assert test_settings.openai_api_key.get_secret_value() == "sk-test-key-123456789abcdef"
    assert test_settings.cohere_api_key.get_secret_value() == "test-cohere-key-123456789"
    assert test_settings.debug_aider is True
    assert test_settings.firecrawl_api_key.get_secret_value() == "test-firecrawl-key-123456789"
    assert test_settings.langchain_api_key.get_secret_value() == "test-langchain-key-123456789"
    assert test_settings.langchain_debug_logs is True
    assert str(test_settings.langchain_endpoint) == "http://localhost:8000/"
    assert test_settings.langchain_hub_api_key.get_secret_value() == "test-hub-key-123456789"
    assert str(test_settings.langchain_hub_api_url) == "http://localhost:8001/"
    assert test_settings.langchain_project == "test-project"
    assert test_settings.langchain_tracing_v2 is True
    assert test_settings.pinecone_api_key.get_secret_value() == "test-pinecone-key-123456789"
    assert test_settings.pinecone_env == "test-env"
    assert test_settings.pinecone_index == "test-index"
    assert test_settings.tavily_api_key.get_secret_value() == "test-tavily-key-123456789"
    assert test_settings.unstructured_api_key.get_secret_value() == "test-unstructured-key-123456789"
    assert str(test_settings.unstructured_api_url) == "http://localhost:8002/"


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
    test_settings = BossSettings()
    str_repr = str(test_settings)

    # Check that sensitive values are masked
    assert "**********" in str_repr
    assert "sk-test-key-123456789abcdef" not in str_repr
    assert "test-cohere-key-123456789" not in str_repr
    assert "test-firecrawl-key-123456789" not in str_repr

    # Check that non-sensitive values are included
    assert str(test_settings.storage_root) in str_repr
    assert str(test_settings.max_file_size_mb) in str_repr
    assert str(test_settings.environment) in str_repr
