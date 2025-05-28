"""Download handlers for various platforms."""

from .base_handler import BaseDownloadHandler, DownloadResult, MediaMetadata
from .instagram_handler import InstagramHandler
from .reddit_handler import RedditHandler
from .twitter_handler import TwitterHandler
from .youtube_handler import YouTubeHandler

__all__ = [
    "BaseDownloadHandler",
    "DownloadResult",
    "MediaMetadata",
    "InstagramHandler",
    "RedditHandler",
    "TwitterHandler",
    "YouTubeHandler",
]
