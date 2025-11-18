#!/usr/bin/env python3
"""
Comprehensive Optimization Tests

Tests for all optimization components:
- Performance Profiler
- Cache Manager
- Query Optimizer
- Resource Monitor
- Benchmarks

Minimum 15 tests required for Task 49.
"""

import sys
import time
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from optimization.profiler import PerformanceProfiler, TimingContext, timed
from optimization.cache_manager import CacheManager, EmbeddingCache, QueryCache
from optimization.query_optimizer import QueryOptimizer
from optimization.resource_monitor import ResourceMonitor
from optimization.benchmarks import BenchmarkSuite


# =============================================================================
# PERFORMANCE PROFILER TESTS (5 tests)
# =============================================================================

def test_profiler_basic():
    """Test 1: Basic profiler functionality."""
    print("\n📝 Test 1: Basic profiler functionality")

    profiler = PerformanceProfiler()

    # Add some profiles
    profiler.add_profile("test_func", 1.5)
    profiler.add_profile("test_func", 2.0)
    profiler.add_profile("test_func", 1.8)

    stats = profiler.get_stats()
    assert stats["function_profiles"] == 1, "Should have 1 function profile"
    assert stats["total_functions_called"] == 3, "Should have 3 total calls"

    print("   ✅ Basic profiler functionality works")


def test_profiler_timing_context():
    """Test 2: Timing context manager."""
    print("\n📝 Test 2: Timing context manager")

    profiler = PerformanceProfiler()

    with TimingContext("test_block", profiler):
        time.sleep(0.1)

    # Check profile was added
    assert "test_block" in profiler.profiles, "Profile should exist"
    assert profiler.profiles["test_block"]["count"] == 1, "Should have 1 call"
    assert profiler.profiles["test_block"]["avg_time"] >= 0.1, "Should be at least 0.1s"

    print("   ✅ Timing context manager works")


def test_profiler_decorator():
    """Test 3: Profiler decorator."""
    print("\n📝 Test 3: Profiler decorator")

    @timed("decorated_func")
    def slow_function():
        time.sleep(0.05)
        return "done"

    result = slow_function()
    assert result == "done", "Function should return correct value"

    # Check global profiler
    from optimization.profiler import get_profiler
    profiler = get_profiler()
    assert "decorated_func" in profiler.profiles, "Profile should exist"

    print("   ✅ Profiler decorator works")


def test_profiler_bottleneck_detection():
    """Test 4: Bottleneck detection."""
    print("\n📝 Test 4: Bottleneck detection")

    profiler = PerformanceProfiler()

    # Add slow function
    profiler.add_profile("slow_func", 6.0)
    profiler.add_profile("fast_func", 0.1)

    bottlenecks = profiler.identify_bottlenecks(threshold_seconds=5.0)
    assert len(bottlenecks) > 0, "Should identify bottlenecks"
    assert any("slow_func" in b for b in bottlenecks), "Should identify slow_func"

    print("   ✅ Bottleneck detection works")


def test_profiler_report_generation():
    """Test 5: Report generation."""
    print("\n📝 Test 5: Report generation")

    profiler = PerformanceProfiler()

    # Add some profiles
    profiler.add_profile("func1", 1.0)
    profiler.add_profile("func2", 2.0)

    report = profiler.generate_profile_report()
    assert "PERFORMANCE PROFILE REPORT" in report, "Should have report header"
    assert "func1" in report, "Should include func1"
    assert "func2" in report, "Should include func2"

    print("   ✅ Report generation works")


# =============================================================================
# CACHE MANAGER TESTS (5 tests)
# =============================================================================

def test_cache_basic_operations():
    """Test 6: Basic cache operations."""
    print("\n📝 Test 6: Basic cache operations")

    cache = CacheManager(cache_dir="./test_cache_1", ttl_seconds=10)

    # Set and get
    cache.set("key1", "value1")
    value = cache.get("key1")
    assert value == "value1", "Should retrieve cached value"

    # Miss
    missing = cache.get("nonexistent")
    assert missing is None, "Should return None for missing key"

    # Cleanup
    cache.clear()
    shutil.rmtree("./test_cache_1", ignore_errors=True)

    print("   ✅ Basic cache operations work")


def test_cache_expiration():
    """Test 7: Cache expiration."""
    print("\n📝 Test 7: Cache expiration")

    cache = CacheManager(cache_dir="./test_cache_2", ttl_seconds=1)

    cache.set("key1", "value1")
    value = cache.get("key1")
    assert value == "value1", "Should get value before expiration"

    # Wait for expiration
    time.sleep(1.5)
    expired = cache.get("key1")
    assert expired is None, "Should return None after expiration"

    # Cleanup
    cache.clear()
    shutil.rmtree("./test_cache_2", ignore_errors=True)

    print("   ✅ Cache expiration works")


