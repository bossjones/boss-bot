"""Metrics module for monitoring system metrics."""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram


class MetricsRegistry:
    """Registry for all application metrics.

    This class manages all Prometheus metrics for the application, providing
    a centralized way to track and expose metrics for monitoring.
    """

    def __init__(self, registry: CollectorRegistry | None = None):
        """Initialize metrics registry.

        Args:
            registry: Optional custom collector registry. If not provided,
                     a new registry will be created.
        """
        self.registry = registry or CollectorRegistry()

        # Initialize all metrics
        self.downloads_total = Counter(
            "boss_bot_downloads_total", "Total number of downloads", ["status", "source"], registry=self.registry
        )

        # Duration buckets in seconds: 1s, 5s, 10s, 30s, 1m, 2m, 5m, 10m
        self.download_duration = Histogram(
            "boss_bot_download_duration_seconds",
            "Time taken to complete downloads",
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
            registry=self.registry,
        )

        # Size buckets in bytes: 1MB, 5MB, 10MB, 25MB, 50MB
        self.download_size = Histogram(
            "boss_bot_download_size_bytes",
            "Size of downloaded files in bytes",
            buckets=(
                1024 * 1024,  # 1MB
                5 * 1024 * 1024,  # 5MB
                10 * 1024 * 1024,  # 10MB
                25 * 1024 * 1024,  # 25MB
                50 * 1024 * 1024,  # 50MB
            ),
            registry=self.registry,
        )

        self.queue_size = Gauge(
            "boss_bot_queue_size", "Current size of various queues", ["type"], registry=self.registry
        )

        self.queue_processing_time = Histogram(
            "boss_bot_queue_processing_time_seconds", "Time taken to process queue items", registry=self.registry
        )

        self.storage_usage = Gauge(
            "boss_bot_storage_usage_bytes", "Current storage usage in bytes", registry=self.registry
        )

        self.storage_operations = Counter(
            "boss_bot_storage_operations_total",
            "Total number of storage operations",
            ["operation", "status"],
            registry=self.registry,
        )

        self.discord_commands = Counter(
            "boss_bot_discord_commands_total",
            "Total number of Discord commands processed",
            ["command", "status"],
            registry=self.registry,
        )

        self.discord_events = Counter(
            "boss_bot_discord_events_total",
            "Total number of Discord events processed",
            ["event_type"],
            registry=self.registry,
        )

    def get_metrics(self) -> bytes:
        """Get all metrics in Prometheus text format.

        Returns:
            bytes: Metrics in Prometheus text format
        """
        from prometheus_client import generate_latest

        return generate_latest(self.registry)
