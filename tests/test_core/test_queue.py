"""Tests for queue manager."""
import pytest
from datetime import datetime
from boss_bot.core.queue import QueueManager, QueueItem, QueueStatus

@pytest.fixture
def queue_manager():
    """Create a queue manager instance for testing."""
    return QueueManager()

@pytest.mark.asyncio
async def test_queue_initialization(queue_manager):
    """Test that queue manager initializes correctly."""
    assert isinstance(queue_manager, QueueManager)
    assert queue_manager.max_queue_size == 50
    assert queue_manager.queue.empty()

@pytest.mark.asyncio
async def test_add_to_queue(queue_manager):
    """Test adding items to queue."""
    item = QueueItem(
        id="test_1",
        url="https://twitter.com/user/status/123",
        user_id=123456789,
        channel_id=987654321,
        status=QueueStatus.QUEUED,
        created_at=datetime.now()
    )

    await queue_manager.add_download(item)
    assert not queue_manager.queue.empty()
    assert queue_manager.get_queue_size() == 1

@pytest.mark.asyncio
async def test_queue_size_limit(queue_manager):
    """Test queue size limit."""
    # Try to add more than max items
    for i in range(queue_manager.max_queue_size + 1):
        item = QueueItem(
            id=f"test_{i}",
            url=f"https://twitter.com/user/status/{i}",
            user_id=123456789,
            channel_id=987654321,
            status=QueueStatus.QUEUED,
            created_at=datetime.now()
        )

        if i < queue_manager.max_queue_size:
            await queue_manager.add_download(item)
        else:
            with pytest.raises(ValueError, match="Queue is full"):
                await queue_manager.add_download(item)

@pytest.mark.asyncio
async def test_get_next_download(queue_manager):
    """Test getting next download from queue."""
    # Add an item
    item = QueueItem(
        id="test_1",
        url="https://twitter.com/user/status/123",
        user_id=123456789,
        channel_id=987654321,
        status=QueueStatus.QUEUED,
        created_at=datetime.now()
    )
    await queue_manager.add_download(item)

    # Get next item
    next_item = await queue_manager.get_next_download()
    assert next_item is not None
    assert next_item.id == "test_1"
    assert next_item.status == QueueStatus.QUEUED

    # Queue should be empty now
    assert queue_manager.queue.empty()

@pytest.mark.asyncio
async def test_queue_status(queue_manager):
    """Test getting queue status."""
    # Add some items
    for i in range(3):
        item = QueueItem(
            id=f"test_{i}",
            url=f"https://twitter.com/user/status/{i}",
            user_id=123456789,
            channel_id=987654321,
            status=QueueStatus.QUEUED,
            created_at=datetime.now()
        )
        await queue_manager.add_download(item)

    status = queue_manager.get_queue_status()
    assert status["total_items"] == 3
    assert status["remaining_capacity"] == queue_manager.max_queue_size - 3
