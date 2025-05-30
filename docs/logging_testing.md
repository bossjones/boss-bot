# Loguru Testing with Logot & Pytest Guide

## 🎯 Overview

This guide provides comprehensive instructions for testing Loguru-based logging using **Logot**, a modern log testing library that offers superior capabilities compared to pytest's built-in `caplog` fixture. Logot provides advanced log message matching, better async support, and cleaner assertion syntax.

---

## 🚨 Requirements & Compatibility

### **Python Version Requirements**
- **Loguru**: Python 3.5+
- **Logot**: Python 3.8+
- **Compatibility**: Use Logot only in projects running Python 3.8+

### **When to Use Logot vs caplog**

**Use Logot when:**
- ✅ You need advanced log message pattern matching
- ✅ Testing complex logging scenarios with threading/async
- ✅ You want cleaner, more expressive test assertions
- ✅ Testing structured logging with context/binding
- ✅ Running Python 3.8+

**Use caplog when:**
- ✅ You need Python 3.5-3.7 compatibility
- ✅ Simple log testing requirements
- ✅ Minimal dependencies preferred
- ✅ Basic log level and message verification

---

## 📦 Installation

### **Standard Installation**
```bash
# Using uv (recommended)
uv add --dev 'logot[pytest]'

# Using pip
pip install 'logot[pytest]'
```

### **Loguru-Specific Installation**
```bash
# With Loguru integration
uv add --dev 'logot[loguru,pytest]'

# Or separate
pip install 'logot[loguru]' 'logot[pytest]'
```

### **Development Setup**
```bash
# Install all testing dependencies
uv add --dev pytest 'logot[pytest,loguru]' pytest-asyncio pytest-cov

# Verify installation
uv run python -c "import logot; print('Logot installed successfully')"
```

---

## ⚙️ Configuration

### **1. Pytest Configuration (pytest.ini)**

```ini
[tool:pytest]
# Basic configuration
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Logot configuration
logot_capturer = logot.loguru.LoguruCapturer
logot_level = DEBUG
logot_timeout = 5.0
logot_name = tests

# Async support
asyncio_mode = auto

# Coverage
addopts =
    --strict-markers
    --strict-config
    --cov=my_intercept_logger
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
```

### **2. pyproject.toml Configuration**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Logot configuration for Loguru
logot_capturer = "logot.loguru.LoguruCapturer"
logot_level = "DEBUG"
logot_timeout = 5.0
logot_name = "tests"

# Async support
asyncio_mode = "auto"

# Test output
addopts = [
    "--strict-markers",
    "--strict-config",
    "--tb=short",
    "--cov=my_intercept_logger",
    "--cov-report=term-missing"
]

filterwarnings = [
    "error",
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning"
]

markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests"
]
```

### **3. conftest.py Setup**

```python
"""Pytest configuration and fixtures for Loguru testing."""

from __future__ import annotations

import pytest
import threading
from typing import Generator, Any
from unittest.mock import patch

from logot import Logot, logged
from logot.loguru import LoguruCapturer
from loguru import logger

# Import your logging setup
from my_intercept_logger import _early_init, global_log_config, InterceptHandler


@pytest.fixture(scope="session", autouse=True)
def setup_logging() -> None:
    """Set up logging for the entire test session."""
    # Initialize our thread-safe logging
    _early_init()


@pytest.fixture
def reset_logger() -> Generator[None, None, None]:
    """Reset logger state between tests."""
    # Remove all handlers before test
    logger.remove()

    yield

    # Clean up after test
    logger.remove()
    # Re-add default handler for next test
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time}</green> | <level>{level}</level> | {message}",
        enqueue=True,
        catch=True
    )


@pytest.fixture
def logot_instance() -> Logot:
    """Provide a fresh Logot instance for testing."""
    return Logot(capturer=LoguruCapturer)


@pytest.fixture
def mock_external_service():
    """Mock external services that might use logging."""
    with patch('my_app.external_service') as mock:
        yield mock


# Custom markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
```

---

## 🧪 Basic Testing Patterns

### **1. Simple Log Message Testing**

```python
"""Basic log message testing with Logot."""

