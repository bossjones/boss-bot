"""Test fixtures for monitoring functionality."""

import pytest
from prometheus_client import CollectorRegistry
from boss_bot.monitoring.metrics import MetricsRegistry

@pytest.fixture(scope="function")
def fixture_metrics_registry_test() -> MetricsRegistry:
    """Create a new metrics registry for testing.

    Scope: function - ensures clean registry for each test
    Returns: Configured MetricsRegistry instance with clean collector
    """
    return MetricsRegistry(registry=CollectorRegistry())
