#!/usr/bin/env python3
"""
Test suite for Test Generator Skill

Tests the automatic test generation capabilities including:
- Function test generation
- Class test generation
- Edge case detection
- Error case handling
- Mock generation
- Framework support (pytest/unittest)
- Coverage levels
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from skills.test_generator import TestGeneratorSkill
from skills.base import SkillValidationError, SkillExecutionError


def test_initialization():
    """Test Test Generator skill initialization."""
    print("\n" + "=" * 70)
    print("TEST: Skill Initialization")
    print("=" * 70)

    skill = TestGeneratorSkill()

    assert skill.name == "test_generator"
    assert skill.description == "Automatically generate unit tests for Python code"
    assert skill.version == "1.0.0"
    assert skill.enabled is True

    print("✓ Skill initialized successfully")
    print(f"  Name: {skill.name}")
    print(f"  Description: {skill.description}")
    print(f"  Version: {skill.version}")


def test_input_validation():
    """Test input validation."""
    print("\n" + "=" * 70)
    print("TEST: Input Validation")
    print("=" * 70)

    skill = TestGeneratorSkill()

    # Test missing code
    try:
        skill.execute({"framework": "pytest"})
        assert False, "Should raise validation error"
    except SkillValidationError as e:
        print("✓ Correctly rejected missing code")
        print(f"  Error: {str(e)}")

    # Test invalid framework
    try:
        skill.execute({"code": "def foo(): pass", "framework": "invalid"})
        assert False, "Should raise validation error"
    except SkillValidationError as e:
        print("✓ Correctly rejected invalid framework")
        print(f"  Error: {str(e)}")

    # Test invalid coverage level
    try:
        skill.execute({"code": "def foo(): pass", "coverage_level": "invalid"})
        assert False, "Should raise validation error"
    except SkillValidationError as e:
        print("✓ Correctly rejected invalid coverage level")
        print(f"  Error: {str(e)}")

    # Test empty code
    try:
        skill.execute({"code": "   "})
        assert False, "Should raise validation error"
    except SkillValidationError as e:
        print("✓ Correctly rejected empty code")
        print(f"  Error: {str(e)}")

    # Test non-string code
    try:
        skill.execute({"code": 123})
        assert False, "Should raise validation error"
    except SkillValidationError as e:
        print("✓ Correctly rejected non-string code")
        print(f"  Error: {str(e)}")


def test_simple_function():
    """Test generation for a simple function."""
    print("\n" + "=" * 70)
    print("TEST: Simple Function")
    print("=" * 70)

    code = """
def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code})

    assert result["success"] is True
    assert result["test_count"] >= 1
    assert "def test_add_happy_path" in result["test_code"]
    assert "import pytest" in result["test_code"]
    assert len(result["test_cases"]) >= 1
    assert "pytest" in result["imports_needed"]

    print("✓ Generated tests for simple function")
    print(f"  Test count: {result['test_count']}")
    print(f"  Coverage estimate: {result['coverage_estimate']}")
    print(f"  Test cases: {[tc['name'] for tc in result['test_cases']]}")


def test_function_with_edge_cases():
    """Test generation for function with edge cases."""
    print("\n" + "=" * 70)
    print("TEST: Function with Edge Cases")
    print("=" * 70)

    code = """
def process_list(items):
    \"\"\"Process a list of items.\"\"\"
    if not items:
        return []
    return [x * 2 for x in items]
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "coverage_level": "standard"})

    assert result["success"] is True
    assert result["test_count"] >= 3  # happy path + edge cases
    assert any("edge_case" in tc["type"] for tc in result["test_cases"])
    assert "test_process_list_with_none" in result["test_code"] or "None" in result["test_code"]

    print("✓ Generated edge case tests")
    print(f"  Test count: {result['test_count']}")
    print(f"  Test types: {set(tc['type'] for tc in result['test_cases'])}")


def test_function_with_exceptions():
    """Test generation for function that raises exceptions."""
    print("\n" + "=" * 70)
    print("TEST: Function with Exceptions")
    print("=" * 70)

    code = """
def divide(a, b):
    \"\"\"Divide two numbers.\"\"\"
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "coverage_level": "standard"})

    assert result["success"] is True
    assert any("error_case" in tc["type"] for tc in result["test_cases"])
    assert "ValueError" in result["test_code"]

    print("✓ Generated exception tests")
    print(f"  Test count: {result['test_count']}")
    print(f"  Error cases: {[tc['name'] for tc in result['test_cases'] if tc['type'] == 'error_case']}")