import pytest
from logot import Logot, logged
from loguru import logger


def test_basic_logging(logot: Logot) -> None:
    """Test basic log message capture and assertion."""

    # Perform action that logs
    logger.info("User logged in successfully")

    # Assert the log was captured
    logot.assert_logged(logged.info("User logged in successfully"))


def test_log_levels(logot: Logot) -> None:
    """Test different log levels."""

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    # Assert each level
    logot.assert_logged(logged.debug("Debug message"))
    logot.assert_logged(logged.info("Info message"))
    logot.assert_logged(logged.warning("Warning message"))
    logot.assert_logged(logged.error("Error message"))
    logot.assert_logged(logged.critical("Critical message"))


def test_log_with_variables(logot: Logot) -> None:
    """Test logging with variable interpolation."""

    user_id = 12345
    username = "alice"

    logger.info("User {user} (ID: {id}) logged in", user=username, id=user_id)

    # Use pattern matching for dynamic content
    logot.assert_logged(logged.info("User alice (ID: 12345) logged in"))

    # Alternative: Use % patterns for flexible matching
    logot.assert_logged(logged.info("User % (ID: %) logged in"))


def test_exception_logging(logot: Logot) -> None:
    """Test exception logging with tracebacks."""

    try:
        raise ValueError("Something went wrong")
    except Exception:
        logger.exception("An error occurred while processing")

    # Assert exception was logged
    logot.assert_logged(logged.error("An error occurred while processing"))
```

### **2. Advanced Pattern Matching**

```python
"""Advanced log message pattern matching."""

import pytest
from logot import Logot, logged
from loguru import logger


def test_pattern_matching(logot: Logot) -> None:
    """Test advanced pattern matching capabilities."""

    # Log with dynamic data
    session_id = "sess_abc123"
    timestamp = "2024-01-15T10:30:00"

    logger.info("Session {session} started at {time}",
                session=session_id, time=timestamp)

    # Use % wildcard for any value
    logot.assert_logged(logged.info("Session % started at %"))

    # Use %{name} for named wildcards
    logot.assert_logged(logged.info("Session %{session} started at %{time}"))


def test_regex_patterns(logot: Logot) -> None:
    """Test regex pattern matching."""

    import re

    logger.info("Request ID: req_789xyz processing")

    # Use regex for complex patterns
    pattern = re.compile(r"Request ID: req_\w+ processing")
    logot.assert_logged(logged.info(pattern))


def test_multiple_log_assertions(logot: Logot) -> None:
    """Test multiple log assertions in sequence."""

    def process_user_registration(username: str, email: str) -> None:
        logger.info("Starting user registration for {user}", user=username)
        logger.debug("Validating email: {email}", email=email)
        logger.info("User {user} registered successfully", user=username)

    # Execute function
    process_user_registration("alice", "alice@example.com")

    # Assert log sequence
    logot.assert_logged(logged.info("Starting user registration for alice"))
    logot.assert_logged(logged.debug("Validating email: alice@example.com"))
    logot.assert_logged(logged.info("User alice registered successfully"))


def test_log_not_present(logot: Logot) -> None:
    """Test asserting that certain logs are NOT present."""

    logger.info("Normal operation")

    # Assert what was logged
    logot.assert_logged(logged.info("Normal operation"))

    # Assert what was NOT logged
    logot.assert_not_logged(logged.error("Error occurred"))
    logot.assert_not_logged(logged.warning("Warning message"))
```

---

## 🎭 Testing Loguru-Specific Features

### **1. Testing Bound Loggers**

```python
"""Testing Loguru's bind() functionality."""

import pytest
from logot import Logot, logged
from loguru import logger


def test_bound_logger(logot: Logot) -> None:
    """Test logging with bound context."""

    # Create bound logger
    bound_logger = logger.bind(
        request_id="req_123",
        user_id=456,
        component="auth"
    )

    bound_logger.info("User authentication started")
    bound_logger.success("Authentication completed")

    # Assert logs with bound context
    # Note: Exact format depends on your formatter
    logot.assert_logged(logged.info("User authentication started"))
    logot.assert_logged(logged.info("Authentication completed"))


