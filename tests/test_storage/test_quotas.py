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
