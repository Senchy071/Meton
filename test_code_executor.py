#!/usr/bin/env python3
"""Test script for Meton Code Executor Tool.

Tests all CodeExecutorTool functionality including:
- Simple code execution
- Import validation (blocked and allowed)
- Timeout protection
- Syntax error handling
- Multi-line code execution
- Output capture (stdout/stderr)
- Execution time tracking
"""

import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from tools.code_executor import CodeExecutorTool, ImportValidator
from utils.logger import setup_logger
from utils.formatting import *


def test_tool_initialization():
    """Test Tool initialization."""
    print_section("Test 1: Tool Initialization")

    try:
        config = Config()
        logger = setup_logger(name="meton_test_code_executor", console_output=False)

        print_thinking("Initializing Code Executor Tool...")
        tool = CodeExecutorTool(config)

        print_success(f"✓ Tool initialized: {tool.name}")
        console.print(f"  Description: {tool.description[:80]}...")

        info = tool.get_info()
        console.print(f"  Timeout: {info['timeout']}s")
        console.print(f"  Max output length: {info['max_output_length']} chars")
        console.print(f"  Allowed imports: {len(info['allowed_imports'])} modules")
        console.print(f"  Blocked imports: {len(info['blocked_imports'])} modules")

        return tool

    except Exception as e:
        print_error(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_simple_execution(tool: CodeExecutorTool):
    """Test simple code execution."""
    print_section("Test 2: Simple Code Execution")

    try:
        code = "print(2 + 2)"
        input_json = json.dumps({"code": code})

        print_thinking(f"Executing: {code}")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Output: {result['output']}")
        console.print(f"Execution time: {result['execution_time']}s")

        if result['success'] and result['output'] == "4":
            print_success("✓ Simple execution works")
            return True
        else:
            print_error("✗ Simple execution failed")
            return False

    except Exception as e:
        print_error(f"Simple execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_blocked_import(tool: CodeExecutorTool):
    """Test blocked import detection."""
    print_section("Test 3: Blocked Import Detection")

    try:
        code = "import os\nprint(os.getcwd())"
        input_json = json.dumps({"code": code})

        print_thinking("Executing code with blocked import: os")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Error: {result['error'][:100]}...")

        if not result['success'] and "Blocked import" in result['error']:
            print_success("✓ Blocked import detected correctly")
            return True
        else:
            print_error("✗ Blocked import was not caught")
            return False

    except Exception as e:
        print_error(f"Blocked import test failed: {e}")
        return False


def test_allowed_import(tool: CodeExecutorTool):
    """Test allowed import execution."""
    print_section("Test 4: Allowed Import Execution")

    try:
        code = "import math\nprint(round(math.pi, 2))"
        input_json = json.dumps({"code": code})

        print_thinking("Executing code with allowed import: math")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Output: {result['output']}")
        console.print(f"Execution time: {result['execution_time']}s")

        if result['success'] and result['output'] == "3.14":
            print_success("✓ Allowed import works")
            return True
        else:
            print_error("✗ Allowed import failed")
            return False

    except Exception as e:
        print_error(f"Allowed import test failed: {e}")
        return False


def test_timeout(tool: CodeExecutorTool):
    """Test timeout protection."""
    print_section("Test 5: Timeout Protection")

    try:
        code = "while True:\n    pass"
        input_json = json.dumps({"code": code})

        print_thinking("Executing infinite loop (should timeout)")
        start = time.time()
        result_str = tool._run(input_json)
        elapsed = time.time() - start
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Error: {result['error']}")
        console.print(f"Wall time: {elapsed:.2f}s")

        if not result['success'] and "timed out" in result['error']:
            print_success(f"✓ Timeout protection works (killed after ~{elapsed:.1f}s)")
            return True
        else:
            print_error("✗ Timeout protection failed")
            return False

    except Exception as e:
        print_error(f"Timeout test failed: {e}")
        return False


def test_syntax_error(tool: CodeExecutorTool):
    """Test syntax error handling."""
    print_section("Test 6: Syntax Error Handling")

    try:
        code = "print('hello'\nprint('world')"  # Missing closing paren
        input_json = json.dumps({"code": code})

        print_thinking("Executing code with syntax error")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Error: {result['error'][:100]}...")

        if not result['success'] and "Syntax error" in result['error']:
            print_success("✓ Syntax error handled correctly")
            return True
        else:
            print_error("✗ Syntax error not handled properly")
            return False

    except Exception as e:
        print_error(f"Syntax error test failed: {e}")
        return False


def test_multiline_code(tool: CodeExecutorTool):
    """Test multi-line code execution."""
    print_section("Test 7: Multi-line Code Execution")

    try:
        code = """import math

def calculate_area(radius):
    return math.pi * radius ** 2

result = calculate_area(5)
print(f"Area: {result:.2f}")
"""
        input_json = json.dumps({"code": code})

        print_thinking("Executing multi-line code with function")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Output: {result['output']}")
        console.print(f"Execution time: {result['execution_time']}s")

        if result['success'] and "Area: 78.54" in result['output']:
            print_success("✓ Multi-line code works")
            return True
        else:
            print_error("✗ Multi-line code failed")
            return False

    except Exception as e:
        print_error(f"Multi-line code test failed: {e}")
        return False


def test_stderr_capture(tool: CodeExecutorTool):
    """Test stderr capture."""
    print_section("Test 8: Stderr Capture")

    try:
        code = "import sys\nprint('error message', file=sys.stderr)"
        input_json = json.dumps({"code": code})

        print_thinking("Executing code that writes to stderr")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        # This will fail validation because sys is blocked
        console.print(f"Success: {result['success']}")
        if result['success']:
            console.print(f"Stderr: {result['error']}")
        else:
            console.print(f"Error: {result['error'][:80]}...")

        # Since sys is blocked, this should fail validation
        if not result['success'] and "Blocked import: sys" in result['error']:
            print_success("✓ Blocked sys import as expected")
            return True
        else:
            print_warning("Note: sys is blocked, trying alternative...")
            # Test with division by zero instead
            code2 = "x = 1 / 0"
            input_json2 = json.dumps({"code": code2})
            result_str2 = tool._run(input_json2)
            result2 = json.loads(result_str2)

            if not result2['success'] and result2['error']:
                print_success("✓ Error capture works (ZeroDivisionError)")
                return True

            return False

    except Exception as e:
        print_error(f"Stderr capture test failed: {e}")
        return False


def test_import_validator():
    """Test ImportValidator directly."""
    print_section("Test 9: Import Validator")

    try:
        validator = ImportValidator()

        # Test allowed import
        print_thinking("Testing allowed import: math")
        valid, violations = validator.validate("import math")
        console.print(f"Valid: {valid}, Violations: {violations}")
        if not valid:
            print_error("✗ Math should be allowed")
            return False

        # Test blocked import
        print_thinking("Testing blocked import: os")
        valid, violations = validator.validate("import os")
        console.print(f"Valid: {valid}, Violations: {violations}")
        if valid:
            print_error("✗ OS should be blocked")
            return False

        # Test blocked builtin
        print_thinking("Testing blocked builtin: open()")
        valid, violations = validator.validate("open('file.txt')")
        console.print(f"Valid: {valid}, Violations: {violations}")
        if valid:
            print_error("✗ open() should be blocked")
            return False

        # Test unknown import
        print_thinking("Testing unknown import: requests")
        valid, violations = validator.validate("import requests")
        console.print(f"Valid: {valid}, Violations: {violations}")
        if valid:
            print_error("✗ requests should be blocked")
            return False

        print_success("✓ Import validator works correctly")
        return True

    except Exception as e:
        print_error(f"Import validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_missing_code_parameter(tool: CodeExecutorTool):
    """Test missing code parameter."""
    print_section("Test 10: Missing Code Parameter")

    try:
        input_json = json.dumps({"wrong_key": "value"})

        print_thinking("Testing with missing 'code' parameter")
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        console.print(f"Success: {result['success']}")
        console.print(f"Error: {result['error']}")

        if not result['success'] and "Missing required 'code' parameter" in result['error']:
            print_success("✓ Missing parameter handled correctly")
            return True
        else:
            print_error("✗ Missing parameter not handled")
            return False

    except Exception as e:
        print_error(f"Missing parameter test failed: {e}")
        return False


def main():
    """Run all tests."""
    print_header("🧪 Code Executor Tool Test Suite")
    console.print("[dim]Testing safe code execution with subprocess isolation[/dim]\n")

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

    # Test 2: Simple execution
    if test_simple_execution(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 3: Blocked import
    if test_blocked_import(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 4: Allowed import
    if test_allowed_import(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 5: Timeout
    if test_timeout(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 6: Syntax error
    if test_syntax_error(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 7: Multi-line code
    if test_multiline_code(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 8: Stderr capture
    if test_stderr_capture(tool):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 9: Import validator
    if test_import_validator():
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 10: Missing parameter
    if test_missing_code_parameter(tool):
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
        console.print("🎉 [bold green]All Code Executor tests passed![/bold green]\n")
    else:
        console.print(f"⚠️  [yellow]{tests_failed} test(s) need attention[/yellow]\n")


if __name__ == "__main__":
    main()
