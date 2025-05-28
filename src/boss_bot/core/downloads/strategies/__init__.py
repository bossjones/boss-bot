"""Download strategy implementations using the Strategy pattern."""

from .base_strategy import BaseDownloadStrategy
from .instagram_strategy import InstagramDownloadStrategy
from .reddit_strategy import RedditDownloadStrategy
from .twitter_strategy import TwitterDownloadStrategy
from .youtube_strategy import YouTubeDownloadStrategy

__all__ = [
    "BaseDownloadStrategy",
    "InstagramDownloadStrategy",
    "RedditDownloadStrategy",
    "TwitterDownloadStrategy",
    "YouTubeDownloadStrategy",
]
