"""Queue management implementation."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class QueueStatus(Enum):
    """Queue status enum."""

    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueueItem:
    """Queue item data class."""

    id: str
    url: str
    user_id: int
    channel_id: int
    status: QueueStatus
    created_at: datetime
    error: str | None = None


class QueueManager:
    """Manages download queue."""

    def __init__(self, max_queue_size: int = 50):
        """Initialize queue manager."""
        self.max_queue_size = max_queue_size
        self.queue: asyncio.Queue[QueueItem] = asyncio.Queue(maxsize=max_queue_size)

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()

    async def add_download(self, item: QueueItem) -> None:
        """Add download to queue."""
        if self.queue.full():
            raise ValueError("Queue is full")
        await self.queue.put(item)

    async def get_next_download(self) -> QueueItem | None:
        """Get next download from queue."""
        try:
            return await self.queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    def get_queue_status(self) -> dict[str, int]:
        """Get queue status."""
        current_size = self.get_queue_size()
        return {"total_items": current_size, "remaining_capacity": self.max_queue_size - current_size}
