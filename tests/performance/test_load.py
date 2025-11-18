#!/usr/bin/env python3
"""
Load and Stress Tests

Tests system under load and concurrent usage.
"""

import sys
import os
import time
import threading
from pathlib import Path
import concurrent.futures

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from optimization.cache_manager import CacheManager
from optimization.profiler import PerformanceProfiler
from core.conversation import ConversationManager
from core.config import ConfigLoader


class TestLoad:
    """Load and stress testing."""

    def test_concurrent_cache_access(self):
        """Test 1: Concurrent cache operations."""
        print("\n📝 Test 1: Concurrent cache access")

        cache = CacheManager(cache_dir="./test_cache_load", ttl_seconds=10)

        def write_to_cache(i):
            cache.set(f"key_{i}", f"value_{i}")
            return cache.get(f"key_{i}")

        # Concurrent writes
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_to_cache, i) for i in range(20)]
            results = [f.result() for f in futures]

        assert len(results) == 20
        assert all(r is not None for r in results)

        # Cleanup
        cache.clear()
        import shutil
        shutil.rmtree("./test_cache_load", ignore_errors=True)

        print("   ✅ Concurrent cache access works")

    def test_sustained_profiling(self):
        """Test 2: Sustained profiling under load."""
        print("\n📝 Test 2: Sustained profiling")

        profiler = PerformanceProfiler()

        # Simulate sustained load
        for i in range(100):
            profiler.add_profile("operation", 0.01 * (i % 10))

        stats = profiler.get_stats()
        assert stats["total_functions_called"] == 100

        print("   ✅ Sustained profiling works")

    def test_memory_stability(self):
        """Test 3: Memory stability under load."""
        print("\n📝 Test 3: Memory stability")

        import psutil
        process = psutil.Process(os.getpid())

        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create and destroy many objects
        cache = CacheManager(cache_dir="./test_cache_memory", ttl_seconds=10)
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}" * 10)

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        # Memory shouldn't increase by more than 100MB for this workload
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB"

        # Cleanup
        cache.clear()
        import shutil
        shutil.rmtree("./test_cache_memory", ignore_errors=True)

        print(f"   ✅ Memory stable (increased by {memory_increase:.1f}MB)")

    def test_conversation_concurrent_access(self):
        """Test 4: Concurrent conversation operations."""
        print("\n📝 Test 4: Concurrent conversation access")

        config = ConfigLoader("config.yaml")

        def add_messages(conv_id):
            conv = ConversationManager(config.config.conversation)
            for i in range(5):
                conv.add_message("user", f"Message {i} from {conv_id}")
            return len(conv.get_history())

        # Concurrent conversation operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(add_messages, i) for i in range(3)]
            results = [f.result() for f in futures]

        assert all(r >= 5 for r in results)

        print("   ✅ Concurrent conversation access works")

    def test_rapid_operations(self):
        """Test 5: Rapid sequential operations."""
        print("\n📝 Test 5: Rapid operations")

        cache = CacheManager(cache_dir="./test_cache_rapid", ttl_seconds=10)

        start = time.time()
        operation_count = 500

        for i in range(operation_count):
            cache.set(f"key_{i}", f"value_{i}")
            cache.get(f"key_{i}")

        duration = time.time() - start
        ops_per_second = operation_count * 2 / duration  # *2 for set+get

        print(f"   ℹ️  Operations per second: {ops_per_second:.1f}")
        assert ops_per_second > 100, "Should handle at least 100 ops/sec"

        # Cleanup
        cache.clear()
        import shutil
        shutil.rmtree("./test_cache_rapid", ignore_errors=True)

        print("   ✅ Rapid operations work")


def run_all_tests():
    """Run all load tests."""
    print("=" * 80)
    print("LOAD AND STRESS TESTS")
    print("=" * 80)

    test_suite = TestLoad()
    tests = [
        test_suite.test_concurrent_cache_access,
        test_suite.test_sustained_profiling,
        test_suite.test_memory_stability,
        test_suite.test_conversation_concurrent_access,
        test_suite.test_rapid_operations,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} total")
    print("=" * 80)

    if failed == 0:
        print("\n✅ All load tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