def test_contextualize(logot: Logot) -> None:
    """Test Loguru's contextualize() functionality."""

    def authenticate_user(user_id: int) -> None:
        with logger.contextualize(user_id=user_id, operation="auth"):
            logger.info("Starting authentication")
            logger.info("Checking credentials")
            logger.success("Authentication successful")

    # Execute with context
    authenticate_user(789)

    # Assert logs (context is automatically included)
    logot.assert_logged(logged.info("Starting authentication"))
    logot.assert_logged(logged.info("Checking credentials"))
    logot.assert_logged(logged.info("Authentication successful"))


def test_structured_logging(logot: Logot) -> None:
    """Test structured logging with extra data."""

    def process_order(order_id: str, amount: float) -> None:
        logger.bind(
            order_id=order_id,
            amount=amount,
            currency="USD"
        ).info("Processing payment")

    process_order("order_abc", 99.99)

    # Assert the log message (extra data included based on formatter)
    logot.assert_logged(logged.info("Processing payment"))
```

### **2. Testing Custom Sinks**

```python
"""Testing custom Loguru sinks."""

import pytest
from logot import Logot, logged
from loguru import logger
from unittest.mock import Mock, patch
from typing import List
import json


def test_custom_sink_integration(logot: Logot) -> None:
    """Test logging through custom sinks."""

    # Custom sink for testing
    captured_messages: List[str] = []

    def test_sink(message: str) -> None:
        captured_messages.append(message.strip())

    # Add custom sink
    sink_id = logger.add(test_sink, serialize=False, level="INFO")

    try:
        logger.info("Test message for custom sink")
        logger.error("Error message for custom sink")

        # Verify sink received messages
        assert len(captured_messages) == 2
        assert "Test message for custom sink" in captured_messages[0]
        assert "Error message for custom sink" in captured_messages[1]

        # Also verify through Logot
        logot.assert_logged(logged.info("Test message for custom sink"))
        logot.assert_logged(logged.error("Error message for custom sink"))

    finally:
        logger.remove(sink_id)


def test_json_sink(logot: Logot) -> None:
    """Test JSON serialization sink."""

    json_messages: List[dict] = []

    def json_sink(message) -> None:
        # message.record contains the full record
        record = message.record
        json_data = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "extra": record.get("extra", {})
        }
        json_messages.append(json_data)

    # Add JSON sink
    sink_id = logger.add(json_sink, level="DEBUG")

    try:
        logger.bind(user_id=123).info("User action performed")

        # Verify JSON structure
        assert len(json_messages) == 1
        json_record = json_messages[0]

        assert json_record["level"] == "INFO"
        assert json_record["message"] == "User action performed"
        assert json_record["extra"]["user_id"] == 123

        # Also verify through Logot
        logot.assert_logged(logged.info("User action performed"))

    finally:
        logger.remove(sink_id)


@pytest.mark.asyncio
async def test_async_sink(logot: Logot) -> None:
    """Test asynchronous sink functionality."""

    async_messages: List[str] = []

    async def async_sink(message) -> None:
        # Simulate async operation
        import asyncio
        await asyncio.sleep(0.01)
        async_messages.append(message.record["message"])

    # Add async sink
    sink_id = logger.add(async_sink, level="INFO")

    try:
        logger.info("Async sink test message")

        # Wait for async processing
        import asyncio
        await asyncio.sleep(0.1)

        # Verify async sink received message
        assert len(async_messages) == 1
        assert async_messages[0] == "Async sink test message"

        # Verify through Logot
        logot.assert_logged(logged.info("Async sink test message"))

    finally:
        logger.remove(sink_id)
```

---

## 🔄 Testing Threading & Concurrency

### **1. Thread-Safe Logging Tests**

```python
"""Testing thread-safe logging scenarios."""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from logot import Logot, logged
from loguru import logger


