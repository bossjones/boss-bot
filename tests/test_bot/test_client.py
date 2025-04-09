"""Tests for the Discord bot client."""

import pytest
import discord
from discord.ext import commands

from boss_bot.bot.client import BossBot
from boss_bot.core.queue import QueueManager
from boss_bot.downloaders.base import DownloadManager

@pytest.fixture
async def bot():
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
async def test_async_setup_hook(mocker):
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
async def test_on_ready(mocker, capsys: pytest.CaptureFixture[str]):
    """Test the on_ready event handler."""
    bot = BossBot()

    # Mock the bot user using pytest-mock
    mock_user = mocker.Mock()
    mock_user.id = 123456789
    mock_user.__str__.return_value = "TestBot"

    # Use mocker.patch.object for setting the user property
    mocker.patch.object(bot, 'user', mock_user)

    await bot.on_ready()

    captured = capsys.readouterr()
    assert "Logged in as TestBot" in captured.out
    assert "(ID: 123456789)" in captured.out
