"""Tests for the metrics module."""
import pytest
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry
from boss_bot.monitoring.metrics import MetricsRegistry

# Fixture migrated to test_monitoring/conftest.py as fixture_metrics_registry_test
# Original fixture: registry
# New fixture: fixture_metrics_registry_test
# Migration date: 2024-03-19

def test_metrics_registry_initialization(fixture_metrics_registry_test: MetricsRegistry):
    """Test that MetricsRegistry initializes with all required metrics."""
    assert isinstance(fixture_metrics_registry_test.downloads_total, Counter)
    assert isinstance(fixture_metrics_registry_test.download_duration, Histogram)
    assert isinstance(fixture_metrics_registry_test.download_size, Histogram)
    assert isinstance(fixture_metrics_registry_test.queue_size, Gauge)
    assert isinstance(fixture_metrics_registry_test.queue_processing_time, Histogram)
    assert isinstance(fixture_metrics_registry_test.storage_usage, Gauge)
    assert isinstance(fixture_metrics_registry_test.storage_operations, Counter)
    assert isinstance(fixture_metrics_registry_test.discord_commands, Counter)
    assert isinstance(fixture_metrics_registry_test.discord_events, Counter)

def test_downloads_total_labels(fixture_metrics_registry_test: MetricsRegistry):
    """Test that downloads_total counter has correct labels."""
    metric = fixture_metrics_registry_test.downloads_total
    assert "status" in metric._labelnames
    assert "source" in metric._labelnames

def test_download_duration_buckets(fixture_metrics_registry_test: MetricsRegistry):
    """Test that download_duration histogram has expected buckets."""
    metric = fixture_metrics_registry_test.download_duration
    # Test by observing values and checking bucket counts
    expected_buckets = (1, 5, 10, 30, 60, 120, 300, 600)

    # Observe values just below and above each bucket boundary
    for bucket in expected_buckets:
        metric.observe(bucket - 0.1)
        metric.observe(bucket + 0.1)

    # Get the current value
    samples = metric.collect()[0].samples

    # Create a mapping of le values to their counts
    bucket_values = {}
    for sample in samples:
        if 'le' in sample.labels:
            bucket_values[float(sample.labels['le'])] = sample.value

    # Verify bucket behavior
    for i, bucket in enumerate(expected_buckets):
        assert float(bucket) in bucket_values, f"Bucket {bucket} not found in {bucket_values.keys()}"
        assert bucket_values[float(bucket)] >= i + 1, f"Expected at least {i + 1} values in bucket {bucket}"

def test_download_size_buckets(fixture_metrics_registry_test: MetricsRegistry):
    """Test that download_size histogram has expected buckets."""
    metric = fixture_metrics_registry_test.download_size
    # Test by observing values and checking bucket counts
    expected_buckets = (1024*1024, 5*1024*1024, 10*1024*1024, 25*1024*1024, 50*1024*1024)

    # Observe values just below and above each bucket boundary
    for bucket in expected_buckets:
        metric.observe(bucket - 1024)
        metric.observe(bucket + 1024)

    # Get the current value
    samples = metric.collect()[0].samples

    # Create a mapping of le values to their counts
    bucket_values = {}
    for sample in samples:
        if 'le' in sample.labels:
            bucket_values[float(sample.labels['le'])] = sample.value

    # Verify bucket behavior
    for i, bucket in enumerate(expected_buckets):
        assert float(bucket) in bucket_values, f"Bucket {bucket} not found in {bucket_values.keys()}"
        assert bucket_values[float(bucket)] >= i + 1, f"Expected at least {i + 1} values in bucket {bucket}"

def test_queue_size_labels(fixture_metrics_registry_test: MetricsRegistry):
    """Test that queue_size gauge has correct labels."""
    metric = fixture_metrics_registry_test.queue_size
    assert "type" in metric._labelnames

def test_storage_operations_labels(fixture_metrics_registry_test: MetricsRegistry):
    """Test that storage_operations counter has correct labels."""
    metric = fixture_metrics_registry_test.storage_operations
    assert "operation" in metric._labelnames
    assert "status" in metric._labelnames

def test_discord_metrics_labels(fixture_metrics_registry_test: MetricsRegistry):
    """Test that Discord-related metrics have correct labels."""
    commands = fixture_metrics_registry_test.discord_commands
    events = fixture_metrics_registry_test.discord_events

    assert "command" in commands._labelnames
    assert "status" in commands._labelnames
    assert "event_type" in events._labelnames

def test_get_metrics(fixture_metrics_registry_test: MetricsRegistry):
    """Test that get_metrics returns all registered metrics."""
    metrics = fixture_metrics_registry_test.get_metrics()
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
def test_metric_types(fixture_metrics_registry_test: MetricsRegistry, metric_name, metric_type):
    """Test that each metric has the correct type."""
    metric = getattr(fixture_metrics_registry_test, metric_name)
    assert isinstance(metric, metric_type)