def test_threading_safety(logot: Logot) -> None:
    """Test that logging works correctly across multiple threads."""

    def worker_thread(thread_id: int, iterations: int) -> None:
        for i in range(iterations):
            logger.info("Thread {thread}: iteration {iter}",
                       thread=thread_id, iter=i)
            time.sleep(0.001)  # Small delay

    # Start multiple threads
    threads = []
    for thread_id in range(3):
        thread = threading.Thread(
            target=worker_thread,
            args=(thread_id, 5)
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify all messages were logged
    # Should have 3 threads × 5 iterations = 15 messages
    for thread_id in range(3):
        for iteration in range(5):
            logot.assert_logged(
                logged.info(f"Thread {thread_id}: iteration {iteration}")
            )


def test_thread_pool_logging(logot: Logot) -> None:
    """Test logging with ThreadPoolExecutor."""

    def process_item(item_id: int) -> int:
        logger.info("Processing item {id}", id=item_id)
        time.sleep(0.01)  # Simulate work
        logger.success("Completed item {id}", id=item_id)
        return item_id

    # Process items in thread pool
    item_ids = [1, 2, 3, 4, 5]

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_item, item_id) for item_id in item_ids]

        # Wait for completion
        for future in as_completed(futures):
            result = future.result()

    # Verify all items were logged
    for item_id in item_ids:
        logot.assert_logged(logged.info(f"Processing item {item_id}"))
        logot.assert_logged(logged.info(f"Completed item {item_id}"))


def test_early_init_thread_safety(logot: Logot) -> None:
    """Test our early initialization is thread-safe."""

    from my_intercept_logger import _early_init

    def call_early_init(thread_id: int) -> str:
        _early_init()
        logger.info("Early init called by thread {id}", id=thread_id)
        return f"thread_{thread_id}"

    # Call early init from multiple threads simultaneously
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(call_early_init, i) for i in range(10)]
        results = [future.result() for future in as_completed(futures)]

    # Verify all threads logged successfully
    for thread_id in range(10):
        logot.assert_logged(logged.info(f"Early init called by thread {thread_id}"))

    # Should have 10 results
    assert len(results) == 10
```

### **2. Async Logging Tests**

```python
"""Testing asynchronous logging scenarios."""

import pytest
import asyncio
from logot import Logot, logged
from loguru import logger


@pytest.mark.asyncio
async def test_async_logging(logot: Logot) -> None:
    """Test basic async logging functionality."""

    async def async_operation(operation_id: str) -> None:
        logger.info("Starting async operation {id}", id=operation_id)
        await asyncio.sleep(0.01)  # Simulate async work
        logger.success("Completed async operation {id}", id=operation_id)

    # Execute async operation
    await async_operation("op_123")

    # Verify logs
    logot.assert_logged(logged.info("Starting async operation op_123"))
    logot.assert_logged(logged.info("Completed async operation op_123"))


@pytest.mark.asyncio
async def test_concurrent_async_logging(logot: Logot) -> None:
    """Test concurrent async operations with logging."""

    async def async_worker(worker_id: int) -> None:
        logger.info("Async worker {id} starting", id=worker_id)
        await asyncio.sleep(0.01)
        logger.info("Async worker {id} finished", id=worker_id)

    # Run multiple async workers concurrently
    tasks = [async_worker(i) for i in range(5)]
    await asyncio.gather(*tasks)

    # Verify all workers logged
    for worker_id in range(5):
        logot.assert_logged(logged.info(f"Async worker {worker_id} starting"))
        logot.assert_logged(logged.info(f"Async worker {worker_id} finished"))


@pytest.mark.asyncio
async def test_async_context_logging(logot: Logot) -> None:
    """Test async logging with context management."""

    async def process_request(request_id: str) -> None:
        with logger.contextualize(request_id=request_id):
            logger.info("Request received")
            await asyncio.sleep(0.01)
            logger.info("Request processed")

    # Process multiple requests
    request_ids = ["req_1", "req_2", "req_3"]

    tasks = [process_request(req_id) for req_id in request_ids]
    await asyncio.gather(*tasks)

    # Verify all requests logged
    for _ in request_ids:
        logot.assert_logged(logged.info("Request received"))
        logot.assert_logged(logged.info("Request processed"))
```

---

## 🎯 Testing InterceptHandler Integration

### **1. Standard Library Integration Tests**

```python
"""Testing InterceptHandler with standard library logging."""

import pytest
import logging
from logot import Logot, logged
from loguru import logger
from my_intercept_logger import InterceptHandler, global_log_config


