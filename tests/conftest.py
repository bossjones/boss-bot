"""Test configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from discord.ext import commands
from pydantic import AnyHttpUrl

from boss_bot.bot.client import BossBot
from boss_bot.core.env import BossSettings, Environment
from boss_bot.core.core_queue import QueueManager
from boss_bot.downloaders.base import DownloadManager

@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create and provide a new event loop for each test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def settings() -> BossSettings:
    """Provide test settings."""
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
        unstructured_api_url=AnyHttpUrl("http://localhost:8002"),

        # Environment variables for backward compatibility
        DISCORD_TOKEN="test_token",
        DISCORD_CLIENT_ID="123456789",
        DISCORD_SERVER_ID="987654321",
        DISCORD_ADMIN_USER_ID="12345"
    )

@pytest.fixture
async def bot(settings: BossSettings, mocker) -> AsyncGenerator[BossBot, None]:
    """Provide a test bot instance."""
    bot = BossBot(settings=settings)

    # Mock necessary Discord.py methods
    bot.wait_until_ready = mocker.AsyncMock()
    bot.login = mocker.AsyncMock()
    bot.connect = mocker.AsyncMock()
    bot.close = mocker.AsyncMock()

    yield bot

    # Cleanup
    await bot.close()

@pytest.fixture
def queue_manager(settings: BossSettings) -> QueueManager:
    """Provide a test queue manager."""
    return QueueManager(max_queue_size=settings.max_queue_size)

@pytest.fixture
def download_manager(settings: BossSettings) -> DownloadManager:
    """Provide a test download manager."""
    return DownloadManager(max_concurrent_downloads=settings.max_concurrent_downloads)

@pytest.fixture
def ctx(mocker) -> commands.Context:
    """Provide a mock Discord context."""
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    return ctx
