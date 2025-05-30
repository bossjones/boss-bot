"""
Pytest tests to verify thread safety of early_init() function.

Tests intentionally try to trigger race conditions by calling
early_init() from multiple threads simultaneously.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from boss_bot.monitoring.logging.interceptor import (
    early_init,
    reset_logging_state,
    is_early_init_done,
)
from loguru import logger


def test_concurrent_early_init():
    """Test that multiple threads calling early_init() is safe."""

    # Reset state for clean test
    reset_logging_state()

    def call_early_init(thread_id: int):
        """Function that each thread will execute."""
        # All threads call early_init - this should be thread-safe
        early_init()
        return thread_id

    # Test with multiple threads starting simultaneously
    num_threads = 10

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit all tasks at once
        futures = [executor.submit(call_early_init, i) for i in range(num_threads)]

        # Wait for all to complete
        results = [future.result() for future in as_completed(futures)]

    # Verify thread safety - all calls should complete successfully
    assert len(results) == num_threads, f"Expected {num_threads} results"
    assert is_early_init_done(), "early_init should be marked as done"


def test_performance_impact():
    """Test the performance impact of the thread safety check."""

    # Ensure initialization is done
    early_init()

    # Test many calls - should be fast returns
    iterations = 10000  # Reduced for faster test runs
    start_time = time.time()

    for _ in range(iterations):
        early_init()  # Should return immediately

    end_time = time.time()
    total_time = end_time - start_time
    per_call = (total_time / iterations) * 1000000  # microseconds

    # Assert performance is acceptable
    assert total_time < 0.1, f"Expected < 0.1 seconds for {iterations} calls, got {total_time:.4f}s"
    assert per_call < 100, f"Expected < 100 microseconds per call, got {per_call:.2f}μs"

    # Verify state is still correct
    assert is_early_init_done(), "early_init should still be marked as done"


def test_logging_after_threaded_init():
    """Test that logging works correctly after threaded initialization."""

    # Ensure early_init has been called
    early_init()

    # Test basic logging
    logger.info("Test message from main thread")

    # Test logging from multiple threads
    def thread_logger(thread_id: int):
        logger.info(f"Test message from thread {thread_id}")
        return True

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(thread_logger, i) for i in range(5)]
        results = [future.result() for future in as_completed(futures)]

    # Verify all threads logged successfully
    assert all(results), "All threads should log successfully"
    assert len(results) == 5, "Expected 5 thread results"


def test_early_init_repeated_calls():
    """Test that repeated calls to early_init are safe."""
    # Reset state
    reset_logging_state()

    # Call multiple times - should be safe
    for i in range(10):
        early_init()
        assert is_early_init_done(), f"Should be done after call {i+1}"


@pytest.mark.parametrize("delay", [0, 0.001, 0.01])
def test_concurrent_early_init_with_delays(delay):
    """Test early_init with artificial delays to increase race condition chances."""
    reset_logging_state()

    def delayed_early_init(thread_id: int):
        if delay > 0:
            time.sleep(delay)
        early_init()
        return thread_id

    num_threads = 20
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(delayed_early_init, i) for i in range(num_threads)]
        results = [future.result() for future in as_completed(futures)]

    assert len(results) == num_threads
    assert is_early_init_done(), "early_init should be marked as done"