def test_class_with_methods():
    """Test generation for class with methods."""
    print("\n" + "=" * 70)
    print("TEST: Class with Methods")
    print("=" * 70)

    code = """
class Calculator:
    \"\"\"Simple calculator class.\"\"\"

    def __init__(self, initial_value=0):
        self.value = initial_value

    def add(self, x):
        \"\"\"Add to current value.\"\"\"
        self.value += x
        return self.value

    def reset(self):
        \"\"\"Reset to zero.\"\"\"
        self.value = 0
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code})

    assert result["success"] is True
    assert result["test_count"] >= 3  # init + add + reset
    assert "test_calculator_initialization" in result["test_code"]
    assert "Calculator" in result["test_code"]

    print("✓ Generated class tests")
    print(f"  Test count: {result['test_count']}")
    print(f"  Test cases: {[tc['name'] for tc in result['test_cases']]}")


def test_function_with_dependencies():
    """Test generation with mocked dependencies."""
    print("\n" + "=" * 70)
    print("TEST: Function with Dependencies")
    print("=" * 70)

    code = """
import requests

def fetch_data(url):
    \"\"\"Fetch data from URL.\"\"\"
    response = requests.get(url)
    return response.json()
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "coverage_level": "comprehensive"})

    assert result["success"] is True
    # Should detect requests as external dependency
    assert "requests" in str(result["test_code"]).lower() or "mock" in str(result["test_code"]).lower()

    print("✓ Generated tests with dependency detection")
    print(f"  Test count: {result['test_count']}")
    print(f"  Imports needed: {result['imports_needed']}")


def test_async_function():
    """Test generation for async function."""
    print("\n" + "=" * 70)
    print("TEST: Async Function")
    print("=" * 70)

    code = """
async def async_fetch(url):
    \"\"\"Async fetch data.\"\"\"
    # Simulated async operation
    return {"data": "test"}
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code})

    assert result["success"] is True
    assert "async" in result["notes"].lower() or "asyncio" in str(result["imports_needed"]).lower()

    print("✓ Generated async function tests")
    print(f"  Test count: {result['test_count']}")
    print(f"  Notes: {result['notes']}")


def test_pytest_framework():
    """Test pytest framework generation."""
    print("\n" + "=" * 70)
    print("TEST: Pytest Framework")
    print("=" * 70)

    code = """
def hello(name):
    return f"Hello, {name}"
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "framework": "pytest"})

    assert result["success"] is True
    assert "import pytest" in result["test_code"]
    assert "def test_" in result["test_code"]
    assert "class Test" not in result["test_code"]  # pytest style, not unittest

    print("✓ Generated pytest-style tests")
    print(f"  Framework: pytest")
    print(f"  Test count: {result['test_count']}")


def test_unittest_framework():
    """Test unittest framework generation."""
    print("\n" + "=" * 70)
    print("TEST: Unittest Framework")
    print("=" * 70)

    code = """
def hello(name):
    return f"Hello, {name}"
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "framework": "unittest"})

    assert result["success"] is True
    assert "import unittest" in result["test_code"]
    assert "class Test" in result["test_code"]  # unittest style
    assert "unittest.main()" in result["test_code"]

    print("✓ Generated unittest-style tests")
    print(f"  Framework: unittest")
    print(f"  Test count: {result['test_count']}")


def test_basic_coverage_level():
    """Test basic coverage level."""
    print("\n" + "=" * 70)
    print("TEST: Basic Coverage Level")
    print("=" * 70)

    code = """
def process(data):
    if not data:
        raise ValueError("No data")
    return data.upper()
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "coverage_level": "basic"})

    assert result["success"] is True
    # Basic coverage should have fewer tests
    basic_count = result["test_count"]

    print(f"✓ Generated basic coverage tests")
    print(f"  Test count: {basic_count}")
    print(f"  Coverage estimate: {result['coverage_estimate']}")


def test_standard_coverage_level():
    """Test standard coverage level."""
    print("\n" + "=" * 70)
    print("TEST: Standard Coverage Level")
    print("=" * 70)

    code = """
def process(data):
    if not data:
        raise ValueError("No data")
    return data.upper()
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "coverage_level": "standard"})

    assert result["success"] is True
    # Standard should include edge cases and errors
    assert any("edge_case" in tc["type"] for tc in result["test_cases"])

    print(f"✓ Generated standard coverage tests")
    print(f"  Test count: {result['test_count']}")
    print(f"  Coverage estimate: {result['coverage_estimate']}")


def test_comprehensive_coverage_level():
    """Test comprehensive coverage level."""
    print("\n" + "=" * 70)
    print("TEST: Comprehensive Coverage Level")
    print("=" * 70)

    code = """
import requests

