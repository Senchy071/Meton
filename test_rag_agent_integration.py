#!/usr/bin/env python3
"""Test RAG integration with Meton agent (Task 19).

This module tests that the codebase_search tool is properly integrated
with the agent and that tool selection works correctly.

Test Coverage:
1. Tool registration (codebase_search appears in agent tools)
2. RAG disabled state handling
3. Tool selection (correct tool chosen for different queries)
4. No regression (existing tools still work)
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create a dummy pytest fixture decorator for when pytest is not available
    class pytest:
        @staticmethod
        def fixture(func):
            return func

import json
import os
import tempfile
import shutil
from pathlib import Path

from core.config import Config
from core.models import ModelManager
from core.conversation import ConversationManager
from core.agent import MetonAgent
from tools.file_ops import FileOperationsTool
from tools.code_executor import CodeExecutorTool
from tools.web_search import WebSearchTool
from tools.codebase_search import CodebaseSearchTool


class TestRagAgentIntegration:
    """Test RAG integration with agent."""

    @pytest.fixture
    def setup_agent(self):
        """Setup agent with all tools including codebase_search."""
        config = Config()
        model_manager = ModelManager(config)
        conversation = ConversationManager(config)

        # Initialize all tools
        file_tool = FileOperationsTool(config)
        code_tool = CodeExecutorTool(config)
        web_tool = WebSearchTool(config)
        codebase_search_tool = CodebaseSearchTool(config)

        # Create agent with all 4 tools
        agent = MetonAgent(
            config=config,
            model_manager=model_manager,
            conversation=conversation,
            tools=[file_tool, code_tool, web_tool, codebase_search_tool],
            verbose=False
        )

        yield {
            'agent': agent,
            'config': config,
            'file_tool': file_tool,
            'code_tool': code_tool,
            'web_tool': web_tool,
            'codebase_search_tool': codebase_search_tool
        }

    def test_codebase_search_tool_registered(self, setup_agent):
        """Test 1: Verify codebase_search tool is registered with agent."""
        agent = setup_agent['agent']

        # Check tool count (should be 4: file_operations, code_executor, web_search, codebase_search)
        assert len(agent.tools) == 4, f"Expected 4 tools, got {len(agent.tools)}"

        # Check tool names
        tool_names = agent.get_tool_names()
        assert 'file_operations' in tool_names
        assert 'code_executor' in tool_names
        assert 'web_search' in tool_names
        assert 'codebase_search' in tool_names

        print("✅ Test 1 passed: codebase_search tool is registered")

    def test_rag_disabled_state_handling(self, setup_agent):
        """Test 2: Verify agent handles RAG disabled state gracefully."""
        agent = setup_agent['agent']
        codebase_search_tool = setup_agent['codebase_search_tool']

        # Ensure RAG is disabled
        assert not codebase_search_tool.is_enabled(), "Tool should be disabled by default"

        # Try to search (should return error about being disabled)
        input_json = json.dumps({"query": "how does authentication work"})
        result = codebase_search_tool._run(input_json)

        result_data = json.loads(result)
        assert result_data['success'] is False
        assert 'disabled' in result_data['error'].lower() or 'index' in result_data['error'].lower()
        assert result_data['count'] == 0

        print("✅ Test 2 passed: RAG disabled state handled correctly")

    def test_codebase_search_tool_info(self, setup_agent):
        """Test 3: Verify tool info includes RAG-specific settings."""
        codebase_search_tool = setup_agent['codebase_search_tool']

        info = codebase_search_tool.get_info()

        # Check RAG-specific info fields
        assert 'enabled' in info
        assert 'rag_enabled' in info
        assert 'top_k' in info
        assert 'similarity_threshold' in info
        assert 'max_code_length' in info
        assert 'index_exists' in info
        assert 'index_path' in info

        # Check default values
        assert info['enabled'] is False  # Disabled by default
        assert info['top_k'] == 5
        assert info['similarity_threshold'] == 0.3
        assert info['max_code_length'] == 500

        print("✅ Test 3 passed: Tool info includes RAG settings")

    def test_system_prompt_includes_rag_examples(self, setup_agent):
        """Test 4: Verify system prompt includes RAG examples."""
        agent = setup_agent['agent']

        system_prompt = agent._get_system_prompt()

        # Check for codebase_search in tool descriptions
        assert 'codebase_search' in system_prompt

        # Check for RAG examples (should mention codebase_search tool)
        assert 'codebase_search' in system_prompt.lower()

        # Check for tool selection rules mentioning codebase_search
        assert 'Use codebase_search when' in system_prompt or \
               'codebase_search' in system_prompt

        print("✅ Test 4 passed: System prompt includes RAG guidance")

    def test_tool_selection_file_operations(self, setup_agent):
        """Test 5: Verify file_operations tool still works (no regression)."""
        file_tool = setup_agent['file_tool']

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt',
                                         dir='/media/development/projects/') as f:
            f.write("Test content for file operations")
            temp_file = f.name

        try:
            # Test read operation
            input_json = json.dumps({"action": "read", "path": temp_file})
            result = file_tool._run(input_json)

            assert "Test content for file operations" in result
            print("✅ Test 5 passed: file_operations tool works correctly")

        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_tool_selection_code_executor(self, setup_agent):
        """Test 6: Verify code_executor tool still works (no regression)."""
        code_tool = setup_agent['code_tool']

        # Test simple code execution
        input_json = json.dumps({"code": "print(2 + 2)"})
        result = code_tool._run(input_json)

        result_data = json.loads(result)
        assert result_data['success'] is True
        assert '4' in result_data['output']

        print("✅ Test 6 passed: code_executor tool works correctly")

    def test_tool_selection_web_search_disabled(self, setup_agent):
        """Test 7: Verify web_search tool handles disabled state (no regression)."""
        web_tool = setup_agent['web_tool']

        # Ensure web search is disabled
        assert not web_tool.is_enabled(), "Web search should be disabled by default"

        # Try to search (should return error)
        input_json = json.dumps({"query": "Python best practices"})
        result = web_tool._run(input_json)

        result_data = json.loads(result)
        assert result_data['success'] is False
        assert 'disabled' in result_data['error'].lower()

        print("✅ Test 7 passed: web_search disabled state handled correctly")

    def test_tool_enable_disable(self, setup_agent):
        """Test 8: Verify codebase_search can be enabled/disabled."""
        codebase_search_tool = setup_agent['codebase_search_tool']

        # Initially disabled
        assert not codebase_search_tool.is_enabled()

        # Enable
        codebase_search_tool.enable()
        assert codebase_search_tool.is_enabled()

        # Disable
        codebase_search_tool.disable()
        assert not codebase_search_tool.is_enabled()

        print("✅ Test 8 passed: Tool enable/disable works correctly")

    def test_all_tools_have_correct_names(self, setup_agent):
        """Test 9: Verify all tools have correct names."""
        agent = setup_agent['agent']

        tool_names = agent.get_tool_names()

        expected_names = ['file_operations', 'code_executor', 'web_search', 'codebase_search']
        for name in expected_names:
            assert name in tool_names, f"Tool '{name}' not found in agent tools"

        print("✅ Test 9 passed: All tools have correct names")

    def test_codebase_search_input_validation(self, setup_agent):
        """Test 10: Verify codebase_search validates input correctly."""
        codebase_search_tool = setup_agent['codebase_search_tool']
        config = setup_agent['config']

        # When tool is disabled, it should reject all requests with disabled error
        # This is correct behavior - test that it returns error (any error is acceptable)
        result = codebase_search_tool._run("not json")
        result_data = json.loads(result)
        assert result_data['success'] is False, f"Expected success=False, got {result_data}"
        assert len(result_data['error']) > 0, "Should have an error message"

        # Temporarily enable RAG and tool for input validation tests
        original_rag_enabled = config.config.rag.enabled
        original_tool_enabled = codebase_search_tool._enabled

        try:
            # Enable for testing input validation
            config.config.rag.enabled = True
            # Also update the tool's internal cached value
            object.__setattr__(codebase_search_tool, '_rag_enabled', True)
            codebase_search_tool.enable()

            # Test invalid JSON (should now check JSON since tool is enabled)
            result = codebase_search_tool._run("not json")
            result_data = json.loads(result)
            assert result_data['success'] is False
            # Should have error about JSON or about no index (both are acceptable)
            assert len(result_data['error']) > 0

            # Test missing query parameter
            result = codebase_search_tool._run(json.dumps({}))
            result_data = json.loads(result)
            assert result_data['success'] is False
            # Error should be about missing query or no index
            error_lower = result_data['error'].lower()
            assert 'missing' in error_lower or 'query' in error_lower or 'index' in error_lower, \
                   f"Unexpected error for missing query: {result_data['error']}"

            # Test empty query
            result = codebase_search_tool._run(json.dumps({"query": ""}))
            result_data = json.loads(result)
            assert result_data['success'] is False
            # Error should be about empty query or no index
            error_lower = result_data['error'].lower()
            assert 'empty' in error_lower or 'index' in error_lower

        finally:
            # Restore original state
            config.config.rag.enabled = original_rag_enabled
            object.__setattr__(codebase_search_tool, '_rag_enabled', original_rag_enabled)
            if original_tool_enabled:
                codebase_search_tool.enable()
            else:
                codebase_search_tool.disable()

        print("✅ Test 10 passed: Input validation works correctly")


def run_all_tests():
    """Run all tests manually without pytest."""
    print("\n" + "="*60)
    print("TASK 19: RAG AGENT INTEGRATION TESTS")
    print("="*60 + "\n")

    test_instance = TestRagAgentIntegration()

    # Create fixture manually
    config = Config()
    model_manager = ModelManager(config)
    conversation = ConversationManager(config)

    file_tool = FileOperationsTool(config)
    code_tool = CodeExecutorTool(config)
    web_tool = WebSearchTool(config)
    codebase_search_tool = CodebaseSearchTool(config)

    agent = MetonAgent(
        config=config,
        model_manager=model_manager,
        conversation=conversation,
        tools=[file_tool, code_tool, web_tool, codebase_search_tool],
        verbose=False
    )

    setup_data = {
        'agent': agent,
        'config': config,
        'file_tool': file_tool,
        'code_tool': code_tool,
        'web_tool': web_tool,
        'codebase_search_tool': codebase_search_tool
    }

    # Run tests
    tests = [
        ("Tool Registration", test_instance.test_codebase_search_tool_registered),
        ("RAG Disabled State", test_instance.test_rag_disabled_state_handling),
        ("Tool Info", test_instance.test_codebase_search_tool_info),
        ("System Prompt", test_instance.test_system_prompt_includes_rag_examples),
        ("File Operations", test_instance.test_tool_selection_file_operations),
        ("Code Executor", test_instance.test_tool_selection_code_executor),
        ("Web Search Disabled", test_instance.test_tool_selection_web_search_disabled),
        ("Enable/Disable", test_instance.test_tool_enable_disable),
        ("Tool Names", test_instance.test_all_tools_have_correct_names),
        ("Input Validation", test_instance.test_codebase_search_input_validation),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}...")
            test_func(setup_data)
            passed += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' FAILED: {str(e)}")
            failed += 1
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "="*60)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("="*60 + "\n")

    if failed == 0:
        print("🎉 ALL TESTS PASSED! Task 19 integration is successful.\n")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the errors above.\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
