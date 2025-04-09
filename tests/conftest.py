"""Test configuration and fixtures for Boss-Bot."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Dict, Any

import pytest
from discord.ext import commands
from pydantic import AnyHttpUrl
from pytest_mock import MockerFixture

from boss_bot.bot.client import BossBot
from boss_bot.core.env import BossSettings, Environment
from boss_bot.core.core_queue import QueueManager
from boss_bot.downloaders.base import DownloadManager
from pytest import MonkeyPatch
import os

# --- Test Environment Configuration --- #

@pytest.fixture(scope="function")
def fixture_env_vars_test(monkeypatch: MonkeyPatch) -> Generator[MonkeyPatch, None, None]:
    """Mock environment variables for unit tests.

    Scope: function - ensures clean environment for each test
    Yields: MonkeyPatch instance for test modifications
    Cleanup: Automatically resets environment after each test
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", "test-anthropic-key"))
    monkeypatch.setenv("BETTER_EXCEPTIONS", os.getenv("BETTER_EXCEPTIONS", "true"))
    monkeypatch.setenv("COHERE_API_KEY", os.getenv("COHERE_API_KEY", "test-cohere-key"))
    monkeypatch.setenv("DEBUG_AIDER", os.getenv("DEBUG_AIDER", "true"))
    monkeypatch.setenv("DISCORD_ADMIN_USER_ID", os.getenv("DISCORD_ADMIN_USER_ID", "12345"))
    monkeypatch.setenv("DISCORD_ADMIN_USER_INVITED", os.getenv("DISCORD_ADMIN_USER_INVITED", "false"))
    monkeypatch.setenv("DISCORD_CLIENT_ID", os.getenv("DISCORD_CLIENT_ID", "123456789"))
    monkeypatch.setenv("DISCORD_SERVER_ID", os.getenv("DISCORD_SERVER_ID", "987654321"))
    monkeypatch.setenv("DISCORD_TOKEN", os.getenv("DISCORD_TOKEN", "test_token"))
    monkeypatch.setenv("ENABLE_AI", os.getenv("ENABLE_AI", "true"))
    monkeypatch.setenv("ENABLE_REDIS", os.getenv("ENABLE_REDIS", "false"))
    monkeypatch.setenv("ENABLE_SENTRY", os.getenv("ENABLE_SENTRY", "false"))
    monkeypatch.setenv("FIRECRAWL_API_KEY", os.getenv("FIRECRAWL_API_KEY", "test-firecrawl-key"))
    monkeypatch.setenv("LANGCHAIN_API_KEY", os.getenv("LANGCHAIN_API_KEY", "test-langchain-key"))
    monkeypatch.setenv("LANGCHAIN_DEBUG_LOGS", os.getenv("LANGCHAIN_DEBUG_LOGS", "true"))
    monkeypatch.setenv("LANGCHAIN_ENDPOINT", os.getenv("LANGCHAIN_ENDPOINT", "http://localhost:8000"))
    monkeypatch.setenv("LANGCHAIN_HUB_API_KEY", os.getenv("LANGCHAIN_HUB_API_KEY", "test-hub-key"))
    monkeypatch.setenv("LANGCHAIN_HUB_API_URL", os.getenv("LANGCHAIN_HUB_API_URL", "http://localhost:8001"))
    monkeypatch.setenv("LANGCHAIN_PROJECT", os.getenv("LANGCHAIN_PROJECT", "test-project"))
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "true"))
    monkeypatch.setenv("LOCAL_TEST_DEBUG", os.getenv("LOCAL_TEST_DEBUG", "true"))
    monkeypatch.setenv("LOCAL_TEST_ENABLE_EVALS", os.getenv("LOCAL_TEST_ENABLE_EVALS", "true"))
    monkeypatch.setenv("OCO_LANGUAGE", os.getenv("OCO_LANGUAGE", "en"))
    monkeypatch.setenv("OCO_MODEL", os.getenv("OCO_MODEL", "gpt-4o"))
    monkeypatch.setenv("OCO_OPENAI_API_KEY", os.getenv("OCO_OPENAI_API_KEY", "sk-test-oco-key"))
    monkeypatch.setenv("OCO_PROMPT_MODULE", os.getenv("OCO_PROMPT_MODULE", "conventional-commit"))
    monkeypatch.setenv("OCO_TOKENS_MAX_INPUT", os.getenv("OCO_TOKENS_MAX_INPUT", "4096"))
    monkeypatch.setenv("OCO_TOKENS_MAX_OUTPUT", os.getenv("OCO_TOKENS_MAX_OUTPUT", "500"))
    monkeypatch.setenv("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "sk-test-key-123456789abcdef"))
    monkeypatch.setenv("PINECONE_API_KEY", os.getenv("PINECONE_API_KEY", "test-pinecone-key"))
    monkeypatch.setenv("PINECONE_ENV", os.getenv("PINECONE_ENV", "test-env"))
    monkeypatch.setenv("PINECONE_INDEX", os.getenv("PINECONE_INDEX", "test-index"))
    monkeypatch.setenv("PYTHON_DEBUG", os.getenv("PYTHON_DEBUG", "true"))
    monkeypatch.setenv("PYTHONASYNCIODEBUG", os.getenv("PYTHONASYNCIODEBUG", "1"))
    monkeypatch.setenv("SENTRY_DSN", os.getenv("SENTRY_DSN", "https://test-sentry-dsn"))
    monkeypatch.setenv("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY", "test-tavily-key"))
    monkeypatch.setenv("UNSTRUCTURED_API_KEY", os.getenv("UNSTRUCTURED_API_KEY", "test-unstructured-key"))
    monkeypatch.setenv("UNSTRUCTURED_API_URL", os.getenv("UNSTRUCTURED_API_URL", "http://localhost:8002"))

    # Return the monkeypatch instance so tests can modify environment variables if needed
    yield monkeypatch

    # No explicit teardown needed - pytest's monkeypatch fixture handles cleanup automatically

