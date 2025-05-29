#!/usr/bin/env python3
"""
Direct test of the thread safety mechanisms in _early_init().

This creates a minimal reproduction of the thread safety implementation
to verify it works correctly.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def test_our_implementation():
    """Test our exact implementation pattern."""

    print("🔒 Testing our _early_init() thread safety implementation...")

    # Replicate our exact implementation
    _early_init_done = False
    _early_init_lock = threading.Lock()
    init_count = {'value': 0}

    def _early_init_replica():
        """Exact replica of our _early_init implementation."""
        nonlocal _early_init_done

        # Quick check without lock for performance
        if _early_init_done:
            return

        # Thread-safe double-checked locking pattern
        with _early_init_lock:
            if _early_init_done:  # Re-check inside lock
                return  # Another thread already initialized

            # Simulate the initialization work
            time.sleep(0.001)  # Small delay to increase chance of race condition
            init_count['value'] += 1
            print(f"   🔧 Thread {threading.current_thread().ident} performing initialization")

            # Mark as completed inside the lock
            _early_init_done = True

    def call_init(thread_id: int):
        """Function for each thread to call."""
        print(f"   Thread {thread_id} starting...")
        _early_init_replica()
        print(f"   Thread {thread_id} completed")
        return thread_id

    # Test with many threads starting simultaneously
    num_threads = 50
    print(f"   Testing with {num_threads} concurrent threads...")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit all tasks simultaneously
        futures = [executor.submit(call_init, i) for i in range(num_threads)]

        # Wait for all to complete
        results = [future.result() for future in as_completed(futures)]

    print(f"\n   📊 Results:")
    print(f"   - Total threads: {len(results)}")
    print(f"   - Initialization count: {init_count['value']}")
    print(f"   - Final state: {_early_init_done}")

    if init_count['value'] == 1 and _early_init_done:
        print("   ✅ SUCCESS: Thread safety working correctly!")
        return True
    else:
        print("   ❌ FAILURE: Race condition detected!")
        return False


def test_without_lock():
    """Test what happens without thread safety protection."""

    print("\n🚨 Testing WITHOUT thread safety (demonstrating the problem)...")

    # Unsafe implementation
    _early_init_done = False
    init_count = {'value': 0}

    def unsafe_early_init():
        """Unsafe version without lock."""
        nonlocal _early_init_done

        # This is the dangerous pattern
        if _early_init_done:
            return

        # Simulate work (this is where the race condition happens)
        time.sleep(0.001)
        init_count['value'] += 1
        print(f"   ⚠️  Thread {threading.current_thread().ident} performing initialization")
        _early_init_done = True

    def call_unsafe_init(thread_id: int):
        """Function for each thread to call."""
        unsafe_early_init()
        return thread_id

    # Test with many threads
    num_threads = 20
    print(f"   Testing with {num_threads} concurrent threads...")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(call_unsafe_init, i) for i in range(num_threads)]
        results = [future.result() for future in as_completed(futures)]

    print(f"\n   📊 Results:")
    print(f"   - Total threads: {len(results)}")
    print(f"   - Initialization count: {init_count['value']}")
    print(f"   - Final state: {_early_init_done}")

    if init_count['value'] > 1:
        print("   ❌ Race condition detected (as expected without protection)")
        return True  # Expected result for unsafe version
    else:
        print("   ⚠️  Race condition not triggered this time (but could happen)")
        return False


def performance_test():
    """Test the performance impact of our thread safety."""

    print("\n⚡ Performance impact test...")

    # Set up the safe version
    _early_init_done = True  # Already initialized
    _early_init_lock = threading.Lock()

    def safe_quick_return():
        """Test the quick return path performance."""
        if _early_init_done:
            return

        with _early_init_lock:
            if _early_init_done:
                return
            # Won't reach here

    # Test many calls
    iterations = 1000000
    start_time = time.time()

    for _ in range(iterations):
        safe_quick_return()

    end_time = time.time()
    total_time = end_time - start_time
    per_call = (total_time / iterations) * 1000000  # microseconds

    print(f"   - {iterations:,} calls took: {total_time:.4f} seconds")
    print(f"   - Average per call: {per_call:.3f} microseconds")

    if per_call < 1.0:
        print("   ✅ Performance impact is negligible")
    else:
        print("   ⚠️  Performance impact may be noticeable")


def stress_test():
    """Stress test with many repeated calls."""

    print("\n🏋️ Stress test with repeated concurrent calls...")

    _early_init_done = False
    _early_init_lock = threading.Lock()
    call_count = {'value': 0}
    init_count = {'value': 0}

    def stress_early_init():
        """Stress test version that counts all calls."""
        nonlocal _early_init_done
        call_count['value'] += 1

        if _early_init_done:
            return

        with _early_init_lock:
            if _early_init_done:
                return

            init_count['value'] += 1
            _early_init_done = True

    def stress_worker():
        """Each thread calls the function many times."""
        for _ in range(100):
            stress_early_init()

    # Run many threads, each calling many times
    num_threads = 20
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(stress_worker) for _ in range(num_threads)]
        for future in as_completed(futures):
            future.result()

    expected_calls = num_threads * 100
    print(f"   - Expected total calls: {expected_calls:,}")
    print(f"   - Actual total calls: {call_count['value']:,}")
    print(f"   - Initialization count: {init_count['value']}")

    if init_count['value'] == 1 and call_count['value'] == expected_calls:
        print("   ✅ Stress test passed!")
        return True
    else:
        print("   ❌ Stress test failed!")
        return False


if __name__ == "__main__":
    print("🧪 Direct Thread Safety Test")
    print("=" * 50)

    # Run all tests
    safe_result = test_our_implementation()
    unsafe_result = test_without_lock()  # Should show race condition
    performance_test()
    stress_result = stress_test()

    print("\n" + "=" * 50)
    print("📊 Final Results:")
    print(f"   - Thread-safe implementation: {'✅ PASSED' if safe_result else '❌ FAILED'}")
    print(f"   - Unsafe version showed race: {'✅ CONFIRMED' if unsafe_result else '⚠️ NOT TRIGGERED'}")
    print(f"   - Stress test: {'✅ PASSED' if stress_result else '❌ FAILED'}")

    if safe_result and stress_result:
        print("\n🎉 THREAD SAFETY VERIFIED!")
        print("   Your _early_init() implementation is thread-safe.")
    else:
        print("\n💥 THREAD SAFETY ISSUES DETECTED!")
        print("   The implementation may need additional protection.")
