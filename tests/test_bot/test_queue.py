"""Tests for queue cog functionality."""

import pytest
import discord
from datetime import datetime
from uuid import UUID

from boss_bot.bot.client import BossBot
from boss_bot.bot.cogs.task_queue import QueueCog
from boss_bot.core.core_queue import QueueItem, QueueStatus

# Note: Using standardized fixtures from conftest.py:
# - settings
# - bot
# - ctx

@pytest.mark.asyncio
async def test_show_queue_empty(bot: BossBot, ctx, mocker):
    """Test showing empty queue."""
    cog = QueueCog(bot)
    bot.queue_manager.get_queue_items = mocker.AsyncMock(return_value=[])

    await cog.show_queue(ctx)
    ctx.send.assert_called_once_with("The download queue is empty.")

@pytest.mark.asyncio
async def test_show_queue_with_items(bot: BossBot, ctx, mocker):
    """Test showing queue with items."""
    cog = QueueCog(bot)

    # Create test queue items
    items = [
        QueueItem(
            download_id=UUID("12345678-1234-5678-1234-567812345678"),
            url="https://example.com/test1",
            user_id=12345,
            channel_id=67890,
            status=QueueStatus.QUEUED,
            created_at=datetime.utcnow(),
            filename="test1.mp4"
        ),
        QueueItem(
            download_id=UUID("87654321-4321-8765-4321-876543210987"),
            url="https://example.com/test2",
            user_id=54321,
            channel_id=67890,
            status=QueueStatus.QUEUED,
            created_at=datetime.utcnow()
        )
    ]
    bot.queue_manager.get_queue_items = mocker.AsyncMock(return_value=items)

    # Mock user lookup
    bot.get_user = mocker.Mock()
    user1, user2 = mocker.Mock(), mocker.Mock()
    user1.name = "User1"
    user2.name = "User2"
    bot.get_user.side_effect = [user1, user2]

    await cog.show_queue(ctx)

    # Verify embed was created and sent
    ctx.send.assert_called_once()
    call_args = ctx.send.call_args[0][0]
    assert isinstance(call_args, discord.Embed)
    assert "Download Queue" in call_args.title
    assert "test1.mp4" in call_args.description
    assert "User1" in call_args.description
    assert "User2" in call_args.description
    assert "Page 1/1" in call_args.footer.text

@pytest.mark.asyncio
async def test_show_queue_pagination(bot, ctx, mocker):
    """Test queue pagination."""
    cog = QueueCog(bot)

    # Create 7 test items (more than one page)
    items = [
        QueueItem(
            download_id=UUID(f"12345678-1234-5678-1234-{i:012d}"),
            url=f"https://example.com/test{i}",
            user_id=12345,
            channel_id=67890,
            status=QueueStatus.QUEUED,
            created_at=datetime.utcnow()
        ) for i in range(7)
    ]
    bot.queue_manager.get_queue_items = mocker.AsyncMock(return_value=items)

    # Mock user lookup
    bot.get_user = mocker.Mock()
    user = mocker.Mock()
    user.name = "User"
    bot.get_user.return_value = user

    # Test first page
    await cog.show_queue(ctx, 1)
    call_args = ctx.send.call_args[0][0]
    assert "Page 1/2" in call_args.footer.text
    assert len(call_args.description.split("\n")) == 5  # 5 items per page

    # Reset mock and test second page
    ctx.send.reset_mock()
    await cog.show_queue(ctx, 2)
    call_args = ctx.send.call_args[0][0]
    assert "Page 2/2" in call_args.footer.text
    assert len(call_args.description.split("\n")) == 2  # 2 remaining items

@pytest.mark.asyncio
async def test_clear_queue(bot, ctx, mocker):
    """Test clearing the queue."""
    cog = QueueCog(bot)
    bot.queue_manager.clear_queue = mocker.AsyncMock()

    await cog.clear_queue(ctx)
    bot.queue_manager.clear_queue.assert_called_once()
    ctx.send.assert_called_once_with("Download queue cleared.")

@pytest.mark.asyncio
async def test_remove_from_queue_success(bot, ctx, mocker):
    """Test successful queue item removal."""
    cog = QueueCog(bot)
    bot.queue_manager.remove_from_queue = mocker.AsyncMock(return_value=True)

    await cog.remove_from_queue(ctx, "test-id")
    ctx.send.assert_called_once_with("Download test-id removed from queue.")

@pytest.mark.asyncio
async def test_remove_from_queue_not_found(bot, ctx, mocker):
    """Test removing non-existent queue item."""
    cog = QueueCog(bot)
    bot.queue_manager.remove_from_queue = mocker.AsyncMock(return_value=False)

    await cog.remove_from_queue(ctx, "test-id")
    ctx.send.assert_called_once_with("Download test-id not found or you don't have permission to remove it.")

@pytest.mark.asyncio
async def test_pause_queue(bot, ctx, mocker):
    """Test pausing the queue."""
    cog = QueueCog(bot)
    bot.queue_manager.pause_queue = mocker.AsyncMock()

    await cog.pause_queue(ctx)
    bot.queue_manager.pause_queue.assert_called_once()
    ctx.send.assert_called_once_with("Download queue paused. Current downloads will complete but no new downloads will start.")

@pytest.mark.asyncio
async def test_resume_queue(bot, ctx, mocker):
    """Test resuming the queue."""
    cog = QueueCog(bot)
    bot.queue_manager.resume_queue = mocker.AsyncMock()

    await cog.resume_queue(ctx)
    bot.queue_manager.resume_queue.assert_called_once()
    ctx.send.assert_called_once_with("Download queue resumed. New downloads will now start.")
