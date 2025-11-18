#!/usr/bin/env python3
"""
End-to-End Integration Tests

Tests complete workflows and integration between components.
"""

import sys
import os
import time
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import ConfigLoader
from core.models import ModelManager
from core.conversation import ConversationManager
from tools.file_ops import FileOperationsTool
from optimization.cache_manager import CacheManager
from optimization.profiler import PerformanceProfiler


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_workflow(self):
        """Test 1: Complete user workflow with all components."""
        print("\n📝 Test 1: Complete user workflow")

        # Setup
        config = ConfigLoader("config.yaml")
        assert config.config is not None

        # Test model manager
        model_mgr = ModelManager(config.config.models)
        assert model_mgr is not None

        # Test conversation
        conv_mgr = ConversationManager(config.config.conversation)
        conv_mgr.add_message("user", "Hello")
        conv_mgr.add_message("assistant", "Hi there!")
        assert len(conv_mgr.get_history()) == 2

        # Test file operations
        file_tool = FileOperationsTool(config.config.tools.file_ops)
        result = file_tool._run('{"action": "exists", "path": "config.yaml"}')
        assert "exists" in result.lower()

        print("   ✅ Complete workflow works")

    def test_optimization_integration(self):
        """Test 2: Optimization components integration."""
        print("\n📝 Test 2: Optimization integration")

        # Test cache
        cache = CacheManager(cache_dir="./test_cache_e2e", ttl_seconds=10)
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        # Test profiler
        profiler = PerformanceProfiler()
        profiler.add_profile("test_operation", 1.5)
        stats = profiler.get_stats()
        assert stats["function_profiles"] > 0

        # Cleanup
        cache.clear()
        shutil.rmtree("./test_cache_e2e", ignore_errors=True)

        print("   ✅ Optimization integration works")

    def test_config_persistence(self):
        """Test 3: Configuration loading and persistence."""
        print("\n📝 Test 3: Configuration persistence")

        # Load config
        config = ConfigLoader("config.yaml")
        assert config.config.project.name == "Meton"
        assert config.config.agent.max_iterations >= 1

        # Check optimization config
        assert hasattr(config.config, "optimization")
        assert config.config.optimization.enabled is True

        print("   ✅ Configuration persistence works")

    def test_conversation_persistence(self):
        """Test 4: Conversation save and load."""
        print("\n📝 Test 4: Conversation persistence")

        # Create conversation
        config = ConfigLoader("config.yaml")
        conv_mgr = ConversationManager(config.config.conversation)

        conv_mgr.add_message("user", "Test message 1")
        conv_mgr.add_message("assistant", "Response 1")

        # Save
        conv_mgr.save()
        session_id = conv_mgr.session_id

        # Load new conversation with same ID
        conv_mgr2 = ConversationManager(config.config.conversation, session_id=session_id)
        history = conv_mgr2.get_history()

        assert len(history) >= 2
        assert any("Test message 1" in msg.get("content", "") for msg in history)

        print("   ✅ Conversation persistence works")

    def test_error_recovery(self):
        """Test 5: Error handling and recovery."""
        print("\n📝 Test 5: Error recovery")

        # Test invalid file operation
        config = ConfigLoader("config.yaml")
        file_tool = FileOperationsTool(config.config.tools.file_ops)

        # Invalid action
        result = file_tool._run('{"action": "invalid_action", "path": "test.txt"}')
        assert "error" in result.lower() or "invalid" in result.lower()

        # Valid operation after error
        result = file_tool._run('{"action": "exists", "path": "config.yaml"}')
        assert "exists" in result.lower()

        print("   ✅ Error recovery works")

    def test_multi_component_integration(self):
        """Test 6: Multiple components working together."""
        print("\n📝 Test 6: Multi-component integration")

        config = ConfigLoader("config.yaml")

        # Models + Conversation
        model_mgr = ModelManager(config.config.models)
        conv_mgr = ConversationManager(config.config.conversation)

        conv_mgr.add_message("user", "Test")
        assert len(conv_mgr.get_history()) > 0

        # File ops + Cache
        cache = CacheManager(cache_dir="./test_cache_multi", ttl_seconds=10)
        file_tool = FileOperationsTool(config.config.tools.file_ops)

        # Cache file operation result
        cache_key = "file_exists_config"
        cached = cache.get(cache_key)

        if not cached:
            result = file_tool._run('{"action": "exists", "path": "config.yaml"}')
            cache.set(cache_key, result)

        # Should be cached now
        cached = cache.get(cache_key)
        assert cached is not None

        # Cleanup
        cache.clear()
        shutil.rmtree("./test_cache_multi", ignore_errors=True)

        print("   ✅ Multi-component integration works")

    def test_performance_tracking(self):
        """Test 7: Performance tracking integration."""
        print("\n📝 Test 7: Performance tracking")

        profiler = PerformanceProfiler()

        # Simulate operations
        for i in range(5):
            start = time.time()
            time.sleep(0.01)  # Simulate work
            duration = time.time() - start
            profiler.add_profile("test_operation", duration)

        stats = profiler.get_stats()
        assert stats["function_profiles"] == 1
        assert stats["total_functions_called"] == 5

        # Generate report
        report = profiler.generate_profile_report()
        assert "test_operation" in report

        print("   ✅ Performance tracking works")


def run_all_tests():
    """Run all end-to-end integration tests."""
    print("=" * 80)
    print("END-TO-END INTEGRATION TESTS")
    print("=" * 80)

    test_suite = TestEndToEnd()
    tests = [
        test_suite.test_complete_workflow,
        test_suite.test_optimization_integration,
        test_suite.test_config_persistence,
        test_suite.test_conversation_persistence,
        test_suite.test_error_recovery,
        test_suite.test_multi_component_integration,
        test_suite.test_performance_tracking,
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
        print("\n✅ All end-to-end integration tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
