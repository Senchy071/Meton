#!/usr/bin/env python3
"""
Performance Profiler - Profile and measure performance bottlenecks.

Features:
- Function execution profiling
- Agent query profiling
- Bottleneck identification
- Performance report generation
"""

import time
import functools
from typing import Callable, Dict, List, Any, Optional
import cProfile
import pstats
from io import StringIO
from datetime import datetime
import threading


class PerformanceProfiler:
    """Profile and measure performance bottlenecks."""

    def __init__(self):
        """Initialize profiler."""
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.query_profiles: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.enabled = True

    @staticmethod
    def profile_function(func: Callable) -> Callable:
        """
        Decorator to profile function execution.

        Args:
            func: Function to profile

        Returns:
            Wrapped function with profiling
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()

            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start

                profiler.disable()

                # Get stats
                s = StringIO()
                ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                ps.print_stats(10)  # Top 10 functions

                print(f"\n⏱️  {func.__name__}: {duration:.3f}s")
                print(s.getvalue())

                return result
            except Exception as e:
                profiler.disable()
                print(f"❌ Error profiling {func.__name__}: {e}")
                raise

        return wrapper

    def profile_agent_query(self, query: str, breakdown: Dict[str, float]) -> Dict[str, Any]:
        """
        Profile complete agent query execution.

        Args:
            query: Query string
            breakdown: Time breakdown by component

        Returns:
            Profiling metrics
        """
        if not self.enabled:
            return {}

        metrics = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "total_time": sum(breakdown.values()),
            "breakdown": breakdown
        }

        with self.lock:
            self.query_profiles.append(metrics)

        return metrics

    def add_profile(self, name: str, duration: float, metadata: Optional[Dict] = None) -> None:
        """
        Add profile measurement.

        Args:
            name: Profile name
            duration: Execution duration in seconds
            metadata: Optional metadata
        """
        if not self.enabled:
            return

        with self.lock:
            if name not in self.profiles:
                self.profiles[name] = {
                    "count": 0,
                    "total_time": 0.0,
                    "min_time": float('inf'),
                    "max_time": 0.0,
                    "avg_time": 0.0,
                    "metadata": metadata or {}
                }

            profile = self.profiles[name]
            profile["count"] += 1
            profile["total_time"] += duration
            profile["min_time"] = min(profile["min_time"], duration)
            profile["max_time"] = max(profile["max_time"], duration)
            profile["avg_time"] = profile["total_time"] / profile["count"]

    def identify_bottlenecks(self, threshold_seconds: float = 5.0) -> List[str]:
        """
        Identify performance bottlenecks.

        Args:
            threshold_seconds: Threshold for identifying bottlenecks

        Returns:
            List of bottleneck descriptions
        """
        bottlenecks = []

        with self.lock:
            # Analyze profiles
            for name, data in self.profiles.items():
                if data["avg_time"] > threshold_seconds:
                    bottlenecks.append(
                        f"{name}: avg={data['avg_time']:.2f}s, "
                        f"max={data['max_time']:.2f}s, count={data['count']}"
                    )

            # Analyze query profiles
            if self.query_profiles:
                avg_query_time = sum(
                    q["total_time"] for q in self.query_profiles
                ) / len(self.query_profiles)

                if avg_query_time > threshold_seconds:
                    bottlenecks.append(
                        f"Agent queries: avg={avg_query_time:.2f}s, "
                        f"count={len(self.query_profiles)}"
                    )

        return bottlenecks

    def generate_profile_report(self) -> str:
        """
        Generate performance profile report.

        Returns:
            Formatted profile report
        """
        with self.lock:
            report = []
            report.append("=" * 80)
            report.append("PERFORMANCE PROFILE REPORT")
            report.append("=" * 80)
            report.append(f"Generated: {datetime.now().isoformat()}")
            report.append("")

            # Function profiles
            if self.profiles:
                report.append("FUNCTION PROFILES:")
                report.append("-" * 80)

                # Sort by total time
                sorted_profiles = sorted(
                    self.profiles.items(),
                    key=lambda x: x[1]["total_time"],
                    reverse=True
                )

                for name, data in sorted_profiles:
                    report.append(f"\n{name}:")
                    report.append(f"  Count:      {data['count']}")
                    report.append(f"  Total:      {data['total_time']:.3f}s")
                    report.append(f"  Average:    {data['avg_time']:.3f}s")
                    report.append(f"  Min:        {data['min_time']:.3f}s")
                    report.append(f"  Max:        {data['max_time']:.3f}s")

            # Query profiles
            if self.query_profiles:
                report.append("\n" + "=" * 80)
                report.append("QUERY PROFILES:")
                report.append("-" * 80)

                total_queries = len(self.query_profiles)
                avg_time = sum(q["total_time"] for q in self.query_profiles) / total_queries

                report.append(f"\nTotal Queries: {total_queries}")
                report.append(f"Average Time:  {avg_time:.3f}s")

                # Recent queries
                report.append("\nRecent Queries (last 10):")
                for query in self.query_profiles[-10:]:
                    report.append(f"\n  Query: {query['query'][:50]}...")
                    report.append(f"  Time:  {query['total_time']:.3f}s")
                    if "breakdown" in query:
                        report.append("  Breakdown:")
                        for component, duration in query["breakdown"].items():
                            report.append(f"    {component}: {duration:.3f}s")

            # Bottlenecks
            bottlenecks = self.identify_bottlenecks(threshold_seconds=2.0)
            if bottlenecks:
                report.append("\n" + "=" * 80)
                report.append("IDENTIFIED BOTTLENECKS:")
                report.append("-" * 80)
                for bottleneck in bottlenecks:
                    report.append(f"  ⚠️  {bottleneck}")

            report.append("\n" + "=" * 80)

            return "\n".join(report)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get profiler statistics.

        Returns:
            Statistics dictionary
        """
        with self.lock:
            return {
                "enabled": self.enabled,
                "function_profiles": len(self.profiles),
                "query_profiles": len(self.query_profiles),
                "total_functions_called": sum(p["count"] for p in self.profiles.values()),
                "avg_query_time": (
                    sum(q["total_time"] for q in self.query_profiles) / len(self.query_profiles)
                    if self.query_profiles else 0.0
                )
            }

    def clear(self) -> None:
        """Clear all profiles."""
        with self.lock:
            self.profiles.clear()
            self.query_profiles.clear()

    def enable(self) -> None:
        """Enable profiling."""
        self.enabled = True

    def disable(self) -> None:
        """Disable profiling."""
        self.enabled = False


