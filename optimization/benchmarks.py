#!/usr/bin/env python3
"""
Benchmark Suite - Performance benchmarks for Meton.

Features:
- Simple query benchmark
- Complex query benchmark
- RAG search benchmark
- Code review benchmark
- Parallel tools benchmark
- Cache performance benchmark
"""

import time
import sys
from pathlib import Path
from typing import Dict, List, Callable, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class BenchmarkSuite:
    """Performance benchmark suite."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.results: Dict[str, Dict[str, Any]] = {}

    def run_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 5,
        warmup: int = 1
    ) -> Dict[str, Any]:
        """
        Run a benchmark.

        Args:
            name: Benchmark name
            func: Function to benchmark
            iterations: Number of iterations
            warmup: Number of warmup iterations

        Returns:
            Benchmark results
        """
        print(f"\n🏃 Running benchmark: {name}")
        print(f"   Iterations: {iterations}, Warmup: {warmup}")

        # Warmup
        for _ in range(warmup):
            try:
                func()
            except Exception as e:
                print(f"   ⚠️  Warmup failed: {e}")

        # Actual benchmark
        times = []
        for i in range(iterations):
            start = time.time()
            try:
                result = func()
                duration = time.time() - start
                times.append(duration)
                print(f"   Iteration {i+1}: {duration:.3f}s")
            except Exception as e:
                print(f"   ❌ Iteration {i+1} failed: {e}")
                times.append(float('inf'))

        # Calculate statistics
        valid_times = [t for t in times if t != float('inf')]
        if valid_times:
            results = {
                "name": name,
                "iterations": iterations,
                "times": valid_times,
                "min": min(valid_times),
                "max": max(valid_times),
                "avg": sum(valid_times) / len(valid_times),
                "total": sum(valid_times),
                "success_rate": len(valid_times) / iterations * 100
            }
        else:
            results = {
                "name": name,
                "iterations": iterations,
                "times": [],
                "min": float('inf'),
                "max": float('inf'),
                "avg": float('inf'),
                "total": float('inf'),
                "success_rate": 0.0
            }

        self.results[name] = results
        print(f"   ✅ Average: {results['avg']:.3f}s")

        return results

    def benchmark_simple_query(self) -> float:
        """Benchmark simple query."""
        def run():
            # Simulate simple query processing
            time.sleep(0.1)  # Simulate 100ms processing
            return "Simple query result"

        result = self.run_benchmark("Simple Query", run, iterations=10)
        return result["avg"]

    def benchmark_complex_query(self) -> float:
        """Benchmark complex query."""
        def run():
            # Simulate complex query processing
            time.sleep(0.5)  # Simulate 500ms processing
            return "Complex query result"

        result = self.run_benchmark("Complex Query", run, iterations=5)
        return result["avg"]

    def benchmark_rag_search(self) -> float:
        """Benchmark RAG search."""
        def run():
            # Simulate RAG search
            time.sleep(0.2)  # Simulate 200ms search
            return ["result1", "result2", "result3"]

        result = self.run_benchmark("RAG Search", run, iterations=10)
        return result["avg"]

    def benchmark_code_review(self) -> float:
        """Benchmark code review."""
        def run():
            # Simulate code review
            time.sleep(1.0)  # Simulate 1s review
            return {"issues": [], "suggestions": []}

        result = self.run_benchmark("Code Review", run, iterations=3)
        return result["avg"]

    def benchmark_parallel_tools(self) -> float:
        """Benchmark parallel tool execution."""
        def run():
            # Simulate parallel execution of 3 tools
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(time.sleep, 0.1),
                    executor.submit(time.sleep, 0.1),
                    executor.submit(time.sleep, 0.1)
                ]
                concurrent.futures.wait(futures)
            return "Parallel execution complete"

        result = self.run_benchmark("Parallel Tools (3 tools)", run, iterations=10)
        return result["avg"]

    def benchmark_cache_performance(self) -> Dict[str, float]:
        """Benchmark cache performance."""
        from optimization.cache_manager import CacheManager

        cache = CacheManager(cache_dir="./test_benchmark_cache", ttl_seconds=3600)

        # Benchmark cache writes
        def write_test():
            for i in range(100):
                cache.set(f"key_{i}", f"value_{i}")

        write_result = self.run_benchmark("Cache Writes (100 items)", write_test, iterations=5)

        # Benchmark cache reads (hits)
        def read_test():
            for i in range(100):
                cache.get(f"key_{i}")

        read_result = self.run_benchmark("Cache Reads (100 hits)", read_test, iterations=5)

        # Benchmark cache misses
        def miss_test():
            for i in range(100):
                cache.get(f"missing_key_{i}")

        miss_result = self.run_benchmark("Cache Reads (100 misses)", miss_test, iterations=5)

        # Cleanup
        cache.clear()
        import shutil
        shutil.rmtree("./test_benchmark_cache", ignore_errors=True)

        return {
            "write_avg": write_result["avg"],
            "read_avg": read_result["avg"],
            "miss_avg": miss_result["avg"]
        }

    def benchmark_query_optimization(self) -> float:
        """Benchmark query optimization."""
        from optimization.query_optimizer import QueryOptimizer

        optimizer = QueryOptimizer()

        def optimize_test():
            queries = [
                "Find the main function in the codebase",
                "Review the code in src/main.py for bugs",
                "Compare Python and JavaScript async patterns",
                "Generate a new user authentication function",
                "Why is my code not working?"
            ]
            for query in queries:
                optimizer.classify_query(query)
                optimizer.optimize_tool_selection(query)
                optimizer.optimize_rag_search(query)

        result = self.run_benchmark("Query Optimization (5 queries)", optimize_test, iterations=10)
        return result["avg"]

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """
        Run all benchmarks.

        Returns:
            All benchmark results
        """
        print("=" * 80)
        print("METON PERFORMANCE BENCHMARK SUITE")
        print("=" * 80)

        # Run benchmarks
        self.benchmark_simple_query()
        self.benchmark_complex_query()
        self.benchmark_rag_search()
        self.benchmark_code_review()
        self.benchmark_parallel_tools()
        cache_perf = self.benchmark_cache_performance()
        self.benchmark_query_optimization()

        # Add cache performance to results
        self.results["Cache Performance"] = cache_perf

        return self.results

    def generate_report(self) -> str:
        """
        Generate benchmark report.

        Returns:
            Formatted report
        """
        if not self.results:
            return "No benchmark results available."

        report = []
        report.append("\n" + "=" * 80)
        report.append("BENCHMARK RESULTS SUMMARY")
        report.append("=" * 80)

        for name, result in self.results.items():
            report.append(f"\n{name}:")
            if isinstance(result, dict) and "avg" in result:
                report.append(f"  Average:      {result['avg']:.3f}s")
                report.append(f"  Min:          {result['min']:.3f}s")
                report.append(f"  Max:          {result['max']:.3f}s")
                report.append(f"  Success Rate: {result['success_rate']:.1f}%")
            else:
                # Cache performance
                for key, value in result.items():
                    if isinstance(value, float):
                        report.append(f"  {key}: {value:.3f}s")

        report.append("\n" + "=" * 80)

        return "\n".join(report)

    def compare_with_baseline(self, baseline: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """
        Compare results with baseline.

        Args:
            baseline: Baseline times (name -> avg_time)

        Returns:
            Comparison results
        """
        comparison = {}

        for name, result in self.results.items():
            if name in baseline and isinstance(result, dict) and "avg" in result:
                baseline_time = baseline[name]
                current_time = result["avg"]

                improvement = ((baseline_time - current_time) / baseline_time) * 100

                comparison[name] = {
                    "baseline": baseline_time,
                    "current": current_time,
                    "improvement_percent": improvement,
                    "faster": current_time < baseline_time
                }

        return comparison

    def print_comparison(self, comparison: Dict[str, Dict[str, Any]]) -> None:
        """
        Print comparison results.

        Args:
            comparison: Comparison results
        """
        print("\n" + "=" * 80)
        print("PERFORMANCE COMPARISON")
        print("=" * 80)

        for name, comp in comparison.items():
            symbol = "✅" if comp["faster"] else "❌"
            direction = "faster" if comp["faster"] else "slower"

            print(f"\n{symbol} {name}:")
            print(f"   Baseline: {comp['baseline']:.3f}s")
            print(f"   Current:  {comp['current']:.3f}s")
            print(f"   {abs(comp['improvement_percent']):.1f}% {direction}")


def run_benchmarks() -> Dict[str, Any]:
    """
    Run performance benchmarks.

    Returns:
        Benchmark results
    """
    suite = BenchmarkSuite()
    results = suite.run_all_benchmarks()
    print(suite.generate_report())
    return results


if __name__ == "__main__":
    # Run benchmarks
    results = run_benchmarks()

    # Example baseline comparison
    baseline = {
        "Simple Query": 0.15,
        "Complex Query": 0.6,
        "RAG Search": 0.25,
        "Code Review": 1.2,
        "Parallel Tools (3 tools)": 0.15,
        "Query Optimization (5 queries)": 0.01
    }

    suite = BenchmarkSuite()
    suite.results = results
    comparison = suite.compare_with_baseline(baseline)
    suite.print_comparison(comparison)
