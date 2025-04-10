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
# - fixture_bot_test: Clean bot instance for each test
# - fixture_settings_test: Test settings fixture
# - fixture_mock_bot_test: Mocked bot instance for testing

@pytest.mark.asyncio
async def test_bot_initialization(fixture_bot_test: BossBot):
    """Test that bot is initialized with correct settings."""
    assert isinstance(fixture_bot_test, commands.Bot)
    assert fixture_bot_test.command_prefix == "$"
    assert isinstance(fixture_bot_test.intents, discord.Intents)
    assert fixture_bot_test.intents.message_content is True
    assert isinstance(fixture_bot_test.queue_manager, QueueManager)
    assert isinstance(fixture_bot_test.download_manager, DownloadManager)

@pytest.mark.asyncio
async def test_async_setup_hook(fixture_settings_test: BossSettings, mocker: MockerFixture):
    """Test that extensions are loaded correctly."""
    bot = BossBot(settings=fixture_settings_test)

    # Mock the load_extension method using pytest-mock
    mock_load_extension = mocker.patch.object(bot, 'load_extension', side_effect=mocker.AsyncMock())

    # Call the setup hook
    await bot._async_setup_hook()

    # Verify extensions were loaded
    mock_load_extension.assert_any_call("boss_bot.cogs.downloads")
    mock_load_extension.assert_any_call("boss_bot.cogs.queue")
    assert mock_load_extension.call_count == 2

@pytest.mark.asyncio
async def test_on_ready(
    capsys: pytest.CaptureFixture[Any],
    fixture_mock_bot_test: BossBot
):
    """Test the on_ready event."""
    # Configure mock bot user
    mock_user = discord.Object(id=123456789)
    mock_user.name = "TestBot"
    fixture_mock_bot_test.user = mock_user

    # Call on_ready
    await fixture_mock_bot_test.on_ready()

    # Check output
    captured = capsys.readouterr()
    assert "Logged in as TestBot (ID: 123456789)" in captured.err