class TimingContext:
    """Context manager for timing code blocks."""

    def __init__(self, name: str, profiler: Optional[PerformanceProfiler] = None):
        """
        Initialize timing context.

        Args:
            name: Name of timed block
            profiler: Optional profiler to add timing to
        """
        self.name = name
        self.profiler = profiler
        self.start_time = None
        self.duration = None

    def __enter__(self):
        """Enter context."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        self.duration = time.time() - self.start_time

        if self.profiler:
            self.profiler.add_profile(self.name, self.duration)

        return False


# Global profiler instance
_global_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get global profiler instance."""
    return _global_profiler


def timed(name: Optional[str] = None):
    """
    Decorator to time function execution.

    Args:
        name: Optional name for timing (defaults to function name)

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        timing_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with TimingContext(timing_name, _global_profiler):
                return func(*args, **kwargs)

        return wrapper

    return decorator


if __name__ == "__main__":
    # Example usage
    profiler = PerformanceProfiler()

    # Test profiling
    @timed()
    def slow_function():
        time.sleep(0.1)
        return "done"

    # Run multiple times
    for _ in range(5):
        slow_function()

    # Generate report
    print(profiler.generate_profile_report())

    # Get stats
    print("\nStats:", profiler.get_stats())

    # Identify bottlenecks
    print("\nBottlenecks:", profiler.identify_bottlenecks(threshold_seconds=0.05))
