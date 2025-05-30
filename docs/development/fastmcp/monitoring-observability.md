# Monitoring & Observability

Comprehensive guide for monitoring FastMCP servers in production, including logging, metrics, health checks, alerting, and observability best practices.

## Overview

Effective monitoring and observability are essential for maintaining reliable FastMCP servers in production. This guide covers comprehensive strategies for:

- **Structured Logging**: Centralized, searchable logs
- **Metrics Collection**: Performance and business metrics
- **Health Monitoring**: Service health and dependency checks
- **Alerting**: Proactive issue detection
- **Distributed Tracing**: Request flow tracking
- **Dashboard Creation**: Visual monitoring interfaces

## Logging

### 1. Structured Logging Setup

**Configure comprehensive logging:**
```python
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.utilities.logging import configure_logging

class StructuredLogger:
    """Enhanced structured logging for FastMCP."""

    def __init__(self, service_name: str, version: str, environment: str):
        self.service_name = service_name
        self.version = version
        self.environment = environment
        self.setup_logging()

    def setup_logging(self):
        """Configure structured logging with multiple outputs."""
        # Create formatters
        json_formatter = self.JsonFormatter()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)

        # File handler for structured logs
        log_dir = Path("/var/log/fastmcp")
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "app.jsonl")
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(logging.INFO)

        # Error file handler
        error_handler = logging.FileHandler(log_dir / "errors.jsonl")
        error_handler.setFormatter(json_formatter)
        error_handler.setLevel(logging.ERROR)

        # Add handlers
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)

    class JsonFormatter(logging.Formatter):
        """JSON formatter for structured logging."""

        def format(self, record: logging.LogRecord) -> str:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "service": getattr(record, 'service', 'fastmcp'),
                "version": getattr(record, 'version', 'unknown'),
                "environment": getattr(record, 'environment', 'development'),
            }

            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)

            # Add custom fields
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno',
                              'pathname', 'filename', 'module', 'lineno',
                              'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process',
                              'exc_info', 'exc_text', 'stack_info', 'getMessage']:
                    log_entry[key] = value

            return json.dumps(log_entry)

# Initialize structured logging
structured_logger = StructuredLogger(
    service_name="fastmcp-server",
    version="1.0.0",
    environment="production"
)

# Configure FastMCP with logging
mcp = FastMCP(
    "Monitored Server",
    debug=False,
    log_level="INFO"
)

logger = logging.getLogger(__name__)

@mcp.tool()
async def logged_operation(data: str, ctx: Context) -> str:
    """Tool with comprehensive logging."""
    # Request-level logging
    logger.info(
        "Tool execution started",
        extra={
            "tool_name": "logged_operation",
            "request_id": ctx.request_id,
            "client_id": ctx.client_id,
            "input_size": len(data),
            "operation": "start"
        }
    )

    try:
        # Business logic
        result = f"Processed: {data}"

        # Success logging
        logger.info(
            "Tool execution completed",
            extra={
                "tool_name": "logged_operation",
                "request_id": ctx.request_id,
                "operation": "complete",
                "output_size": len(result),
                "success": True
            }
        )

        # Context logging (sent to client)
        await ctx.info(f"Successfully processed {len(data)} characters")

        return result

    except Exception as e:
        # Error logging
        logger.error(
            "Tool execution failed",
            extra={
                "tool_name": "logged_operation",
                "request_id": ctx.request_id,
                "operation": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "success": False
            },
            exc_info=True
        )

        await ctx.error(f"Operation failed: {e}")
        raise
```

### 2. Context-based Logging

