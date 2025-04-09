"""Test configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from discord.ext import commands

from boss_bot.bot.client import BossBot
from boss_bot.core.env import BossSettings
from boss_bot.core.queue import QueueManager
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
        discord_token="test_token",
        discord_client_id="123456789",
        discord_server_id="987654321",
        discord_admin_user_id="12345",
        max_concurrent_downloads=2,
        max_queue_size=5,
        storage_path="/tmp/boss-bot-test",
        log_level="DEBUG"
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