def fetch_and_process(url):
    if not url:
        raise ValueError("URL required")
    response = requests.get(url)
    return response.json()
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "coverage_level": "comprehensive"})

    assert result["success"] is True
    # Comprehensive should have the most tests
    assert result["test_count"] >= 3

    print(f"✓ Generated comprehensive coverage tests")
    print(f"  Test count: {result['test_count']}")
    print(f"  Coverage estimate: {result['coverage_estimate']}")
    print(f"  Imports needed: {result['imports_needed']}")


def test_function_with_docstring_examples():
    """Test generation for function with docstring examples."""
    print("\n" + "=" * 70)
    print("TEST: Function with Docstring Examples")
    print("=" * 70)

    code = """
def multiply(a, b):
    \"\"\"
    Multiply two numbers.

    Examples:
        >>> multiply(2, 3)
        6
        >>> multiply(0, 5)
        0
    \"\"\"
    return a * b
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code})

    assert result["success"] is True
    # Should generate tests even with examples
    assert result["test_count"] >= 1

    print("✓ Generated tests for documented function")
    print(f"  Test count: {result['test_count']}")


def test_complex_function():
    """Test generation for complex function."""
    print("\n" + "=" * 70)
    print("TEST: Complex Function")
    print("=" * 70)

    code = """
def complex_process(data, threshold=10, validate=True, transform=None):
    \"\"\"Complex function with many parameters.\"\"\"
    if validate and not data:
        raise ValueError("Invalid data")

    result = []
    for item in data:
        if item > threshold:
            if transform:
                result.append(transform(item))
            else:
                result.append(item)
    return result
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "coverage_level": "comprehensive"})

    assert result["success"] is True
    # Should note the complexity
    assert "parameter" in result["notes"].lower() or result["test_count"] >= 3

    print("✓ Generated tests for complex function")
    print(f"  Test count: {result['test_count']}")
    print(f"  Notes: {result['notes']}")


def test_enable_disable():
    """Test enable/disable functionality."""
    print("\n" + "=" * 70)
    print("TEST: Enable/Disable")
    print("=" * 70)

    skill = TestGeneratorSkill()
    code = """
def simple():
    return True
"""

    # Disable skill
    skill.disable()
    assert skill.enabled is False

    try:
        skill.execute({"code": code})
        assert False, "Should raise error when disabled"
    except SkillExecutionError as e:
        print("✓ Correctly blocked execution when disabled")
        print(f"  Error: {str(e)}")

    # Re-enable skill
    skill.enable()
    assert skill.enabled is True

    result = skill.execute({"code": code})
    assert result["success"] is True

    print("✓ Successfully executed after re-enabling")


def test_syntax_error_handling():
    """Test handling of syntax errors."""
    print("\n" + "=" * 70)
    print("TEST: Syntax Error Handling")
    print("=" * 70)

    code = """
def broken(
    # Missing closing parenthesis and colon
    return True
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code})

    assert result["success"] is False
    assert "error" in result
    assert "syntax" in result["error"].lower()

    print("✓ Correctly handled syntax error")
    print(f"  Error: {result['error']}")


def test_empty_code_structure():
    """Test with code that has no functions or classes."""
    print("\n" + "=" * 70)
    print("TEST: Empty Code Structure")
    print("=" * 70)

    code = """
# Just a comment
x = 10
y = 20
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code})

    assert result["success"] is True
    # Should return empty or minimal tests
    assert result["test_count"] == 0
    assert result["coverage_estimate"] == "0%"

    print("✓ Handled code with no testable structures")
    print(f"  Test count: {result['test_count']}")
    print(f"  Coverage: {result['coverage_estimate']}")


def test_multiple_functions():
    """Test generation for multiple functions."""
    print("\n" + "=" * 70)
    print("TEST: Multiple Functions")
    print("=" * 70)

    code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "coverage_level": "standard"})

    assert result["success"] is True
    # Should have tests for all three functions
    assert result["test_count"] >= 9  # 3 functions × 3 tests each (happy + 2 edge cases)
    assert "test_add" in result["test_code"]
    assert "test_subtract" in result["test_code"]
    assert "test_multiply" in result["test_code"]

    print("✓ Generated tests for multiple functions")
    print(f"  Test count: {result['test_count']}")
    print(f"  Functions tested: add, subtract, multiply")