def test_cache_statistics():
    """Test 8: Cache statistics."""
    print("\n📝 Test 8: Cache statistics")

    cache = CacheManager(cache_dir="./test_cache_3", ttl_seconds=10)

    # Set some values
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    # Get (hits)
    cache.get("key1")
    cache.get("key2")

    # Miss
    cache.get("missing")

    stats = cache.get_stats()
    assert stats["hits"] == 2, "Should have 2 hits"
    assert stats["misses"] == 1, "Should have 1 miss"
    assert stats["memory_cache_items"] == 2, "Should have 2 items in memory"
    assert stats["hit_rate_percent"] > 0, "Should have positive hit rate"

    # Cleanup
    cache.clear()
    shutil.rmtree("./test_cache_3", ignore_errors=True)

    print("   ✅ Cache statistics work")


def test_embedding_cache():
    """Test 9: Embedding cache."""
    print("\n📝 Test 9: Embedding cache")

    cache_mgr = CacheManager(cache_dir="./test_cache_4", ttl_seconds=10)
    emb_cache = EmbeddingCache(cache_mgr)

    # Mock embedding function
    call_count = [0]

    def compute_embedding(text):
        call_count[0] += 1
        return [1.0, 2.0, 3.0]

    # First call - should compute
    emb1 = emb_cache.get_or_compute("test text", compute_embedding)
    assert call_count[0] == 1, "Should compute on first call"

    # Second call - should use cache
    emb2 = emb_cache.get_or_compute("test text", compute_embedding)
    assert call_count[0] == 1, "Should not compute on second call (cached)"
    assert emb1 == emb2, "Should return same embedding"

    # Cleanup
    cache_mgr.clear()
    shutil.rmtree("./test_cache_4", ignore_errors=True)

    print("   ✅ Embedding cache works")


def test_query_cache():
    """Test 10: Query cache."""
    print("\n📝 Test 10: Query cache")

    cache_mgr = CacheManager(cache_dir="./test_cache_5", ttl_seconds=10)
    query_cache = QueryCache(cache_mgr)

    # Cache query result
    query_cache.set_query_result("What is Python?", "Python is a programming language")

    # Retrieve
    result = query_cache.get_query_result("What is Python?")
    assert result == "Python is a programming language", "Should retrieve cached result"

    # Different query
    result2 = query_cache.get_query_result("What is Java?")
    assert result2 is None, "Should return None for uncached query"

    # Cleanup
    cache_mgr.clear()
    shutil.rmtree("./test_cache_5", ignore_errors=True)

    print("   ✅ Query cache works")


# =============================================================================
# QUERY OPTIMIZER TESTS (3 tests)
# =============================================================================

def test_query_classification():
    """Test 11: Query classification."""
    print("\n📝 Test 11: Query classification")

    optimizer = QueryOptimizer()

    # Test different query types
    assert optimizer.classify_query("Find the main function") == "code_search"
    assert optimizer.classify_query("Review this code for bugs") == "code_review"
    assert optimizer.classify_query("What is async/await?") == "research"
    assert optimizer.classify_query("Generate a login function") == "generation"
    assert optimizer.classify_query("Debug this error") == "debugging"

    print("   ✅ Query classification works")


def test_tool_selection():
    """Test 12: Tool selection optimization."""
    print("\n📝 Test 12: Tool selection optimization")

    optimizer = QueryOptimizer()

    # Code search should suggest codebase_search
    tools = optimizer.optimize_tool_selection("Find the main function")
    assert "codebase_search" in tools, "Should suggest codebase_search for code search"

    # Research should suggest web_search
    tools = optimizer.optimize_tool_selection("Compare Python and JavaScript")
    assert "web_search" in tools, "Should suggest web_search for research"

    print("   ✅ Tool selection optimization works")


def test_rag_optimization():
    """Test 13: RAG search optimization."""
    print("\n📝 Test 13: RAG search optimization")

    optimizer = QueryOptimizer()

    # Simple query
    params = optimizer.optimize_rag_search("Find function")
    assert params["top_k"] == 3, "Simple query should use top_k=3"

    # Complex query
    params = optimizer.optimize_rag_search("Explain how the authentication system works and compare it with authorization")
    assert params["top_k"] == 10, "Complex query should use top_k=10"
    assert params["similarity_threshold"] == 0.6, "Should use lower threshold for exploratory queries"

    print("   ✅ RAG optimization works")


# =============================================================================
# RESOURCE MONITOR TESTS (2 tests)
# =============================================================================

