"""Tests for queue command cog."""
import pytest
from discord.ext import commands
import discord.ext.test as dpytest
from boss_bot.bot.client import BossBot
from boss_bot.bot.cogs.task_queue import QueueCog
from pathlib import Path
from boss_bot.core.env import BossSettings

@pytest.mark.asyncio
async def test_clear_queue_command(fixture_bot_test: BossBot) -> None:
    """Test clearing the queue."""
    # Configure dpytest with our bot
    dpytest.configure(fixture_bot_test)

    # Create test guild and channel
    guild = dpytest.backend.make_guild("Test Guild")
    channel = dpytest.backend.make_text_channel("test-channel", guild)

    # Create test user
    member = dpytest.backend.make_member("TestUser", guild)

    # Add some downloads first
    for i in range(3):
        message = await dpytest.message(f"$download https://twitter.com/user/status/{i}", channel=channel, member=member)
        assert "Added" in message.content

    # Clear queue
    message = await dpytest.message("$clear", channel=channel, member=member)
    assert "Download queue cleared" in message.content

    # Verify queue is empty
    message = await dpytest.message("$status", channel=channel, member=member)
    assert "Queue size: 0" in message.content

@pytest.mark.asyncio
async def test_cancel_download_command(fixture_bot_test: BossBot) -> None:
    """Test canceling a specific download."""
    # Configure dpytest with our bot
    dpytest.configure(fixture_bot_test)

    # Create test guild and channel
    guild = dpytest.backend.make_guild("Test Guild")
    channel = dpytest.backend.make_text_channel("test-channel", guild)

    # Create test user
    member = dpytest.backend.make_member("TestUser", guild)

    # Add a download
    message = await dpytest.message("$download https://twitter.com/user/status/123", channel=channel, member=member)
    assert "Added" in message.content

    # Try to cancel with invalid ID
    message = await dpytest.message("$cancel invalid_id", channel=channel, member=member)
    assert "not found" in message.content.lower()

@pytest.mark.asyncio
async def test_queue_status_empty(fixture_bot_test: BossBot) -> None:
    """Test queue status when empty."""
    # Configure dpytest with our bot
    dpytest.configure(fixture_bot_test)

    # Create test guild and channel
    guild = dpytest.backend.make_guild("Test Guild")
    channel = dpytest.backend.make_text_channel("test-channel", guild)

    # Create test user
    member = dpytest.backend.make_member("TestUser", guild)

    # Check empty queue
    message = await dpytest.message("$status", channel=channel, member=member)
    assert "Queue size: 0" in message.content

@pytest.mark.asyncio
async def test_queue_status_with_items(fixture_bot_test: BossBot) -> None:
    """Test queue status with items."""
    # Configure dpytest with our bot
    dpytest.configure(fixture_bot_test)

    # Create test guild and channel
    guild = dpytest.backend.make_guild("Test Guild")
    channel = dpytest.backend.make_text_channel("test-channel", guild)

    # Create test user
    member = dpytest.backend.make_member("TestUser", guild)

    # Add some downloads
    for i in range(3):
        message = await dpytest.message(f"$download https://twitter.com/user/status/{i}", channel=channel, member=member)
        assert "Added" in message.content

    # Check queue status
    message = await dpytest.message("$status", channel=channel, member=member)
    assert "Queue size: 3" in message.content
