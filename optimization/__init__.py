"""
Optimization module for Meton.

Provides performance optimization capabilities including:
- Performance profiling
- Intelligent caching
- Query optimization
- Resource monitoring
"""

from optimization.profiler import PerformanceProfiler, get_profiler, timed, TimingContext
from optimization.cache_manager import CacheManager, get_cache_manager, EmbeddingCache, QueryCache
from optimization.query_optimizer import QueryOptimizer, get_optimizer
from optimization.resource_monitor import ResourceMonitor, get_resource_monitor

__all__ = [
    "PerformanceProfiler",
    "get_profiler",
    "timed",
    "TimingContext",
    "CacheManager",
    "get_cache_manager",
    "EmbeddingCache",
    "QueryCache",
    "QueryOptimizer",
    "get_optimizer",
    "ResourceMonitor",
    "get_resource_monitor",
]