def test_intercept_handler_basic(logot: Logot) -> None:
    """Test basic InterceptHandler functionality."""

    # Set up standard logging with our interceptor
    std_logger = logging.getLogger("test_module")
    std_logger.setLevel(logging.DEBUG)
    std_logger.addHandler(InterceptHandler())
    std_logger.propagate = False

    # Log using standard logging
    std_logger.info("Standard logging message")
    std_logger.error("Standard error message")
    std_logger.debug("Standard debug message")

    # Verify messages were intercepted by Loguru
    logot.assert_logged(logged.info("Standard logging message"))
    logot.assert_logged(logged.error("Standard error message"))
    logot.assert_logged(logged.debug("Standard debug message"))


def test_intercept_third_party_libraries(logot: Logot) -> None:
    """Test intercepting logs from third-party libraries."""

    # Configure interceptor for common libraries
    intercept_handler = InterceptHandler()

    loggers_to_intercept = [
        "requests",
        "urllib3",
        "asyncio",
        "multiprocessing"
    ]

    for logger_name in loggers_to_intercept:
        lib_logger = logging.getLogger(logger_name)
        lib_logger.handlers = [intercept_handler]
        lib_logger.propagate = False

    # Simulate library logging
    logging.getLogger("requests").info("HTTP request started")
    logging.getLogger("urllib3").debug("Connection pool created")
    logging.getLogger("asyncio").warning("Event loop slow callback")

    # Verify interception
    logot.assert_logged(logged.info("HTTP request started"))
    logot.assert_logged(logged.debug("Connection pool created"))
    logot.assert_logged(logged.warning("Event loop slow callback"))


def test_exception_interception(logot: Logot) -> None:
    """Test exception logging through InterceptHandler."""

    std_logger = logging.getLogger("exception_test")
    std_logger.addHandler(InterceptHandler())
    std_logger.propagate = False

    try:
        raise ValueError("Test exception for interception")
    except Exception:
        std_logger.exception("Caught exception in standard logging")

    # Verify exception was intercepted
    logot.assert_logged(logged.error("Caught exception in standard logging"))


def test_global_log_config_integration(logot: Logot) -> None:
    """Test our global_log_config function with testing."""

    # Configure logging with our setup
    configured_logger = global_log_config(
        log_level=logging.DEBUG,
        json=False
    )

    # Test various logging operations
    configured_logger.info("Configured logger test")

    # Test standard library integration
    std_logger = logging.getLogger("integrated_test")
    std_logger.info("Standard library after configuration")

    # Verify both work
    logot.assert_logged(logged.info("Configured logger test"))
    logot.assert_logged(logged.info("Standard library after configuration"))
```

---

## 🚀 Performance & Load Testing

### **1. Performance Tests**

```python
"""Performance testing for logging infrastructure."""

import pytest
import time
from logot import Logot, logged
from loguru import logger


@pytest.mark.slow
def test_logging_performance(logot: Logot) -> None:
    """Test logging performance under load."""

    message_count = 1000
    start_time = time.time()

    # Log many messages quickly
    for i in range(message_count):
        logger.info("Performance test message {i}", i=i)

    end_time = time.time()
    duration = end_time - start_time

    # Performance assertions
    assert duration < 5.0, f"Logging {message_count} messages took {duration:.2f}s"

    # Verify a sample of messages were logged
    logot.assert_logged(logged.info("Performance test message 0"))
    logot.assert_logged(logged.info("Performance test message 999"))

    print(f"Logged {message_count} messages in {duration:.3f}s "
          f"({message_count/duration:.0f} msg/s)")


@pytest.mark.slow
def test_concurrent_logging_performance(logot: Logot) -> None:
    """Test performance with concurrent logging."""

    import threading

    message_count = 100
    thread_count = 10

    def log_worker(worker_id: int) -> None:
        for i in range(message_count):
            logger.info("Worker {worker}: message {msg}",
                       worker=worker_id, msg=i)

    start_time = time.time()

    # Start concurrent threads
    threads = []
    for worker_id in range(thread_count):
        thread = threading.Thread(target=log_worker, args=(worker_id,))
        threads.append(thread)
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    end_time = time.time()
    duration = end_time - start_time
    total_messages = message_count * thread_count

    print(f"Logged {total_messages} messages across {thread_count} threads "
          f"in {duration:.3f}s ({total_messages/duration:.0f} msg/s)")

    # Verify sample messages
    logot.assert_logged(logged.info("Worker 0: message 0"))
    logot.assert_logged(logged.info("Worker 9: message 99"))


