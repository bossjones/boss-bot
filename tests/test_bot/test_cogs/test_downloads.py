"""Tests for the downloads cog."""

import pytest
import discord
from discord.ext import commands

from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.bot.client import BossBot

@pytest.fixture
def mock_bot(mocker):
    """Create a mocked bot instance."""
    bot = mocker.Mock(spec=BossBot)
    bot.download_manager = mocker.Mock()
    bot.queue_manager = mocker.Mock()
    return bot

@pytest.fixture
def cog(mock_bot):
    """Create a downloads cog instance for testing."""
    return DownloadCog(mock_bot)

@pytest.mark.asyncio
async def test_download_command(mocker, mock_bot, cog):
    """Test the download command."""
    # Create mock context
    ctx = mocker.Mock()
    url = "https://example.com/video.mp4"

    # Set up mock behaviors using pytest-mock
    mocker.patch.object(mock_bot.download_manager, 'validate_url',
                       return_value=True, autospec=True)
    mocker.patch.object(mock_bot.queue_manager, 'add_to_queue',
                       side_effect=mocker.AsyncMock(), autospec=True)

    # Call the download command
    await cog.download(ctx, url)

    # Verify interactions
    mock_bot.download_manager.validate_url.assert_called_once_with(url)
    mock_bot.queue_manager.add_to_queue.assert_called_once_with(url, ctx.author)
    ctx.send.assert_called_once()

@pytest.mark.asyncio
async def test_download_command_invalid_url(mocker, mock_bot, cog):
    """Test the download command with an invalid URL."""
    # Create mock context
    ctx = mocker.Mock()
    url = "invalid_url"

    # Set up mock behavior for invalid URL
    mocker.patch.object(mock_bot.download_manager, 'validate_url',
                       return_value=False, autospec=True)

    # Call the download command
    await cog.download(ctx, url)

    # Verify error message was sent
    ctx.send.assert_called_once()
    assert "Invalid URL" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_status_command(mocker, mock_bot, cog):
    """Test the status command."""
    # Create mock context
    ctx = mocker.Mock()

    # Set up mock behaviors
    mocker.patch.object(mock_bot.download_manager, 'get_active_downloads',
                       return_value=2, autospec=True)
    mocker.patch.object(mock_bot.queue_manager, 'get_queue_size',
                       return_value=5, autospec=True)

    # Call the status command
    await cog.status(ctx)

    # Verify status was sent
    ctx.send.assert_called_once()
    assert "Active downloads" in ctx.send.call_args[0][0]
    assert "Queue size" in ctx.send.call_args[0][0]
