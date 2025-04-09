"""Tests for the Discord bot client."""

import pytest
import discord
from discord.ext import commands
from pytest_mock import MockerFixture
from typing import Any

from boss_bot.bot.client import BossBot
from boss_bot.core.core_queue import QueueManager
from boss_bot.downloaders.base import DownloadManager
from boss_bot.core.env import BossSettings

# Note: Using standardized fixtures from conftest.py:
# - settings
# - bot
# - mock_env_vars

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
async def test_async_setup_hook(mock_settings: BossSettings, mocker: MockerFixture):
    """Test that extensions are loaded correctly."""
    bot = BossBot(settings=mock_settings)

    # Mock the load_extension method using pytest-mock
    mock_load_extension = mocker.patch.object(bot, 'load_extension', side_effect=mocker.AsyncMock())

    # Call the setup hook
    await bot._async_setup_hook()

    # Verify extensions were loaded
    mock_load_extension.assert_any_call("boss_bot.cogs.downloads")
    mock_load_extension.assert_any_call("boss_bot.cogs.queue")
    assert mock_load_extension.call_count == 2

@pytest.mark.asyncio
async def test_on_ready(capsys: pytest.CaptureFixture, mock_settings: BossSettings, mocker: MockerFixture):
    """Test the on_ready event."""
    # Create bot with test settings
    bot = BossBot(settings=mock_settings)

    # Mock the user property
    mock_user = mocker.Mock()
    mock_user.name = "TestBot"
    mock_user.id = 123456789
    type(bot).user = mocker.PropertyMock(return_value=mock_user)

    # Call on_ready
    await bot.on_ready()

    # Check output
    captured = capsys.readouterr()
    assert "Logged in as TestBot (ID: 123456789)" in captured.err

    # Cleanup
    await bot.close()
