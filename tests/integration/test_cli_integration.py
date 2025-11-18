#!/usr/bin/env python3
"""
CLI Integration Tests

Tests CLI commands and interactions.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import ConfigLoader
from optimization.cache_manager import CacheManager
from optimization.profiler import PerformanceProfiler
from optimization.resource_monitor import ResourceMonitor


class TestCLIIntegration:
    """Test CLI integration without subprocess calls."""

    def test_config_loading(self):
        """Test 1: Configuration loads correctly for CLI."""
        print("\n📝 Test 1: Config loading for CLI")

        config = ConfigLoader("config.yaml")
        assert config.config is not None
        assert config.config.project.name == "Meton"

        print("   ✅ CLI config loading works")

    def test_optimization_cli_components(self):
        """Test 2: Optimization CLI components."""
        print("\n📝 Test 2: Optimization CLI components")

        # Test profiler (for /optimize profile)
        profiler = PerformanceProfiler()
        profiler.add_profile("test_func", 1.0)
        report = profiler.generate_profile_report()
        assert "PERFORMANCE PROFILE REPORT" in report

        # Test cache (for /optimize cache stats)
        cache = CacheManager(cache_dir="./test_cache_cli", ttl_seconds=10)
        cache.set("key1", "value1")
        stats = cache.get_stats()
        assert "hits" in stats
        assert "misses" in stats

        # Test resource monitor (for /optimize resources)
        monitor = ResourceMonitor()
        usage = monitor.get_current_usage()
        assert "cpu_percent" in usage
        assert "memory_mb" in usage

        # Cleanup
        cache.clear()
        import shutil
        shutil.rmtree("./test_cache_cli", ignore_errors=True)

        print("   ✅ Optimization CLI components work")

    def test_config_profiles(self):
        """Test 3: Configuration profiles functionality."""
        print("\n📝 Test 3: Configuration profiles")

        config = ConfigLoader("config.yaml")
        assert hasattr(config.config, "profiles")

        # Check if profiles directory exists or can be created
        profiles_dir = Path(config.config.profiles.profiles_dir if hasattr(config.config, "profiles") else "config/profiles")
        if not profiles_dir.exists():
            print(f"   ℹ️  Profiles directory doesn't exist: {profiles_dir}")

        print("   ✅ Configuration profiles structure works")


def run_all_tests():
    """Run all CLI integration tests."""
    print("=" * 80)
    print("CLI INTEGRATION TESTS")
    print("=" * 80)

    test_suite = TestCLIIntegration()
    tests = [
        test_suite.test_config_loading,
        test_suite.test_optimization_cli_components,
        test_suite.test_config_profiles,
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
        print("\n✅ All CLI integration tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