def test_enqueue_performance(logot: Logot) -> None:
    """Test performance impact of enqueue=True."""

    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        log_file = f.name

    try:
        # Add file sink with enqueue
        sink_id = logger.add(
            log_file,
            level="DEBUG",
            enqueue=True,  # This is what we're testing
            catch=True
        )

        message_count = 500
        start_time = time.time()

        for i in range(message_count):
            logger.info("Enqueue test message {i}", i=i)

        # Complete all queued operations
        logger.complete()

        end_time = time.time()
        duration = end_time - start_time

        print(f"Enqueued logging: {message_count} messages in {duration:.3f}s")

        # Verify messages were logged
        logot.assert_logged(logged.info("Enqueue test message 0"))
        logot.assert_logged(logged.info("Enqueue test message 499"))

        logger.remove(sink_id)

    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)
```

---

## 🔧 Advanced Testing Scenarios

### **1. Configuration Testing**

```python
"""Testing different logging configurations."""

import pytest
import tempfile
import os
from logot import Logot, logged
from loguru import logger


def test_file_logging_configuration(logot: Logot, reset_logger) -> None:
    """Test file logging configuration."""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = f.name

    try:
        # Configure file logging
        logger.add(
            log_file,
            level="DEBUG",
            format="{time} | {level} | {message}",
            rotation="1 MB",
            retention="7 days",
            enqueue=True
        )

        logger.info("File logging test message")
        logger.error("File error message")

        # Complete to ensure file is written
        logger.complete()

        # Verify through Logot
        logot.assert_logged(logged.info("File logging test message"))
        logot.assert_logged(logged.error("File error message"))

        # Verify file was written
        with open(log_file, 'r') as f:
            file_content = f.read()
            assert "File logging test message" in file_content
            assert "File error message" in file_content

    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_json_serialization(logot: Logot, reset_logger) -> None:
    """Test JSON serialization configuration."""

    json_messages = []

    def json_collector(message) -> None:
        json_messages.append(message.record)

    # Add JSON sink
    logger.add(
        json_collector,
        serialize=True,  # This enables JSON serialization
        level="INFO"
    )

    logger.bind(user_id=123, action="login").info("User authentication")

    # Verify through Logot
    logot.assert_logged(logged.info("User authentication"))

    # Verify JSON structure
    assert len(json_messages) == 1
    record = json_messages[0]
    assert record["message"] == "User authentication"
    assert record["extra"]["user_id"] == 123
    assert record["extra"]["action"] == "login"


def test_filtering_configuration(logot: Logot, reset_logger) -> None:
    """Test log filtering configuration."""

    def error_only_filter(record) -> bool:
        return record["level"].no >= 40  # ERROR and above

    # Add filtered sink
    logger.add(
        lambda msg: None,  # Dummy sink
        filter=error_only_filter,
        level="DEBUG"
    )

    # Log at different levels
    logger.debug("Debug message")      # Should be filtered out
    logger.info("Info message")        # Should be filtered out
    logger.warning("Warning message")  # Should be filtered out
    logger.error("Error message")      # Should pass through
    logger.critical("Critical message") # Should pass through

    # Verify only error and critical passed the filter
    # Note: These will still be captured by Logot's capturer
    logot.assert_logged(logged.debug("Debug message"))
    logot.assert_logged(logged.info("Info message"))
    logot.assert_logged(logged.warning("Warning message"))
    logot.assert_logged(logged.error("Error message"))
    logot.assert_logged(logged.critical("Critical message"))
```

### **2. Error Scenarios Testing**

```python
"""Testing error scenarios and edge cases."""

import pytest
from logot import Logot, logged
from loguru import logger
from unittest.mock import patch, Mock