**Leverage FastMCP's built-in logging:**
```python
@mcp.tool()
async def context_logging_demo(data: str, ctx: Context) -> str:
    """Demonstrate FastMCP context logging capabilities."""

    # Debug logging (development only)
    await ctx.debug(f"Input validation: {len(data)} characters")

    # Info logging (general information)
    await ctx.info("Starting data processing")

    # Progress reporting with logging
    total_steps = 5
    for step in range(total_steps):
        await ctx.report_progress(step, total_steps, f"Step {step + 1}")
        await ctx.debug(f"Completed step {step + 1}")
        await asyncio.sleep(0.1)  # Simulate work

    # Warning for edge cases
    if len(data) > 1000:
        await ctx.warning("Large input detected, processing may be slow")

    # Completion logging
    await ctx.info("Data processing completed successfully")

    return f"Processed {len(data)} characters"

@mcp.tool()
async def error_logging_demo(should_fail: bool, ctx: Context) -> str:
    """Demonstrate error logging patterns."""

    await ctx.info("Starting operation with error handling")

    try:
        if should_fail:
            raise ValueError("Intentional failure for demonstration")

        await ctx.info("Operation completed successfully")
        return "Success"

    except ValueError as e:
        # Log error with context
        await ctx.error(f"Operation failed: {e}")

        # Also log to application logger for monitoring
        logger.error(
            "Tool error occurred",
            extra={
                "tool_name": "error_logging_demo",
                "request_id": ctx.request_id,
                "error_type": "ValueError",
                "error_message": str(e),
                "user_requested_failure": should_fail
            }
        )

        # Re-raise or handle gracefully
        raise
```

## Metrics Collection

### 1. Application Metrics

**Custom metrics collection:**
```python
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List
import psutil

@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: float
    value: float
    labels: Dict[str, str]

class MetricsCollector:
    """Collect and expose application metrics."""

    def __init__(self):
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timeseries: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.Lock()

        # Start system metrics collection
        self.start_system_metrics_collection()

    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        with self.lock:
            key = self._build_key(name, labels)
            self.counters[key] += value
            self.timeseries[key].append(MetricPoint(time.time(), self.counters[key], labels or {}))

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric."""
        with self.lock:
            key = self._build_key(name, labels)
            self.gauges[key] = value
            self.timeseries[key].append(MetricPoint(time.time(), value, labels or {}))

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value."""
        with self.lock:
            key = self._build_key(name, labels)
            self.histograms[key].append(value)
            # Keep only recent values
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]

    def _build_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Build metric key with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        with self.lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    name: {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0,
                    }
                    for name, values in self.histograms.items()
                },
                "timestamp": time.time()
            }

    def start_system_metrics_collection(self):
        """Start collecting system metrics."""
        def collect_system_metrics():
            while True:
                try:
                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.set_gauge("system_cpu_percent", cpu_percent)

                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.set_gauge("system_memory_percent", memory.percent)
                    self.set_gauge("system_memory_used_bytes", memory.used)
                    self.set_gauge("system_memory_available_bytes", memory.available)

                    # Disk usage
                    disk = psutil.disk_usage('/')
                    self.set_gauge("system_disk_percent", (disk.used / disk.total) * 100)
                    self.set_gauge("system_disk_used_bytes", disk.used)
                    self.set_gauge("system_disk_free_bytes", disk.free)

                    # Process-specific metrics
                    process = psutil.Process()
                    self.set_gauge("process_memory_rss_bytes", process.memory_info().rss)
                    self.set_gauge("process_memory_vms_bytes", process.memory_info().vms)
                    self.set_gauge("process_cpu_percent", process.cpu_percent())
                    self.set_gauge("process_num_threads", process.num_threads())

                except Exception as e:
                    logger.error(f"Failed to collect system metrics: {e}")

                time.sleep(30)  # Collect every 30 seconds

        # Start background thread
        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()

# Global metrics collector
metrics = MetricsCollector()

# Decorator for automatic metrics collection
def collect_metrics(operation_name: str):
    """Decorator to automatically collect metrics for operations."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            # Find context for additional labels
            ctx = None
            for arg in args:
                if isinstance(arg, Context):
                    ctx = arg
                    break

            labels = {
                "operation": operation_name,
                "client_id": ctx.client_id if ctx else "unknown"
            }

            # Increment request counter
            metrics.increment_counter("fastmcp_requests_total", labels=labels)

            try:
                result = await func(*args, **kwargs)

                # Record success
                labels["status"] = "success"
                metrics.increment_counter("fastmcp_requests_success_total", labels=labels)

                return result

            except Exception as e:
                # Record error
                labels["status"] = "error"
                labels["error_type"] = type(e).__name__
                metrics.increment_counter("fastmcp_requests_error_total", labels=labels)
                raise

            finally:
                # Record duration
                duration = time.time() - start_time
                metrics.record_histogram("fastmcp_request_duration_seconds", duration, labels)

        return wrapper
    return decorator

@mcp.tool()
@collect_metrics("data_processing")
async def metrics_demo_tool(data: str, ctx: Context) -> str:
    """Tool with automatic metrics collection."""
    await ctx.info("Processing data with metrics collection")

    # Custom business metrics
    metrics.increment_counter(
        "business_data_processed_total",
        labels={"data_type": "text", "size_category": "large" if len(data) > 100 else "small"}
    )

    metrics.set_gauge("business_current_data_size", len(data))

    # Simulate processing time
    processing_time = len(data) * 0.001  # 1ms per character
    await asyncio.sleep(processing_time)

    return f"Processed {len(data)} characters"
```

