"""Discord cogs package for Boss-Bot."""

from .downloads import DownloadCog
from .task_queue import QueueCog

__all__ = ["DownloadCog", "QueueCog"]