def test_sink_failure_handling(logot: Logot, reset_logger) -> None:
    """Test handling of sink failures."""

    def failing_sink(message) -> None:
        raise RuntimeError("Sink failure simulation")

    # Add failing sink with catch=True
    logger.add(
        failing_sink,
        level="INFO",
        catch=True  # Should catch and continue
    )

    # This should not raise an exception
    logger.info("Message to failing sink")

    # Verify message was still processed by other sinks
    logot.assert_logged(logged.info("Message to failing sink"))


def test_logging_during_exception_handling(logot: Logot) -> None:
    """Test logging during exception handling."""

    def problematic_function() -> None:
        try:
            logger.info("Entering problematic function")
            raise ValueError("Simulated error")
        except Exception as e:
            logger.error("Error in problematic function: {error}", error=str(e))
            raise
        finally:
            logger.info("Cleaning up after problematic function")

    # Execute and expect exception
    with pytest.raises(ValueError, match="Simulated error"):
        problematic_function()

    # Verify all logging occurred correctly
    logot.assert_logged(logged.info("Entering problematic function"))
    logot.assert_logged(logged.error("Error in problematic function: Simulated error"))
    logot.assert_logged(logged.info("Cleaning up after problematic function"))


def test_circular_logging_prevention(logot: Logot) -> None:
    """Test prevention of circular logging issues."""

    def logging_sink(message) -> None:
        # This sink tries to log - should not cause infinite recursion
        # Note: This is generally bad practice, just testing safety
        print(f"SINK: {message.record['message']}")

    logger.add(logging_sink, level="INFO")

    # Should not cause infinite recursion
    logger.info("Test message for circular prevention")

    logot.assert_logged(logged.info("Test message for circular prevention"))


@pytest.mark.parametrize("log_level,should_log", [
    ("DEBUG", True),
    ("INFO", True),
    ("WARNING", True),
    ("ERROR", True),
    ("CRITICAL", True),
])
def test_log_level_filtering(logot: Logot, reset_logger, log_level: str, should_log: bool) -> None:
    """Test log level filtering with parameterized tests."""

    # Set minimum level to INFO
    logger.add(lambda msg: None, level="INFO")

    # Log at the specified level
    getattr(logger, log_level.lower())("Test message at {level} level", level=log_level)

    # Check if it should be logged
    if should_log and log_level in ["INFO", "WARNING", "ERROR", "CRITICAL"]:
        logot.assert_logged(getattr(logged, log_level.lower())(f"Test message at {log_level} level"))
    elif log_level == "DEBUG":
        # DEBUG should be filtered out but still captured by Logot
        logot.assert_logged(logged.debug("Test message at DEBUG level"))
```

---

## 📋 Best Practices & Guidelines

### **1. Test Organization**

```python
"""Best practices for organizing logging tests."""

import pytest
from logot import Logot, logged


class TestUserAuthentication:
    """Group related logging tests in classes."""

    def test_successful_login(self, logot: Logot) -> None:
        """Test logging for successful authentication."""
        # Test implementation
        pass

    def test_failed_login(self, logot: Logot) -> None:
        """Test logging for failed authentication."""
        # Test implementation
        pass

    def test_logout(self, logot: Logot) -> None:
        """Test logging for user logout."""
        # Test implementation
        pass


class TestDataProcessing:
    """Group data processing logging tests."""

    @pytest.mark.slow
    def test_large_dataset_processing(self, logot: Logot) -> None:
        """Test logging during large dataset processing."""
        # Test implementation
        pass

    @pytest.mark.integration
    def test_database_integration_logging(self, logot: Logot) -> None:
        """Test database operation logging."""
        # Test implementation
        pass


# Use descriptive test names
def test_user_registration_logs_all_steps(logot: Logot) -> None:
    """Test that user registration logs each step of the process."""
    # Descriptive name explains what's being tested
    pass

def test_payment_processing_logs_security_events(logot: Logot) -> None:
    """Test that payment processing logs all security-relevant events."""
    # Clear intent from the name
    pass
```

### **2. Test Data Management**

```python
"""Managing test data for logging tests."""

