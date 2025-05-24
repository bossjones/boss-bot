"""Queue management implementation."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class QueueStatus(Enum):
    """Queue status enum."""

    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueItem:
    """Queue item data class."""

    download_id: UUID
    url: str
    user_id: int
    channel_id: int
    status: QueueStatus
    created_at: datetime
    filename: str | None = None
    error: str | None = None


class QueueManager:
    """Manages download queue."""

    def __init__(self, max_queue_size: int = 50):
        """Initialize queue manager."""
        self.max_queue_size = max_queue_size
        self._queue: list[QueueItem] = []
        self._paused = False
        self._lock = asyncio.Lock()

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return len(self._queue)

    async def add_to_queue(self, url: str, user_id: int, channel_id: int, filename: str | None = None) -> int:
        """Add download to queue.

        Args:
            url: URL to download
            user_id: ID of user adding download
            channel_id: ID of channel where download was requested
            filename: Optional custom filename

        Returns:
            int: Position in queue (1-based)

        Raises:
            ValueError: If queue is full
        """
        async with self._lock:
            if len(self._queue) >= self.max_queue_size:
                raise ValueError("Queue is full")

            item = QueueItem(
                download_id=uuid4(),
                url=url,
                user_id=user_id,
                channel_id=channel_id,
                filename=filename,
                status=QueueStatus.QUEUED,
                created_at=datetime.utcnow(),
            )

            self._queue.append(item)
            return len(self._queue)  # 1-based position

    async def get_next_download(self) -> QueueItem | None:
        """Get next download from queue.

        Returns:
            Optional[QueueItem]: Next item if available
        """
        async with self._lock:
            if not self._queue or self._paused:
                return None

            return self._queue.pop(0)

    async def get_queue_items(self) -> list[QueueItem]:
        """Get all items in queue.

        Returns:
            List[QueueItem]: List of queue items
        """
        async with self._lock:
            return self._queue.copy()

    async def remove_from_queue(self, download_id: UUID, user_id: int) -> bool:
        """Remove item from queue.

        Args:
            download_id: ID of download to remove
            user_id: ID of user requesting removal

        Returns:
            bool: True if item was removed
        """
        async with self._lock:
            for i, item in enumerate(self._queue):
                if item.download_id == download_id:
                    # Check if user has permission
                    if item.user_id != user_id:
                        return False

                    self._queue.pop(i)
                    return True

            return False

    async def clear_queue(self) -> None:
        """Clear all items from queue."""
        async with self._lock:
            self._queue.clear()

    async def pause_queue(self) -> None:
        """Pause queue processing."""
        async with self._lock:
            self._paused = True

    async def resume_queue(self) -> None:
        """Resume queue processing."""
        async with self._lock:
            self._paused = False

    def get_queue_status(self) -> dict[str, int]:
        """Get queue status.

        Returns:
            Dict[str, int]: Queue status information
        """
        current_size = self.queue_size
        return {
            "total_items": current_size,
            "remaining_capacity": self.max_queue_size - current_size,
            "is_paused": self._paused,
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        async with self._lock:
            self._queue.clear()
            self._paused = False