def test_resource_monitor_current_usage():
    """Test 14: Current resource usage monitoring."""
    print("\n📝 Test 14: Current resource usage monitoring")

    monitor = ResourceMonitor()

    usage = monitor.get_current_usage()
    assert "cpu_percent" in usage, "Should have CPU usage"
    assert "memory_mb" in usage, "Should have memory usage"
    assert "memory_percent" in usage, "Should have memory percentage"
    assert usage["cpu_percent"] >= 0, "CPU usage should be non-negative"

    print("   ✅ Current resource usage monitoring works")


def test_resource_monitor_tracking():
    """Test 15: Resource usage tracking."""
    print("\n📝 Test 15: Resource usage tracking")

    monitor = ResourceMonitor(sample_interval=1)

    # Start monitoring
    monitor.start_monitoring()
    time.sleep(2.5)  # Let it collect a few samples
    monitor.stop_monitoring()

    # Check metrics
    history = monitor.get_metrics_history()
    assert len(history) >= 2, "Should have at least 2 samples"

    peak = monitor.get_peak_usage()
    assert "peak_cpu_percent" in peak, "Should have peak CPU"
    assert peak["samples"] >= 2, "Should track multiple samples"

    print("   ✅ Resource usage tracking works")


# =============================================================================
# BENCHMARK TESTS (2 tests)
# =============================================================================

def test_benchmark_suite_basic():
    """Test 16: Basic benchmark execution."""
    print("\n📝 Test 16: Basic benchmark execution")

    suite = BenchmarkSuite()

    # Run a simple benchmark
    def test_func():
        time.sleep(0.01)

    result = suite.run_benchmark("test", test_func, iterations=3, warmup=0)
    assert "avg" in result, "Should have average time"
    assert result["avg"] >= 0.01, "Average should be at least 0.01s"
    assert result["iterations"] == 3, "Should run 3 iterations"

    print("   ✅ Basic benchmark execution works")


def test_benchmark_report():
    """Test 17: Benchmark report generation."""
    print("\n📝 Test 17: Benchmark report generation")

    suite = BenchmarkSuite()

    # Add some results
    suite.results["test1"] = {
        "name": "test1",
        "avg": 0.5,
        "min": 0.4,
        "max": 0.6,
        "success_rate": 100.0
    }

    report = suite.generate_report()
    assert "BENCHMARK RESULTS SUMMARY" in report, "Should have report header"
    assert "test1" in report, "Should include test1"
    assert "0.500s" in report or "0.5" in report, "Should show timing"

    print("   ✅ Benchmark report generation works")


# =============================================================================
# INTEGRATION TEST (1 test)
# =============================================================================

def test_optimization_integration():
    """Test 18: Integration of all optimization components."""
    print("\n📝 Test 18: Optimization integration")

    # Initialize all components
    profiler = PerformanceProfiler()
    cache = CacheManager(cache_dir="./test_cache_integration", ttl_seconds=10)
    optimizer = QueryOptimizer()
    monitor = ResourceMonitor()

    # Simulate optimized query processing
    query = "Find the authentication function"

    # Optimize query
    query_type = optimizer.classify_query(query)
    assert query_type is not None, "Should classify query"

    # Check cache
    cache_key = f"query:{query}"
    cached_result = cache.get(cache_key)

    if not cached_result:
        # Simulate query processing
        with TimingContext("query_processing", profiler):
            time.sleep(0.05)
            result = "Mock query result"

        # Cache result
        cache.set(cache_key, result)

    # Check resource usage
    usage = monitor.get_current_usage()
    assert usage["memory_mb"] > 0, "Should have memory usage"

    # Cleanup
    cache.clear()
    shutil.rmtree("./test_cache_integration", ignore_errors=True)

    print("   ✅ Optimization integration works")


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all optimization tests."""
    print("=" * 80)
    print("OPTIMIZATION TESTS")
    print("=" * 80)
    print(f"Running {18} comprehensive tests...")

    tests = [
        # Profiler tests (5)
        test_profiler_basic,
        test_profiler_timing_context,
        test_profiler_decorator,
        test_profiler_bottleneck_detection,
        test_profiler_report_generation,

        # Cache tests (5)
        test_cache_basic_operations,
        test_cache_expiration,
        test_cache_statistics,
        test_embedding_cache,
        test_query_cache,

        # Optimizer tests (3)
        test_query_classification,
        test_tool_selection,
        test_rag_optimization,

        # Monitor tests (2)
        test_resource_monitor_current_usage,
        test_resource_monitor_tracking,

        # Benchmark tests (2)
        test_benchmark_suite_basic,
        test_benchmark_report,

        # Integration test (1)
        test_optimization_integration,
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
        print("\n✅ All optimization tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