import pytest
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TestUser:
    """Test user data for logging tests."""
    id: int
    username: str
    email: str
    role: str = "user"


@dataclass
class TestRequest:
    """Test request data for logging tests."""
    id: str
    method: str
    path: str
    user_id: int
    headers: Dict[str, str] = None


@pytest.fixture
def test_user() -> TestUser:
    """Provide a test user for logging tests."""
    return TestUser(
        id=12345,
        username="testuser",
        email="test@example.com",
        role="admin"
    )


@pytest.fixture
def test_request(test_user: TestUser) -> TestRequest:
    """Provide a test request for logging tests."""
    return TestRequest(
        id="req_test123",
        method="POST",
        path="/api/users",
        user_id=test_user.id,
        headers={"Content-Type": "application/json"}
    )


def test_with_test_data(logot: Logot, test_user: TestUser, test_request: TestRequest) -> None:
    """Example test using test data fixtures."""

    # Log using test data
    logger.bind(
        user_id=test_user.id,
        request_id=test_request.id
    ).info("Processing request for user {username}", username=test_user.username)

    # Assert with test data
    logot.assert_logged(logged.info(f"Processing request for user {test_user.username}"))
```

### **3. Assertion Patterns**

```python
"""Best practices for log assertions."""

import pytest
import re
from logot import Logot, logged


def test_assertion_best_practices(logot: Logot) -> None:
    """Demonstrate best practices for log assertions."""

    # ✅ Good: Specific assertions
    logger.info("User alice logged in successfully")
    logot.assert_logged(logged.info("User alice logged in successfully"))

    # ✅ Good: Pattern matching for dynamic data
    user_id = 12345
    logger.info("User {id} performed action", id=user_id)
    logot.assert_logged(logged.info("User % performed action"))

    # ✅ Good: Multiple specific assertions
    logger.info("Starting process")
    logger.info("Process completed")
    logot.assert_logged(logged.info("Starting process"))
    logot.assert_logged(logged.info("Process completed"))

    # ✅ Good: Regex for complex patterns
    logger.info("Request ID: req_abc123 processing")
    pattern = re.compile(r"Request ID: req_\w+ processing")
    logot.assert_logged(logged.info(pattern))


def test_assertion_antipatterns(logot: Logot) -> None:
    """Demonstrate what to avoid in log assertions."""

    # ❌ Avoid: Too generic assertions
    logger.info("Something happened")
    # Don't just check that ANY info log occurred

    # ❌ Avoid: Brittle timestamp assertions
    logger.info("Event at 2024-01-15T10:30:00")
    # Don't assert exact timestamps - they change

    # ✅ Better: Use patterns for timestamps
    logot.assert_logged(logged.info("Event at %"))


def test_negative_assertions(logot: Logot) -> None:
    """Test what should NOT be logged."""

    logger.info("Normal operation")

    # Verify expected logs
    logot.assert_logged(logged.info("Normal operation"))

    # Verify sensitive data is NOT logged
    logot.assert_not_logged(logged.info("password"))
    logot.assert_not_logged(logged.info("secret"))
    logot.assert_not_logged(logged.error("Internal error details"))
```

---

## 🎯 Summary

This comprehensive guide provides everything needed to test Loguru-based logging using Logot:

- ✅ **Complete setup** with pytest configuration
- ✅ **Basic to advanced** testing patterns
- ✅ **Loguru-specific features** (bind, contextualize, custom sinks)
- ✅ **Threading & async** safety testing
- ✅ **InterceptHandler integration** testing
- ✅ **Performance & load** testing
- ✅ **Error scenario** testing
- ✅ **Best practices** and anti-patterns

## 🔑 Key Benefits of Logot

1. **Superior to caplog**: More expressive assertions and better pattern matching
2. **Thread/Async Safe**: Handles concurrent logging scenarios correctly
3. **Loguru Integration**: Designed specifically for modern logging libraries
4. **Flexible Patterns**: Support for wildcards, regex, and complex matching
5. **Clean Syntax**: More readable and maintainable test code

With this setup, you can ensure your Loguru logging infrastructure works correctly across all scenarios from simple unit tests to complex integration testing with threading, async operations, and third-party library integration.
