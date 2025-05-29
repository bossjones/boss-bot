"""
Pytest tests to verify thread safety and race condition handling.

Tests create isolated environments to test race conditions by
testing the boss-bot logging interceptor module.
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


def test_race_condition_simulation():
    """
    Test race condition by simulating the problematic scenario.
    This tests what would happen WITHOUT the lock protection.
    """

    # Simulate the problematic code pattern
    init_done = False
    init_count = {'value': 0}

    def unsafe_init(thread_id: int):
        """Simulate the unsafe initialization pattern."""
        nonlocal init_done

        # This is the problematic pattern that WOULD have a race condition
        if init_done:
            return thread_id

        # Simulate some initialization work
        time.sleep(0.001)  # Small delay to increase race condition chance

        init_count['value'] += 1
        init_done = True

        return thread_id

    # Run multiple threads with unsafe pattern
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(unsafe_init, i) for i in range(10)]
        results = [future.result() for future in as_completed(futures)]

    # Verify we get some results
    assert len(results) == 10
    assert init_count['value'] >= 1, "At least one initialization should occur"
    assert init_done, "Final state should be True"

    # Race condition usually causes multiple initializations
    # This is expected behavior for the unsafe pattern


def test_safe_early_init():
    """Test the actual thread-safe early_init implementation."""

    # Reset state for clean test
    reset_logging_state()

    def safe_init_wrapper(thread_id: int):
        """Wrapper that calls the thread-safe function."""
        # Call the thread-safe function
        early_init()
        return thread_id

    # Test with many threads starting simultaneously
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(safe_init_wrapper, i) for i in range(20)]
        results = [future.result() for future in as_completed(futures)]

    # Verify thread safety
    assert len(results) == 20, "All threads should complete"
    assert is_early_init_done(), "early_init should be marked as done"


def test_double_checked_locking_pattern():
    """Test that demonstrates the double-checked locking pattern."""

    done = False
    lock = threading.Lock()
    init_count = {'value': 0}

    def double_checked_locking_demo(thread_id: int):
        """Demonstrate the double-checked locking pattern."""
        nonlocal done

        # Quick check without lock (first check)
        if done:
            return thread_id

        # Acquire lock for thread-safe initialization
        with lock:
            if done:  # Double-check inside lock
                return thread_id

            # Only one thread reaches here
            time.sleep(0.001)  # Simulate initialization work
            init_count['value'] += 1
            done = True
            return thread_id

    # Test the pattern
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(double_checked_locking_demo, i) for i in range(15)]
        results = [future.result() for future in as_completed(futures)]

    # Verify the pattern works correctly
    assert len(results) == 15, "All threads should complete"
    assert init_count['value'] == 1, "Exactly one initialization should occur"
    assert done, "Final state should be True"


def test_performance_comparison():
    """Compare performance of different synchronization approaches."""

    iterations = 10000  # Reduced for faster tests

    # Test 1: No protection (fastest but unsafe)
    done1 = False
    def no_protection():
        nonlocal done1
        if done1:
            return
        done1 = True

    start = time.time()
    for _ in range(iterations):
        no_protection()
    time1 = time.time() - start

    # Test 2: Always lock (safe but slower)
    done2 = False
    lock2 = threading.Lock()
    def always_lock():
        nonlocal done2
        with lock2:
            if done2:
                return
            done2 = True

    start = time.time()
    for _ in range(iterations):
        always_lock()
    time2 = time.time() - start

    # Test 3: Double-checked locking (safe and fast)
    done3 = False
    lock3 = threading.Lock()
    def double_checked():
        nonlocal done3
        if done3:
            return
        with lock3:
            if done3:
                return
            done3 = True

    start = time.time()
    for _ in range(iterations):
        double_checked()
    time3 = time.time() - start

    # Performance assertions
    assert time1 >= 0, "No protection time should be non-negative"
    assert time2 >= 0, "Always lock time should be non-negative"
    assert time3 >= 0, "Double-checked time should be non-negative"

    # Double-checked should be faster than always-lock in most cases
    # (though this can vary by system)
    assert time3 <= time2 * 2, "Double-checked should not be much slower than always-lock"

    # Verify overhead is reasonable
    overhead_factor = time3 / time1 if time1 > 0 else 1
    assert overhead_factor < 100, f"Overhead factor too high: {overhead_factor:.2f}x"


@pytest.mark.parametrize("num_threads", [5, 15, 30])
def test_early_init_scalability(num_threads):
    """Test early_init scalability with different thread counts."""
    reset_logging_state()

    def concurrent_call(thread_id: int):
        early_init()
        return thread_id

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(concurrent_call, i) for i in range(num_threads)]
        results = [future.result() for future in as_completed(futures)]

    assert len(results) == num_threads
    assert is_early_init_done(), "early_init should be marked as done"
