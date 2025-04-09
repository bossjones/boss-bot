"""Tests for queue management functionality."""

import pytest
from datetime import datetime, timedelta

from boss_bot.core.core_queue import QueueManager, QueueStatus, QueueItem

@pytest.fixture
def queue_manager():
    """Create a queue manager instance for testing."""
    return QueueManager()

@pytest.mark.asyncio
async def test_queue_initialization(queue_manager: QueueManager):
    """Test queue manager initialization."""
    assert queue_manager.max_queue_size == 50
    assert queue_manager.queue_size == 0
    assert not queue_manager._paused

@pytest.mark.asyncio
async def test_add_to_queue(queue_manager: QueueManager):
    """Test adding items to queue."""
    # Add first item
    pos = await queue_manager.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    assert pos == 1
    assert queue_manager.queue_size == 1

    # Add second item
    pos = await queue_manager.add_to_queue(
        url="https://example.com/test2",
        user_id=12345,
        channel_id=67890,
        filename="test.mp4"
    )
    assert pos == 2
    assert queue_manager.queue_size == 2

@pytest.mark.asyncio
async def test_queue_full(queue_manager: QueueManager):
    """Test queue full behavior."""
    # Fill queue
    for i in range(queue_manager.max_queue_size):
        await queue_manager.add_to_queue(
            url=f"https://example.com/test{i}",
            user_id=12345,
            channel_id=67890
        )

    # Try to add one more
    with pytest.raises(ValueError, match="Queue is full"):
        await queue_manager.add_to_queue(
            url="https://example.com/testfull",
            user_id=12345,
            channel_id=67890
        )

@pytest.mark.asyncio
async def test_get_next_download(queue_manager: QueueManager):
    """Test getting next download from queue."""
    # Add items
    await queue_manager.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    await queue_manager.add_to_queue(
        url="https://example.com/test2",
        user_id=12345,
        channel_id=67890
    )

    # Get first item
    item = await queue_manager.get_next_download()
    assert item is not None
    assert item.url == "https://example.com/test1"
    assert queue_manager.queue_size == 1

    # Get second item
    item = await queue_manager.get_next_download()
    assert item is not None
    assert item.url == "https://example.com/test2"
    assert queue_manager.queue_size == 0

    # Queue empty
    item = await queue_manager.get_next_download()
    assert item is None

@pytest.mark.asyncio
async def test_pause_resume_queue(queue_manager: QueueManager):
    """Test queue pause/resume functionality."""
    # Add item
    await queue_manager.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )

    # Pause queue
    await queue_manager.pause_queue()
    assert queue_manager._paused
    assert await queue_manager.get_next_download() is None

    # Resume queue
    await queue_manager.resume_queue()
    assert not queue_manager._paused
    assert await queue_manager.get_next_download() is not None

@pytest.mark.asyncio
async def test_remove_from_queue(queue_manager: QueueManager):
    """Test removing items from queue."""
    # Add items
    await queue_manager.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    pos = await queue_manager.add_to_queue(
        url="https://example.com/test2",
        user_id=54321,
        channel_id=67890
    )

    # Get items
    items = await queue_manager.get_queue_items()
    item_id = items[1].download_id

    # Try to remove with wrong user
    assert not await queue_manager.remove_from_queue(item_id, 12345)
    assert queue_manager.queue_size == 2

    # Remove with correct user
    assert await queue_manager.remove_from_queue(item_id, 54321)
    assert queue_manager.queue_size == 1

@pytest.mark.asyncio
async def test_clear_queue(queue_manager: QueueManager):
    """Test clearing the queue."""
    # Add items
    await queue_manager.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    await queue_manager.add_to_queue(
        url="https://example.com/test2",
        user_id=12345,
        channel_id=67890
    )

    assert queue_manager.queue_size == 2

    # Clear queue
    await queue_manager.clear_queue()
    assert queue_manager.queue_size == 0

@pytest.mark.asyncio
async def test_queue_status(queue_manager: QueueManager):
    """Test queue status reporting."""
    status = queue_manager.get_queue_status()
    assert status["total_items"] == 0
    assert status["remaining_capacity"] == queue_manager.max_queue_size
    assert not status["is_paused"]

    # Add item and pause
    await queue_manager.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    await queue_manager.pause_queue()

    status = queue_manager.get_queue_status()
    assert status["total_items"] == 1
    assert status["remaining_capacity"] == queue_manager.max_queue_size - 1
    assert status["is_paused"]