@pytest.fixture
def set_langsmith_env_vars_evals(monkeypatch: MonkeyPatch) -> None:
    """Set environment variables for LangSmith evals."""
    monkeypatch.setenv("LANGCHAIN_API_KEY", os.getenv("LANGCHAIN_API_KEY"))
    monkeypatch.setenv("LANGCHAIN_ENDPOINT", os.getenv("LANGCHAIN_ENDPOINT"))
    monkeypatch.setenv("LANGCHAIN_PROJECT", os.getenv("LANGCHAIN_PROJECT"))


# --- Core Test Fixtures --- #

@pytest.fixture(scope="function")
def fixture_event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create and provide a new event loop for each test.

    Scope: function - ensures each test gets a fresh event loop
    Yields: asyncio.AbstractEventLoop
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def fixture_settings_test(fixture_env_vars_test: MonkeyPatch) -> BossSettings:
    """Provide standardized test settings.

    Scope: function - ensures clean settings for each test
    Args:
        fixture_env_vars_test: Environment variables fixture
    Returns: BossSettings instance with test configuration
    """
    return BossSettings(
        # Discord settings
        discord_token="test_token",
        discord_client_id=123456789,
        discord_server_id=987654321,
        discord_admin_user_id=12345,
        discord_admin_user_invited=False,

        # Feature flags
        enable_ai=True,
        enable_redis=False,
        enable_sentry=False,

        # Service settings
        sentry_dsn=None,
        openai_api_key="sk-test123456789",

        # Storage Configuration
        storage_root=Path("/tmp/boss-bot-test"),
        max_file_size_mb=50,
        max_concurrent_downloads=2,
        max_queue_size=50,

        # Monitoring Configuration
        log_level="DEBUG",
        enable_metrics=True,
        metrics_port=9090,
        enable_health_check=True,
        health_check_port=8080,

        # Security Configuration
        rate_limit_requests=100,
        rate_limit_window_seconds=60,
        enable_file_validation=True,

        # Development Settings
        debug=True,
        environment=Environment.DEVELOPMENT,

        # Additional API Keys and Settings
        cohere_api_key="test-cohere-key",
        debug_aider=True,
        firecrawl_api_key="test-firecrawl-key",
        langchain_api_key="test-langchain-key",
        langchain_debug_logs=True,
        langchain_endpoint=AnyHttpUrl("http://localhost:8000"),
        langchain_hub_api_key="test-langchain-hub-key",
        langchain_hub_api_url=AnyHttpUrl("http://localhost:8001"),
        langchain_project="test-project",
        langchain_tracing_v2=True,
        pinecone_api_key="test-pinecone-key",
        pinecone_env="test-env",
        pinecone_index="test-index",
        tavily_api_key="test-tavily-key",
        unstructured_api_key="test-unstructured-key",
        unstructured_api_url=AnyHttpUrl("http://localhost:8002")
    )