### 2. Prometheus Integration

**Export metrics to Prometheus:**
```python
from starlette.responses import PlainTextResponse
from starlette.requests import Request

class PrometheusExporter:
    """Export metrics in Prometheus format."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector

    def export_metrics(self) -> str:
        """Export all metrics in Prometheus format."""
        lines = []
        current_metrics = self.metrics.get_metrics()

        # Export counters
        for name, value in current_metrics["counters"].items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        # Export gauges
        for name, value in current_metrics["gauges"].items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        # Export histograms
        for name, hist_data in current_metrics["histograms"].items():
            lines.append(f"# TYPE {name} histogram")
            lines.append(f"{name}_count {hist_data['count']}")
            lines.append(f"{name}_sum {hist_data['sum']}")

            # Add buckets (simplified)
            buckets = [0.001, 0.01, 0.1, 1.0, 10.0, float('inf')]
            for bucket in buckets:
                count = hist_data['count']  # Simplified bucket counting
                lines.append(f"{name}_bucket{{le=\"{bucket}\"}} {count}")

        return '\n'.join(lines) + '\n'

prometheus_exporter = PrometheusExporter(metrics)

@mcp.custom_route("/metrics", methods=["GET"])
async def metrics_endpoint(request: Request) -> PlainTextResponse:
    """Prometheus metrics endpoint."""
    metrics_data = prometheus_exporter.export_metrics()
    return PlainTextResponse(
        metrics_data,
        headers={"Content-Type": "text/plain; version=0.0.4; charset=utf-8"}
    )
```

## Health Checks

### 1. Basic Health Monitoring

