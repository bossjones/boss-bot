"""Tests for the downloads cog."""

import pytest
import discord
from discord.ext import commands

from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.bot.client import BossBot
from boss_bot.core.core_queue import QueueItem, QueueStatus
from pytest_mock import MockerFixture

# Fixtures migrated to test_bot/conftest.py as fixture_mock_bot_test and fixture_download_cog_test
# Original fixtures: mock_bot, cog
# New fixtures: fixture_mock_bot_test, fixture_download_cog_test
# Migration date: 2024-03-19

@pytest.mark.asyncio
async def test_download_command(mocker: MockerFixture, fixture_mock_bot_test: BossBot, fixture_download_cog_test: DownloadCog):
    """Test the download command."""
    # Create mock context with required attributes
    ctx = mocker.Mock(spec=commands.Context)
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    ctx.send = mocker.AsyncMock()
    url = "https://example.com/video.mp4"

    # Set up mock behaviors
    fixture_mock_bot_test.download_manager.validate_url = mocker.AsyncMock(return_value=True)
    fixture_mock_bot_test.queue_manager.add_to_queue = mocker.AsyncMock()

    # Call the download command's callback directly
    await fixture_download_cog_test.download.callback(fixture_download_cog_test, ctx, url)

    # Verify interactions
    fixture_mock_bot_test.download_manager.validate_url.assert_called_once_with(url)
    fixture_mock_bot_test.queue_manager.add_to_queue.assert_called_once_with(url, ctx.author.id, ctx.channel.id)
    ctx.send.assert_called_once()

@pytest.mark.asyncio
async def test_download_command_invalid_url(mocker: MockerFixture, fixture_mock_bot_test: BossBot, fixture_download_cog_test: DownloadCog):
    """Test the download command with an invalid URL."""
    # Create mock context with required attributes
    ctx = mocker.Mock(spec=commands.Context)
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    ctx.send = mocker.AsyncMock()
    url = "invalid_url"

    # Set up mock behavior for invalid URL
    fixture_mock_bot_test.download_manager.validate_url = mocker.AsyncMock(return_value=False)

    # Call the download command's callback directly
    await fixture_download_cog_test.download.callback(fixture_download_cog_test, ctx, url)

    # Verify error message was sent
    ctx.send.assert_called_once()
    assert "Invalid URL" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_status_command(mocker: MockerFixture, fixture_mock_bot_test: BossBot, fixture_download_cog_test: DownloadCog):
    """Test the status command."""
    # Create mock context with required attributes
    ctx = mocker.Mock(spec=commands.Context)
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    ctx.send = mocker.AsyncMock()

    # Set up mock behaviors
    fixture_mock_bot_test.download_manager.get_active_downloads.return_value = 2
    fixture_mock_bot_test.queue_manager.get_queue_size.return_value = 5

    # Call the status command's callback directly
    await fixture_download_cog_test.status.callback(fixture_download_cog_test, ctx)

    # Verify status was sent
    ctx.send.assert_called_once()
    assert "Active downloads" in ctx.send.call_args[0][0]
    assert "Queue size" in ctx.send.call_args[0][0]
