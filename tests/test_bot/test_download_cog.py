"""Tests for download command cog."""
import pytest
from discord.ext import commands
import discord.ext.test as dpytest
from boss_bot.bot.client import BossBot
from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.core.core_queue import QueueItem, QueueStatus

# Fixture migrated to test_bot/conftest.py as fixture_bot_test
# Original fixture: bot
# New fixture: fixture_bot_test
# Migration date: 2024-03-19

@pytest.mark.asyncio
async def test_download_command_invalid_url(fixture_bot_test: BossBot):
    """Test download command with invalid URL."""
    # Send command with invalid URL
    await dpytest.message("$dl invalid_url")

    # Check response
    assert dpytest.verify().message().content(
        "Invalid URL. Please provide a valid Twitter or Reddit URL."
    )

@pytest.mark.asyncio
async def test_download_command_valid_url(fixture_bot_test: BossBot):
    """Test download command with valid URL."""
    # Send command with valid URL
    await dpytest.message("$dl https://twitter.com/user/status/123")

    # Check response
    assert dpytest.verify().message().contains().content(
        "Download started! Your position in queue:"
    )

@pytest.mark.asyncio
async def test_download_command_queue_full(fixture_bot_test: BossBot):
    """Test download command when queue is full."""
    # Fill the queue
    for i in range(50):  # Max queue size
        await dpytest.message(f"$dl https://twitter.com/user/status/{i}")

    # Try one more download
    await dpytest.message("$dl https://twitter.com/user/status/extra")

    # Check response
    assert dpytest.verify().message().content(
        "Queue is currently full. Please try again later."
    )

@pytest.mark.asyncio
async def test_queue_command(fixture_bot_test: BossBot):
    """Test queue status command."""
    # Add some downloads
    for i in range(3):
        await dpytest.message(f"$dl https://twitter.com/user/status/{i}")

    # Check queue status
    await dpytest.message("$queue")

    # Verify response contains queue information
    assert dpytest.verify().message().contains().content(
        "Current Queue Status"
    )
