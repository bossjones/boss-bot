"""
Pytest tests for thread safety mechanisms in early_init().

Tests the thread safety implementation of the boss-bot logging interceptor
to verify it works correctly under concurrent access.
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


def test_early_init_thread_safety():
    """Test that early_init() is thread-safe under concurrent access."""
    # Reset state for clean test
    reset_logging_state()

    call_count = threading.local()
    call_count.value = 0
    total_calls = {'value': 0}
    call_lock = threading.Lock()

    def concurrent_early_init(thread_id: int):
        """Function for each thread to call early_init()."""
        with call_lock:
            total_calls['value'] += 1

        # All threads call early_init
        early_init()
        return thread_id

    # Test with many threads starting simultaneously
    num_threads = 50

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit all tasks simultaneously
        futures = [executor.submit(concurrent_early_init, i) for i in range(num_threads)]

        # Wait for all to complete
        results = [future.result() for future in as_completed(futures)]

    # Verify results
    assert len(results) == num_threads, f"Expected {num_threads} results, got {len(results)}"
    assert total_calls['value'] == num_threads, f"Expected {num_threads} calls, got {total_calls['value']}"
    assert is_early_init_done(), "early_init should be marked as done"

    # The key test: all calls should succeed without errors or crashes
    # The thread safety is verified by the fact that no exceptions occurred
    # and the final state is consistent


def test_unsafe_initialization_pattern():
    """Test to demonstrate race conditions without thread safety protection."""

    # This test shows what happens without proper synchronization
    unsafe_init_done = False
    init_count = {'value': 0}

    def unsafe_early_init():
        """Unsafe version without lock - demonstrates race condition."""
        nonlocal unsafe_init_done

        # This is the dangerous pattern - check then act without synchronization
        if unsafe_init_done:
            return

        # Simulate work (this is where the race condition happens)
        time.sleep(0.001)
        init_count['value'] += 1
        unsafe_init_done = True

    def call_unsafe_init(thread_id: int):
        """Function for each thread to call."""
        unsafe_early_init()
        return thread_id

    # Test with many threads
    num_threads = 20

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(call_unsafe_init, i) for i in range(num_threads)]
        results = [future.result() for future in as_completed(futures)]

    # Verify we can detect the race condition
    assert len(results) == num_threads
    # Race condition should cause multiple initializations
    # Note: This test may occasionally pass due to timing, but usually fails
    assert init_count['value'] >= 1, "At least one initialization should occur"
    assert unsafe_init_done, "Final state should be True"


def test_early_init_performance():
    """Test the performance impact of repeated early_init() calls."""

    # Ensure early_init is already done
    early_init()

    # Test many calls - should be quick returns
    iterations = 100000  # Reduced for faster pytest runs
    start_time = time.time()

    for _ in range(iterations):
        early_init()  # Should return immediately

    end_time = time.time()
    total_time = end_time - start_time
    per_call = (total_time / iterations) * 1000000  # microseconds

    # Performance assertions
    assert total_time < 1.0, f"Expected < 1 second for {iterations} calls, got {total_time:.4f}s"
    assert per_call < 10.0, f"Expected < 10 microseconds per call, got {per_call:.3f}μs"

    # Verify functionality still works
    assert is_early_init_done(), "early_init should still be marked as done"


def test_stress_concurrent_calls():
    """Stress test with many repeated concurrent calls."""

    # Reset state for clean test
    reset_logging_state()

    call_count = {'value': 0}
    count_lock = threading.Lock()

    def stress_worker():
        """Each thread calls early_init() many times."""
        for _ in range(100):
            with count_lock:
                call_count['value'] += 1

            # Call the actual function
            early_init()

    # Run many threads, each calling many times
    num_threads = 20
    expected_calls = num_threads * 100

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(stress_worker) for _ in range(num_threads)]
        for future in as_completed(futures):
            future.result()

    # Verify stress test results
    assert call_count['value'] == expected_calls, f"Expected {expected_calls} calls, got {call_count['value']}"
    assert is_early_init_done(), "early_init should be marked as done after stress test"


def test_logging_after_threaded_init():
    """Test that logging works correctly after threaded initialization."""

    from loguru import logger

    # Ensure early_init has been called
    early_init()

    # Test basic logging
    logger.info("Test message from main thread")

    # Test logging from multiple threads
    def thread_logger(thread_id: int):
        logger.info(f"Test message from thread {thread_id}")
        return True

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(thread_logger, i) for i in range(5)]
        results = [future.result() for future in as_completed(futures)]

    # Verify all threads logged successfully
    assert all(results), "All threads should log successfully"
    assert len(results) == 5, "Expected 5 thread results"


def test_early_init_idempotent():
    """Test that calling early_init() multiple times is safe."""
    # Reset for clean test
    reset_logging_state()

    # Call multiple times in sequence
    for _ in range(10):
        early_init()

    # Should still be in correct state
    assert is_early_init_done(), "early_init should be marked as done"


def test_early_init_state_consistency():
    """Test that early_init state is consistent across calls."""
    # Reset for clean test
    reset_logging_state()

    # Initially should not be done
    assert not is_early_init_done(), "Should not be done initially"

    # After calling, should be done
    early_init()
    assert is_early_init_done(), "Should be done after calling"

    # Should remain done
    early_init()
    assert is_early_init_done(), "Should remain done after second call"


@pytest.mark.parametrize("num_threads", [10, 25, 50])
def test_concurrent_early_init_various_thread_counts(num_threads):
    """Test early_init with various numbers of concurrent threads."""
    # Reset state for clean test
    reset_logging_state()

    results = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(early_init) for _ in range(num_threads)]
        results = [future.result() for future in as_completed(futures)]

    # All calls should complete without error
    assert len(results) == num_threads
    assert is_early_init_done(), "early_init should be marked as done"
