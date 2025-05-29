#!/usr/bin/env python3
"""
Isolated test to verify the thread safety of _early_init() function.

This test creates a clean environment to test race conditions by
importing the module within the test functions.
"""

import threading
import time
import sys
import importlib
from concurrent.futures import ThreadPoolExecutor, as_completed


def test_race_condition_simulation():
    """
    Test race condition by simulating the problematic scenario.
    This tests what would happen WITHOUT the lock protection.
    """
    print("🧪 Simulating race condition scenario...")

    # Simulate the problematic code pattern
    init_done = False
    init_count = {'value': 0}

    def unsafe_init(thread_id: int):
        """Simulate the unsafe initialization pattern."""
        nonlocal init_done

        # This is the problematic pattern that WOULD have a race condition
        if init_done:
            return f"Thread {thread_id}: Already done"

        # Simulate some initialization work
        time.sleep(0.001)  # Small delay to increase race condition chance

        init_count['value'] += 1
        init_done = True

        return f"Thread {thread_id}: Performed init"

    # Run multiple threads with unsafe pattern
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(unsafe_init, i) for i in range(10)]
        results = [future.result() for future in as_completed(futures)]

    print(f"   Unsafe pattern results:")
    for result in results:
        print(f"   - {result}")

    print(f"   Total initializations: {init_count['value']}")

    if init_count['value'] > 1:
        print("   ❌ Race condition detected (as expected without protection)")
    else:
        print("   ⚠️ Race condition not triggered (but could happen)")

    return init_count['value']


def test_safe_early_init():
    """Test the actual thread-safe _early_init implementation."""
    print("\n🔒 Testing thread-safe _early_init implementation...")

    # Fresh import to avoid any previous state
    import my_intercept_logger
    if 'my_intercept_logger' in sys.modules:
        # Force reload to reset state
        importlib.reload(my_intercept_logger)

    from my_intercept_logger import _early_init, _early_init_done, _early_init_lock

    # Reset state for clean test
    with _early_init_lock:
        my_intercept_logger._early_init_done = False

    init_count = {'value': 0}

    def safe_init_wrapper(thread_id: int):
        """Wrapper to track which threads actually perform initialization."""

        # Check state before
        was_done_before = _early_init_done

        # Call the thread-safe function
        _early_init()

        # Check if this thread did the initialization
        if not was_done_before and _early_init_done:
            init_count['value'] += 1
            return f"Thread {thread_id}: ✅ Performed init"
        else:
            return f"Thread {thread_id}: ⏭️ Skipped (already done)"

    # Test with many threads starting simultaneously
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(safe_init_wrapper, i) for i in range(20)]
        results = [future.result() for future in as_completed(futures)]

    print(f"   Thread-safe pattern results:")
    for result in results:
        print(f"   - {result}")

    print(f"   Total initializations: {init_count['value']}")
    print(f"   Final state: {_early_init_done}")

    if init_count['value'] == 1:
        print("   ✅ SUCCESS: Exactly one initialization (thread-safe)")
        return True
    else:
        print("   ❌ FAILURE: Race condition detected")
        return False


def test_double_checked_locking_pattern():
    """Test that demonstrates the double-checked locking pattern."""
    print("\n🔍 Testing double-checked locking pattern...")

    done = False
    lock = threading.Lock()
    init_count = {'value': 0}

    def double_checked_locking_demo(thread_id: int):
        """Demonstrate the double-checked locking pattern."""
        nonlocal done

        # Quick check without lock (first check)
        if done:
            return f"Thread {thread_id}: Quick return"

        # Acquire lock for thread-safe initialization
        with lock:
            if done:  # Double-check inside lock
                return f"Thread {thread_id}: Double-check return"

            # Only one thread reaches here
            time.sleep(0.001)  # Simulate initialization work
            init_count['value'] += 1
            done = True
            return f"Thread {thread_id}: Performed initialization"

    # Test the pattern
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(double_checked_locking_demo, i) for i in range(15)]
        results = [future.result() for future in as_completed(futures)]

    print(f"   Double-checked locking results:")
    for result in results:
        print(f"   - {result}")

    print(f"   Total initializations: {init_count['value']}")

    if init_count['value'] == 1:
        print("   ✅ Double-checked locking pattern works correctly")
        return True
    else:
        print("   ❌ Double-checked locking pattern failed")
        return False


def performance_comparison():
    """Compare performance of different approaches."""
    print("\n⚡ Performance comparison...")

    # Test 1: No protection (fastest but unsafe)
    done1 = False
    def no_protection():
        nonlocal done1
        if done1:
            return
        done1 = True

    start = time.time()
    for _ in range(100000):
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
    for _ in range(100000):
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
    for _ in range(100000):
        double_checked()
    time3 = time.time() - start

    print(f"   No protection:      {time1:.4f}s (unsafe)")
    print(f"   Always lock:        {time2:.4f}s (safe, slow)")
    print(f"   Double-checked:     {time3:.4f}s (safe, fast)")
    print(f"   Overhead factor:    {time3/time1:.2f}x")


if __name__ == "__main__":
    print("🧪 Comprehensive Thread Safety Test for _early_init()")
    print("=" * 60)

    # Run all tests
    race_count = test_race_condition_simulation()
    safe_result = test_safe_early_init()
    pattern_result = test_double_checked_locking_pattern()
    performance_comparison()

    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"   - Unsafe pattern triggered {race_count} initializations")
    print(f"   - Safe _early_init: {'✅ PASSED' if safe_result else '❌ FAILED'}")
    print(f"   - Locking pattern: {'✅ PASSED' if pattern_result else '❌ FAILED'}")

    if safe_result and pattern_result:
        print("\n🎉 ALL THREAD SAFETY TESTS PASSED!")
        print("   The _early_init() function is properly protected against race conditions.")
    else:
        print("\n💥 SOME TESTS FAILED!")
        print("   There may be race condition issues that need to be addressed.")
