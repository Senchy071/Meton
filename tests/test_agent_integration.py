#!/usr/bin/env python3
"""Test script for Agent integration with new tools.

Tests that the agent can use:
- Code execution tool
- Web search tool (disabled by default)
- File operations tool (existing, verify still works)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.models import ModelManager
from core.conversation import ConversationManager
from core.agent import MetonAgent
from tools.file_ops import FileOperationsTool
from tools.code_executor import CodeExecutorTool
from tools.web_search import WebSearchTool
from utils.logger import setup_logger
from utils.formatting import *


def test_agent_initialization():
    """Test that agent initializes with all three tools."""
    print_section("Test 1: Agent Initialization with New Tools")

    try:
        config = Config()
        logger = setup_logger(name="test_agent_integration", console_output=False)

        print_thinking("Initializing components...")
        model_manager = ModelManager(config, logger=logger)
        conversation = ConversationManager(config, logger=logger)

        # Create all tools
        file_tool = FileOperationsTool(config)
        code_tool = CodeExecutorTool(config)
        web_tool = WebSearchTool(config)

        print_thinking("Creating agent with 3 tools...")
        agent = MetonAgent(
            config=config,
            model_manager=model_manager,
            conversation=conversation,
            tools=[file_tool, code_tool, web_tool],
            verbose=False
        )

        # Verify tools are registered
        console.print(f"  Tools registered: {list(agent.tool_map.keys())}")

        expected_tools = {'file_operations', 'code_executor', 'web_search'}
        actual_tools = set(agent.tool_map.keys())

        if expected_tools == actual_tools:
            print_success(f"✓ Agent initialized with all 3 tools: {actual_tools}")
            return agent
        else:
            print_error(f"✗ Expected {expected_tools}, got {actual_tools}")
            return None

    except Exception as e:
        print_error(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_code_execution_simple(agent: MetonAgent):
    """Test agent using code_executor tool."""
    print_section("Test 2: Code Execution via Agent")

    try:
        query = "Run this code: print('hello world')"

        print_thinking(f"Asking agent: '{query}'")
        console.print(f"[dim]Note: Using verbose=False, so agent thinking is hidden[/dim]\n")

        result = agent.run(query)

        console.print(f"Success: {result.get('success', False)}")
        console.print(f"Output preview: {result.get('output', '')[:200]}...")

        # Check if agent actually used code_executor tool
        tool_calls = result.get('tool_calls', [])
        used_code_executor = any(
            tc.get('tool_name') == 'code_executor'
            for tc in tool_calls
        )

        if used_code_executor:
            print_success("✓ Agent successfully used code_executor tool")
            return True
        else:
            print_warning("⚠ Agent did not use code_executor tool")
            console.print(f"  Tools used: {[tc.get('tool_name') for tc in tool_calls]}")
            return False

    except Exception as e:
        print_error(f"Code execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_search_disabled(agent: MetonAgent):
    """Test agent handling web search when disabled."""
    print_section("Test 3: Web Search (Disabled) via Agent")

    try:
        query = "Search for Python tutorials"

        print_thinking(f"Asking agent: '{query}'")
        console.print(f"[dim]Web search is disabled by default in config[/dim]\n")

        result = agent.run(query)

        console.print(f"Success: {result.get('success', False)}")
        output = result.get('output', '')
        console.print(f"Output preview: {output[:200]}...")

        # Check if agent used web_search and got disabled error
        tool_calls = result.get('tool_calls', [])
        used_web_search = any(
            tc.get('tool_name') == 'web_search'
            for tc in tool_calls
        )

        # Check if output mentions it's disabled
        mentions_disabled = 'disabled' in output.lower()

        if used_web_search and mentions_disabled:
            print_success("✓ Agent used web_search and correctly reported it's disabled")
            return True
        elif mentions_disabled:
            print_success("✓ Agent correctly reported web search is disabled")
            return True
        else:
            print_warning("⚠ Agent may not have handled disabled web search correctly")
            console.print(f"  Tools used: {[tc.get('tool_name') for tc in tool_calls]}")
            return False

    except Exception as e:
        print_error(f"Web search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_operations(agent: MetonAgent):
    """Test that file operations still work (existing functionality)."""
    print_section("Test 4: File Operations (Verify Still Works)")

    try:
        query = "List files in the current directory"

        print_thinking(f"Asking agent: '{query}'")

        result = agent.run(query)

        console.print(f"Success: {result.get('success', False)}")
        console.print(f"Output preview: {result.get('output', '')[:200]}...")

        # Check if agent used file_operations tool
        tool_calls = result.get('tool_calls', [])
        used_file_ops = any(
            tc.get('tool_name') == 'file_operations'
            for tc in tool_calls
        )

        if used_file_ops:
            print_success("✓ Agent successfully used file_operations tool (existing tool still works)")
            return True
        else:
            print_error("✗ Agent did not use file_operations tool")
            console.print(f"  Tools used: {[tc.get('tool_name') for tc in tool_calls]}")
            return False

    except Exception as e:
        print_error(f"File operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print_header("🧪 Agent Integration Test Suite")
    console.print("[dim]Testing agent with code_executor, web_search, and file_operations tools[/dim]\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Initialize agent
    agent = test_agent_initialization()
    if agent:
        tests_passed += 1
    else:
        tests_failed += 1
        print_error("\n❌ Cannot continue without agent initialization")
        return

    console.print()

    # Test 2: Code execution
    if test_code_execution_simple(agent):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 3: Web search (disabled)
    if test_web_search_disabled(agent):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 4: File operations
    if test_file_operations(agent):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Summary
    print_header("📊 Test Summary")
    console.print(f"✅ Tests passed: [green]{tests_passed}[/green]")
    console.print(f"❌ Tests failed: [red]{tests_failed}[/red]")
    console.print(f"📈 Success rate: {tests_passed}/{tests_passed + tests_failed} ({100 * tests_passed // (tests_passed + tests_failed)}%)\n")

    if tests_failed == 0:
        console.print("🎉 [bold green]All Agent Integration tests passed![/bold green]\n")
    else:
        console.print(f"⚠️  [yellow]{tests_failed} test(s) need attention[/yellow]\n")


if __name__ == "__main__":
    main()
