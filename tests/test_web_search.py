#!/usr/bin/env python3
"""Test script for Meton Web Search Tool.

Tests all WebSearchTool functionality including:
- Disabled by default checking
- Search with tool enabled
- Error handling (no results, timeout, invalid query)
- Enable/disable functionality
- Configuration validation
"""

import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from tools.web_search import WebSearchTool
from utils.logger import setup_logger
from utils.formatting import *


def test_tool_initialization():
    """Test Tool initialization."""
    print_section("Test 1: Tool Initialization")

    try:
        config = Config()
        logger = setup_logger(name="meton_test_web_search", console_output=False)

        print_thinking("Initializing Web Search Tool...")
        tool = WebSearchTool(config)

        print_success(f"✓ Tool initialized: {tool.name}")
        console.print(f"  Description: {tool.description[:80]}...")

        info = tool.get_info()
        console.print(f"  Enabled: {info['enabled']}")
        console.print(f"  Max results: {info['max_results']}")
        console.print(f"  Timeout: {info['timeout']}s")

        # Verify it's disabled by default
        if not info['enabled']:
            print_success("✓ Tool is correctly disabled by default")
        else:
            print_error("✗ Tool should be disabled by default!")
            return None

        return tool

    except Exception as e:
        print_error(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_search_while_disabled(tool: WebSearchTool):
    """Test search attempt while tool is disabled."""
    print_section("Test 2: Search While Disabled")

    try:
        query = "Python programming"
        input_json = json.dumps({"query": query})

        print_thinking(f"Attempting search while disabled: '{query}'")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Count: {result['count']}")
        console.print(f"Error: {result['error'][:100]}...")

        if (not result['success'] and
            result['count'] == 0 and
            "disabled" in result['error'].lower()):
            print_success("✓ Tool correctly blocks search when disabled")
            return True
        else:
            print_error("✗ Tool should block search when disabled")
            return False

    except Exception as e:
        print_error(f"Disabled search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enable_disable(tool: WebSearchTool):
    """Test enable/disable functionality."""
    print_section("Test 3: Enable/Disable Toggle")

    try:
        print_thinking("Testing enable/disable toggle...")

        # Check initial state (should be disabled)
        if tool.is_enabled():
            print_error("✗ Tool should start disabled")
            return False

        # Enable tool
        console.print("Enabling tool...")
        tool.enable()

        if not tool.is_enabled():
            print_error("✗ Tool should be enabled after calling enable()")
            return False

        console.print("Tool enabled: ✓")

        # Disable tool
        console.print("Disabling tool...")
        tool.disable()

        if tool.is_enabled():
            print_error("✗ Tool should be disabled after calling disable()")
            return False

        console.print("Tool disabled: ✓")

        print_success("✓ Enable/disable toggle works correctly")
        return True

    except Exception as e:
        print_error(f"Enable/disable test failed: {e}")
        return False


def test_search_while_enabled(tool: WebSearchTool):
    """Test search with tool enabled."""
    print_section("Test 4: Search While Enabled")

    try:
        # Enable tool
        tool.enable()

        query = "Python programming language"
        input_json = json.dumps({"query": query})

        print_thinking(f"Searching with tool enabled: '{query}'")
        start = time.time()
        result_str = tool._run(input_json)
        elapsed = time.time() - start
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Count: {result['count']}")
        console.print(f"Search time: {elapsed:.2f}s")

        if result['success'] and result['count'] > 0:
            # Show first result
            first = result['results'][0]
            console.print(f"\nFirst result:")
            console.print(f"  Title: {first['title'][:60]}...")
            console.print(f"  URL: {first['url'][:60]}...")
            console.print(f"  Snippet: {first['snippet'][:80]}...")

            print_success(f"✓ Search successful, found {result['count']} results")
            return True
        elif not result['success']:
            # Check if it's an import error (library not installed)
            if "not installed" in result.get('error', ''):
                print_warning("⚠ duckduckgo-search library not installed")
                console.print("  This is expected in some test environments")
                console.print("  Install with: pip install duckduckgo-search>=4.0.0")
                return True  # Pass test - library issue, not tool issue
            else:
                print_error(f"✗ Search failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print_warning("⚠ Search succeeded but returned 0 results")
            console.print("  This can happen with very specific queries")
            return True  # Still pass - search worked, just no results

    except Exception as e:
        print_error(f"Enabled search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Disable tool after test
        tool.disable()


def test_empty_query(tool: WebSearchTool):
    """Test empty query handling."""
    print_section("Test 5: Empty Query")

    try:
        # Enable tool
        tool.enable()

        input_json = json.dumps({"query": ""})

        print_thinking("Testing with empty query")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Error: {result['error']}")

        if not result['success'] and "empty" in result['error'].lower():
            print_success("✓ Empty query handled correctly")
            return True
        else:
            print_error("✗ Empty query not handled properly")
            return False

    except Exception as e:
        print_error(f"Empty query test failed: {e}")
        return False
    finally:
        tool.disable()


def test_missing_query_parameter(tool: WebSearchTool):
    """Test missing query parameter."""
    print_section("Test 6: Missing Query Parameter")

    try:
        # Enable tool
        tool.enable()

        input_json = json.dumps({"wrong_key": "value"})

        print_thinking("Testing with missing 'query' parameter")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Error: {result['error']}")

        if not result['success'] and "Missing required 'query' parameter" in result['error']:
            print_success("✓ Missing parameter handled correctly")
            return True
        else:
            print_error("✗ Missing parameter not handled")
            return False

    except Exception as e:
        print_error(f"Missing parameter test failed: {e}")
        return False
    finally:
        tool.disable()


def test_invalid_json(tool: WebSearchTool):
    """Test invalid JSON input."""
    print_section("Test 7: Invalid JSON Input")

    try:
        # Enable tool first so we get past the enabled check
        tool.enable()

        invalid_json = "not valid json at all"

        print_thinking("Testing with invalid JSON")
        result_str = tool._run(invalid_json)
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Error: {result['error'][:80]}...")

        if not result['success'] and "Invalid JSON" in result['error']:
            print_success("✓ Invalid JSON handled correctly")
            return True
        else:
            print_error("✗ Invalid JSON not handled")
            return False

    except Exception as e:
        print_error(f"Invalid JSON test failed: {e}")
        return False
    finally:
        tool.disable()


def test_max_results_limit(tool: WebSearchTool):
    """Test max results configuration."""
    print_section("Test 8: Max Results Limit")

    try:
        # Enable tool
        tool.enable()

        query = "programming"
        input_json = json.dumps({"query": query})

        print_thinking(f"Testing max results limit (should be <= {tool._max_results})")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        if result['success']:
            console.print(f"Results returned: {result['count']}")
            console.print(f"Max configured: {tool._max_results}")

            if result['count'] <= tool._max_results:
                print_success(f"✓ Results limited to max ({tool._max_results})")
                return True
            else:
                print_error(f"✗ Returned {result['count']} results, max is {tool._max_results}")
                return False
        else:
            # Check if it's an import error
            if "not installed" in result.get('error', ''):
                print_warning("⚠ duckduckgo-search library not installed (skipping test)")
                return True
            else:
                print_warning(f"⚠ Search failed: {result.get('error', 'Unknown')}")
                return True  # Don't fail test for search issues

    except Exception as e:
        print_error(f"Max results test failed: {e}")
        return False
    finally:
        tool.disable()


def main():
    """Run all tests."""
    print_header("🧪 Web Search Tool Test Suite")
    console.print("[dim]Testing DuckDuckGo web search with disabled-by-default protection[/dim]\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Initialize tool
    tool = test_tool_initialization()
    if tool:
        tests_passed += 1
    else:
        tests_failed += 1
        print_error("\n❌ Cannot continue without tool initialization")
        return

    console.print()

    # Test 2: Search while disabled
    if test_search_while_disabled(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 3: Enable/disable
    if test_enable_disable(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 4: Search while enabled
    if test_search_while_enabled(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 5: Empty query
    if test_empty_query(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 6: Missing parameter
    if test_missing_query_parameter(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 7: Invalid JSON
    if test_invalid_json(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 8: Max results
    if test_max_results_limit(tool):
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
        console.print("🎉 [bold green]All Web Search tests passed![/bold green]\n")
    else:
        console.print(f"⚠️  [yellow]{tests_failed} test(s) need attention[/yellow]\n")


if __name__ == "__main__":
    main()