**Implement comprehensive health checks:**
```python
from enum import Enum
from typing import Dict, List
import asyncio

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: str

class HealthMonitor:
    """Comprehensive health monitoring system."""

    def __init__(self):
        self.checks: Dict[str, callable] = {}
        self.last_results: Dict[str, HealthCheck] = {}

    def register_check(self, name: str, check_func: callable, timeout: float = 5.0):
        """Register a health check."""
        self.checks[name] = (check_func, timeout)

    async def run_check(self, name: str, check_func: callable, timeout: float) -> HealthCheck:
        """Run a single health check."""
        start_time = time.time()

        try:
            # Run check with timeout
            async with asyncio.timeout(timeout):
                result = await check_func()

            response_time = (time.time() - start_time) * 1000

            if result is True:
                status = HealthStatus.HEALTHY
                message = "OK"
            elif isinstance(result, dict):
                status = HealthStatus(result.get("status", "healthy"))
                message = result.get("message", "OK")
            else:
                status = HealthStatus.HEALTHY
                message = str(result)

            return HealthCheck(
                name=name,
                status=status,
                message=message,
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat()
            )

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check timed out after {timeout}s",
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat()
            )

    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks."""
        tasks = []
        for name, (check_func, timeout) in self.checks.items():
            task = self.run_check(name, check_func, timeout)
            tasks.append((name, task))

        results = {}
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
                self.last_results[name] = result
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Unexpected error: {e}",
                    response_time_ms=0,
                    timestamp=datetime.utcnow().isoformat()
                )

        return results

    def get_overall_status(self, results: Dict[str, HealthCheck]) -> HealthStatus:
        """Determine overall system health."""
        if not results:
            return HealthStatus.UNHEALTHY

        statuses = [check.status for check in results.values()]

        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED

# Initialize health monitor
health_monitor = HealthMonitor()

# Database health check
async def check_database_health():
    """Check database connectivity and performance."""
    try:
        # Replace with your actual database check
        start_time = time.time()
        # await db.fetchval("SELECT 1")
        query_time = (time.time() - start_time) * 1000

        if query_time > 1000:  # Slow query threshold
            return {
                "status": "degraded",
                "message": f"Database slow: {query_time:.1f}ms"
            }

        return True
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database error: {e}"
        }

# Cache health check
async def check_cache_health():
    """Check cache connectivity."""
    try:
        # Replace with your actual cache check
        # await redis_client.ping()
        return True
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Cache error: {e}"
        }

# External API health check
async def check_external_api_health():
    """Check external API dependencies."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.example.com/health", timeout=5.0)
            if response.status_code == 200:
                return True
            else:
                return {
                    "status": "degraded",
                    "message": f"API returned {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"API unreachable: {e}"
        }

# Register health checks
health_monitor.register_check("database", check_database_health, timeout=5.0)
health_monitor.register_check("cache", check_cache_health, timeout=3.0)
health_monitor.register_check("external_api", check_external_api_health, timeout=10.0)

@mcp.custom_route("/health", methods=["GET"])
async def health_endpoint(request: Request) -> JSONResponse:
    """Basic health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "fastmcp-server",
        "version": "1.0.0"
    })

@mcp.custom_route("/health/detailed", methods=["GET"])
async def detailed_health_endpoint(request: Request) -> JSONResponse:
    """Detailed health check with all dependencies."""
    results = await health_monitor.run_all_checks()
    overall_status = health_monitor.get_overall_status(results)

    response_data = {
        "status": overall_status.value,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "fastmcp-server",
        "version": "1.0.0",
        "checks": {
            name: {
                "status": check.status.value,
                "message": check.message,
                "response_time_ms": check.response_time_ms,
                "timestamp": check.timestamp
            }
            for name, check in results.items()
        }
    }

    # Return appropriate HTTP status
    status_code = 200
    if overall_status == HealthStatus.DEGRADED:
        status_code = 200  # Still operational
    elif overall_status == HealthStatus.UNHEALTHY:
        status_code = 503  # Service unavailable

    return JSONResponse(response_data, status_code=status_code)
```

## Alerting

### 1. Alert Configuration

