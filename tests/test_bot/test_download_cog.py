"""Tests for download command cog."""
import pytest
from discord.ext import commands
from pytest_mock import MockerFixture

from boss_bot.bot.client import BossBot
from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.core.core_queue import QueueItem, QueueStatus

# Fixture migrated to test_bot/conftest.py as fixture_bot_test
# Original fixture: bot
# New fixture: fixture_bot_test
# Migration date: 2024-03-19

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
async def test_download_command_valid_url(mocker: MockerFixture, fixture_mock_bot_test: BossBot, fixture_download_cog_test: DownloadCog):
    """Test the download command with a valid URL."""
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
    assert "Added" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_download_command_queue_full(mocker: MockerFixture, fixture_mock_bot_test: BossBot, fixture_download_cog_test: DownloadCog):
    """Test download command when queue is full."""
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
    queue_full_error = Exception("Queue is currently full")
    fixture_mock_bot_test.queue_manager.add_to_queue.side_effect = queue_full_error

    # Call the download command's callback directly
    await fixture_download_cog_test.download.callback(fixture_download_cog_test, ctx, url)

    # Verify interactions
    fixture_mock_bot_test.download_manager.validate_url.assert_called_once_with(url)
    fixture_mock_bot_test.queue_manager.add_to_queue.assert_called_once_with(url, ctx.author.id, ctx.channel.id)
    ctx.send.assert_called_once()
    assert "Queue is currently full" in ctx.send.call_args[0][0]

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
