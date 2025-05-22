"""Tests for download command cog."""
import pytest
import discord
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
    # Configure dpytest with our bot
    dpytest.configure(fixture_bot_test)

    # Create test guild and channel
    guild = dpytest.backend.make_guild("Test Guild")
    channel = dpytest.backend.make_text_channel("test-channel", guild)

    # Create test user correctly (using discord.Object)
    user = discord.Object(id=12345)
    user.name = "TestUser"
    user.discriminator = "0000"
    user.avatar = None
    member = dpytest.backend.make_member(user, guild)

    # Send command with invalid URL
    message = await dpytest.message("$download invalid_url", channel=channel, member=member)

    # Check response
    assert "Invalid URL" in message.content

@pytest.mark.asyncio
async def test_download_command_valid_url(fixture_bot_test: BossBot):
    """Test download command with valid URL."""
    # Configure dpytest with our bot
    dpytest.configure(fixture_bot_test)

    # Create test guild and channel
    guild = dpytest.backend.make_guild("Test Guild")
    channel = dpytest.backend.make_text_channel("test-channel", guild)

    # Create test user
    member = dpytest.backend.make_member("TestUser", guild)

    # Send command with valid URL
    message = await dpytest.message("$download https://twitter.com/user/status/123", channel=channel, member=member)

    # Check response
    assert "Added" in message.content

@pytest.mark.asyncio
async def test_download_command_queue_full(fixture_bot_test: BossBot):
    """Test download command when queue is full."""
    # Configure dpytest with our bot
    dpytest.configure(fixture_bot_test)

    # Create test guild and channel
    guild = dpytest.backend.make_guild("Test Guild")
    channel = dpytest.backend.make_text_channel("test-channel", guild)

    # Create test user
    member = dpytest.backend.make_member("TestUser", guild)

    # Fill the queue
    for i in range(50):  # Max queue size
        await dpytest.message(f"$download https://twitter.com/user/status/{i}", channel=channel, member=member)

    # Try one more download
    message = await dpytest.message("$download https://twitter.com/user/status/extra", channel=channel, member=member)

    # Check response
    assert "Queue is currently full" in message.content

@pytest.mark.asyncio
async def test_queue_command(fixture_bot_test: BossBot):
    """Test queue status command."""
    # Configure dpytest with our bot
    dpytest.configure(fixture_bot_test)

    # Create test guild and channel
    guild = dpytest.backend.make_guild("Test Guild")
    channel = dpytest.backend.make_text_channel("test-channel", guild)

    # Create test user
    member = dpytest.backend.make_member("TestUser", guild)

    # Add some downloads
    for i in range(3):
        await dpytest.message(f"$download https://twitter.com/user/status/{i}", channel=channel, member=member)

    # Check queue status
    message = await dpytest.message("$status", channel=channel, member=member)

    # Verify response contains queue information
    assert "Queue size" in message.content
