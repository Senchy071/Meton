#!/usr/bin/env python3
"""
User Scenario Tests

Tests real-world user workflows and scenarios.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import ConfigLoader
from core.conversation import ConversationManager
from optimization.cache_manager import CacheManager
from optimization.query_optimizer import QueryOptimizer


class TestUserScenarios:
    """Real-world user scenario tests."""

    def test_new_user_onboarding(self):
        """Test 1: New user onboarding flow."""
        print("\n📝 Test 1: New user onboarding")

        # User loads configuration
        config = ConfigLoader("config.yaml")
        assert config.config is not None

        # User starts conversation
        conv = ConversationManager(config.config.conversation)
        conv.add_message("user", "How do I get started?")

        assert len(conv.get_history()) > 0

        print("   ✅ New user onboarding works")

    def test_development_workflow(self):
        """Test 2: Daily development workflow."""
        print("\n📝 Test 2: Development workflow")

        config = ConfigLoader("config.yaml")
        conv = ConversationManager(config.config.conversation)

        # Morning: Start work
        conv.add_message("user", "Review yesterday's changes")
        conv.add_message("assistant", "Reviewing changes...")

        # Write code and ask for help
        conv.add_message("user", "How should I implement authentication?")
        conv.add_message("assistant", "Here's how to implement authentication...")

        # Review implementation
        conv.add_message("user", "Review my auth code")
        conv.add_message("assistant", "Reviewing your authentication code...")

        assert len(conv.get_history()) == 6

        print("   ✅ Development workflow works")

    def test_research_workflow(self):
        """Test 3: Research and analysis workflow."""
        print("\n📝 Test 3: Research workflow")

        config = ConfigLoader("config.yaml")
        optimizer = QueryOptimizer()

        # Research query
        query = "Compare FastAPI vs Flask for web development"
        query_type = optimizer.classify_query(query)

        assert query_type == "research"

        # Should suggest web search
        tools = optimizer.optimize_tool_selection(query)
        assert "web_search" in tools

        print("   ✅ Research workflow works")

    def test_debugging_workflow(self):
        """Test 4: Debugging workflow."""
        print("\n📝 Test 4: Debugging workflow")

        optimizer = QueryOptimizer()

        # Debug query
        query = "Debug this KeyError in my code"
        query_type = optimizer.classify_query(query)

        assert query_type == "debugging"

        # Should suggest appropriate tools
        tools = optimizer.optimize_tool_selection(query)
        assert len(tools) > 0

        print("   ✅ Debugging workflow works")

    def test_optimization_workflow(self):
        """Test 5: Performance optimization workflow."""
        print("\n📝 Test 5: Optimization workflow")

        # User enables caching
        cache = CacheManager(cache_dir="./test_cache_scenario", ttl_seconds=10)

        # First query (cache miss)
        result1 = cache.get("expensive_operation")
        assert result1 is None

        # Cache result
        cache.set("expensive_operation", "result")

        # Second query (cache hit)
        result2 = cache.get("expensive_operation")
        assert result2 == "result"

        # Check stats
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

        # Cleanup
        cache.clear()
        import shutil
        shutil.rmtree("./test_cache_scenario", ignore_errors=True)

        print("   ✅ Optimization workflow works")


def run_all_tests():
    """Run all user scenario tests."""
    print("=" * 80)
    print("USER SCENARIO TESTS")
    print("=" * 80)

    test_suite = TestUserScenarios()
    tests = [
        test_suite.test_new_user_onboarding,
        test_suite.test_development_workflow,
        test_suite.test_research_workflow,
        test_suite.test_debugging_workflow,
        test_suite.test_optimization_workflow,
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
        print("\n✅ All user scenario tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
