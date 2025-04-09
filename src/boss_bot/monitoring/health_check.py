"""Health check module for monitoring component status."""

from collections.abc import Callable
from typing import Dict, Optional

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


class HealthCheck:
    """Manages health status of different components."""

    def __init__(self):
        """Initialize health check with all components marked as healthy."""
        self._component_status: dict[str, bool] = {"discord": True, "storage": True, "queue": True}

    def mark_component_healthy(self, component: str) -> None:
        """Mark a component as healthy."""
        if component not in self._component_status:
            raise ValueError(f"Invalid component: {component}")
        self._component_status[component] = True

    def mark_component_unhealthy(self, component: str) -> None:
        """Mark a component as unhealthy."""
        if component not in self._component_status:
            raise ValueError(f"Invalid component: {component}")
        self._component_status[component] = False

    def is_component_healthy(self, component: str) -> bool:
        """Check if a component is healthy."""
        if component not in self._component_status:
            raise ValueError(f"Invalid component: {component}")
        return self._component_status[component]

    def is_healthy(self) -> bool:
        """Check if all components are healthy."""
        return all(self._component_status.values())

    async def start_periodic_check(
        self, component: str, check_fn: Callable[[], bool], interval_seconds: int = 60
    ) -> None:
        """Start periodic health check for a component."""
        import asyncio

        while True:
            try:
                is_healthy = check_fn()
                if is_healthy:
                    self.mark_component_healthy(component)
                else:
                    self.mark_component_unhealthy(component)
                await asyncio.sleep(interval_seconds)
            except Exception:
                self.mark_component_unhealthy(component)
                await asyncio.sleep(interval_seconds)


def create_health_check_app() -> FastAPI:
    """Create FastAPI app with health check endpoints."""
    app = FastAPI()
    health_check = HealthCheck()

    @app.get("/health")
    async def health():
        """Basic health check endpoint."""
        return {"status": "healthy" if health_check.is_healthy() else "unhealthy"}

    @app.get("/health/details")
    async def health_details():
        """Detailed health check endpoint."""
        return {
            "components": {
                component: "healthy" if health_check.is_component_healthy(component) else "unhealthy"
                for component in ["discord", "storage", "queue"]
            }
        }

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        return generate_latest(), {"Content-Type": CONTENT_TYPE_LATEST}

    return app
