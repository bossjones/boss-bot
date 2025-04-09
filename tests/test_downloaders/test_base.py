"""Tests for download manager functionality."""

import asyncio
import pytest
from uuid import uuid4

from boss_bot.downloaders.base import Download, DownloadManager, DownloadStatus

@pytest.fixture
def download_manager():
    """Create a download manager instance for testing."""
    return DownloadManager()

@pytest.mark.asyncio
async def test_download_manager_initialization(download_manager: DownloadManager):
    """Test download manager initialization."""
    assert download_manager.max_concurrent_downloads == 2
    assert len(download_manager.active_downloads) == 0

@pytest.mark.asyncio
async def test_start_download(download_manager: DownloadManager):
    """Test starting a download."""
    download = Download(
        download_id=uuid4(),
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )

    # Start first download
    success = await download_manager.start_download(download)
    assert success
    assert len(download_manager.active_downloads) == 1
    assert download.status == DownloadStatus.DOWNLOADING

    # Start second download
    download2 = Download(
        download_id=uuid4(),
        url="https://example.com/test2",
        user_id=12345,
        channel_id=67890
    )
    success = await download_manager.start_download(download2)
    assert success
    assert len(download_manager.active_downloads) == 2

    # Try to start third download (should fail)
    download3 = Download(
        download_id=uuid4(),
        url="https://example.com/test3",
        user_id=12345,
        channel_id=67890
    )
    success = await download_manager.start_download(download3)
    assert not success
    assert len(download_manager.active_downloads) == 2

@pytest.mark.asyncio
async def test_download_progress(download_manager: DownloadManager):
    """Test download progress tracking."""
    download = Download(
        download_id=uuid4(),
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )

    await download_manager.start_download(download)

    # Wait for some progress
    await asyncio.sleep(2)

    status = await download_manager.get_download_status(download.download_id)
    assert status is not None
    assert "20.0%" in status

@pytest.mark.asyncio
async def test_cancel_download(download_manager: DownloadManager):
    """Test cancelling a download."""
    download = Download(
        download_id=uuid4(),
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )

    await download_manager.start_download(download)

    # Try to cancel with wrong user
    success = await download_manager.cancel_download(download.download_id, 54321)
    assert not success
    assert download.status == DownloadStatus.DOWNLOADING

    # Cancel with correct user
    success = await download_manager.cancel_download(download.download_id, 12345)
    assert success
    assert download.status == DownloadStatus.CANCELLED

    # Wait for task to complete
    await asyncio.sleep(0.1)
    assert len(download_manager.active_downloads) == 0

@pytest.mark.asyncio
async def test_get_download_status(download_manager: DownloadManager):
    """Test getting download status."""
    download = Download(
        download_id=uuid4(),
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )

    # Status for non-existent download
    status = await download_manager.get_download_status(download.download_id)
    assert status is None

    # Start download and check status
    await download_manager.start_download(download)
    status = await download_manager.get_download_status(download.download_id)
    assert status is not None
    assert "Status: downloading" in status.lower()

@pytest.mark.asyncio
async def test_get_active_downloads(download_manager: DownloadManager):
    """Test getting active downloads."""
    downloads = await download_manager.get_active_downloads()
    assert len(downloads) == 0

    # Add downloads
    download1 = Download(
        download_id=uuid4(),
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    download2 = Download(
        download_id=uuid4(),
        url="https://example.com/test2",
        user_id=12345,
        channel_id=67890
    )

    await download_manager.start_download(download1)
    await download_manager.start_download(download2)

    downloads = await download_manager.get_active_downloads()
    assert len(downloads) == 2

@pytest.mark.asyncio
async def test_cleanup(download_manager: DownloadManager):
    """Test cleanup functionality."""
    # Start some downloads
    download1 = Download(
        download_id=uuid4(),
        url="https://example.com/test1",
        user_id=12345,
        channel_id=67890
    )
    download2 = Download(
        download_id=uuid4(),
        url="https://example.com/test2",
        user_id=12345,
        channel_id=67890
    )

    await download_manager.start_download(download1)
    await download_manager.start_download(download2)
    assert len(download_manager.active_downloads) == 2

    # Cleanup
    await download_manager.cleanup()
    assert len(download_manager.active_downloads) == 0
    assert download1.status == DownloadStatus.CANCELLED
    assert download2.status == DownloadStatus.CANCELLED

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
