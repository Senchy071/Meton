#!/usr/bin/env python3
"""
Performance Benchmark Tests

Establishes performance baselines for key operations.
"""

import sys
import os
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from optimization.cache_manager import CacheManager
from optimization.profiler import PerformanceProfiler
from optimization.query_optimizer import QueryOptimizer
from optimization.resource_monitor import ResourceMonitor
from core.conversation import ConversationManager
from core.config import ConfigLoader


class TestBenchmarks:
    """Performance benchmark tests."""

    def test_cache_performance(self):
        """Test 1: Cache operation benchmarks."""
        print("\n📝 Test 1: Cache performance")

        cache = CacheManager(cache_dir="./test_cache_bench", ttl_seconds=10)

        # Benchmark writes
        write_times = []
        for i in range(100):
            start = time.time()
            cache.set(f"key_{i}", f"value_{i}")
            write_times.append(time.time() - start)

        # Benchmark reads (hits)
        read_times = []
        for i in range(100):
            start = time.time()
            cache.get(f"key_{i}")
            read_times.append(time.time() - start)

        avg_write = sum(write_times) / len(write_times) * 1000  # ms
        avg_read = sum(read_times) / len(read_times) * 1000  # ms

        print(f"   ℹ️  Avg write: {avg_write:.3f}ms, Avg read: {avg_read:.3f}ms")

        assert avg_write < 10.0, "Write should be under 10ms"
        assert avg_read < 5.0, "Read should be under 5ms"

        # Cleanup
        cache.clear()
        import shutil
        shutil.rmtree("./test_cache_bench", ignore_errors=True)

        print("   ✅ Cache performance meets targets")

    def test_profiler_overhead(self):
        """Test 2: Profiler overhead benchmark."""
        print("\n📝 Test 2: Profiler overhead")

        profiler = PerformanceProfiler()

        # Measure overhead
        iterations = 1000
        start = time.time()

        for i in range(iterations):
            profiler.add_profile("test_op", 0.001)

        duration = (time.time() - start) / iterations * 1000  # ms per operation

        print(f"   ℹ️  Profiler overhead: {duration:.3f}ms per operation")
        assert duration < 1.0, "Profiler overhead should be under 1ms"

        print("   ✅ Profiler overhead acceptable")

    def test_query_optimizer_performance(self):
        """Test 3: Query optimizer benchmarks."""
        print("\n📝 Test 3: Query optimizer performance")

        optimizer = QueryOptimizer()

        queries = [
            "Find the main function in the codebase",
            "Review the code in src/main.py for bugs",
            "Compare Python and JavaScript async patterns",
            "Generate a new user authentication function",
            "Debug this error in my code"
        ]

        times = []
        for query in queries:
            start = time.time()
            optimizer.classify_query(query)
            optimizer.optimize_tool_selection(query)
            optimizer.optimize_rag_search(query)
            times.append(time.time() - start)

        avg_time = sum(times) / len(times) * 1000  # ms

        print(f"   ℹ️  Avg optimization time: {avg_time:.3f}ms")
        assert avg_time < 10.0, "Query optimization should be under 10ms"

        print("   ✅ Query optimizer performance meets targets")

    def test_resource_monitor_overhead(self):
        """Test 4: Resource monitor overhead benchmark."""
        print("\n📝 Test 4: Resource monitor overhead")

        monitor = ResourceMonitor()

        # Measure get_current_usage overhead
        times = []
        for _ in range(50):
            start = time.time()
            monitor.get_current_usage()
            times.append(time.time() - start)

        avg_time = sum(times) / len(times) * 1000  # ms

        print(f"   ℹ️  Avg monitoring overhead: {avg_time:.3f}ms")
        assert avg_time < 50.0, "Monitoring should be under 50ms"

        print("   ✅ Resource monitor overhead acceptable")

    def test_conversation_operations(self):
        """Test 5: Conversation operation benchmarks."""
        print("\n📝 Test 5: Conversation operations")

        config = ConfigLoader("config.yaml")
        conv = ConversationManager(config.config.conversation)

        # Benchmark message addition
        add_times = []
        for i in range(50):
            start = time.time()
            conv.add_message("user", f"Test message {i}")
            add_times.append(time.time() - start)

        # Benchmark history retrieval
        get_times = []
        for _ in range(50):
            start = time.time()
            conv.get_history()
            get_times.append(time.time() - start)

        avg_add = sum(add_times) / len(add_times) * 1000  # ms
        avg_get = sum(get_times) / len(get_times) * 1000  # ms

        print(f"   ℹ️  Avg add: {avg_add:.3f}ms, Avg get: {avg_get:.3f}ms")

        assert avg_add < 10.0, "Message addition should be under 10ms"
        assert avg_get < 5.0, "History retrieval should be under 5ms"

        print("   ✅ Conversation operations meet targets")


def run_all_tests():
    """Run all benchmark tests."""
    print("=" * 80)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 80)

    test_suite = TestBenchmarks()
    tests = [
        test_suite.test_cache_performance,
        test_suite.test_profiler_overhead,
        test_suite.test_query_optimizer_performance,
        test_suite.test_resource_monitor_overhead,
        test_suite.test_conversation_operations,
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
        print("\n✅ All benchmark tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
