#!/usr/bin/env python3
"""
Test script to verify thread safety of _early_init() function.

This test intentionally tries to trigger race conditions by calling
_early_init() from multiple threads simultaneously.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import our updated logger with thread-safe _early_init
from my_intercept_logger import _early_init, logger, _early_init_done, _early_init_lock


def reset_for_testing():
    """Reset the early init state for testing purposes."""
    import my_intercept_logger
    with my_intercept_logger._early_init_lock:
        # Reset the state for testing
        # Note: This is only safe for testing, don't do this in production
        my_intercept_logger._early_init_done = False
        # Also remove any existing handlers for clean test
        from loguru import logger
        logger.remove()


def test_concurrent_early_init():
    """Test that multiple threads calling _early_init() is safe."""

    # Reset state for clean test
    reset_for_testing()

    # Track how many threads actually performed initialization
    init_count = {'value': 0}
    init_lock = threading.Lock()

    def call_early_init(thread_id: int):
        """Function that each thread will execute."""
        print(f"Thread {thread_id}: Starting _early_init()")

        # Check if we're the first to initialize
        was_done_before = _early_init_done

        # Call the function
        _early_init()

        # Check if we actually did the initialization
        if not was_done_before and _early_init_done:
            with init_lock:
                init_count['value'] += 1
                print(f"Thread {thread_id}: ✅ Performed initialization")
        else:
            print(f"Thread {thread_id}: ⏭️ Skipped (already done)")

        return thread_id

    # Test with multiple threads starting simultaneously
    num_threads = 10
    print(f"\n🧪 Testing {num_threads} threads calling _early_init() simultaneously...")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit all tasks at once
        futures = [executor.submit(call_early_init, i) for i in range(num_threads)]

        # Wait for all to complete
        for future in as_completed(futures):
            thread_id = future.result()
            # print(f"Thread {thread_id} completed")

    print(f"\n📊 Results:")
    print(f"   - Threads that performed initialization: {init_count['value']}")
    print(f"   - Expected: 1 (only one should initialize)")
    print(f"   - Final _early_init_done state: {_early_init_done}")

    # Verify only one thread actually did the initialization
    if init_count['value'] == 1:
        print("   ✅ SUCCESS: Thread safety test passed!")
    else:
        print("   ❌ FAILURE: Race condition detected!")

    return init_count['value'] == 1


def test_performance_impact():
    """Test the performance impact of the thread safety check."""

    # Ensure initialization is done
    _early_init()

    def call_early_init_repeatedly():
        """Call _early_init many times (should be fast returns)."""
        for _ in range(1000):
            _early_init()  # Should return immediately

    print(f"\n⚡ Testing performance impact of quick-return path...")

    start_time = time.time()
    call_early_init_repeatedly()
    end_time = time.time()

    total_time = end_time - start_time
    per_call = (total_time / 1000) * 1000000  # microseconds

    print(f"   - 1000 calls took: {total_time:.4f} seconds")
    print(f"   - Average per call: {per_call:.2f} microseconds")

    if per_call < 10:  # Less than 10 microseconds per call
        print("   ✅ Performance impact is negligible")
    else:
        print("   ⚠️ Performance impact may be noticeable")


def test_logging_after_threaded_init():
    """Test that logging works correctly after threaded initialization."""

    print(f"\n📝 Testing logging functionality after threaded init...")

    # Test basic logging
    logger.info("Test message from main thread")

    # Test logging from multiple threads
    def thread_logger(thread_id: int):
        logger.info(f"Test message from thread {thread_id}")
        return True

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(thread_logger, i) for i in range(5)]
        results = [future.result() for future in as_completed(futures)]

    print(f"   ✅ All threading logging tests completed successfully")


if __name__ == "__main__":
    print("🔒 Thread Safety Test for _early_init()")
    print("=" * 50)

    # Run the tests
    thread_safety_passed = test_concurrent_early_init()
    test_performance_impact()
    test_logging_after_threaded_init()

    print("\n" + "=" * 50)
    if thread_safety_passed:
        print("🎉 ALL TESTS PASSED - Thread safety is working correctly!")
    else:
        print("💥 TESTS FAILED - Race condition detected!")

    logger.success("Thread safety testing completed")
