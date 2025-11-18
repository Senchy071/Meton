#!/usr/bin/env python3
"""
Cache Manager - Intelligent caching for query results and embeddings.

Features:
- Two-tier caching (memory + disk)
- TTL-based expiration
- LRU eviction for memory cache
- Cache statistics and hit rate tracking
- Thread-safe operations
"""

from typing import Any, Optional, Dict, Tuple
import hashlib
import json
import pickle
from pathlib import Path
import time
import threading
from collections import OrderedDict


class CacheManager:
    """Intelligent caching for query results and embeddings."""

    def __init__(
        self,
        cache_dir: str = "./cache",
        ttl_seconds: int = 3600,
        max_memory_items: int = 1000
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for disk cache
            ttl_seconds: Time-to-live for cached items
            max_memory_items: Maximum items in memory cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = ttl_seconds
        self.max_memory_items = max_memory_items

        # Memory cache (LRU)
        self.memory_cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()

        # Statistics
        self.hits = 0
        self.misses = 0

        # Thread safety
        self.lock = threading.Lock()

        # Enabled flag
        self.enabled = True

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None

        with self.lock:
            # Check memory cache first
            if key in self.memory_cache:
                value, timestamp = self.memory_cache[key]

                # Check expiration
                if time.time() - timestamp < self.ttl:
                    # Move to end (LRU)
                    self.memory_cache.move_to_end(key)
                    self.hits += 1
                    return value
                else:
                    # Expired, remove
                    del self.memory_cache[key]

            # Check disk cache
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)

                    # Check expiration
                    if time.time() - data["timestamp"] < self.ttl:
                        # Add to memory cache
                        self._add_to_memory(key, data["value"], data["timestamp"])
                        self.hits += 1
                        return data["value"]
                    else:
                        # Expired, remove
                        cache_file.unlink()
                except Exception:
                    # Corrupted cache file, remove
                    cache_file.unlink()

            # Cache miss
            self.misses += 1
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Cache value.

        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.enabled:
            return

        timestamp = time.time()

        with self.lock:
            # Add to memory cache
            self._add_to_memory(key, value, timestamp)

            # Add to disk cache
            try:
                cache_file = self._get_cache_file(key)
                with open(cache_file, 'wb') as f:
                    pickle.dump({
                        "value": value,
                        "timestamp": timestamp
                    }, f)
            except Exception as e:
                print(f"Warning: Failed to write disk cache: {e}")

    def _add_to_memory(self, key: str, value: Any, timestamp: float) -> None:
        """
        Add item to memory cache with LRU eviction.

        Args:
            key: Cache key
            value: Cached value
            timestamp: Cache timestamp
        """
        # Add/update
        self.memory_cache[key] = (value, timestamp)
        self.memory_cache.move_to_end(key)

        # Evict oldest if over limit
        while len(self.memory_cache) > self.max_memory_items:
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]

    def clear(self) -> None:
        """Clear all caches."""
        with self.lock:
            self.memory_cache.clear()

            # Clear disk cache
            for f in self.cache_dir.glob("*"):
                if f.is_file():
                    f.unlink()

            # Reset statistics
            self.hits = 0
            self.misses = 0

    def clear_expired(self) -> int:
        """
        Clear expired cache entries.

        Returns:
            Number of entries cleared
        """
        cleared = 0
        current_time = time.time()

        with self.lock:
            # Clear expired memory cache entries
            expired_keys = [
                key for key, (_, timestamp) in self.memory_cache.items()
                if current_time - timestamp >= self.ttl
            ]
            for key in expired_keys:
                del self.memory_cache[key]
                cleared += 1

            # Clear expired disk cache entries
            for cache_file in self.cache_dir.glob("*"):
                if cache_file.is_file():
                    try:
                        with open(cache_file, 'rb') as f:
                            data = pickle.load(f)

                        if current_time - data["timestamp"] >= self.ttl:
                            cache_file.unlink()
                            cleared += 1
                    except Exception:
                        # Corrupted file, remove it
                        cache_file.unlink()
                        cleared += 1

        return cleared

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Statistics dictionary
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

            # Calculate disk cache size
            disk_cache_files = list(self.cache_dir.glob("*"))
            disk_cache_size_bytes = sum(f.stat().st_size for f in disk_cache_files if f.is_file())

            return {
                "enabled": self.enabled,
                "memory_cache_items": len(self.memory_cache),
                "disk_cache_items": len(disk_cache_files),
                "disk_cache_size_mb": disk_cache_size_bytes / (1024 * 1024),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_percent": hit_rate,
                "ttl_seconds": self.ttl,
                "max_memory_items": self.max_memory_items
            }

    def _get_cache_file(self, key: str) -> Path:
        """
        Get cache file path for key.

        Args:
            key: Cache key

        Returns:
            Cache file path
        """
        return self.cache_dir / self._hash_key(key)

    def _hash_key(self, key: str) -> str:
        """
        Hash key for filename.

        Args:
            key: Cache key

        Returns:
            Hashed filename
        """
        return hashlib.sha256(key.encode()).hexdigest()

    def enable(self) -> None:
        """Enable caching."""
        self.enabled = True

    def disable(self) -> None:
        """Disable caching."""
        self.enabled = False

    def get_memory_cache_keys(self) -> list:
        """
        Get all keys in memory cache.

        Returns:
            List of cache keys
        """
        with self.lock:
            return list(self.memory_cache.keys())

    def get_disk_cache_size(self) -> int:
        """
        Get disk cache size in bytes.

        Returns:
            Size in bytes
        """
        with self.lock:
            return sum(
                f.stat().st_size
                for f in self.cache_dir.glob("*")
                if f.is_file()
            )