**Set up intelligent alerting:**
```python
from enum import Enum
from typing import List, Dict, Callable
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    name: str
    severity: AlertSeverity
    message: str
    timestamp: str
    labels: Dict[str, str]
    resolved: bool = False

class AlertManager:
    """Manage alerts and notifications."""

    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_rules: List[Dict] = []
        self.notification_channels: List[Callable] = []

        # Set up alert rules
        self.setup_default_rules()

    def setup_default_rules(self):
        """Set up default alerting rules."""
        self.alert_rules = [
            {
                "name": "high_error_rate",
                "condition": lambda m: m.get("fastmcp_requests_error_total", 0) / max(m.get("fastmcp_requests_total", 1), 1) > 0.1,
                "severity": AlertSeverity.CRITICAL,
                "message": "Error rate above 10%"
            },
            {
                "name": "high_response_time",
                "condition": lambda m: m.get("fastmcp_request_duration_seconds", {}).get("avg", 0) > 5.0,
                "severity": AlertSeverity.WARNING,
                "message": "Average response time above 5 seconds"
            },
            {
                "name": "high_memory_usage",
                "condition": lambda m: m.get("system_memory_percent", 0) > 85,
                "severity": AlertSeverity.WARNING,
                "message": "Memory usage above 85%"
            },
            {
                "name": "high_cpu_usage",
                "condition": lambda m: m.get("system_cpu_percent", 0) > 80,
                "severity": AlertSeverity.WARNING,
                "message": "CPU usage above 80%"
            },
            {
                "name": "service_down",
                "condition": lambda m: m.get("health_status", "healthy") == "unhealthy",
                "severity": AlertSeverity.CRITICAL,
                "message": "Service health check failed"
            }
        ]

    def add_notification_channel(self, channel: Callable):
        """Add a notification channel."""
        self.notification_channels.append(channel)

    def evaluate_rules(self, metrics: Dict[str, Any]):
        """Evaluate alert rules against current metrics."""
        for rule in self.alert_rules:
            try:
                if rule["condition"](metrics):
                    self.trigger_alert(
                        name=rule["name"],
                        severity=rule["severity"],
                        message=rule["message"],
                        labels={"source": "metrics"}
                    )
                else:
                    # Check if alert should be resolved
                    if rule["name"] in self.active_alerts:
                        self.resolve_alert(rule["name"])
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule['name']}: {e}")

    def trigger_alert(self, name: str, severity: AlertSeverity, message: str, labels: Dict[str, str] = None):
        """Trigger an alert."""
        alert_key = f"{name}_{hash(str(labels))}"

        if alert_key not in self.active_alerts:
            alert = Alert(
                name=name,
                severity=severity,
                message=message,
                timestamp=datetime.utcnow().isoformat(),
                labels=labels or {},
                resolved=False
            )

            self.active_alerts[alert_key] = alert

            # Send notifications
            for channel in self.notification_channels:
                try:
                    channel(alert)
                except Exception as e:
                    logger.error(f"Failed to send alert notification: {e}")

            # Log alert
            logger.warning(
                f"Alert triggered: {name}",
                extra={
                    "alert_name": name,
                    "severity": severity.value,
                    "message": message,
                    "labels": labels
                }
            )

    def resolve_alert(self, name: str):
        """Resolve an alert."""
        # Find and resolve matching alerts
        resolved_alerts = []
        for alert_key, alert in list(self.active_alerts.items()):
            if alert.name == name and not alert.resolved:
                alert.resolved = True
                resolved_alerts.append(alert)
                del self.active_alerts[alert_key]

        # Send resolution notifications
        for alert in resolved_alerts:
            for channel in self.notification_channels:
                try:
                    channel(alert, resolved=True)
                except Exception as e:
                    logger.error(f"Failed to send resolution notification: {e}")

            logger.info(
                f"Alert resolved: {alert.name}",
                extra={
                    "alert_name": alert.name,
                    "severity": alert.severity.value,
                    "resolved": True
                }
            )

# Email notification channel
def email_notification(alert: Alert, resolved: bool = False):
    """Send email notification for alerts."""
    smtp_server = "smtp.example.com"
    smtp_port = 587
    sender_email = "alerts@example.com"
    sender_password = "password"
    recipient_emails = ["admin@example.com"]

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipient_emails)

        if resolved:
            msg['Subject'] = f"[RESOLVED] FastMCP Alert: {alert.name}"
            body = f"""
            Alert Resolved: {alert.name}

            Original Message: {alert.message}
            Severity: {alert.severity.value}
            Timestamp: {alert.timestamp}
            Labels: {alert.labels}
            """
        else:
            msg['Subject'] = f"[{alert.severity.value.upper()}] FastMCP Alert: {alert.name}"
            body = f"""
            Alert: {alert.name}

            Message: {alert.message}
            Severity: {alert.severity.value}
            Timestamp: {alert.timestamp}
            Labels: {alert.labels}

            Please investigate immediately.
            """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")

# Slack notification channel
async def slack_notification(alert: Alert, resolved: bool = False):
    """Send Slack notification for alerts."""
    webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

    color = {
        AlertSeverity.INFO: "good",
        AlertSeverity.WARNING: "warning",
        AlertSeverity.CRITICAL: "danger"
    }.get(alert.severity, "warning")

    if resolved:
        color = "good"
        title = f"✅ Resolved: {alert.name}"
    else:
        title = f"🚨 Alert: {alert.name}"

    payload = {
        "attachments": [
            {
                "color": color,
                "title": title,
                "text": alert.message,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value, "short": True},
                    {"title": "Timestamp", "value": alert.timestamp, "short": True},
                ],
                "footer": "FastMCP Monitoring"
            }
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=payload)
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")

# Initialize alert manager
alert_manager = AlertManager()
alert_manager.add_notification_channel(email_notification)
alert_manager.add_notification_channel(slack_notification)

# Background monitoring task
async def monitoring_task():
    """Background task to monitor metrics and trigger alerts."""
    while True:
        try:
            # Get current metrics
            current_metrics = metrics.get_metrics()

            # Add health status to metrics
            health_results = await health_monitor.run_all_checks()
            overall_health = health_monitor.get_overall_status(health_results)
            current_metrics["health_status"] = overall_health.value

            # Evaluate alert rules
            alert_manager.evaluate_rules(current_metrics)

            # Wait before next check
            await asyncio.sleep(30)  # Check every 30 seconds

        except Exception as e:
            logger.error(f"Monitoring task error: {e}")
            await asyncio.sleep(30)

# Start monitoring when server starts
async def start_monitoring():
    """Start background monitoring task."""
    asyncio.create_task(monitoring_task())

# Add to server startup
@asynccontextmanager
async def lifespan_with_monitoring(app: FastMCP):
    """Lifespan with monitoring."""
    await start_monitoring()
    logger.info("Monitoring system started")
    try:
        yield
    finally:
        logger.info("Monitoring system stopped")

mcp = FastMCP("Monitored Server", lifespan=lifespan_with_monitoring)
```