# --- Discord Bot Fixtures --- #

@pytest.fixture(scope="function")
def fixture_discord_bot(
    fixture_settings_test: BossSettings,
    mocker: MockerFixture
) -> AsyncGenerator[BossBot, None]:
    """Provide a test bot instance with configurable mocking.

    Scope: function - ensures clean bot instance for each test
    Args:
        fixture_settings_test: Test settings fixture
        mocker: PyTest mocker fixture
    Yields: Configured BossBot instance
    Cleanup: Closes bot connection and resets state
    """
    bot = BossBot(settings=fixture_settings_test)
    bot.is_mock = True  # New flag for consistent mocking behavior

    def configure_mock(mock_all: bool = True):
        """Configure bot mocking level."""
        if mock_all:
            bot.wait_until_ready = mocker.AsyncMock()
            bot.login = mocker.AsyncMock()
            bot.connect = mocker.AsyncMock()
            bot.close = mocker.AsyncMock()

    bot.configure_mock = configure_mock
    bot.configure_mock()  # Default to full mocking

    yield bot

    # Cleanup
    if not bot.is_closed():
        await bot.close()

@pytest.fixture(scope="function")
def fixture_discord_context(
    fixture_discord_bot: BossBot,
    mocker: MockerFixture
) -> commands.Context:
    """Provide a mock Discord context for command testing.

    Scope: function - ensures clean context for each test
    Args:
        fixture_discord_bot: Bot fixture
        mocker: PyTest mocker fixture
    Returns: Mocked Discord Context
    """
    ctx = mocker.Mock(spec=commands.Context)
    ctx.bot = fixture_discord_bot
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    return ctx

# --- Service Fixtures --- #

@pytest.fixture(scope="function")
def fixture_queue_manager(fixture_settings_test: BossSettings) -> QueueManager:
    """Provide a test queue manager instance.

    Scope: function - ensures clean queue for each test
    Args:
        fixture_settings_test: Test settings fixture
    Returns: Configured QueueManager instance
    """
    manager = QueueManager(max_queue_size=fixture_settings_test.max_queue_size)

    def reset_state():
        """Reset queue state between tests."""
        manager.queue.clear()
        manager.processing.clear()

    manager.reset_state = reset_state
    manager.reset_state()  # Start clean

    return manager

@pytest.fixture(scope="function")
def fixture_download_manager(fixture_settings_test: BossSettings) -> DownloadManager:
    """Provide a test download manager instance.

    Scope: function - ensures clean manager for each test
    Args:
        fixture_settings_test: Test settings fixture
    Returns: Configured DownloadManager instance
    """
    manager = DownloadManager(
        max_concurrent_downloads=fixture_settings_test.max_concurrent_downloads
    )

    def reset_state():
        """Reset download state between tests."""
        manager.active_downloads.clear()
        manager.completed_downloads.clear()
        manager.failed_downloads.clear()

    manager.reset_state = reset_state
    manager.reset_state()  # Start clean

    return manager