class EmbeddingCache:
    """Specialized cache for embeddings."""

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize embedding cache.

        Args:
            cache_manager: Underlying cache manager
        """
        self.cache = cache_manager

    def get_or_compute(self, text: str, compute_func: callable) -> Any:
        """
        Get cached embedding or compute and cache it.

        Args:
            text: Text to embed
            compute_func: Function to compute embedding

        Returns:
            Embedding vector
        """
        cache_key = f"embedding:{self._hash_text(text)}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Compute and cache
        embedding = compute_func(text)
        self.cache.set(cache_key, embedding)

        return embedding

    def _hash_text(self, text: str) -> str:
        """
        Hash text for cache key.

        Args:
            text: Text to hash

        Returns:
            Hash string
        """
        return hashlib.sha256(text.encode()).hexdigest()[:16]


class QueryCache:
    """Specialized cache for query results."""

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize query cache.

        Args:
            cache_manager: Underlying cache manager
        """
        self.cache = cache_manager

    def get_query_result(self, query: str, context: Optional[Dict] = None) -> Optional[str]:
        """
        Get cached query result.

        Args:
            query: Query string
            context: Optional context

        Returns:
            Cached result or None
        """
        cache_key = self._make_query_key(query, context)
        return self.cache.get(cache_key)

    def set_query_result(self, query: str, result: str, context: Optional[Dict] = None) -> None:
        """
        Cache query result.

        Args:
            query: Query string
            result: Query result
            context: Optional context
        """
        cache_key = self._make_query_key(query, context)
        self.cache.set(cache_key, result)

    def _make_query_key(self, query: str, context: Optional[Dict]) -> str:
        """
        Make cache key for query.

        Args:
            query: Query string
            context: Optional context

        Returns:
            Cache key
        """
        if context:
            # Include context in key
            context_str = json.dumps(context, sort_keys=True)
            return f"query:{query}::{context_str}"
        else:
            return f"query:{query}"


# Global cache manager instance
_global_cache = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    return _global_cache


if __name__ == "__main__":
    # Example usage
    cache = CacheManager(cache_dir="./test_cache", ttl_seconds=10)

    # Test basic caching
    print("Setting values...")
    cache.set("key1", "value1")
    cache.set("key2", {"data": "value2"})
    cache.set("key3", [1, 2, 3])

    print("\nGetting values...")
    print(f"key1: {cache.get('key1')}")
    print(f"key2: {cache.get('key2')}")
    print(f"key3: {cache.get('key3')}")
    print(f"key4 (not cached): {cache.get('key4')}")

    # Check stats
    print("\nCache stats:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test expiration
    print("\nWaiting for expiration...")
    time.sleep(11)
    print(f"key1 after expiration: {cache.get('key1')}")

    # Final stats
    print("\nFinal stats:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Cleanup
    import shutil
    shutil.rmtree("./test_cache")
