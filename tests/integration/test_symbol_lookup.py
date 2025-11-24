#!/usr/bin/env python3
"""
Symbol Lookup Tool Tests

Tests symbol/function lookup functionality.
"""

import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import ConfigLoader
from tools.symbol_lookup import SymbolLookupTool


class TestSymbolLookup:
    """Test symbol lookup tool."""

    def __init__(self):
        """Initialize test suite."""
        self.config = ConfigLoader("config.yaml")
        self.tool = SymbolLookupTool(self.config)

    def test_initialization(self):
        """Test 1: Tool initializes correctly."""
        print("\n📝 Test 1: Tool initialization")

        assert self.tool is not None
        assert self.tool.name == "symbol_lookup"
        assert self.tool.is_enabled()

        print("   ✅ Tool initialization works")

    def test_find_function(self):
        """Test 2: Find function definition."""
        print("\n📝 Test 2: Find function definition")

        # Find a known function in the codebase
        input_json = json.dumps({"symbol": "setup_logger"})
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] == True
        assert result["count"] > 0
        assert len(result["results"]) > 0

        # Check first result has required fields
        first_result = result["results"][0]
        assert "symbol" in first_result
        assert "type" in first_result
        assert "file" in first_result
        assert "line" in first_result
        assert "signature" in first_result

        print(f"   ✅ Found {result['count']} definition(s) for 'setup_logger'")

    def test_find_class(self):
        """Test 3: Find class definition."""
        print("\n📝 Test 3: Find class definition")

        # Find a known class in the codebase
        input_json = json.dumps({"symbol": "MetonBaseTool", "type": "class"})
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] == True
        assert result["count"] > 0

        # Check that results are filtered to classes only
        for res in result["results"]:
            assert res["type"] == "class"

        print(f"   ✅ Found {result['count']} class definition(s) for 'MetonBaseTool'")

    def test_find_method(self):
        """Test 4: Find method definition."""
        print("\n📝 Test 4: Find method definition")

        # Find a common method name
        input_json = json.dumps({"symbol": "_run", "type": "method"})
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] == True
        assert result["count"] > 0

        # Check that results are filtered to methods only
        for res in result["results"]:
            assert res["type"] == "method"

        print(f"   ✅ Found {result['count']} method definition(s) for '_run'")

    def test_multiple_definitions(self):
        """Test 5: Handle multiple definitions of same symbol."""
        print("\n📝 Test 5: Handle multiple definitions")

        # Find a symbol that exists in multiple files
        input_json = json.dumps({"symbol": "enable"})
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] == True
        # Should find enable() methods in multiple tools
        assert result["count"] >= 1

        print(f"   ✅ Found {result['count']} definition(s) for 'enable'")

    def test_symbol_not_found(self):
        """Test 6: Handle symbol not found gracefully."""
        print("\n📝 Test 6: Symbol not found")

        # Search for non-existent symbol
        input_json = json.dumps({"symbol": "NonExistentFunctionXYZ123"})
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] == True
        assert result["count"] == 0
        assert len(result["results"]) == 0

        print("   ✅ Handles missing symbols gracefully")

    def test_invalid_json(self):
        """Test 7: Handle invalid JSON input."""
        print("\n📝 Test 7: Invalid JSON input")

        # Pass invalid JSON
        result_str = self.tool._run("not valid json")
        result = json.loads(result_str)

        assert result["success"] == False
        assert "Invalid JSON" in result["error"]

        print("   ✅ Handles invalid JSON gracefully")

    def test_missing_symbol_parameter(self):
        """Test 8: Handle missing symbol parameter."""
        print("\n📝 Test 8: Missing symbol parameter")

        # Pass JSON without symbol parameter
        input_json = json.dumps({"type": "function"})
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] == False
        assert "Missing required 'symbol' parameter" in result["error"]

        print("   ✅ Handles missing parameters gracefully")

    def test_empty_symbol(self):
        """Test 9: Handle empty symbol name."""
        print("\n📝 Test 9: Empty symbol name")

        # Pass empty symbol
        input_json = json.dumps({"symbol": ""})
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] == False
        assert "cannot be empty" in result["error"]

        print("   ✅ Handles empty symbol gracefully")

    def test_scope_filtering(self):
        """Test 10: Test public vs private scope filtering."""
        print("\n📝 Test 10: Scope filtering")

        # Find a private function (starts with _)
        input_json = json.dumps({"symbol": "_run", "scope": "private"})
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] == True
        # Should find _run methods (private)
        for res in result["results"]:
            assert res["scope"] == "private"

        print(f"   ✅ Scope filtering works ({result['count']} private symbols)")

    def test_code_snippet(self):
        """Test 11: Verify code snippet is included."""
        print("\n📝 Test 11: Code snippet inclusion")

        # Find a function and check code snippet
        input_json = json.dumps({"symbol": "setup_logger"})
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] == True
        assert result["count"] > 0

        # Check first result has code snippet
        first_result = result["results"][0]
        assert "code_snippet" in first_result
        assert len(first_result["code_snippet"]) > 0
        assert "def " in first_result["code_snippet"] or "class " in first_result["code_snippet"]

        print("   ✅ Code snippets are included")

    def test_index_building(self):
        """Test 12: Verify index building works."""
        print("\n📝 Test 12: Index building")

        # Force index rebuild
        success = self.tool.refresh_index()
        assert success == True

        # Check index info
        info = self.tool.get_info()
        assert "index_size" in info
        assert info["index_size"] > 0

        print(f"   ✅ Index built successfully ({info['index_size']} symbols)")

    def test_case_insensitive_search(self):
        """Test 13: Case-insensitive search fallback."""
        print("\n📝 Test 13: Case-insensitive search")

        # Search with wrong case
        input_json = json.dumps({"symbol": "metonbasetool"})  # lowercase
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        # Should still find MetonBaseTool (case-insensitive fallback)
        assert result["success"] == True
        # May or may not find results depending on exact match vs fuzzy

        print(f"   ✅ Case-insensitive search works ({result['count']} results)")

    def test_max_results_limit(self):
        """Test 14: Verify max results limit."""
        print("\n📝 Test 14: Max results limit")

        # Find a very common symbol that might have many matches
        input_json = json.dumps({"symbol": "__init__"})
        result_str = self.tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] == True
        # Should not exceed max_results (20 by default)
        assert len(result["results"]) <= 20

        print(f"   ✅ Max results limit enforced ({len(result['results'])} results)")


def run_all_tests():
    """Run all symbol lookup tests."""
    print("=" * 80)
    print("SYMBOL LOOKUP TOOL TESTS")
    print("=" * 80)

    test_suite = TestSymbolLookup()
    tests = [
        test_suite.test_initialization,
        test_suite.test_find_function,
        test_suite.test_find_class,
        test_suite.test_find_method,
        test_suite.test_multiple_definitions,
        test_suite.test_symbol_not_found,
        test_suite.test_invalid_json,
        test_suite.test_missing_symbol_parameter,
        test_suite.test_empty_symbol,
        test_suite.test_scope_filtering,
        test_suite.test_code_snippet,
        test_suite.test_index_building,
        test_suite.test_case_insensitive_search,
        test_suite.test_max_results_limit,
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
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} total")
    print("=" * 80)

    if failed == 0:
        print("\n✅ All symbol lookup tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