## Dashboard Integration

### 1. Grafana Dashboard

**Grafana dashboard configuration (JSON):**
```json
{
  "dashboard": {
    "id": null,
    "title": "FastMCP Server Monitoring",
    "tags": ["fastmcp", "monitoring"],
    "timezone": "UTC",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(fastmcp_requests_total[5m])",
            "legendFormat": "{{operation}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(fastmcp_requests_error_total[5m]) / rate(fastmcp_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ],
        "valueName": "current",
        "format": "percentunit"
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(fastmcp_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(fastmcp_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "System Resources",
        "type": "graph",
        "targets": [
          {
            "expr": "system_cpu_percent",
            "legendFormat": "CPU %"
          },
          {
            "expr": "system_memory_percent",
            "legendFormat": "Memory %"
          }
        ]
      }
    ]
  }
}
```

## Best Practices

### 1. Monitoring Strategy

```python
# ✅ Good: Comprehensive monitoring setup
@mcp.tool()
async def well_monitored_tool(data: str, ctx: Context) -> str:
    """Tool with comprehensive monitoring."""

    # Request logging
    await ctx.info(f"Processing request: {len(data)} characters")

    # Metrics collection
    metrics.increment_counter("business_operations_total", labels={"type": "data_processing"})

    start_time = time.time()

    try:
        # Business logic
        result = process_data(data)

        # Success metrics
        duration = time.time() - start_time
        metrics.record_histogram("operation_duration_seconds", duration)
        metrics.set_gauge("last_operation_size", len(data))

        await ctx.info("Operation completed successfully")
        return result

    except Exception as e:
        # Error handling and alerting
        metrics.increment_counter("business_errors_total", labels={"error_type": type(e).__name__})

        alert_manager.trigger_alert(
            name="operation_failure",
            severity=AlertSeverity.WARNING,
            message=f"Data processing failed: {e}",
            labels={"operation": "data_processing", "error": str(e)}
        )

        await ctx.error(f"Operation failed: {e}")
        raise

# ✅ Good: Structured logging with correlation IDs
logger.info(
    "User action completed",
    extra={
        "user_id": user_id,
        "action": "data_export",
        "request_id": ctx.request_id,
        "duration_ms": duration * 1000,
        "success": True
    }
)
```

### 2. Monitoring Checklist

**Production monitoring checklist:**

- [ ] **Application Metrics**
  - [ ] Request rate and response time
  - [ ] Error rate and error types
  - [ ] Business-specific metrics
  - [ ] Queue lengths and processing times

- [ ] **System Metrics**
  - [ ] CPU, memory, disk usage
  - [ ] Network I/O and connections
  - [ ] File descriptors and threads
  - [ ] Process-specific metrics

- [ ] **Health Checks**
  - [ ] Basic liveness check
  - [ ] Database connectivity
  - [ ] External service dependencies
  - [ ] Cache availability

- [ ] **Logging**
  - [ ] Structured logging format
  - [ ] Appropriate log levels
  - [ ] Request correlation IDs
  - [ ] Error stack traces

- [ ] **Alerting**
  - [ ] Error rate thresholds
  - [ ] Response time thresholds
  - [ ] Resource usage alerts
  - [ ] Health check failures

- [ ] **Dashboards**
  - [ ] Real-time metrics visualization
  - [ ] Historical trend analysis
  - [ ] SLA/SLO tracking
  - [ ] Alert status overview

This comprehensive monitoring and observability setup ensures your FastMCP servers are well-instrumented and maintainable in production environments.