def test_class_with_inheritance():
    """Test generation for class with inheritance."""
    print("\n" + "=" * 70)
    print("TEST: Class with Inheritance")
    print("=" * 70)

    code = """
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code})

    assert result["success"] is True
    assert "inheritance" in result["notes"].lower() or "polymorphism" in result["notes"].lower()

    print("✓ Generated tests for inherited classes")
    print(f"  Test count: {result['test_count']}")
    print(f"  Notes: {result['notes']}")


def test_decorated_function():
    """Test generation for decorated function."""
    print("\n" + "=" * 70)
    print("TEST: Decorated Function")
    print("=" * 70)

    code = """
def decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@decorator
def decorated_function(x):
    return x * 2
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code})

    assert result["success"] is True
    # Should generate tests for both functions
    assert result["test_count"] >= 2

    print("✓ Generated tests for decorated function")
    print(f"  Test count: {result['test_count']}")


def test_coverage_estimates():
    """Test coverage estimation accuracy."""
    print("\n" + "=" * 70)
    print("TEST: Coverage Estimates")
    print("=" * 70)

    code = """
def simple():
    return True
"""

    skill = TestGeneratorSkill()

    # Test different coverage levels
    basic = skill.execute({"code": code, "coverage_level": "basic"})
    standard = skill.execute({"code": code, "coverage_level": "standard"})
    comprehensive = skill.execute({"code": code, "coverage_level": "comprehensive"})

    # Extract percentages
    basic_pct = int(basic["coverage_estimate"].rstrip("%"))
    standard_pct = int(standard["coverage_estimate"].rstrip("%"))
    comprehensive_pct = int(comprehensive["coverage_estimate"].rstrip("%"))

    # Comprehensive should be higher than basic
    assert comprehensive_pct >= basic_pct

    print("✓ Coverage estimates vary by level")
    print(f"  Basic: {basic['coverage_estimate']}")
    print(f"  Standard: {standard['coverage_estimate']}")
    print(f"  Comprehensive: {comprehensive['coverage_estimate']}")


def test_test_case_metadata():
    """Test that test case metadata is complete."""
    print("\n" + "=" * 70)
    print("TEST: Test Case Metadata")
    print("=" * 70)

    code = """
def process(data):
    if not data:
        raise ValueError("No data")
    return data
"""

    skill = TestGeneratorSkill()
    result = skill.execute({"code": code, "coverage_level": "standard"})

    assert result["success"] is True

    # Check each test case has required fields
    for tc in result["test_cases"]:
        assert "name" in tc
        assert "description" in tc
        assert "type" in tc
        assert tc["type"] in ["happy_path", "edge_case", "error_case", "integration"]

    print("✓ All test cases have complete metadata")
    print(f"  Test cases:")
    for tc in result["test_cases"]:
        print(f"    - {tc['name']} ({tc['type']})")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING TEST GENERATOR SKILL TESTS")
    print("=" * 70)

    tests = [
        ("Initialization", test_initialization),
        ("Input Validation", test_input_validation),
        ("Simple Function", test_simple_function),
        ("Function with Edge Cases", test_function_with_edge_cases),
        ("Function with Exceptions", test_function_with_exceptions),
        ("Class with Methods", test_class_with_methods),
        ("Function with Dependencies", test_function_with_dependencies),
        ("Async Function", test_async_function),
        ("Pytest Framework", test_pytest_framework),
        ("Unittest Framework", test_unittest_framework),
        ("Basic Coverage Level", test_basic_coverage_level),
        ("Standard Coverage Level", test_standard_coverage_level),
        ("Comprehensive Coverage Level", test_comprehensive_coverage_level),
        ("Function with Docstring Examples", test_function_with_docstring_examples),
        ("Complex Function", test_complex_function),
        ("Enable/Disable", test_enable_disable),
        ("Syntax Error Handling", test_syntax_error_handling),
        ("Empty Code Structure", test_empty_code_structure),
        ("Multiple Functions", test_multiple_functions),
        ("Class with Inheritance", test_class_with_inheritance),
        ("Decorated Function", test_decorated_function),
        ("Coverage Estimates", test_coverage_estimates),
        ("Test Case Metadata", test_test_case_metadata),
    ]

    passed = 0
    failed = 0
    errors = []

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append(f"{test_name}: {str(e)}")
            print(f"\n✗ FAILED: {test_name}")
            print(f"  Error: {str(e)}")
        except Exception as e:
            failed += 1
            errors.append(f"{test_name}: {str(e)}")
            print(f"\n✗ ERROR: {test_name}")
            print(f"  Error: {str(e)}")

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if errors:
        print("\nFailed tests:")
        for error in errors:
            print(f"  ✗ {error}")

    if failed == 0:
        print("\n" + "=" * 70)
        print("✅ ALL TEST GENERATOR SKILL TESTS PASSED!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print(f"❌ {failed} TEST(S) FAILED")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
