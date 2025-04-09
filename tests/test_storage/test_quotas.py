"""Tests for the storage quota management system."""
import pytest
from pathlib import Path

from boss_bot.storage.quotas import QuotaManager, QuotaConfig, QuotaExceededError

def test_quota_manager_initialization():
    """Test that QuotaManager initializes correctly with default settings."""
    storage_path = Path("/tmp/storage")
    quota_manager = QuotaManager(storage_path)

    assert quota_manager.storage_root == storage_path
    assert isinstance(quota_manager.config, QuotaConfig)
    assert quota_manager.config.max_total_size_mb == 50  # From story constraints
    assert quota_manager.config.max_concurrent_downloads == 5  # From story constraints

def test_quota_check_under_limit():
    """Test that quota check passes when under the limit."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    # Test with a file size well under the 50MB limit
    assert quota_manager.check_quota(size_mb=25) is True

def test_quota_check_over_limit():
    """Test that quota check fails when over the limit."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    # Test with a file size over the 50MB limit
    assert quota_manager.check_quota(size_mb=75) is False

def test_quota_check_at_limit():
    """Test that quota check passes when exactly at the limit."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    # Test with a file size exactly at the 50MB limit
    assert quota_manager.check_quota(size_mb=50) is True

def test_quota_add_file():
    """Test that adding a file updates the current usage correctly."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    # Add a file and check usage is updated
    quota_manager.add_file("test.mp4", size_mb=25)
    assert quota_manager.current_usage_mb == 25

    # Add another file
    quota_manager.add_file("test2.mp4", size_mb=15)
    assert quota_manager.current_usage_mb == 40

def test_quota_add_file_over_limit():
    """Test that adding a file that would exceed quota raises an error."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    # First add a file that takes up most of the quota
    quota_manager.add_file("test.mp4", size_mb=40)

    # Trying to add a file that would exceed quota should raise an error
    with pytest.raises(QuotaExceededError):
        quota_manager.add_file("test2.mp4", size_mb=15)  # Would total 55MB > 50MB limit

def test_concurrent_downloads_under_limit():
    """Test that concurrent downloads are allowed when under the limit."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    # Start multiple downloads
    for i in range(3):  # Well under the limit of 5
        assert quota_manager.can_start_download() is True
        quota_manager.start_download(f"download_{i}")

def test_concurrent_downloads_at_limit():
    """Test that concurrent downloads are blocked at the limit."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    # Start downloads up to the limit
    for i in range(5):  # At the limit
        assert quota_manager.can_start_download() is True
        quota_manager.start_download(f"download_{i}")

    # Try to start one more
    assert quota_manager.can_start_download() is False

def test_concurrent_downloads_complete():
    """Test that completing downloads frees up slots."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    # Fill all slots
    for i in range(5):
        quota_manager.start_download(f"download_{i}")

    # Complete some downloads
    quota_manager.complete_download("download_0")
    quota_manager.complete_download("download_1")

    # Should be able to start new downloads
    assert quota_manager.can_start_download() is True
    quota_manager.start_download("new_download")

def test_concurrent_downloads_invalid_complete():
    """Test that completing non-existent download raises error."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    with pytest.raises(ValueError):
        quota_manager.complete_download("non_existent")

def test_remove_file():
    """Test that removing a file updates the quota correctly."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    # Add some files
    quota_manager.add_file("test1.mp4", size_mb=20)
    quota_manager.add_file("test2.mp4", size_mb=15)

    # Initial usage should be 35MB
    assert quota_manager.current_usage_mb == 35

    # Remove a file
    quota_manager.remove_file("test1.mp4")

    # Usage should be reduced by 20MB
    assert quota_manager.current_usage_mb == 15

    # File should no longer be tracked
    with pytest.raises(KeyError):
        quota_manager.remove_file("test1.mp4")

def test_remove_nonexistent_file():
    """Test that removing a non-existent file raises an error."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    with pytest.raises(KeyError):
        quota_manager.remove_file("nonexistent.mp4")

def test_get_quota_status():
    """Test that quota status reporting works correctly."""
    quota_manager = QuotaManager(Path("/tmp/storage"))

    # Add some files and downloads
    quota_manager.add_file("test1.mp4", size_mb=20)
    quota_manager.add_file("test2.mp4", size_mb=15)
    quota_manager.start_download("download1")
    quota_manager.start_download("download2")

    status = quota_manager.get_quota_status()
    assert status["total_size_mb"] == quota_manager.config.max_total_size_mb
    assert status["used_size_mb"] == 35
    assert status["available_size_mb"] == 15
    assert status["usage_percentage"] == 70
    assert status["active_downloads"] == 2
    assert status["max_concurrent_downloads"] == quota_manager.config.max_concurrent_downloads
