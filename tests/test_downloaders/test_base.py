"""Tests for base download manager."""
import pytest
from pathlib import Path
from boss_bot.downloaders.base import DownloadManager, DownloadStatus

@pytest.fixture
def download_manager():
    """Create a download manager instance for testing."""
    return DownloadManager()

def test_download_manager_initialization(download_manager):
    """Test that download manager initializes correctly."""
    assert isinstance(download_manager, DownloadManager)
    assert download_manager.max_concurrent_downloads == 5
    assert len(download_manager.active_downloads) == 0

@pytest.mark.asyncio
async def test_download_url_validation(download_manager):
    """Test URL validation."""
    # Valid URLs
    assert await download_manager.validate_url("https://twitter.com/user/status/123")
    assert await download_manager.validate_url("https://reddit.com/r/subreddit/comments/123")

    # Invalid URLs
    assert not await download_manager.validate_url("not_a_url")
    assert not await download_manager.validate_url("http://invalid.domain/path")

@pytest.mark.asyncio
async def test_download_status_tracking(download_manager):
    """Test download status tracking."""
    download_id = "test_download_123"
    url = "https://twitter.com/user/status/123"

    # Start download
    await download_manager.start_download(url, download_id)
    assert download_manager.get_download_status(download_id) == DownloadStatus.DOWNLOADING

    # Complete download
    await download_manager.mark_download_complete(download_id)
    assert download_manager.get_download_status(download_id) == DownloadStatus.COMPLETED

    # Failed download
    error_id = "error_download_123"
    await download_manager.start_download(url, error_id)
    await download_manager.mark_download_failed(error_id, "Download failed")
    assert download_manager.get_download_status(error_id) == DownloadStatus.FAILED

@pytest.mark.asyncio
async def test_concurrent_download_limit(download_manager):
    """Test concurrent download limit."""
    # Start max number of downloads
    for i in range(download_manager.max_concurrent_downloads):
        await download_manager.start_download(
            f"https://twitter.com/user/status/{i}",
            f"download_{i}"
        )

    # Try to start one more download
    with pytest.raises(ValueError, match="Maximum concurrent downloads reached"):
        await download_manager.start_download(
            "https://twitter.com/user/status/extra",
            "extra_download"
        )
