"""Prometheus metrics configuration for monitoring."""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest


class MetricsRegistry:
    """Registry for all application metrics."""

    def __init__(self, registry: CollectorRegistry = None):
        """Initialize metrics registry with all required metrics."""
        self.registry = registry or CollectorRegistry()

        # Download metrics
        self.downloads_total = Counter(
            "boss_bot_downloads_total",
            "Total number of download requests",
            ["status", "source"],
            registry=self.registry,
        )

        self.download_duration = Histogram(
            "boss_bot_download_duration_seconds",
            "Time taken to complete downloads",
            ["source"],
            buckets=(1, 5, 10, 30, 60, 120, 300, 600),
            registry=self.registry,
        )

        self.download_size = Histogram(
            "boss_bot_download_size_bytes",
            "Size of downloaded files",
            ["source"],
            buckets=(1024 * 1024, 5 * 1024 * 1024, 10 * 1024 * 1024, 25 * 1024 * 1024, 50 * 1024 * 1024),
            registry=self.registry,
        )

        # Queue metrics
        self.queue_size = Gauge(
            "boss_bot_queue_size", "Current number of items in queue", ["type"], registry=self.registry
        )

        self.queue_processing_time = Histogram(
            "boss_bot_queue_processing_time_seconds",
            "Time taken to process queue items",
            ["type"],
            buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
            registry=self.registry,
        )

        # Storage metrics
        self.storage_usage = Gauge(
            "boss_bot_storage_usage_bytes", "Current storage usage", ["type"], registry=self.registry
        )

        self.storage_operations = Counter(
            "boss_bot_storage_operations_total",
            "Total number of storage operations",
            ["operation", "status"],
            registry=self.registry,
        )

        # Discord metrics
        self.discord_commands = Counter(
            "boss_bot_discord_commands_total",
            "Total number of Discord commands",
            ["command", "status"],
            registry=self.registry,
        )

        self.discord_events = Counter(
            "boss_bot_discord_events_total", "Total number of Discord events", ["event_type"], registry=self.registry
        )

    def get_metrics(self) -> bytes:
        """Get all metrics in Prometheus format."""
        return generate_latest(self.registry)


# Create global metrics registry
metrics = MetricsRegistry()
