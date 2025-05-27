"""API-direct download clients for gallery-dl and yt-dlp."""

from .aio_gallery_dl import AsyncGalleryDL
from .aio_yt_dlp import AsyncYtDlp

__all__ = ["AsyncGalleryDL", "AsyncYtDlp"]
