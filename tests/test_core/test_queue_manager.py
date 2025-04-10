"""Tests for queue management functionality."""

import pytest
from datetime import datetime, timedelta

from boss_bot.core.core_queue import QueueManager, QueueStatus, QueueItem

# Fixture migrated to conftest.py as fixture_queue_manager_test
# Original fixture: queue_manager
# New fixture: fixture_queue_manager_test
# Migration date: 2024-03-19

@pytest.mark.asyncio
async def test_queue_initialization(fixture_queue_manager_test: QueueManager):
    """Test queue manager initialization."""
    assert fixture_queue_manager_test.max_queue_size == 50
    assert fixture_queue_manager_test.queue_size == 0
    assert not fixture_queue_manager_test._paused

@pytest.mark.asyncio
async def test_add_to_queue(fixture_queue_manager_test: QueueManager):
    """Test adding items to queue."""
    # Add first item
    pos = await fixture_queue_manager_test.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    assert pos == 1
    assert fixture_queue_manager_test.queue_size == 1

    # Add second item
    pos = await fixture_queue_manager_test.add_to_queue(
        url="https://example.com/test2",
        user_id=12345,
        channel_id=67890,
        filename="test.mp4"
    )
    assert pos == 2
    assert fixture_queue_manager_test.queue_size == 2

@pytest.mark.asyncio
async def test_queue_full(fixture_queue_manager_test: QueueManager):
    """Test queue full behavior."""
    # Fill queue
    for i in range(fixture_queue_manager_test.max_queue_size):
        await fixture_queue_manager_test.add_to_queue(
            url=f"https://example.com/test{i}",
            user_id=12345,
            channel_id=67890
        )

    # Try to add one more
    with pytest.raises(ValueError, match="Queue is full"):
        await fixture_queue_manager_test.add_to_queue(
            url="https://example.com/testfull",
            user_id=12345,
            channel_id=67890
        )

@pytest.mark.asyncio
async def test_get_next_download(fixture_queue_manager_test: QueueManager):
    """Test getting next download from queue."""
    # Add items
    await fixture_queue_manager_test.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    await fixture_queue_manager_test.add_to_queue(
        url="https://example.com/test2",
        user_id=12345,
        channel_id=67890
    )

    # Get first item
    item = await fixture_queue_manager_test.get_next_download()
    assert item is not None
    assert item.url == "https://example.com/test1"
    assert fixture_queue_manager_test.queue_size == 1

    # Get second item
    item = await fixture_queue_manager_test.get_next_download()
    assert item is not None
    assert item.url == "https://example.com/test2"
    assert fixture_queue_manager_test.queue_size == 0

    # Queue empty
    item = await fixture_queue_manager_test.get_next_download()
    assert item is None

@pytest.mark.asyncio
async def test_pause_resume_queue(fixture_queue_manager_test: QueueManager):
    """Test queue pause/resume functionality."""
    # Add item
    await fixture_queue_manager_test.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )

    # Pause queue
    await fixture_queue_manager_test.pause_queue()
    assert fixture_queue_manager_test._paused
    assert await fixture_queue_manager_test.get_next_download() is None

    # Resume queue
    await fixture_queue_manager_test.resume_queue()
    assert not fixture_queue_manager_test._paused
    assert await fixture_queue_manager_test.get_next_download() is not None

@pytest.mark.asyncio
async def test_remove_from_queue(fixture_queue_manager_test: QueueManager):
    """Test removing items from queue."""
    # Add items
    await fixture_queue_manager_test.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    pos = await fixture_queue_manager_test.add_to_queue(
        url="https://example.com/test2",
        user_id=54321,
        channel_id=67890
    )

    # Get items
    items = await fixture_queue_manager_test.get_queue_items()
    item_id = items[1].download_id

    # Try to remove with wrong user
    assert not await fixture_queue_manager_test.remove_from_queue(item_id, 12345)
    assert fixture_queue_manager_test.queue_size == 2

    # Remove with correct user
    assert await fixture_queue_manager_test.remove_from_queue(item_id, 54321)
    assert fixture_queue_manager_test.queue_size == 1

@pytest.mark.asyncio
async def test_clear_queue(fixture_queue_manager_test: QueueManager):
    """Test clearing the queue."""
    # Add items
    await fixture_queue_manager_test.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    await fixture_queue_manager_test.add_to_queue(
        url="https://example.com/test2",
        user_id=12345,
        channel_id=67890
    )

    assert fixture_queue_manager_test.queue_size == 2

    # Clear queue
    await fixture_queue_manager_test.clear_queue()
    assert fixture_queue_manager_test.queue_size == 0

@pytest.mark.asyncio
async def test_queue_status(fixture_queue_manager_test: QueueManager):
    """Test queue status reporting."""
    status = fixture_queue_manager_test.get_queue_status()
    assert status["total_items"] == 0
    assert status["remaining_capacity"] == fixture_queue_manager_test.max_queue_size
    assert not status["is_paused"]

    # Add item and pause
    await fixture_queue_manager_test.add_to_queue(
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    await fixture_queue_manager_test.pause_queue()

    status = fixture_queue_manager_test.get_queue_status()
    assert status["total_items"] == 1
    assert status["remaining_capacity"] == fixture_queue_manager_test.max_queue_size - 1
    assert status["is_paused"]
