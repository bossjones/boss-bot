"""Tests for queue command cog."""
import pytest
from discord.ext import commands
import discord.ext.test as dpytest
from boss_bot.bot.client import BossBot
from boss_bot.bot.cogs.task_queue import QueueCog

@pytest.fixture
async def bot():
    """Create a bot instance for testing."""
    bot = BossBot()
    await bot._async_setup_hook()
    dpytest.configure(bot)
    return bot

@pytest.mark.asyncio
async def test_clear_queue_command(bot):
    """Test clearing the queue."""
    # Add some downloads first
    for i in range(3):
        await dpytest.message(f"$dl https://twitter.com/user/status/{i}")

    # Clear queue
    await dpytest.message("$clearqueue")

    # Check response
    assert dpytest.verify().message().content(
        "Queue cleared successfully."
    )

    # Verify queue is empty
    await dpytest.message("$queue")
    assert dpytest.verify().message().contains().content(
        "Downloads in Queue: 0"
    )

@pytest.mark.asyncio
async def test_cancel_download_command(bot):
    """Test canceling a specific download."""
    # Add a download
    await dpytest.message("$dl https://twitter.com/user/status/123")

    # Get download ID from response
    messages = dpytest.get_message()
    # Note: In a real scenario, we'd parse the download ID from the message

    # Try to cancel with invalid ID
    await dpytest.message("$cancel invalid_id")
    assert dpytest.verify().message().content(
        "Download not found."
    )

@pytest.mark.asyncio
async def test_queue_status_empty(bot):
    """Test queue status when empty."""
    await dpytest.message("$queue")
    assert dpytest.verify().message().contains().content(
        "Downloads in Queue: 0"
    )

@pytest.mark.asyncio
async def test_queue_status_with_items(bot):
    """Test queue status with items."""
    # Add some downloads
    for i in range(3):
        await dpytest.message(f"$dl https://twitter.com/user/status/{i}")

    await dpytest.message("$queue")
    messages = dpytest.get_message()

    # Verify queue information is displayed
    assert "Current Queue Status" in messages[-1].content
    assert "Downloads in Queue: 3" in messages[-1].content
