"""Tests for the Discord bot client."""

import pytest
import discord
from discord.ext import commands
from unittest.mock import Mock, PropertyMock

from boss_bot.bot.client import BossBot
from boss_bot.core.env import BossSettings
from boss_bot.core.core_queue import QueueManager
from boss_bot.downloaders.base import DownloadManager

@pytest.fixture
def mock_env(monkeypatch):
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

@pytest.fixture
async def bot(mock_env):
    """Create a bot instance for testing."""
    bot = BossBot()
    yield bot
    # Cleanup
    await bot.close()

@pytest.mark.asyncio
async def test_bot_initialization(bot: BossBot):
    """Test that bot is initialized with correct settings."""
    assert isinstance(bot, commands.Bot)
    assert bot.command_prefix == "$"
    assert isinstance(bot.intents, discord.Intents)
    assert bot.intents.message_content is True
    assert isinstance(bot.queue_manager, QueueManager)
    assert isinstance(bot.download_manager, DownloadManager)

@pytest.mark.asyncio
async def test_async_setup_hook(mock_env, mocker):
    """Test that extensions are loaded correctly."""
    bot = BossBot()

    # Mock the load_extension method using pytest-mock
    mock_load_extension = mocker.patch.object(bot, 'load_extension', side_effect=mocker.AsyncMock())

    # Call the setup hook
    await bot._async_setup_hook()

    # Verify extensions were loaded
    mock_load_extension.assert_any_call("boss_bot.cogs.downloads")
    mock_load_extension.assert_any_call("boss_bot.cogs.queue")
    assert mock_load_extension.call_count == 2

@pytest.mark.asyncio
async def test_on_ready(capsys, settings):
    """Test the on_ready event."""
    # Create bot with test settings
    bot = BossBot(settings=settings)

    # Mock the user property
    mock_user = Mock()
    mock_user.name = "TestBot"
    mock_user.id = 123456789
    type(bot).user = PropertyMock(return_value=mock_user)

    # Call on_ready
    await bot.on_ready()

    # Check output
    captured = capsys.readouterr()
    assert "Logged in as TestBot (ID: 123456789)" in captured.err

    # Cleanup
    await bot.close()
