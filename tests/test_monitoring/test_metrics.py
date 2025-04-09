"""Tests for the metrics module."""
import pytest
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry
from boss_bot.monitoring.metrics import MetricsRegistry

@pytest.fixture
def registry():
    """Create a new registry for each test."""
    return MetricsRegistry(registry=CollectorRegistry())

def test_metrics_registry_initialization(registry):
    """Test that MetricsRegistry initializes with all required metrics."""
    assert isinstance(registry.downloads_total, Counter)
    assert isinstance(registry.download_duration, Histogram)
    assert isinstance(registry.download_size, Histogram)
    assert isinstance(registry.queue_size, Gauge)
    assert isinstance(registry.queue_processing_time, Histogram)
    assert isinstance(registry.storage_usage, Gauge)
    assert isinstance(registry.storage_operations, Counter)
    assert isinstance(registry.discord_commands, Counter)
    assert isinstance(registry.discord_events, Counter)

def test_downloads_total_labels(registry):
    """Test that downloads_total counter has correct labels."""
    metric = registry.downloads_total
    assert "status" in metric._labelnames
    assert "source" in metric._labelnames

def test_download_duration_buckets(registry):
    """Test that download_duration histogram has expected buckets."""
    metric = registry.download_duration
    # Test by observing values and checking bucket counts
    expected_buckets = (1, 5, 10, 30, 60, 120, 300, 600)

    # Observe values just below and above each bucket boundary
    for bucket in expected_buckets:
        metric.observe(bucket - 0.1)
        metric.observe(bucket + 0.1)

    # Get the current value
    samples = metric.collect()[0].samples
    bucket_values = {s.name: s.value for s in samples if s.name.endswith('_bucket')}

    # Verify bucket behavior
    for i, bucket in enumerate(expected_buckets):
        bucket_name = f'boss_bot_download_duration_seconds_bucket_le_{bucket}'
        assert bucket_name in bucket_values
        assert bucket_values[bucket_name] >= i + 1  # At least i+1 values should be in this bucket

def test_download_size_buckets(registry):
    """Test that download_size histogram has expected buckets."""
    metric = registry.download_size
    # Test by observing values and checking bucket counts
    expected_buckets = (1024*1024, 5*1024*1024, 10*1024*1024, 25*1024*1024, 50*1024*1024)

    # Observe values just below and above each bucket boundary
    for bucket in expected_buckets:
        metric.observe(bucket - 1024)
        metric.observe(bucket + 1024)

    # Get the current value
    samples = metric.collect()[0].samples
    bucket_values = {s.name: s.value for s in samples if s.name.endswith('_bucket')}

    # Verify bucket behavior
    for i, bucket in enumerate(expected_buckets):
        bucket_name = f'boss_bot_download_size_bytes_bucket_le_{bucket}'
        assert bucket_name in bucket_values
        assert bucket_values[bucket_name] >= i + 1  # At least i+1 values should be in this bucket

def test_queue_size_labels(registry):
    """Test that queue_size gauge has correct labels."""
    metric = registry.queue_size
    assert "type" in metric._labelnames

def test_storage_operations_labels(registry):
    """Test that storage_operations counter has correct labels."""
    metric = registry.storage_operations
    assert "operation" in metric._labelnames
    assert "status" in metric._labelnames

def test_discord_metrics_labels(registry):
    """Test that Discord-related metrics have correct labels."""
    commands = registry.discord_commands
    events = registry.discord_events

    assert "command" in commands._labelnames
    assert "status" in commands._labelnames
    assert "event_type" in events._labelnames

def test_get_metrics(registry):
    """Test that get_metrics returns all registered metrics."""
    metrics = registry.get_metrics()
    assert len(metrics) > 0
    assert isinstance(metrics, bytes)
    assert b"boss_bot_downloads_total" in metrics

@pytest.mark.parametrize("metric_name,metric_type", [
    ("downloads_total", Counter),
    ("download_duration", Histogram),
    ("download_size", Histogram),
    ("queue_size", Gauge),
    ("queue_processing_time", Histogram),
    ("storage_usage", Gauge),
    ("storage_operations", Counter),
    ("discord_commands", Counter),
    ("discord_events", Counter)
])
def test_metric_types(registry, metric_name, metric_type):
    """Test that each metric has the correct type."""
    metric = getattr(registry, metric_name)
    assert isinstance(metric, metric_type)
